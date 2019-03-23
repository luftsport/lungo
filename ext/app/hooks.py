"""
To hook all the different changes to our api!
"""
from eve.methods.patch import patch_internal
from eve.methods.get import get_internal
from datetime import datetime, timezone
from operator import itemgetter
from dateutil import tz
from flask import current_app as app

# import dateutil.parser


RESOURCE_PERSONS_PROCESS = 'persons_process'
RESOURCE_FUNCTIONS_PROCESS = 'functions_process'
LOCAL_TIMEZONE = "Europe/Oslo"  # UTC
tz_utc = tz.gettz('UTC')
tz_local = tz.gettz(LOCAL_TIMEZONE)


def _get_end_of_year():
    return datetime(datetime.utcnow().year, 12, 31, 23, 59, 59, 999999).replace(tzinfo=tz_utc)


def _get_end_of_january():
    """End of jan next year"""
    return datetime(datetime.utcnow().year + 1, 1, 31, 23, 59, 59, 999999).replace(tzinfo=tz_utc)


def _fix_naive(date_time):
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
    person = _get_person(response.get('person_id', None))

    # Expiry date
    expiry = response.get('to_date', None)

    if '_id' in person:

        # Club member! has_paid_membership?
        clubs = person.get('clubs', []).copy()
        activities = person.get('activities', []).copy()

        # Will get all org_type_id's not only 5
        if response.get('type_id', 0) == 10000000:

            # Set expiry to end year
            if expiry is None:
                expiry = _get_end_of_january()
                expiry = _fix_naive(expiry)

            # If not deleted and is valid expiry add to club list
            if not response['is_deleted'] and not response['is_passive'] and \
                            expiry is not None and expiry > _get_now():

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
            # clubs[:] = [d for d in clubs if d.get('expiry') >= _get_now()]


            # Activities
            # Do not know which club is actually which activity
            # Need to redo all.
            # san_clubs is sanitized clubs
            san_clubs = []
            for club_id in clubs:
                try:
                    org = _get_org(club_id)
                    
                    if org.get('type_id', 0) != 5:
                        continue
                    
                    san_clubs.append(club_id)
                    # Gets the id of main activity
                    # If None, go for 27 (Luftsport/370)
                    # @TODO see if should be None to pass next
                    activity = org.get('main_activity', {}).get('id', 27)
                    club_activities = org.get('activities', [])
                    if activity is not None:
                        # @TODO see if code should be integer? String now.
                        # activity['code'] = int(activity.get('code', 0))
                        activities.append(activity)
                    for act in club_activities:
                        a = act.get('id', 27)
                        activities.append(a)

                except:
                    pass

            # Unique list of activities
            activities.append(27)
            activities = list(set(activities))

            # List of dicts
            # activities = list({v['id']: v for v in activities}.values())
            # Valid expiry?
            # activities[:] = [d for d in activities if d.get('expiry') >= _get_now()]

        # The rest of the functions
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

        f = list(set(functions))
        # Valid expiry?
        # f[:] = [d for d in f if d.get('expiry') >= _get_now()]

        lookup = {'_id': person['_id']}

        # Update person with new values
        # response, last_modified, etag, status =
        if _compare_lists(functions, person.get('functions', [])) is True or \
                _compare_lists(activities, person.get('activities', [])) is True or \
                _compare_lists(san_clubs, person.get('clubs', [])) is True:

            resp, _, _, status = patch_internal(RESOURCE_PERSONS_PROCESS,
                                                {'functions': functions, 'activities': activities, 'clubs': san_clubs},
                                                False, True, **lookup)
            if status != 200:
                app.logger.error('Patch returned {} for functions, activities, clubs'.format(status))

    # Always check and get type name
    # Update the function
    if response.get('type_name', None) is None:
        function_type = _get_functions_types(response.get('type_id', 0))
        if len(function_type) > 0:
            type_name = function_type.get('name', None)
            if type_name is not None:
                resp, _, _, status = patch_internal(RESOURCE_FUNCTIONS_PROCESS,
                                                    {'type_name': type_name},
                                                    False,
                                                    True,
                                                    **{'_id': response.get('_id')})
                if status != 200:
                    app.logger.error('Patch returned {} for function update type_name'.format(status))


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


def on_competence_post(items):
    """Competence fields:

    passed bool
    valid_until datetime

    """
    for response in items:
        on_competence_put(response)


def on_competence_put(response, original=None):
    """"""

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
                                   'paid': response.get('paid_date', None)})
            except:
                pass

        # Always remove stale competences
        competence[:] = [d for d in competence if _fix_naive(d.get('expiry')) >= _get_now()]

        # Always unique by id
        competence = list({v['id']: v for v in competence}.values())

        # Patch if difference
        if _compare_list_of_dicts(competence, person.get('competence', [])) is True:
            lookup = {'_id': person['_id']}
            resp, _, _, status = patch_internal(RESOURCE_PERSONS_PROCESS, {'competences': competence}, False, True,
                                                **lookup)
            if status != 200:
                app.logger.error('Patch returned {} for competence'.format(status))


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
