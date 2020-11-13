"""
To hook all the different changes to our api!
"""
from eve.methods.patch import patch_internal
from eve.methods.get import get_internal, getitem_internal
from datetime import datetime, timezone
from operator import itemgetter
from dateutil import tz
from dateutil import parser
from flask import Response, abort, current_app as app
import json

from dateutil.parser import parse as date_parse

from ext.auth.clients import LUNGO_SIO_TOKEN
from ext.app.decorators import async, debounce
import time
import socketio

# import dateutil.parser


RESOURCE_PERSONS_PROCESS = 'persons_process'
RESOURCE_FUNCTIONS_PROCESS = 'functions_process'
RESOURCE_LICENSES_PROCESS = 'licenses_process'
RESOURCE_COMPETENCES_PROCESS = 'competences_process'
RESOURCE_ORGANIZATIONS_PROCESS = 'organizations_process'
RESOURCE_PAYMENTS_PROCESS = 'payments_process'
RESOURCE_MERGED_FROM = 'persons_merged_from'


NLF_ORG_STRUCTURE = {
    'fallskjerm': {'activity': 109, 'org_id': 90972},
    'mikrofly': {'activity': 237, 'org_id': 203030},
    'motorfly': {'activity': 238, 'org_id': 203025},
    'seilfly': {'activity': 111, 'org_id': 90968},
    'modellfly': {'activity': 236, 'org_id': 203027},
    'ballong': {'activity': 235, 'org_id': 203026},
    'hps': {'activity': 110, 'org_id': 90969},
}

LOCAL_TIMEZONE = "Europe/Oslo"  # UTC
tz_utc = tz.gettz('UTC')
tz_local = tz.gettz(LOCAL_TIMEZONE)


@debounce(10)
@async
def broadcast(change_data):
    try:
        sio = socketio.Client()
        sio.connect('http://localhost:7000?token={}'.format(LUNGO_SIO_TOKEN))
        sio.emit('broadcast_change', change_data)
        time.sleep(0.1)
        sio.disconnect()
    except Exception as e:
        pass


def after_get_persons(response):
    if '_merged_to' in response:
        headers = {
            'Location': '/api/v1/persons/{}'.format(response.get('_merged_to', 0)),
        }
        return abort(
            Response(
                response=None,
                status=301,
                headers=headers
            )
        )


def assign_lookup(resource, request, lookup):
    """If lookup then we do add this"""
    if app.auth.resource_lookup is not None:
        for key, val in app.auth.resource_lookup.items():
            lookup[key] = val


def _get_end_of_year():
    return datetime(datetime.utcnow().year, 12, 31, 23, 59, 59, 999999).replace(tzinfo=tz_utc)


def _get_end_of_january():
    """End of jan next year"""
    return datetime(datetime.utcnow().year + 1, 1, 31, 23, 59, 59, 999999).replace(tzinfo=tz_utc)


def _fix_naive(date_time):
    if date_time is not None:
        if isinstance(date_time, str):
            try:
                date_time = parser.parse(date_time)
            except:
                date_time = None

    if isinstance(date_time, datetime):
        if date_time.tzinfo is None or date_time.tzinfo.utcoffset(date_time) is None:
            """self.org_created is naive, no timezone we assume UTC"""
            date_time = date_time.replace(tzinfo=tz_utc)

    return date_time


def _get_now():
    return datetime.utcnow().replace(tzinfo=tz_utc)


def _get_person(person_id) -> dict:
    """Get person from persons internal

    :param person_id: Person id
    :type person_id: int
    :return org: Returns the person given
    :rtype: dict
    """
    if person_id is not None:

        person, _, _, status, _ = get_internal('persons', **{'id': person_id})

        if status == 200:
            if '_items' in person and len(person['_items']) == 1:
                return person['_items'][0]

    return {}


