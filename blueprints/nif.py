from ext.auth.decorators import require_token, require_superadmin
from nif_tools import KA
from datetime import datetime, timezone, timedelta, UTC
from hashlib import sha224
from flask import Blueprint, current_app as app, request, Response, abort, jsonify
# from eve.methods.post import post_internal
from ext.scf import KA_USERNAME, KA_PASSWORD, NIF_CLIENT_SECRET, NIF_CLIENT_ID, NIF_TOKEN_FILE
from ext.app.eve_helper import eve_response, eve_error_response
from eve.methods.post import post_internal
from eve.methods.get import getitem_internal, get_internal
from eve.methods.patch import patch_internal
from eve.methods.put import put_internal
from nif_rest_api_client import NifRestApiClient
from dateutil import parser
from nif_tools import KA
from ext.app.product_checker import ProductChecker
from ext.app.email import send_email
from ext.app.fids import get_fid, create_fid, update_fid
from ext.app.helpers import _fix_naive

from functools import wraps
import inspect

NIF = Blueprint('NIF tools', __name__)

API = None


def get_nif_api_client() -> NifRestApiClient:
    global API
    if API is None:
        return NifRestApiClient(client_id=NIF_CLIENT_ID, client_secret=NIF_CLIENT_SECRET, token_file=NIF_TOKEN_FILE)

    return API


def _gen_change_msg(entity_id, entity_type, change_type='Modified', org_id=376, realm='PROD'):
    payload = {}
    sequence_ordinal = datetime.now(UTC)

    payload['id'] = entity_id

    payload['change_type'] = change_type
    payload['entity_type'] = entity_type
    payload['created'] = sequence_ordinal
    payload['modified'] = sequence_ordinal
    payload['merge_result_of'] = []
    payload['name'] = 'Manuell endringsmelding'
    payload['_ordinal'] = sha224(bytearray("%s%s%s%s" % (entity_type,
                                                         entity_id,
                                                         sequence_ordinal,
                                                         org_id),
                                           'utf-8')).hexdigest()
    payload['_status'] = 'ready'
    payload['_org_id'] = org_id
    payload['_realm'] = realm

    response, _, _, status, _ = post_internal(resource='integration_changes',
                                              payl=payload,
                                              skip_validation=True)

    return status, response


def _get_ka_person_competences(person_id):
    ka = KA(KA_USERNAME, KA_PASSWORD)
    return ka.get_person_competence(person_id)


def _get_ka_person_licenses(person_id):
    ka = KA(KA_USERNAME, KA_PASSWORD)
    return ka.get_person_licenses(person_id)


def _get_nif_person_competences_list(person_id) -> list:
    """
    Get competences for person then mk list and return only unique id's for valid competence id's
    :param person_id:
    :return:
    """

    status, result = get_nif_api_client().get_person_competences(person_id)
    # print(result)
    if status is True:
        try:
            return [x['id'] for x in result['competences'] if
                    x['passed'] is True or
                    (x['expires'] is None or parser.parse(x['expires']) > datetime.now())]
        except Exception as e:
            pass  # print('[ERR]', e)

    return []


def _get_lungo_person(person_id):
    response, _, _, status = getitem_internal(resource='persons', **{'id': person_id})

    if status == 200:
        return True, response

    return False, {}


def _get_lungo_person_competences(person_id):
    response, _, _, status, _ = get_internal(resource='competences', **{'person_id': person_id})

    if status == 200:
        return True, response.get('_items', [])

    return False, {}


def _gen_flydrone_email(first_name, registration, registration_expiry, type_of_change):
    change_msg = {
        'created': 'created',
        'updated': 'updated',
        'new_registration': 'updated with a new registration number',
        'new_expiry': 'updated with a new expiry'
    }
    msg = f'Hi {first_name}\r\n\r\n'
    msg += f'Your registration at flydrone.no has been {change_msg[type_of_change]}.\r\n\r\n'
    msg += f'Registration number: {registration}\r\n'
    msg += f'Registration expiry: {str(registration_expiry)[:10]}\r\n\r\n'
    msg += 'Remember to mark your model/drone with your operator number - this is mandatory\r\n\r\n'
    msg += 'This connects your drone registration to your membership in NLF. You can also view your registration at https://www.flydrone.no.\r\n\r\n'
    msg += 'This is an automatic generated message from the Norwegian Air Sports Federation, replies will not be answered.\r\n\r\n'

    return msg


