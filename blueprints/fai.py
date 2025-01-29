import json

import requests
from urllib.parse import urlencode
import base64
from flask import Blueprint, current_app as app, request, Response, abort, jsonify
from ext.auth.decorators import require_token
from ext.app.fids import fid_exists, create_fid, update_fid
from ext.scf import FAI_USERNAME, FAI_PASSWD, FAI_URL, COMPETENCE_FAI_MAPPING_IDS, FAI_ID_MAPPINGS_INV, COMPETENCE_FAI_MAPPING
from ext.app.eve_helper import eve_response, eve_abort
from eve.methods.get import getitem_internal
from eve.methods.post import post_internal
from eve.methods.patch import patch_internal
from datetime import datetime
from dateutil import parser

Fai = Blueprint('FAI resources', __name__)


def make_params():
    params = {
        'auth_username': FAI_USERNAME,
        'auth_password': base64.b64encode(FAI_PASSWD),
        # 'country': 'NOR'
    }
    return params


def _get_license(license_id):
    r = requests.get(f'{FAI_URL}/licence/{license_id}', params=make_params())

    try:
        return r.status_code, r.json()
    except Exception as e:
        app.logger.exception(f'[FAI] get license {license_id} gave status {r.status_code} with response {r.text}')

    return 500, 'Unknown error'


def _get_licenses(query, nac='NOR'):
    query.update(make_params())

    r = requests.get(f'{FAI_URL}/licences', params=query)
    try:
        result = sorted([x for x in r.json() if x['IOC'] == nac and x['editable'] is True], key=lambda d: datetime.strptime(d["validuntil_lic"], '%Y-%m-%d'))
        return r.status_code, result
    except Exception as e:
        app.logger.exception(f'[FAI] get licenses with query {query} gave status {r.status_code} with response {r.text} and sorted {result}')

    return 500, 'Unknown error'


def _create_or_update_license(license):
    license.update(make_params())
    r = requests.get(f'{FAI_URL}/create', params=license)
    try:
        return r.status_code, r.json()
    except Exception as e:
        app.logger.exception(f'[FAI] create or update failed with status code {r.status_code} and response {r.text}')

    return 500, 'Unknown error'


def _get_ISO_country(country_id):
    if country_id == 0:
        return 'NOR'

    try:
        response, _, _, status = getitem_internal('countries', **{'id': country_id})
        if status == 200:
            return response.get('iso_alpha3', 'NOR')
    except Exception as e:
        app.logger.exception(f'[FAI] error getting ISO country from id {country_id}')

    return 'NOR'


def _get_ISO_country_from_name(country_name):
    try:
        response, _, _, status = getitem_internal('countries', **{'name_en': country_name})
        if status == 200:
            return response.get('iso_alpha3', 'NOR')
    except Exception as e:
        app.logger.exception(f'[FAI] error getting ISO country from name {country_name}')

    return 'NOR'


def _get_person(person_id):
    response, _, _, status = getitem_internal('persons', **{'id': person_id})
    return status, response


def fix_fid(person_id, fai_person_id):
    if fid_exists(person_id, 'fai'):
        return update_fid(person_id, 'fai', {'fai_person_id': fai_person_id})

    return create_fid(person_id, 'fai', {'fai_person_id': fai_person_id})


def fai_create(person, competence, fai_person_id=None):
    # Build license object:
    license = {
        'address1': person.get('address', {}).get('street_address', ''),
        'address3': person.get('address', {}).get('zip', '') + ' ' + person.get('address', {}).get('city', ''),
        'address_country': _get_ISO_country(person.get('address', {}).get('country_id', 0)),
        'phone_mobile': person.get('address', {}).get('phone_mobile', ''),
        'licence_number': str(person['id']),
        'licencee_birthdate': str(person['birth_date'])[:10],
        'licencee_email': person['primary_email'],
        'licencee_firstname': person['first_name'],
        'licencee_gender': person['gender'],
        'licencee_lastname': person['last_name'],
        'licencee_nationality': _get_ISO_country(person.get('nationality_id', 0)),
        'licencee_residencecountry': _get_ISO_country(person.get('address', {}).get('country_id', 0)),
        'dateissued': str(competence.get('date', datetime.now()))[:10],
        'discipline': COMPETENCE_FAI_MAPPING_IDS[competence['type_id']],
        'validuntil': str(competence['valid_until'])[:10],
    }

    # If we have the fai person id:
    if fai_person_id is not None:
        license['idlicencee'] = fai_person_id

    # Add required params
    license.update(make_params())

    # Let's go!
    s, r = _create_or_update_license(license)
    if s in [200, 201]:
        app.logger.debug(f'[FAI] created or updated fai license for competence {competence["id"]}')

    # If we also created the fai person then we need to get that id
    if fai_person_id is None and r.get('success', False) is True:
        # get license, then extract idlicencee
        status, license = _get_license(r['idlicence'])
        if status == 200:
            r['fai_person_id'] = license['idlicencee_lic']
    elif fai_person_id:
        r['fai_person_id'] = fai_person_id

    return s, r