def _compare_list_of_dicts(l1, l2, dict_id='id') -> bool:
    """Sorts lists then compares on the given id in the dicts
    :param l1: list of dicts
    :type l1: list(dict)
    :param l2: list of dicts
    :type l2: list(dict)
    :param dict_id: The id for the dicts
    :type dict_id: any
    :return: True if difference, False if not or can't decide
    """
    if len(l1) != len(l2):
        return True

    try:
        list_1, list_2 = [sorted(l, key=itemgetter(dict_id)) for l in (l1, l2)]
        pairs = zip(list_1, list_2)
        if any(x != y for x, y in pairs):
            return True
        else:
            return False  # They are equal
    except:
        return True  # We do not know if difference


def _compare_list_of_dicts_no_id(l1, l2):
    return [d for d in l1 if d not in l2] == []


def _compare_lists(l1, l2) -> bool:
    """Just compare set(list)
    :param l1: list
    :param l2: list
    :return: True if difference, False if """
    return set(l1) != set(l2)


def _get_org(org_id) -> dict:
    """Get org from organizations internal

    :param org_id: Organization id
    :type org_id: int
    :return org: Returns the organization
    :rtype: dict
    """

    org, _, _, status, _ = get_internal('organizations', **{'id': org_id})

    if status == 200:
        if '_items' in org and len(org['_items']) == 1:
            return org['_items'][0]

    return {}


def _get_functions_types(type_id) -> dict:
    """Get org from organizations internal

    :param org_id: Organization id
    :type org_id: int
    :return org: Returns the organization
    :rtype: dict
    """

    function_type, _, _, status, _ = get_internal('functions_types', **{'id': type_id})

    if status == 200:
        if '_items' in function_type and len(function_type['_items']) == 1:
            return function_type['_items'][0]

    return {}


def on_function_post(items) -> None:
    """On every function change, let's update person's functions.

    Function of type ``10000000`` is club membership and this implicates both clubs and activities

    Other function types are updated in a list

    :param items: the function object to be inserted or replaced

    @TODO can "has_paid_membership": false | true be of use?
    """

    for response in items:
        on_function_put(response)