def _register_flydrone(person_id):
    """
    1. get fids, check if flydrone
    2. create or update or do nothing

    :param person_id:
    :return:
    """
    CHECK_EXPIRY = False
    DEBOUNCE_MINUTES = 2

    fid_flydrone = get_fid(person_id, 'flydrone')
    if fid_flydrone is None:
        # CREATE Register new!!
        status, result = get_nif_api_client().register_drone_pilot(person_id)

        if status is True:
            try:
                create_status, create_resp = create_fid(person_id, 'flydrone', result)
                if create_status in [200, 201]:
                    person_status, person = _get_lungo_person(person_id)
                    app.logger.info(f'[FLYDRONE] sending email to {person_id}')
                    send_email(
                        recepient=person['primary_email'],
                        subject='Flydrone.no registration',
                        message=_gen_flydrone_email(
                            person['first_name'],
                            result['operatorRegistrationNumber'],
                            result['expiredOperatorRegistrationNumberTime'],
                            'created')
                    )
                    return create_status, create_resp
                else:
                    app.logger.info(f'[FLYDRONE] Could not create fid for {person_id}')
            except Exception as e:
                app.logger.error('[FLYDRONE] error while sending email for created')
                app.logger.exception(e)

    elif _fix_naive(fid_flydrone['_updated']) > datetime.now(UTC) - timedelta(minutes=DEBOUNCE_MINUTES):
        return 304, None
    elif CHECK_EXPIRY is True and parser.parse(fid_flydrone['data']['expiredOperatorRegistrationNumberTime']).date() > datetime.now().date():
        return 304, None
    else:
        status, result = get_nif_api_client().register_drone_pilot(person_id)

        if status is True:
            try:
                type_of_change = 'updated'
                if fid_flydrone['data']['expiredOperatorRegistrationNumberTime'] != result['expiredOperatorRegistrationNumberTime']:
                    type_of_change = 'new_expiry'
                elif fid_flydrone['data']['operatorRegistrationNumber'] != result['operatorRegistrationNumber']:
                    type_of_change = 'new_registration'

                create_status, create_resp = update_fid(person_id, 'flydrone', result)
                if create_status in [200, 201]:
                    person_status, person = _get_lungo_person(person_id)

                    if type_of_change not in ['updated']:
                        app.logger.info(f'[FLYDRONE] sending email to {person_id}')
                        send_email(
                            recepient=person['primary_email'],
                            subject='Flydrone.no registration',
                            message=_gen_flydrone_email(
                                person['first_name'],
                                result['operatorRegistrationNumber'],
                                result['expiredOperatorRegistrationNumberTime'],
                                type_of_change)
                        )
                    return create_status, create_resp
                else:
                    app.logger.info(f'[FLYDRONE] Could not create fid for {person_id}')
                    app.logger.error(f'[FLYDRONE] error while sending email for {type_of_change}')

            except Exception as e:
                app.logger.error(f'[FLYDRONE] error while updating flydrone')
                app.logger.exception(e)

    return 500, 'Unknown'


@NIF.route('/api-doc', methods=['GET'])
@require_token()
def get_paths():
    resp = [str(p) for p in app.url_map.iter_rules() if str(p).startswith('/api/v1/nif')]
    return eve_response(resp)


@NIF.route('/change', methods=['POST'])
@require_token()
def generate_change_message():
    data = request.get_json()
    status, response = _gen_change_msg(data['entity_id'], data['entity_type'])
    return eve_response(response, status)
    # return {}, 201


@NIF.route('/persons/<int:person_id>', methods=['GET'])
@require_token()
def get_person(person_id):
    status, person = get_nif_api_client().get_person(person_id)
    return eve_response(person, 200 if status is True else 404)


@NIF.route('competences/<int:person_id>', methods=['GET'])
@require_token()
def get_person_competences(person_id):
    status, competences = get_nif_api_client().get_person_competences(person_id)

    if status is True:
        # Only valid competences?
        competences = [x for x in competences['competences'] if x['passed'] is True or x['expires'] is None]
        return eve_response(competences, 200)

    abort(404)