def fai_update(person, competence, fai_license_id):
    # Get the licence
    fai_status, fai_license = _get_license(fai_license_id)

    if fai_status == 200:  # and fai_license.get('success', False) is True:

        # Let's make it as simple as possible
        license = {
            'idlicence': fai_license['idlicence'],
            'idlicencee': fai_license['idlicencee_lic'],
            'licence_number': str(person['id']),
            'licencee_birthdate': fai_license['birthdate_lip'],
            'licencee_email': person['primary_email'],
            'licencee_firstname': fai_license['givenname_lip'],
            'licencee_gender': fai_license['gender_lip'],
            'licencee_lastname': fai_license['surname_lip'],
            'licencee_nationality': _get_ISO_country_from_name(fai_license['idnationality_lip']),
            'licencee_residencecountry': _get_ISO_country_from_name(fai_license['idresidencecountry_lip']),
            'dateissued': fai_license['dateissued_lic'],
            'discipline': FAI_ID_MAPPINGS_INV[fai_license['idsport_lic']],
            'validuntil': str(competence['valid_until'])[:10],
        }

        # Add required params
        license.update(make_params())

        # Let's go!
        s, r = _create_or_update_license(license)

        # Add fai person id, same as fai_license['idlicencee_lic']
        r['fai_person_id'] = license['idlicencee']

        return s, r

    app.logger.error(f'[FAI] Error getting fai license {fai_license_id} for updating triggered by competence {competence["id"]}')
    return fai_status, None


def upsert_fai(competence):
    # Get person
    status, person = _get_person(competence['person_id'])
    if status == 200:

        # make sure it's the correct fai license, get existing from person competences!
        person_competences = [x for x in person.get('competences', []) if x['type_id'] == competence['type_id']]

        if len(person_competences) == 1:  # Exactly one - perfect!
            person_competence = person_competences[0]
        elif len(person_competences) > 1:  # Multiple, then choose newst
            person_competence = sorted(person_competences, key=lambda d: parser.parse(d['valid_until']))
        else:
            person_competence = None

        # Assign the used fai license id if exists
        if person_competence is not None and '_fai' in person_competence:
            _fai_license_id = person_competence['_fai']['license_id']
        else:
            _fai_license_id = None

        # We have a competence, person, now get those fai licenses?
        fai_status, licenses = _get_licenses(query={'search_number': competence['person_id'], 'include_invalid': 0, 'discipline': COMPETENCE_FAI_MAPPING_IDS[competence['type_id']]})

        if fai_status == 200:

            # Get fai license - newest!
            fai_licenses = [x for x in licenses if x['licencenumber_lic'] == f"{person['id']}" and x['Sport'] == COMPETENCE_FAI_MAPPING[competence['type_id']] and x['editable'] is True]

            if len(fai_licenses) == 1:  # Exactly one - perfect!
                fai_license = fai_licenses[0]
            elif len(fai_licenses) > 1:  # Multiple, then choose newest expiry and then newest issued date
                fai_license = [y[2] for y in sorted([(parser.parse(x['validuntil_lic']), parser.parse(x['dateissued_lic']), x) for x in fai_licenses], reverse=True)][0]
            else:
                fai_license = None

            # Try to set fai person id, also if no
            if fai_license is None:
                # Try if other
                try:
                    fai_person_id = [x for x in fai_licenses if str(x['licencenumber_lic']) == str(person['id'])][0]['idlicencee']
                except:
                    fai_person_id = None
            else:
                fai_person_id = fai_license['idlicencee']

            # See if we need to change anything?
            if fai_license is not None:
                if fai_license['validuntil_lic'] == str(competence["valid_until"])[:10]:
                    app.logger.debug(f'[FAI] Same date, no action taken for compentence {competence["id"]} fai license {fai_license["idlicence"]}')
                    return 304, {'success': True, 'idlicence': fai_license['idlicence'], 'fai_person_id': fai_person_id}
                elif parser.parse(fai_license['validuntil_lic']) < parser.parse(str(competence["valid_until"])[:10]):
                    app.logger.debug(f'[FAI] Updating expiry longer for compentence {competence["id"]} fai license {fai_license["idlicence"]}')
                    s, r = fai_update(person, competence, fai_license['idlicence'])
                    if s in [200, 201]:
                        _, _ = fix_fid(person['id'], fai_person_id)
                    return s, r
                elif parser.parse(fai_license['validuntil_lic']) > parser.parse(str(competence["valid_until"])[:10]):
                    app.logger.debug(f'[FAI] Updating expiry shorter for compentence {competence["id"]} fai license {fai_license["idlicence"]}')
                    s, r = fai_update(person, competence, fai_license['idlicence'])
                    if s in [200, 201]:
                        _, _ = fix_fid(person['id'], fai_person_id)
                    return s, r

            elif fai_license is None:
                app.logger.debug(f'[FAI] Creating new fai license for compentence {competence["id"]}')
                if fai_person_id is None:
                    app.logger.debug(f'[FAI] No person in fai for person_id {competence["person_id"]}')
                s, r = fai_create(person, competence, fai_person_id)
                if s in [200, 201]:
                    _, _ = fix_fid(person['id'], r['fai_person_id'])
                return s, r

        else:
            app.logger.error(f'[FAI] Error getting licenses compentence {competence["id"]} gave status {fai_status} and response {licenses}')
            return fai_status, None

    app.logger.error(f'[FAI] Error getting person for compentence {competence["id"]} gave status {status} and response {person}')
    return status, None


