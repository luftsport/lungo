from ext.auth.decorators import require_token, require_superadmin
from nif_tools import KA
import datetime
from hashlib import sha224
from flask import Blueprint, current_app as app, request, Response, abort, jsonify
# from eve.methods.post import post_internal
from ext.scf import KA_USERNAME, KA_PASSWORD, NIF_CLIENT_SECRET, NIF_CLIENT_ID, NIF_TOKEN_FILE
from ext.app.eve_helper import eve_response, eve_error_response
from eve.methods.post import post_internal
from eve.methods.get import getitem_internal, get_internal
from eve.methods.patch import patch_internal
from nif_rest_api_client import NifRestApiClient
from dateutil import parser
from nif_tools import KA
from ext.app.product_checker import ProductChecker
from ext.app.email import send_email

from functools import wraps
import inspect

NIF = Blueprint('NIF tools', __name__)

API = None


def _gen_flydrone_email(first_name, registration, registration_expiry, type_of_change):
    change_msg = {
        'created': 'created',
        'updated': 'updated',
        'new_registration': 'updated with a new registration number',
        'new_expiry': 'updated with a new expiry'
    }
    msg = f'Hi {first_name}\r\n\r\n'
    msg += f'Your registration at flydrone.no has been {type_of_change}.\r\n\r\n'
    msg += f'Registration number: {registration}\r\n'
    msg += f'Registration expiry: {registration_expiry}\r\n\r\n'
    msg += 'Remember to mark your model/drone with your operator number - this is mandatory\r\n\r\n'
    msg += 'This connects your drone registration to your membership in NLF. You can also view your registration at https://www.flydrone.no.\r\n\r\n'
    msg += 'This is an automatic generated message from the Norwegian Air Sports Federation, replies will not be answered.\r\n\r\n'

    return msg


def get_nif_api_client() -> NifRestApiClient:
    global API
    if API is None:
        return NifRestApiClient(client_id=NIF_CLIENT_ID, client_secret=NIF_CLIENT_SECRET, token_file=NIF_TOKEN_FILE)

    return API


def _gen_change_msg(entity_id, entity_type, change_type='Modified', org_id=376, realm='PROD'):
    payload = {}
    sequence_ordinal = datetime.datetime.utcnow()

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
                    (x['expires'] is None or parser.parse(x['expires']) > datetime.datetime.now())]
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
    return eve_response(response, 200 if status is True else 500)
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
        status, result = get_nif_api_client().register_drone_pilot(person_id)

        if status is True:
            status, person = _get_lungo_person(person_id)
            lookup = {'_id': person['_id']}

            _fids = person.get('_fids', {})

            # Verfify if changes and what
            type_of_change = None
            try:
                if 'flydrone' not in _fids:
                    type_of_change = 'created'
                else:
                    if result['operatorRegistrationNumber'] != _fids['flydrone']['operatorRegistrationNumber']:
                        type_of_change = 'new_registration_number'
                    elif result['expiredOperatorRegistrationNumberTime'] != _fids['flydrone'][
                        'expiredOperatorRegistrationNumberTime']:
                        type_of_change = 'new_expiry'
                    else:
                        type_of_change = 'updated'
            except Exception as e:
                app.logger.error('[FLYDRONE] Could not assign type of change')
                app.logger.exception(e)

            # Set to new/updated
            _fids['flydrone'] = result

            resp, _, _, patch_status = patch_internal('persons_process',
                                                      {'_fids': _fids},
                                                      False,
                                                      True,
                                                      **lookup)

            if patch_status in [200, 201]:
                # Create email and send!
                try:
                    send_email(
                        recepient=person['primary_email'],
                        subject='Flydrone.no registration',
                        message=_gen_flydrone_email(
                            person['first_name'],
                            result['operatorRegistrationNumber'],
                            result['expiredOperatorRegistrationNumberTime'],
                            type_of_change)
                    )
                except Exception as e:
                    app.logger.error('[FLYDRONE] error while sending email')
                    app.logger.exception(e)

            return eve_response(result, patch_status)

        return eve_error_response(
            "The requested URL was not found on the server. If you entered the URL manually please check your spelling and try again.",
            404)
