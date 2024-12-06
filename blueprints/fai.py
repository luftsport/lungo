import json

import requests
from urllib.parse import urlencode
import base64
from flask import Blueprint, current_app as app, request, Response, abort, jsonify
from ext.auth.decorators import require_token
from ext.scf import FAI_USERNAME, FAI_PASSWD, FAI_URL
from ext.app.eve_helper import eve_response, eve_abort
from eve.methods.get import getitem_internal
from datetime import datetime

Fai = Blueprint('FAI resources', __name__)

"""
Mapping:
A = Motorfly 
F = Fallskjerm
H = HPS
M = Modellfly (Aeromodelling hos FAI vel)
B = Ballong
S = Seilfly
U = Sportsfly (som jeg vil anta er general aviation)

MAPPING = {
    109: "Parachuting",
    111: "Gliding",
    238: "General Aviation",
    236: "Aeromodelling and Spacemodelling",
    222: "Ballooning",
    110: "Hang Gliding and Paragliding"
}

{
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
}
"""

FAI_SPORTING_CODES = {
    1: {'name': "Ballooning", 'initials': 'CIA', 'classes': [{'A': 'Free Balloons'}, {'B': 'Dirigibles, Airships'}]},
    2: {'name': "General Aviation", 'initials': 'GAC', 'classes': [{'C': 'Aeroplanes'}, {'H': 'Dirigibles, Airships'}]},
    3: {'name': "Gliding", 'initials': 'IGC', 'classes': [{'D': 'Gliders'}, {'DM': 'Motor Gliders'}]},
    4: {'name': "Aeromodelling", 'initials': 'CIAM',
        'classes': [{'F': 'Model Aircragt'}, {'S': 'Space Models'}, {'U': 'Unmanned Aerial Veichles'}]},
    5: {'name': "Parachuting and Indoor Skydiving", 'initials': 'ISC', 'classes': [{'G': 'Parachutes, Wind Tunnels'}]},
    6: {'name': "Aerobatics", 'initials': 'CIVA', 'classes': [{'C': 'Aeroplanes'}, {'D': 'Gliders'}]},
    7: {'name': "Hang Gliding", 'initials': 'CIVL', 'classes': [{'O': 'Hang Gliders, Paragliders'}]},
    8: {'name': "Astronautics", 'initials': 'ICARE', 'classes': [{'K': 'Spacecraft'}, {'P': 'Aero-Spacecraft'}]},
    9: {'name': "Rotocraft", 'initials': 'CIG',
        'classes': [{'E': 'Helicopters, Tilt Rotocraft, Autogyros, Multi-Rotors, Compound Helicopters'},
                    {'M': 'Tilt-Wing/Tilt-Engine Aircraft'}]},
    10: {'name': "Microlights and Paramotors", 'initials': 'CIMA',
         'classes': [{'R': 'Microlight Aircraft, Microlight Autogyros, Powered Hang Gliders, Paramotors'}]},
    11: {'name': "General", 'initials': 'CASI', 'classes': [{'I': 'Human Powered Aircraft'}, {'J': 'Jet Pack'}]},
    12: {'name': "General", 'initials': 'CASI', 'classes': [{'All': 'All Classes'}]},
    13: {'name': "General Aviation", 'initials': 'CIACA',
         'classes': [{'CS': 'Solar-powered Aircraft'}, {'CE': 'Electrically powered aircraft'}]},
}




def make_params():
    params = {
        'auth_username': FAI_USERNAME,
        'auth_password': base64.b64encode(FAI_PASSWD),
        'country': 'NOR'
    }
    return params


def _get_license(license_id):
    r = requests.get(f'{FAI_URL}/licence/{license_id}', params=make_params())

    try:
        return r.status_code, r.json()
    except:
        pass

    return 500, 'Unknown error'


def _get_licenses(query, nac='NOR'):
    query.update(make_params())

    r = requests.get(f'{FAI_URL}/licences', params=query)
    try:
        result = sorted([x for x in r.json() if x['IOC']==nac], key=lambda d: datetime.strptime(d["validuntil_lic"], '%Y-%m-%d'))
        return r.status_code, result
    except:
        pass

    return 500, 'Unknown error'


def _create_or_update_license(license):
    license.update(make_params())
    r = requests.get(f'{FAI_URL}/create', params=license)
    try:
        return r.status_code, r.json()
    except:
        pass

    return 500, 'Unknown error'


def _get_ISO_country(country_id):
    if country_id == 0:
        return 'NOR'

    response, _, _, status = getitem_internal('countries', **{'id': country_id})

    if status == 200:
        try:
            return response.json().get('iso_alpha3', 'NOR')
        except:
            pass


    return 'NOR'


def upsert_fai(person, competence_id, license_id, discipline)->(bool, str, str):
    """

    :param person:
    :param competence_id:
    :param license_id:
    :param discipline:
    :return: bool status, str fai_person_id, int fai_license_id
    """

    try:
        _competence = next(x for x in person.get('competences') if x['id'] == competence_id)

    except:
        _competence = None

    if _competence is not None:

        params = {
            'address1': person.get('address', {}).get('street_address', ''),
            'address3': person.get('address', {}).get('zip', '') + ' ' + person.get('address', {}).get('city', ''),
            'address_country': _get_ISO_country(person.get('address', {}).get('country_id', 1500152)),
            'licence_number': person['id'],
            'licencee_birthdate': str(person.get('birth_date', '1900-01-01'))[0:10],
            'licencee_email': person.get('primary_email', ' '),
            'licencee_firstname': person.get('first_name', ''),
            'licencee_gender': person.get('gender', ''),
            'licencee_lastname': person.get('last_name', ''),
            'licencee_nationality': _get_ISO_country(person.get('nationality_id', 1500152)),
            'licencee_residencecountry': _get_ISO_country(person.get('address', {}).get('country_id', 1500152)),
            'phonemobile': _get_ISO_country(person.get('address', {}).get('phone_mobile', '')),

            'dateissued': str(datetime.now().date()),
            'discipline': discipline,
            'validuntil': _competence.get('expiry', str(datetime.now().date()))[0:10]
        }

        # We have a fai id?
        if '_fids' in person and 'fai_person_id' in person['_fids']:
            params.update({
                'idlicencee': person['_fids']['fai_person_id']
            })
        else:
            # Try to get person!
            status, fai_person = _get_licenses(query={'nac_org': 'NOR', 'search_number': person['id'], 'include_invalid': 0})
            if status in [200]:
                try:
                    params.update({
                        'idlicencee': fai_person[0]['idlicencee']
                    })
                except Exception as e:
                    app.logger.debug(f'[FAI] Exception finding licensee')
                    app.logger.exception(e)

        # We already have the fai license id in our existing competence
        if '_fai' in _competence:
            # Get the license and check if editable!
            try:
                status_code, response = _get_license(_competence['_fai'].get('license_id', None))
                if status_code is True and response.get('editable', False) is not False:
                    params.update({
                        'idlicence': _competence['_fai'].get('license_id', None),  # 380469,
                    })
            except Exception as e:
                app.logger.exception('Error removing competence from person')
                app.logger.exception(e)

        status, result = _create_or_update_license(params)
        if status in [200, 201]:
            r = result.json()
            return True, r['idlicencee'], r['idlicence']
        else:
            app.logger.debug(f'[FAI] Error create or update license, status: {status} and result {result.text}')

        return False, None, None

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