def on_function_put(response, original=None) -> None:
    """
    :param response: database object
    :return: None
    """
    org = None
    person = _get_person(response.get('person_id', None))

    # Expiry date
    expiry = response.get('to_date', None)
    if expiry is not None:
        expiry = _fix_naive(expiry)

    if '_id' in person:

        # Club member! has_paid_membership?
        memberships = person.get('memberships', []).copy()
        clubs = person.get('clubs', []).copy()
        activities = person.get('activities', []).copy()

        # All memberships
        if response.get('type_id', 0) == 10000000:

            # Set expiry to end year
            if expiry is None:
                expiry = _get_end_of_january()
                expiry = _fix_naive(expiry)

            # Always get org
            org = _get_org(response['active_in_org_id'])

            # Groups = clubs
            if response['is_deleted'] is False \
                    and response['is_passive'] is False \
                    and expiry is not None and expiry > _get_now():

                clubs.append(response['active_in_org_id'])

                if org.get('type_id', 0) == 14:

                    for c in org.get('_up', []):
                        if c['type'] == 6:
                            memberships.append({
                                'id': response['id'],
                                'club': c['id'],
                                'discipline': response['active_in_org_id'],
                                'activity': org.get('main_activity', {}).get('id', 27),
                                'from_date': response.get('from_date', datetime.utcnow())
                            })

            else:
                try:
                    memberships = [x for x in memberships if x['id'] != response['id']]
                    clubs.remove(response['active_in_org_id'])
                except ValueError:
                    pass
                except Exception as e:
                    pass

            # Keep clubs
            clubs = list(set(clubs))

            # Activities follows memberships
            activities = [v['activity'] for v in memberships]
            activities.append(27)
            activities = list(set(activities))

        # The rest of the functions
        # Functions ex and including 1000000
        # Considers expiry date, if None then still valid
        functions = person.get('functions', []).copy()

        if expiry is not None:
            expiry = _fix_naive(expiry)
        else:
            expiry = _get_end_of_year()

        if expiry is None or expiry > _get_now():
            functions.append(response['id'])
        else:
            try:
                functions.remove(response.get('id'))
            except:
                pass

        functions = list(set(functions))

        # I If we have more than one memberships make unique by discipline
        if len(memberships) > 1:
            memberships = list({v['discipline']: v for v in memberships}.values())

        # Valid expiry?
        # f[:] = [d for d in f if d.get('expiry') >= _get_now()]

        lookup = {'_id': person['_id']}

        # Update person with new values IF anything is changed
        if _compare_lists(functions, person.get('functions', [])) is True or \
                _compare_lists(activities, person.get('activities', [])) is True or \
                memberships != person.get('memberships', []) or \
                _compare_lists(clubs, person.get('clubs', [])) is True:

            resp, _, _, status = patch_internal(RESOURCE_PERSONS_PROCESS,
                                                {'functions': functions,
                                                 'clubs': clubs,
                                                 'activities': activities,
                                                 'memberships': memberships},
                                                False,
                                                True,
                                                **lookup)

            if status != 200:
                app.logger.error('Patch returned {} for functions, activities, memberships'.format(status))

            else:
                # Fix payments
                # Always run
                # Get all duplicate person_id's via /persons/merged?aggregate={"$person_id": person['id']} ?? list(set(merged_from+person['id'])) sjekk at id er id!
                # persons/merged?aggregate={"$person_id":person['id']}
                merged_from_ids = []
                try:
                    merged_from, _, _, merged_status, _ = get_internal(RESOURCE_MERGED_FROM, **{"aggregate": {"$person_id": person['id']}})

                    if merged_status == 200:
                        merged_from_ids = merged_from.get('_items', []).get('merged_from', [])


                except Exception as e:
                    pass

                payments, _, _, p_status, _ = get_internal(RESOURCE_PAYMENTS_PROCESS,
                                                           **{
                                                               'person_id': {'$in': list(set([person['id']] + merged_from_ids))},
                                                               'org_id': {
                                                                   '$in': [x['club'] for x in memberships]
                                                               }
                                                              }
                                                           )
                if p_status == 200:
                    on_payment_after_post(payments.get('_items', []))

    # PURE RESPONSE
    # Update the function

    function_payload = {}

    # Type name
    if response.get('type_name', None) is None:

        function_type = _get_functions_types(response.get('type_id', 0))
        if len(function_type) > 0:
            type_name = function_type.get('name', None)

            if type_name is not None:
                function_payload['type_name'] = type_name

    # org id
    # Needs to be backwards compatible with active in org id
    if response.get('org_id', 0) == 0 and response.get('active_in_org_id', 0) > 0:
        function_payload['org_id'] = response['active_in_org_id']

    # Org type, always supply
    if response.get('org_type_id', 0) == 0:
        if org is None:
            org = _get_org(response['active_in_org_id'])

        # org_id
        if org.get('type_id', 0) > 0:
            function_payload['org_type_id'] = org.get('type_id')

    if len(function_payload) > 0:
        resp, _, _, status = patch_internal(RESOURCE_FUNCTIONS_PROCESS,
                                            function_payload,
                                            False,
                                            True,
                                            **{'_id': response.get('_id')})
        if status != 200:
            app.logger.error('Patch returned {} for function update type_name'.format(status))
            pass


def on_license_post(items):
    """pass"""

    for response in items:
        on_license_put(response)


def on_license_put(response, original=None):
    """pass"""

    expiry = response.get('period_to_date', None)  # dateutil.parser.parse(response.get('period_to_date', None))

    # Set expiry to end year
    if expiry is None:
        expiry = _get_end_of_year()

    expiry = _fix_naive(expiry)

    # Always get person
    person = _get_person(response.get('person_id', None))
    if '_id' in person:

        licenses = person.get('licenses', []).copy()

        # If valid expiry
        if expiry is None or expiry > _get_now():

            try:
                licenses.append({'id': response.get('id'),
                                 'status_id': response.get('status_id', 0),
                                 'status_date': response.get('status_date', None),
                                 'expiry': expiry,
                                 'type_id': response.get('type_id', None),
                                 'type_name': response.get('type_name', None)})

            except:
                pass

        # Unique
        licenses = list({v['id']: v for v in licenses}.values())

        # Valid expiry
        licenses[:] = [d for d in licenses if _fix_naive(d.get('expiry')) >= _get_now()]

        # Patch if difference
        if _compare_list_of_dicts(licenses, person.get('licenses', [])) is True:

            lookup = {'_id': person['_id']}
            resp, _, _, status = patch_internal(RESOURCE_PERSONS_PROCESS, {'licenses': licenses}, False, True, **lookup)
            if status != 200:
                app.logger.error('Patch returned {} for license'.format(status))
                pass


