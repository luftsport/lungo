"""
To hook all the different changes to our api!
"""
from eve.methods.patch import patch_internal
from eve.methods.get import get_internal, getitem_internal
from datetime import datetime, timezone, UTC
from dateutil import tz
from dateutil import parser
from flask import Response, request as flask_request, abort, current_app as app, g
import json

from dateutil.parser import parse as date_parse

from ext.auth.clients import LUNGO_SIO_TOKEN
from ext.app.decorators import _async, debounce
import time
import socketio
from blueprints.fai import upsert_fai
from blueprints.nif import _register_flydrone
# import dateutil.parser
from ext.app.fids import get_fids

from ext.scf import FAI_SYNC

from ext.app.helpers import (
    _get_merged_from,
    _get_now,
    _get_org,
    _get_person,
    _get_functions_types,
    _get_end_of_year,
    _get_end_of_january,
    _compare_list_of_dicts,
    _compare_lists,
    _compare_list_of_dicts_no_id,
    _fix_naive
)

RESOURCE_PERSONS_PROCESS = 'persons_process'
RESOURCE_FUNCTIONS_PROCESS = 'functions_process'
RESOURCE_LICENSES_PROCESS = 'licenses_process'
RESOURCE_COMPETENCES_PROCESS = 'competences_process'
RESOURCE_ORGANIZATIONS_PROCESS = 'organizations_process'
RESOURCE_PAYMENTS_PROCESS = 'payments_process'
RESOURCE_MERGED_FROM = 'persons_merged_from'

# meta types which are considered "kompetanse"
COMPETENCE_META_TYPES = ['Kompetansedefinisjon']
COMPETENCE_ATTESTATION_TYPES = [66677325, 66677394, 66679452, 66679458]
"""
66667584 A-SPO - SPORTSLISENS [238]
66667674 M-SPO - SPORTSLISENS [27, 236]
66669579 U-SPO - SPORTSLISENS [27, 237]
66667695 NLF-S-SPO - SPORTSLISENS [27, 111]
66667588 NLF-B-SPO - SPORTSLISENS [27, 235]
66667720 NLF-U-SPO - Ikke i bruk [27, 237]
66667614 F-SPO - FAI SPORTING LICENCE [109]
66667663 H-SPO - NLF/HPS SPORTING LICENSE [110]
17: '-',
7: 'Aerobatics', 
9: 'Aeromodelling',
5: 'Aeromodelling and Spacemodelling',
21: 'Airships',
15: 'Amateur-built and Experimental Aircraft',
16: 'Astronautics',
1: 'Ballooning',
23: 'FPV Racing',
3: 'General Aviation',
2: 'Gliding',
13: 'Hang Gliding',
4: 'Hang Gliding and Paragliding',
20: 'Human Powered',
11: 'Microlights and Paramotors',
12: 'Motor Gliding',
6: 'Parachuting',
14: 'Paragliding',
10: 'Rotorcraft',
18: 'Space Modelling',
22: 'Special Projects',
19: 'UAV',
8: 'Universal'
"""
COMPETENCE_FAI_MAPPING = {
    66667584: 3,  # {'fai_type_id': 3 #'General Aviation'}, , , ]
    66667674: 5,
    66669579: 15,
    66667695: 2,
    66667588: 1,
    # 66667720:
    66667614: 6,
    66667663: 4
}
# If True, will always run the patch on person object and not verify changes exists
ALWAYS_PATCH = True