@NIF.route('competences/search', methods=['GET'])
@require_token()
def search_competences():
    status, competences = get_nif_api_client().search_competences(query={})

    if status is True:
        return eve_response(competences, 200)

    abort(404)


@NIF.route('licenses/<int:person_id>', methods=['GET'])
@require_token()
def get_person_licenses(person_id):
    """
    :param person_id:
    :return:
    """
    status, licenses = get_nif_api_client().get_person_licenses(person_id)
    return eve_response(licenses, 200 if status is True else 404)


@NIF.route('licenses/check/<int:person_id>', methods=['GET'])
@require_token()
def get_person_licenses_check(person_id):
    """
    Uses KA, no access in nif api
    :param person_id:
    :return:
    """
    status, licenses = get_nif_api_client().get_person_licenses_check(person_id)
    return eve_response(licenses, 200 if status is True else 404)


@NIF.route('licenses/org/<int:org_id>', methods=['GET'])
@require_token()
def get_organization_licenses(org_id):
    """
    Uses KA, no access in nif api
    :param org_id:
    :return:
    """
    status, licenses = get_nif_api_client().get_org_licenses(org_id)
    return eve_response(licenses, 200 if status is True else 404)


@NIF.route('licenses/fed/<string:xorg_id>', methods=['GET'])
@require_token()
def get_fed_licenses(xorg_id):
    """
    Uses KA, no access in nif api
    :param org_id:
    :return:
    """
    xorg_id = 'cfp50qbs0001uc7db6o0'
    status, licenses = get_nif_api_client().get_fed_licenses(xorg_id)
    return eve_response(licenses, 200 if status is True else 404)


@NIF.route('check/<int:person_id>', methods=['POST'])
@require_token()
def check_and_fix(person_id):
    """

    :param person_id:
    :return:
    """
    nif_competences_list = _get_nif_person_competences_list(person_id)
    person_status, person = _get_lungo_person(person_id)
    competences_status, person_competences = _get_lungo_person_competences(person_id)

    # 1. Competences in nif api not in membership api:
    delta = [x for x in nif_competences_list if x not in [x['id'] for x in person.get('competences', [])]]

    to_make_change_messages = [x for x in delta if x not in [c['id'] for c in person_competences]]

    change_messages = []
    for competence in to_make_change_messages:
        change_type = 'Modified'
        if competence not in [c['id'] for c in person_competences]:
            change_type = 'Created'

        status, r = _gen_change_msg(entity_id=competence, entity_type='Competence', change_type=change_type)
        if status in [200, 201]:
            change_messages.append({'id': competence, 'status': True})
        else:
            change_messages.append({'id': competence, 'status': False, 'err': r.text})

    return eve_response({
        'api_competences': [c['id'] for c in person_competences],
        'api_person_competences': [x['id'] for x in person['competences']],
        'nif_api': nif_competences_list,
        'delta_nif_person': delta,
        'change_messages': change_messages
    })


@NIF.route('ka/productchecker/<int:person_id>', methods=['GET'])
@require_token()
def product_checker(person_id):
    """
    Switch dry_run on method GET=True, POST=False
    @Todo: refactor and make the status from pc be a bit smarter so you can make correct response codes
    :param person_id:
    :return:
    """
    for r in [str(p) for p in app.url_map.iter_rules()]:
        if '/healthcheck' not in r:
            print(r)
    try:
        ka = KA(KA_USERNAME, KA_PASSWORD)
        pc = ProductChecker(ka=ka)
        status, response = pc.check(person_id, dry_run=True)
        return eve_response(response, 200 if status is False else 201)
    except:
        pass

    abort(500)


@NIF.route('flydrone/<int:person_id>', methods=['GET', 'POST'])
@require_token()
def flydrone(person_id):
    if request.method == 'GET':
        status, person = _get_lungo_person(person_id)
        if status is True:
            drone = person.get('_fids', {}).get('flydrone', None)
            if drone is not None:
                return eve_response(drone, 200)

        return eve_error_response(
            "The requested URL was not found on the server. If you entered the URL manually please check your spelling and try again.",
            404)

    elif request.method == 'POST':

        status, result = _register_flydrone(person_id)
        if status in [200, 201, 304]:  # result from patch, if status is False, error
            return eve_response(result, status)

    return eve_error_response(
        "The requested URL was not found on the server... If you entered the URL manually please check your spelling and try again.",
        404)