def on_competence_post(items):
    """Competence fields:

    passed bool
    valid_until datetime

    """
    for response in items:
        on_competence_put(response)


def on_competence_put(response, original=None):
    """"""

    if response.get('passed', False) is True:

        expiry = response.get('valid_until', None)

        # Set expiry to end year
        if expiry is None:
            expiry = _get_end_of_year()

        expiry = _fix_naive(expiry)

        person = _get_person(response.get('person_id', None))

        if '_id' in person:

            competence = person.get('competences', []).copy()

            # Add this competence?
            if expiry is not None and isinstance(expiry, datetime) and expiry >= _get_now():

                try:
                    competence.append({'id': response.get('id'),
                                       '_code': response.get('_code', None),
                                       'issuer': response.get('approved_by_person_id', None),
                                       'expiry': expiry,
                                       # 'paid': response.get('paid_date', None)
                                       })
                except:
                    pass

            # Always remove stale competences
            # Note that _code is for removing old competences, should be removed
            competence[:] = [d for d in competence if
                             _fix_naive(d.get('expiry')) >= _get_now() and d.get('_code', None) is not None]

            # Always unique by id
            competence = list({v['id']: v for v in competence}.values())

            # Patch if difference
            if _compare_list_of_dicts(competence, person.get('competence', [])) is True:
                lookup = {'_id': person['_id']}
                resp, _, _, status = patch_internal(RESOURCE_PERSONS_PROCESS, {'competences': competence}, False, True,
                                                    **lookup)
                if status != 200:
                    app.logger.error('Patch returned {} for competence'.format(status))
                    pass


def on_organizations_post(items):
    for item in items:
        on_organizations_put(item)


def on_organizations_put(response, original=None):
    # Only on NIF groups / NLF clubs
    if response.get('type_id', 0) == 6 or len(response.get('activities', [])) == 0:

        for v in response.get('_down'):
            if v.get('type') == 14:
                discipline = _get_org(v.get('id'))
                if 'activities' in discipline:
                    for a in discipline['activities']:
                        response['activities'].append(a)
                if 'main_activity' in discipline:
                    response['main_activity'] = discipline.get('main_activity')

        response['activities'] = list({v['id']: v for v in response['activities']}.values())

        lookup = {'_id': response['_id']}
        resp, _, _, status = patch_internal(RESOURCE_ORGANIZATIONS_PROCESS,
                                            {'activities': response['activities'],
                                             'main_activity': response['main_activity']},
                                            False, True, **lookup)
        if status != 200:
            app.logger.error('Patch returned {} for license'.format(status))
            pass

    # Broadcast to all activities and own org
    broadcast({'entity': 'organization',
               'entity_id': response['id'],
               'orgs': list(set([response['id']] + [x['id'] for x in response.get('activities', [])]))
               })


######## PAYMENTS ###########

def _get_pmt_group_from_club(org_id):
    lookup = {'parent_id': org_id, 'type_id': 6, 'is_active': True}
    group, _, _, status_code = getitem_internal(RESOURCE_ORGANIZATIONS_PROCESS, **lookup)
    if status_code == 200:
        return group.get('id', org_id)

    return org_id


def _get_pmt_year(text):
    try:
        return date_parse(text, fuzzy=True).year
    except:
        # Error could not extract a year use todays year!
        pass

    return datetime.now().year