@Fai.route('/api-doc', methods=['GET'])
@require_token()
def get_paths():
    resp = [str(p) for p in app.url_map.iter_rules() if str(p).startswith('/api/v1/fai')]
    return eve_response(resp)


@Fai.route("/licenses", methods=['GET'])
@require_token()
def get_licenses():
    """
    SEARCH for a licence by name, id, discipline
    nac_org: autoincrement ID or name of NAC
    country: autoincrement ID or IOC or name of country
    valid_from
    valid_to
    search_name: first name or last name of athlete
    search_number: autoincrement FAI license ID or FAI ID or NAC license ID
    discipline: autoincrement ID or name of sport
    include_invalid: 1, if include expired licenses, 0 if not to include expired licenses, ignored
    when either valid_from or valid_to is given
    limit_start: db select limit start
    limit_length: db select limit length
    :return:
    """

    query_params = request.args.lists()  # get_json()

    query = {}

    for key, value in list(query_params):
        if key == 'where':
            query.update(json.loads(value[0]))
        else:
            query[key] = value

    query['nac_org'] = 'NOR'

    if 'include_invalid' not in query:
        query['include_invalid'] = 1

    # Translate
    if 'max_results' in query:
        query['limit_length'] = query['max_results']
        query.pop('max_results', None)
    if 'page' in query:
        query['limit_start'] = query['page']
        query.pop('page', None)
    if '$text' in query:
        query['search_name'] = query.get('$text', {}).get('$search', None)
        query.pop('$search', None)
    if 'id' in query:
        query['search_number'] = query['id']
        query.pop('id', None)
    if 'person_id' in query:
        query['search_number'] = query['person_id']
        query.pop('person_id')

    # discipline

    # valid_from, valid_to

    if 'limit_start' not in query:
        query['limit_start'] = 0
    if 'limit_length' not in query:
        query['limit_length'] = 25
    print('[QUERY]', query)
    status_code, response = _get_licenses(query)

    return eve_response(response, status_code)


@Fai.route("/licenses/<int:license_id>", methods=['GET'])
@require_token()
def get_license(license_id):
    """
    Response
    idlicence: autoincrement ID of license
    idlicencee_lic: autoincrement ID of athlete (FAI ID)
    idissue_lic: NAC name (issuer)
    idsport_lic: name of the sport
    licencetype_lic: license type
    validuntil_lic: valid until date of license
    licencenumber_lic: NAC license ID
    dateissued_lic: issue date of license
    surname_lip: athlete’s last name
    givenname_lip: athlete’s first name
    middlename_lip: athlete’s middle name
    gender_lip: athlete’s gender
    birthdate_lip: athlete’s birthdate
    suspended_lip: 1 if athlete is suspended else 0
    idlecencecountry_lip: name of country
    idnationality_lip: name of athlete’s nationality country
    idresidencecountry_lip: name of athlete’s residency country
    is_expired: 1 if license is expired else 0
    editable: 1 if license is editable by the user else 0
    id_licencee_history: array of licenses with same FAI license ID
         idlicence: autincrement ID f license
         idlicencee_lic: autincrement ID f athlete (FAI ID)
         licencenumber_lic: NAC license ID
         dateissued_lic: issue date f license
         validuntil_lic: valid until date f license
         discipline: name f the sprt
         issued_by_ic: IC f cuntry
         is_expired: 1 if license if expired else 0
         is_suspended: 1 if athlete is suspended else 0

    """

    status_code, response = _get_license(license_id)

    if len(response) > 0:
        return eve_response(response, status_code)

    return abort(404)


