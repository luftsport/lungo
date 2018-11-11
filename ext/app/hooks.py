"""
To hook all the different changes to our api!
"""
from eve.methods.patch import patch_internal
from eve.methods.get import get_internal
import geocoder
import dateutil.parser
from datetime import datetime

RESOURCE_PERSONS_PROCESS = 'persons_process'
# import requests
# from ext.auth.clients import users as USERS

"""
All functions are on database events!

  items = [{
    "_id": 10000000, Klubbmedlem
    "count": 198
  }, {
    "_id": 1, Leder
    "count": 67
  }, {
    "_id": 7, Utdanningskontakt
    "count": 30
  }, {
    "_id": 3, Styremedlem
    "count": 10
  }, {
    "_id": 40000004, Medlemsansvarlig
    "count": 8
  }, {
    "_id": 2, Nestleder
    "count": 6
  }, {
    "_id": 40000008, Org.ansvarlig KL"
    "count": 4
  }, {
    "_id": 201380,  Webansvarlig
    "count": 4
  }, {
    "_id": 24, Adm.leder (ansatt)
    "count": 4
  }, {
    "_id": 202427, SA-Integrasjonsbruker
    "count": 2
  }, {
    "_id": 9, Varamedlem
    "count": 2
  }, {
    "_id": 5, Kasserer (Styremedlem)
    "count": 2
  }, {
    "_id": 202401, Ansvarlig politiattest
    "count": 1
  }]
"""


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

        if response['type_id'] == 10000000:

            if not response['is_deleted'] and not response['is_passive']:
                clubs.append(response['active_in_org_id'])
            else:
                try:
                    clubs.remove(response['active_in_org_id'])
                except ValueError:
                    pass
                except:
                    pass

            # Unique list
            clubs = list(set(clubs))

            # Activities!
            for club_id in clubs:
                try:
                    org = _get_org(club_id)
                    activity = org.get('main_activity', None)
                    if activity is not None:
                        # @TODO see if code should be integer? String now.
                        activities.append(activity)
                except:
                    pass

            # Unique list of activities
            activities = list({v['id']: v for v in activities}.values())

        f = person.get('functions', [])
        try:
            f.append(response['id'])
            f = list(set(f))
        except:
            pass

        # if f != person.get('functions', []):
        lookup = {'_id': person['_id']}

        response, last_modified, etag, status = patch_internal(RESOURCE_PERSONS_PROCESS,
                                                               {'functions': f, 'activities': activities, 'clubs': clubs},
                                                               False, True, **lookup)
        # print(response, status)
        # patch_internal(RESOURCE_PERSONS_PROCESS, {'competences': l}, False, True, **look)


def on_license_post(items):
    """pass"""

    for response in items:
        on_license_put(response)



def on_license_put(response):
    """pass"""
    try:
        expiry = dateutil.parser.parse(response.get('period_to_date', None))
    except:
        expiry = None

    if expiry is None or expiry >= datetime.now():
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

                licenses = list({v['id']: v for v in licenses}.values())
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
    if expiry is not None and isinstance(expiry, datetime) and expiry >= datetime.now():

        person = _get_person(response['person_id'])

        if '_id' in person:
            competence = person.get('competences', [])

            # Remove stale competences?
            try:
                competence[:] = [d for d in competence if d.get('expiry') >= datetime.now()]
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

    # Geocode address
    # Stream do this async is better
    # _update_person_location(item)


def _update_person_location(item):
    """pass"""

    # If moved to then this should not be geocoded
    if '_merged_to' not in item:

        # Make the address dict
        if 'address' not in item:
            item['address'] = {}

        # Already geocoded?
        if 'location' not in item['address']:

            # Need a city at least, and not Ukjent
            city = item['address'].get('city', '')
            if len(city) > 0 and city != 'Ukjent':

                geo, score, quality, confidence = get_geo(street=item['address'].get('street_address', ''),
                                                          city=item['address'].get('city', ''),
                                                          zip=item['address'].get('zip_code', ''),
                                                          )

                if score and int(score) > 0:
                    item['address']['location'] = {}
                    item['address']['location']['geo'] = geo
                    item['address']['location']['score'] = score
                    item['address']['location']['confidence'] = confidence
                    item['address']['location']['quality'] = quality

                    lookup = {'_id': item['_id']}
                    patch_internal(RESOURCE_PERSONS_PROCESS, {'address': item['address']}, False, True, **lookup)
                    # request.post('https://')


def get_geo(street, city='', zip='', country='Norway'):
    try:
        g = geocoder.arcgis('{0} {1} {2}, {3}'.format(street, zip, city, country))
        return g.geometry, g.score, g.quality, g.confidence

    except:
        # Møllergata!
        return {'type': 'Point', 'coordinates': [10.749232432252462, 59.91643658534826]}, 0, 'PointAddress', 0