def _get_pmt_type(text):
    if 'støttemedlem' in text.lower():
        return 'Støttemedlem'
    elif 'ufør' in text.lower():
        return 'Ufør'
    elif 'modellmedlem' in text.lower():
        return 'Modellmedlem'
    elif 'æresmedlem' in text.lower():
        return 'Æresmedlem'
    elif 'Tandemmedlem' in text.lower():
        return 'Tandemmedlem'
    elif 'kroppsfyker' in text.lower():
        return 'Kroppsfykermedlem'
    elif 'familie' in text.lower():
        return 'Familiemedlem'

    return None


def _get_pmt_activity(text):
    if 'modellfly' in text.lower():
        return NLF_ORG_STRUCTURE['modellfly']['activity']
    elif 'mikrofly' in text.lower():
        return NLF_ORG_STRUCTURE['mikrofly']['activity']
    elif 'sportsfly' in text.lower():
        return NLF_ORG_STRUCTURE['mikrofly']['activity']
    elif 'fallskjerm' in text.lower():
        return NLF_ORG_STRUCTURE['fallskjerm']['activity']
    elif 'motorfly' in text.lower():
        return NLF_ORG_STRUCTURE['motorfly']['activity']
    elif 'ballong' in text.lower():
        return NLF_ORG_STRUCTURE['ballong']['activity']
    elif 'seilfly' in text.lower():
        return NLF_ORG_STRUCTURE['seilfly']['activity']
    elif 'speedglider' in text.lower():
        return NLF_ORG_STRUCTURE['hps']['activity']

    return 27


def _get_pmt_person_age_membership(person):
    membership = 'Senior'
    try:
        age = datetime.now().year - person.get('birth_date').year - 1
    except:
        age = datetime.now().year - date_parse(person.get('birth_date')).year - 1

    if age <= 12:
        membership = 'Barn'
    elif age > 12 and age <= 18:
        membership = 'Ungdom'
    elif age > 18 and age <= 25:
        membership = 'Junior'
    elif age > 25 and age <= 66:
        membership = 'Senior'
    elif age > 66:
        membership = 'Pensjonist'

    return membership


def _get_org_id_and_activity(club_id):
    # Get org from org id (5)
    # return org_id and main_activity.id
    org_id = 376
    activity = 27
    return org_id, activity


def _get_pmt(payment):
    text = payment.get('product_name', '')
    year = _get_pmt_year(text)

    activity = _get_pmt_activity(text)
    org_id = payment['org_id']  # or 376  # The real org_id
    product_type = None
    product_type_exception = None
    product_type_id = payment['product_type_id']

    if product_type_id == 20:
        # Forbund
        product_type = 'Forbundskontigent'
        payment['product_type'] = product_type
        product_type_exception = _get_pmt_type(text)
        pass
    elif product_type_id == 21:
        # medlemskap klubb
        product_type = 'Klubbkontigent'
        payment['product_type'] = product_type
        org_id = _get_pmt_group_from_club(payment['org_id'])
        product_type_exception = _get_pmt_type(text)
    elif product_type_id == 22:
        # Seksjon
        activity = _get_pmt_activity(text)
        product_type = 'Seksjonskontigent'
        payment['product_type'] = product_type
        product_type_exception = _get_pmt_type(text)
    elif product_type_id == 23:
        payment['product_type'] = 'magazine'
        # Magazines
        if 'fritt' in text.lower():
            product_type = 'Fritt Fall'
            activity = 109
        elif 'flynytt' in text.lower():
            product_type = 'Flynytt'
            activity = 27
        elif 'gliding' in text.lower():
            product_type = 'Nordic Gliding'
            activity = 111
        elif 'modell' in text.lower():
            product_type = 'Modellinformasjon'
            activity = 236
        elif 'flukt' in text.lower():
            product_type = 'Fri Flukt'
            activity = 110

        # self.value['product_name'] = product_name
        # product_type = 'magazine' # We know that since 23

        # Magasin
        pass
    else:
        # What just happened?
        pass

    return org_id, \
           activity, \
           product_type, \
           product_type_exception, \
           product_type_id, \
           year, \
           payment['amount'], \
           payment['paid_date']