NLF_ORG_STRUCTURE = {
    'fallskjerm': {'activity': 109, 'org_id': 90972},
    'sportsfly': {'activity': 237, 'org_id': 203030},
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
@_async
def broadcast(change_data):
    try:
        sio = socketio.Client()
        sio.connect('http://localhost:7000?token={}'.format(LUNGO_SIO_TOKEN))
        sio.emit('broadcast_change', change_data)
        time.sleep(0.1)
        sio.disconnect()
    except Exception as e:
        pass


def _add_payment_for_next_year(memberships) -> list:
    """
    Adding missing payments when members pay for next year before year end
    :param memberships: list of membership dicts
    :return: memberships
    """
    _payment = {
        "id": 9999999999,
        "year": datetime.now(UTC).year + 1,
        "exception": None,
        "type": "Senior",
        "amount": 0.0,
        "paid": "{}-11-01T00:00:00.000000Z".format(datetime.now(UTC).year + 1)
    }
    try:
        _start_date = datetime(datetime.now(UTC).year, 11, 1).replace(tzinfo=tz_utc)

        for k, v in enumerate(memberships.copy()):
            if 'payment' not in v and 'from_date' in v:
                if v['from_date'] > _start_date:
                    memberships[k]['payment'] = _payment
    except Exception as e:
        app.logger.error('Error adding next years payment to memberships for person', e)

    return memberships


def _after_get_person(item):
    # Modify memberships add missing payments
    if len(item.get('memberships', [])) > 0:
        item['memberships'] = _add_payment_for_next_year(item.get('memberships', []))

    # Remove secret values
    if item.get('address', {}).get('secret_address', False) is True and g.whitelist_secret_contact.get('secret_address',
                                                                                                       False) is False:
        item['address'].pop('contact_id', None)
        item['address'].pop('contact_information_id', None)
        item['address'].pop('country_id', None)
        item['address'].pop('street_address', None)
        item['address'].pop('city', None)
        item['address'].pop('zip_code', None)
        item['address'].pop('location', None)

    if item.get('address', {}).get('secret_email', False) is True and g.whitelist_secret_contact.get('secret_email_all', False) is False:
        item['address']['email'] = []

        # Only primary email!
        if g.whitelist_secret_contact.get('secret_email', False) is False:
            item.pop('primary_email', None)

    if item.get('address', {}).get('secret_phone_home', False) is True and g.whitelist_secret_contact.get(
            'secret_phone_home', False) is False:
        item['address'].pop('phone_home', None)

    if item.get('address', {}).get('secret_phone_mobile', False) is True and g.whitelist_secret_contact.get(
            'secret_phone_mobile', False) is False:
        item['address'].pop('phone_mobile', None)

    if item.get('address', {}).get('secret_phone_work', False) is True and g.whitelist_secret_contact.get(
            'secret_phone_work', False) is False:
        item['address'].pop('phone_work', None)

    # Add fids if exists
    fids = get_fids(item['id'])
    if fids is not None:
        item['_fids'] = fids

    return item


def after_get_person(response):
    if '_merged_to' in response:
        # replace id with _merged_to
        headers = {'Location': '{}'.format(
            # Also, rewrites to https
            flask_request.url.replace('http:', 'https:').replace(str(response.get('id', 0)), str(response.get('_merged_to', 0)))
        )
        }
        #from flask import redirect
        #return redirect(headers['Location'], 301)
        return abort(
            Response(
                response=None,
                status=301,
                headers=headers
            )
        )

    return _after_get_person(response)


def after_get_persons(response):
    for key, item in enumerate(response.get('_items', []).copy()):
        response['_items'][key] = _after_get_person(response['_items'][key])


def assign_lookup(resource, request, lookup):
    """If lookup then we do add this"""
    if app.auth.resource_lookup is not None:
        for key, val in app.auth.resource_lookup.items():
            lookup[key] = val


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
    @TODO functions excluding memberships to same schema as competences
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
                                'from_date': response.get('from_date', datetime.now(UTC))
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
                # Fix payments all payments from merged person id's
                payments, _, _, p_status, _ = get_internal(RESOURCE_PAYMENTS_PROCESS,
                                                           **{
                                                               'person_id': {'$in': list(
                                                                   set([person['id']] + _get_merged_from(person['id'])))},
                                                               'org_id': {
                                                                   '$in': [x['club'] for x in memberships] + [
                                                                       v['org_id'] for k, v in NLF_ORG_STRUCTURE.items()
                                                                       if NLF_ORG_STRUCTURE[k]['activity'] in [
                                                                           val['activity'] for val in memberships]] + [
                                                                              376]
                                                               }
                                                           }
                                                           )
                if p_status == 200:

                    payments = payments.get('_items', [])
                    for p in payments:
                        p.update({'person_id': person['id']})
                    on_payment_after_post(payments)

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


def _get_competence_type_meta_type(type_id):
    try:
        competence_type, _, _, status, _ = get_internal('competences_types', **{'id': type_id})
        if status == 200:
            if '_items' in competence_type and len(competence_type['_items']) == 1:
                return competence_type['_items'][0]['meta_type']
    except Exception as e:
        pass

    return None


def on_competence_post(items):
    """Competence fields:

    passed bool
    valid_until datetime

    """
    for response in items:
        on_competence_put(response)


def on_competence_put(response, original=None):
    """"""
    # if response.get('passed', False) is True:

    passed = response.get('passed', False)
    expiry = response.get('valid_until', response.get('expiry', None))

    # Always require an expiry date!
    # if expiry is None:
    #    # expiry = _get_end_of_year()
    #    pass
    # else:
    expiry = _fix_naive(expiry)

    person = _get_person(response.get('person_id', None))

    if '_id' in person:

        competences = person.get('competences', []).copy()

        try:
            existing_competence = next(x for x in person.get('competences') if x['id'] == response.get('id'))
        except:
            existing_competence = {}

        # Always remove existing:
        competences = [x for x in competences if x['id'] != response['id']]

        competence_meta_type = _get_competence_type_meta_type(response.get('type_id', 0))

        # Add this competence if valid
        if competence_meta_type in COMPETENCE_META_TYPES and expiry is not None and isinstance(expiry, datetime) and expiry >= _get_now():

            _competence = {
                'id': response.get('id'),
                '_code': response.get('_code', response.get('title', 'Ukjent')),
                'type_id': response.get('type_id', 0),
                'issuer': response.get('approved_by_person_id', None),
                'expiry': expiry,
                # 'paid': response.get('paid_date', None)
            }

            # Handle Fai sporting codes
            try:
                if FAI_SYNC is True and response['type_id'] in list(COMPETENCE_FAI_MAPPING.keys()):

                    # True, r['idlicencee'], r['idlicence']
                    fai_status, fai_person_id, fai_license_id = upsert_fai(person,
                                                                           competence_id=response.get('id'),
                                                                           license_id=existing_competence.get('_fai', {}).get('license_id', None),
                                                                           discipline=COMPETENCE_FAI_MAPPING[response['type_id']])

                    if fai_status is True and fai_person_id is not None and fai_license_id is not None:
                        _competence['_fai'] = {
                            'license_id': fai_license_id,
                            'person_id': fai_person_id
                        }
            except Exception as e:
                app.logger.error('[FAI] error handling FAI competence')
                app.logger.error('[FAI] List of competencens:')
                try:
                    app.logger.error(str(COMPETENCE_FAI_MAPPING))
                except:
                    app.logger.error('Could not log list of competences')
                app.logger.error('[FAI] response:')
                try:
                    app.logger.error(str(response))
                except:
                    app.logger.error('Could not log response')
                app.logger.exception(e)

            # Append the competence to the existing competences
            try:
                # print('append')
                competences.append(_competence)
            except Exception as e:
                app.logger.error('[COMPETENCE]')
                app.logger.exception(e)

        # Always remove stale competences
        # Note that _code is for removing old competences, should be removed
        competences[:] = [d for d in competences if _fix_naive(d.get('expiry')) >= _get_now() and d.get('_code', None) is not None]
        # print(competences)
        # If competence valid_to is None # or competence not passed
        if expiry is None:  # or passed is False:
            # print('expiry is none')
            try:
                competences[:] = [d for d in competences if d.get('id', 0) != response.get('id')]
            except Exception as e:
                app.logger.exception('Error removing competence from person')

        # Always unique by id
        competences = list({v['id']: v for v in competences}.values())
        # print(competences)
        # Patch if difference
        if ALWAYS_PATCH is True or _compare_list_of_dicts(competences, person.get('competences', [])) is True:
            lookup = {'_id': person['_id']}
            resp, _, _, status = patch_internal(RESOURCE_PERSONS_PROCESS, {'competences': competences}, False, True,
                                                **lookup)
            if status != 200:
                app.logger.error('Patch returned {} for competence'.format(status))
                # print('Not 200')
                pass
        else:
            # print('Not always')
            pass

    # print('Check', _compare_list_of_dicts(competences, person.get('competences', [])))


def on_organizations_post(items):
    for item in items:
        on_organizations_put(item)


def on_organizations_put(response, original=None):
    # Only on NIF groups / NLF clubs
    if response.get('type_id', 0) == 6 or len(response.get('activities', [])) == 0:

        # Rebuild activities, only active disciplines
        for v in response.get('_down'):
            if v.get('type') == 14:
                discipline = _get_org(v.get('id'))
                if discipline.get('is_active', False) is True and 'activities' in discipline:
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

    # Just return original text
    return None


def _get_pmt_activity(text):
    if 'modellfly' in text.lower():
        return NLF_ORG_STRUCTURE['modellfly']['activity']
    elif 'mikrofly' in text.lower():
        return NLF_ORG_STRUCTURE['sportsfly']['activity']
    elif 'sportsfly' in text.lower():
        return NLF_ORG_STRUCTURE['sportsfly']['activity']
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
                                'exception': _get_pmt_type(item['product_name']),
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
                    year = _get_pmt_year(item['product_name'])
                    # Magazines
                    # Original text
                    name = item['product_name']
                    # CHeck magazines
                    if 'flydrone' in item['product_name'].lower():
                        name = item['product_name']
                        flydrone_status, flydrone_result = _register_flydrone(item['person_id'])
                        if flydrone_status not in [200, 201, 304]:
                            app.logger.error(f'[FLYDRONE] Error registering flydrone for {item["person_id"]}, result:')
                            app.logger.error(flydrone_result)
                    elif 'fritt' in item['product_name'].lower():
                        name = 'Fritt Fall'
                    elif 'flynytt' in item['product_name'].lower():
                        name = 'Flynytt'
                    elif 'gliding' in item['product_name'].lower():
                        name = 'Nordic Gliding'
                    elif 'modell' in item['product_name'].lower():
                        name = 'Modellinformasjon'
                    elif 'flukt' in item['product_name'].lower():
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
                    app.logger.exception('Error {} for payment id {}'.format(item['product_name'], item['id']))

            elif type_id in [20, 22]:  # Federation/section
                # Seksjonsavgifter
                # memberships org_id fra section..
                fed = person.get('federation', [])

                if refund is True:
                    fed = [x for x in fed if x.get('id', item['id']) != item['id']]
                else:
                    if type_id == 22:
                        product_type = 'Seksjonskontigent'
                        activity = _get_pmt_activity(item['product_name'])
                    else:
                        product_type = 'Forbundskontigent'
                        activity = 27

                    fed.append({
                        'id': item['id'],
                        'name': product_type,
                        'activity': activity,
                        'year': _get_pmt_year(item['product_name']),
                        'exception': _get_pmt_type(item['product_name']),
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
                    app.logger.exception('Error {} for payment id {}'.format(item['product_name'], item['id']))


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
        app.logger.exception('Broadcast of item with id {} did not work out!'.format(item['id']))


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
