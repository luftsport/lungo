from ext.auth.decorators import require_token, require_superadmin
from nif_tools import KA
import datetime
from hashlib import sha224
from flask import Blueprint, current_app as app, request, Response, abort, jsonify
# from eve.methods.post import post_internal
from ext.scf import KA_USERNAME, KA_PASSWORD
from ext.app.eve_helper import eve_response
from eve.methods.post import post_internal
from eve.methods.get import getitem_internal, get_internal

NIF = Blueprint('NIF tools', __name__)


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


def _get_person_competences(person_id):
    ka = KA(KA_USERNAME, KA_PASSWORD)
    return ka.get_person_competence(person_id)


def _get_person_licenses(person_id):
    ka = KA(KA_USERNAME, KA_PASSWORD)
    return ka.get_person_licenses(person_id)


def _get_api_person(person_id):
    response, _, _, status = getitem_internal(resource='persons', **{'id': person_id})

    if status == 200:
        return True, response

    return False, {}


def _get_api_person_competences(person_id):
    response, _, _, status, _ = get_internal(resource='competences', **{'person_id': person_id})

    if status == 200:
        return True, response.get('_items', [])

    return False, {}


@NIF.route('/change', methods=['POST'])
@require_token()
def generate_change_message():
    data = request.get_json()
    status, response = _gen_change_msg(data['entity_id'], data['entity_type'])
    return eve_response(response, status)
    # return {}, 201


@NIF.route('competences/<int:person_id>', methods=['GET'])
@require_token()
def get_person_competences(person_id):
    status, competences = _get_person_competences(person_id)
    return eve_response(competences, status)


@NIF.route('licenses/<int:person_id>', methods=['GET'])
@require_token()
def get_person_licenses(person_id):
    status, licenses = _get_person_licenses(person_id)
    return eve_response(licenses, status)


@NIF.route('check/<int:person_id>', methods=['POST'])
@require_token()
def check_and_fix(person_id):
    """Compares data from ka and internal, if needed, generate change messages"""
    ka_status, ka_competences = _get_person_competences(person_id)
    # ka_licenses = _get_person_licenses(person_id)
    person_status, person = _get_api_person(person_id)
    competences_status, person_competences = _get_api_person_competences(person_id)

    # 1. Competences in ka not in api:
    delta = [c['CompetenceId'] for c in ka_competences if c['CompetenceId'] not in [x['id'] for x in person.get('competences', [])]]

    to_make_change_messages = [x for x in delta if x not in [c['id'] for c in person_competences]]

    change_messages = []
    for competence in to_make_change_messages:
        change_type = 'Modified'
        if competence not in [c['id'] for c in person_competences]:
            change_type = 'Created'

        s, r = _gen_change_msg(entity_id=competence, entity_type='Competence', change_type=change_type)
        if s in [200, 201]:
            change_messages.append({'id': competence, 'status': True})
        else:
            change_messages.append({'id': competence, 'status': False, 'err': r.text})


    return eve_response({
        'api_competences': [c['id'] for c in person_competences],
        'api_person_competences': [x['id'] for x in person['competences']],
        'klubbadmin': [c['CompetenceId'] for c in ka_competences],
        'delta_ka_person': delta,
        'change_messages': change_messages
    })