### PAYMENTS HOOKS ###

def on_payment_before_post(items):
    # club -> memberships!
    for k, item in enumerate(items):
        if item['product_type_id'] == 21:  # Only clubs
            items[k]['org_id'] = _get_pmt_group_from_club(items[k]['org_id'])


def on_payment_after_post(items):
    for item in items:
        on_payment_after_put(item)


def on_payment_before_put(item, orginal=None):
    if item['product_type_id'] == 21:  # Only clubs
        item['org_id'] = _get_pmt_group_from_club(item['org_id'])


def on_payment_after_put(item, orginal=None):
    """Every time some payments comes through, fix person"""

    # Only this year?
    if _get_pmt_year(item['product_name']) >= datetime.now().year:

        # Gets person
        person, _, _, status_code = getitem_internal(RESOURCE_PERSONS_PROCESS, **{'id': item['person_id']})

        if status_code == 200:

            current_year = datetime.now().year

            # Change to group org_id
            type_id = item.get('product_type_id', None)
            text = item['product_name']

            try:
                item['amount'] = float(item['amount'])
                item['amount_at_payment_time'] = float(item['amount_at_payment_time'])
            except:
                pass

            # Is this a refund?
            if item['amount_at_payment_time'] + item['amount'] == 0:
                refund = True
            else:
                refund = False

            # Build and insert payments types
            #
            if type_id == 21:  # Club Membership
                # club -> fix memberships!
                org_id = item.get('org_id')  # _get_pmt_group_from_club(item.get('org_id'))
                changes = False
                for k, v in enumerate(person.get('memberships', [])):
                    if v['club'] == org_id:

                        if refund is True:
                            person['memberships'][k].pop('payment', None)
                        else:
                            person['memberships'][k]['payment'] = {
                                'id': item['id'],
                                'year': _get_pmt_year(item['product_name']),
                                'exception': _get_pmt_type(text),
                                'type': _get_pmt_person_age_membership(person),
                                'amount': item['amount'],
                                'paid': item['paid_date']
                            }
                        changes = True

                if changes is True:
                    resp, _, _, status = patch_internal(RESOURCE_PERSONS_PROCESS,
                                                        {'memberships': person['memberships']},
                                                        False,
                                                        True,
                                                        **{'_id': person['_id']})
                    if status != 200:
                        app.logger.exception(
                            'Error memberships, org {} for payment id {}'.format(item['org_id'], item['id']))





            elif type_id == 23:  # Magazines

                magazines = person.get('magazines', [])

                if refund is True:
                    magazines = [x for x in magazines if x.get('id', item['id']) != item['id']]
                else:
                    year = _get_pmt_year(text)
                    # Magazines
                    if 'fritt' in text.lower():
                        name = 'Fritt Fall'
                    elif 'flynytt' in text.lower():
                        name = 'Flynytt'
                    elif 'gliding' in text.lower():
                        name = 'Nordic Gliding'
                    elif 'modell' in text.lower():
                        name = 'Modellinformasjon'
                    elif 'flukt' in text.lower():
                        name = 'Fri Flukt'

                    magazines.append(
                        {
                            'id': item['id'],
                            'name': name,
                            'year': year,
                            # 'paid': item['paid_date'],
                            # 'amount': item['amount']
                        }
                    )

                # Remove old ones
                magazines = [x for x in magazines if x['year'] >= datetime.now().year and 'id' in x]

                # Unique list of dicts
                magazines = list({v['id']: v for v in magazines}.values())
                # magazines = [dict(p) for p in set(tuple(i.items()) for i in magazines)]

                resp, _, _, status = patch_internal(
                    RESOURCE_PERSONS_PROCESS,
                    {'magazines': magazines},
                    False,
                    True,
                    **{'_id': person['_id']}
                )

                if status != 200:
                    app.logger.exception('Error {} for payment id {}'.format(name, item['id']))

            elif type_id in [20, 22]:  # Federation/section
                # Seksjonsavgifter
                # memberships org_id fra section..
                fed = person.get('federation', [])

                if refund is True:
                    fed = [x for x in fed if x.get('id', item['id']) != item['id']]
                else:
                    if type_id == 22:
                        product_type = 'Seksjonskontigent'
                        activity = _get_pmt_activity(text)
                    else:
                        product_type = 'Forbundskontigent'
                        activity = 27

                    fed.append({
                        'id': item['id'],
                        'name': product_type,
                        'activity': activity,
                        'year': _get_pmt_year(text),
                        'exception': _get_pmt_type(text),
                        'type': _get_pmt_person_age_membership(person),
                        'paid': item['paid_date'],
                        'amount': item['amount'],
                    })

                # Remove old ones
                fed = [x for x in fed if x['year'] >= datetime.now().year and 'id' in x]

                # Unique
                fed = list({v['id']: v for v in fed}.values())
                # fed = [dict(p) for p in set(tuple(i.items()) for i in fed)]

                resp, _, _, status = patch_internal(RESOURCE_PERSONS_PROCESS,
                                                    {'federation': fed},
                                                    False, True, **{'_id': person['_id']})
                if status != 200:
                    app.logger.exception('Error {} for payment id {}'.format(product_type, item['id']))


