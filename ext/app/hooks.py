"""
To hook all the different changes to our api!
"""
from eve.methods.patch import patch_internal
from eve.methods.get import get_internal
import geocoder
import dateutil.parser
from datetime import datetime

RESOURCE_PERSONS_PROCESS = 'persons_process'


def _get_end_of_year():
    return datetime(datetime.utcnow().year, 12, 31, 23, 59, 59, 999999)


def _get_person(person_id) -> dict:
    """Get person from persons internal

    :param person_id: Person id
    :type person_id: int
    :return org: Returns the person given
    :rtype: dict
    """
    person, _, _, status, _ = get_internal('persons', **{'id': person_id})

    if status == 200:
        if '_items' in person and len(person['_items']) == 1:
            return person['_items'][0]

    return {}


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


def on_function_post(items) -> None:
    """On every function change, let's update person's functions.

    Function of type ``10000000`` is club membership and this implicates both clubs and activities

    Other function types are updated in a list

    :param items: the function object to be inserted or replaced

    @TODO can "has_paid_membership": false | true be of use?
    """

    for response in items:
        on_function_put(response)


def on_function_put(response):
    person = _get_person(response['person_id'])

    if '_id' in person:

        # Club member! has_paid_membership?
        clubs = person.get('clubs', [])
        activities = person.get('activities', [])

        # Expiry date
        expiry = response.get('to_date', None)
        # Set expiry to end year
        if expiry is None:
            expiry = _get_end_of_year()

        if response.get('type_id', None) == 10000000:

            if not response['is_deleted'] and not response['is_passive'] and \
                            expiry is not None and expiry > datetime.utcnow():

                clubs.append(response.get('active_in_org_id'))
            else:
                try:
                    clubs.remove(response.get('active_in_org_id'))
                except ValueError:
                    pass
                except:
                    pass

            # Unique list
            clubs = list(set(clubs))
            # Valid expiry?
            # clubs[:] = [d for d in clubs if d.get('expiry') >= datetime.utcnow()]

            # Activities!
            for club_id in clubs:
                try:
                    org = _get_org(club_id)
                    activity = org.get('main_activity', None)
                    if activity is not None:
                        # @TODO see if code should be integer? String now.
                        activity['code'] = int(activity.get('code', 0))
                        activities.append(activity)
                except:
                    pass

            # Unique list of activities
            activities = list({v['id']: v for v in activities}.values())
            # Valid expiry?
            # activities[:] = [d for d in activities if d.get('expiry') >= datetime.utcnow()]

        # The rest of the functions
        # Also exoiry date!
        f = person.get('functions', [])
        if expiry > datetime.utcnow():
            f.append(response['id'])
        else:
            try:
                f.remove(response.get('id'))
            except:
                pass

        f = list(set(f))
        # Valid expiry?
        # f[:] = [d for d in f if d.get('expiry') >= datetime.utcnow()]

        lookup = {'_id': person['_id']}

        # response, last_modified, etag, status =
        patch_internal(RESOURCE_PERSONS_PROCESS,
                       {'functions': f, 'activities': activities,
                        'clubs': clubs},
                       False, True, **lookup)
        # print(response, status)
        # patch_internal(RESOURCE_PERSONS_PROCESS, {'competences': l}, False, True, **look)


def on_license_post(items):
    """pass"""

    for response in items:
        on_license_put(response)


def on_license_put(response):
    """pass"""

    expiry = response.get('period_to_date', None)  # dateutil.parser.parse(response.get('period_to_date', None))
    # Set expiry to end year
    if expiry is None:
        expiry = _get_end_of_year()

    if expiry is None or expiry >= datetime.utcnow():
        person = _get_person(response['person_id'])

        if '_id' in person:

            licenses = person.get('licenses')
            try:
                licenses.append({'id': response.get('id'),
                                 'status_id': response.get('status_id', 0),
                                 'status_date': response.get('status_date', None),
                                 'expiry': response.get('period_to_date', None),
                                 'type_id': response.get('type_id', None),
                                 'type_name': response.get('type_name', None)})

                # Unique
                licenses = list({v['id']: v for v in licenses}.values())
                # Valid expiry
                licenses[:] = [d for d in licenses if d.get('expiry') >= datetime.utcnow()]
            except:
                pass

            lookup = {'_id': person['_id']}
            patch_internal(RESOURCE_PERSONS_PROCESS, {'licenses': licenses}, False, True, **lookup)


def on_competence_post(items):
    """Competence fields:

    passed bool
    valid_until datetime

    """
    for response in items:
        on_competence_put(response)


def on_competence_put(response):
    """"""
    # try:
    #    expiry = dateutil.parser.parse(response.get('valid_until', None))
    # except:
    #    expiry = None
    expiry = response.get('valid_until', None)

    # Set expiry to end year
    if expiry is None:
        expiry = _get_end_of_year()

    if expiry is not None and isinstance(expiry, datetime) and expiry >= datetime.utcnow():

        person = _get_person(response['person_id'])

        if '_id' in person:
            competence = person.get('competences', [])

            # Remove stale competences?
            try:
                competence[:] = [d for d in competence if d.get('expiry') >= datetime.utcnow()]
            except:
                pass

            try:
                competence.append({'id': response.get('id'),
                                   '_code': response.get('_code', None),
                                   'issuer': response.get('approved_by_person_id', None),
                                   'expiry': response.get('valid_until', None),
                                   'paid': response.get('paid_date', None)})

                competence = list({v['id']: v for v in competence}.values())


            except:
                pass

            lookup = {'_id': person['_id']}
            patch_internal(RESOURCE_PERSONS_PROCESS, {'competences': competence}, False, True, **lookup)


def on_person_after_post(items):
    for response in items:
        _update_person(response)


def on_person_after_put(item, original=None):
    _update_person(item)


def _update_person(item):
    lookup = {'person_id': item['id']}

    competences, _, _, c_status, _ = get_internal('competences', **lookup)
    if c_status == 200:
        on_competence_post(competences.get('_items', []))

    licenses, _, _, l_status, _ = get_internal('licenses', **lookup)
    if l_status == 200:
        on_license_post(licenses.get('_items', []))

    functions, _, _, f_status, _ = get_internal('functions', **lookup)
    if f_status == 200:
        on_function_post(functions.get('_items', []))