@Fai.route("/licenses/", methods=['POST'])
@require_token()
def create():
    """
    GET create?auth_username=&auth_password=&idlicencee=&licencee_firstname=&licencee_middlename=&licencee_lastname=&licencee_gender=&licencee_birthdate=&licencee_nationality=&licencee_residencecountry=&address1=&address2=&address3=&address_country=&licencee_email=&phone_home=&phone_office=&phone_mobile=&licence_number=&dateissued=&validuntil=&discipline=

    auth_username sportinglicences2.fai.org username String
    auth_password password, base64 encoded String
    -> idlicencee If empty, new pilot will be created. Otherwise pilot with idlicencee id be updated String
    licencee_firstname String
    licencee_middlename String
    licencee_lastname String
    licencee_gender M or F String
    licencee_birthdate Date in the format YYYY-MM-DD [ example: 2016-01-18 ] String
    licencee_nationality Country ID or 3 Letter IOC Code eg. FIN,SWE String
    licencee_residencecountry Country ID or 3 Letter IOC Code eg. FIN,SWE String
    address1 Address text 1 String
    address2 Address text 2 String
    address3 Address text 3 String
    address_country Country ID or 3 Letter IOC Code eg. FIN,SWE String
    licencee_email String
    phone_home String
    phone_office String
    phone_mobile String
    licence_number Licence Number, String
    dateissued Date in the format YYYY-MM-DD [ example: 2016-01-18 ] String
    validuntil Date in the format YYYY-MM-DD [ example: 2016-01-18 ] String
    discipline Sport ID or discipline text as shown in http://sl-test.fai.org/sl/search
    :return:
    """
    raise NotImplemented


@Fai.route("/licenses/<int:licensee_id>", methods=['PATCH'])
@require_token()
def update(licensee_id):
    """
    GET create?auth_username=&auth_password=&idlicence=&idlicencee=&licencee_firstname=&licencee_middlename=&licencee_lastname=&licencee_gender=&licencee_birthdate=&licencee_nationality=&licencee_residencecountry=&address1=&address2=&address3=&address_country=&licencee_email=&phone_home=&phone_office=&phone_mobile=&licence_number=&dateissued=&validuntil=&discipline=
    auth_username sportinglicences2.fai.org username String
    auth_password password, base64 encoded String
    -> idlicencee If empty, new pilot will be created. Otherwise pilot with idlicencee id be updated String
    licencee_firstname String
    licencee_middlename String
    licencee_lastname String
    licencee_gender M or F String
    licencee_birthdate Date in the format YYYY-MM-DD [ example: 2016-01-18 ] String
    licencee_nationality Country ID or 3 Letter IOC Code eg. FIN,SWE String
    licencee_residencecountry Country ID or 3 Letter IOC Code eg. FIN,SWE String
    address1 Address text 1 String
    address2 Address text 2 String
    address3 Address text 3 String
    address_country Country ID or 3 Letter IOC Code eg. FIN,SWE String
    licencee_email String
    phone_home String
    phone_office String
    phone_mobile String
    licence_number Licence Number, String
    dateissued Date in the format YYYY-MM-DD [ example: 2016-01-18 ] String
    validuntil Date in the format YYYY-MM-DD [ example: 2016-01-18 ] String
    discipline Sport ID or discipline text as shown in http://sl-test.fai.org/sl/search
    """
    raise NotImplemented
    where = request.get_json()

    query = make_params()  # urlencode()

    for key, value in where:
        query[key] = value

    query['idlicencee'] = licensee_id

    response = requests.get('{}/create?{}'.format(FAI_URL, urlencode(query)))
    return eve_response(response.json(), response.status_code)


@Fai.route("/country/<int:country_id>", methods=['GET'])
@require_token()
def get_country(country_id):
    return eve_response(_get_ISO_country(country_id))