def on_person_after_post(items):
    for response in items:
        _update_person(response)


def on_person_before_put(item, original):
    # if original then use and not rebuild because
    # functions, competences, licenses, memberships and clubs, activities
    item['functions'] = original.get('functions', [])
    item['competences'] = original.get('competences', [])
    item['licenses'] = original.get('licenses', [])

    item['memberships'] = original.get('memberships', [])

    item['magazines'] = original.get('magazines', [])
    item['federation'] = original.get('federation', [])

    # @TODO remove - legacy
    item['clubs'] = original.get('clubs', [])
    item['activities'] = original.get('activities', [])


def on_person_after_put(item, original=None):
    _update_person(item)
    try:
        broadcast({'entity': 'person',
                   'entity_id': item['id'],
                   'orgs': list(set(
                       [x['activity'] for x in item['memberships']] +
                       [x['discipline'] for x in item['memberships']] +
                       [x['club'] for x in item['memberships']]
                   ))
                   })
    except Exception as e:
        app.logger.exception('Something did not work out!')


def _update_person(item):
    """Runs AFTER person replaced"""
    lookup = {'person_id': item['id']}

    competences, _, _, c_status, _ = get_internal(RESOURCE_COMPETENCES_PROCESS, **lookup)
    if c_status == 200:
        on_competence_post(competences.get('_items', []))

    licenses, _, _, l_status, _ = get_internal(RESOURCE_LICENSES_PROCESS, **lookup)
    if l_status == 200:
        on_license_post(licenses.get('_items', []))

    functions, _, _, f_status, _ = get_internal(RESOURCE_FUNCTIONS_PROCESS, **lookup)
    app.logger.debug('Functions\n{}'.format(functions))
    if f_status == 200:
        on_function_post(functions.get('_items', []))

    """ In functions for now!
    payments, _, _, p_status, _ = get_internal(RESOURCE_PAYMENTS_PROCESS, **lookup)
    app.logger.debug('Payments\n{}'.format(functions))
    if f_status == 200:
        on_payment_after_post(payments.get('_items', []))
    """

    try:
        # Need to get person return response, last_modified, etag, 200
        person, _, _, p_status = getitem_internal(RESOURCE_PERSONS_PROCESS, **{'id': item['id']})
        if p_status == 200:
            # Broadcast all
            broadcast({'entity': 'person',
                       'entity_id': item['id'],
                       'orgs': list(set(
                           [x['activity'] for x in person['memberships']] +
                           [x['discipline'] for x in person['memberships']] +
                           [x['club'] for x in person['memberships']]
                       ))
                       })
    except Exception as e:
        app.logger.exception('Error finishing off person')
