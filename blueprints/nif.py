from ext.auth.decorators import require_token, require_superadmin
from nif_tools import KA
import datetime
from hashlib import sha224
from flask import Blueprint, current_app as app, request, Response, abort, jsonify
# from eve.methods.post import post_internal
from ext.scf import KA_USERNAME, KA_PASSWORD
from ext.app.eve_helper import eve_response
from eve.methods.post import post_internal

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

    # Post internal instead!
    # r = requests.post('{}/integration/changes'.format(API_URL),
    #                  data=json.dumps(payload, cls=EveJSONEncoder),
    #                  headers=API_HEADERS)

    # if r.status_code in [200, 201]:
    #    return True, r.json()

    # return False, r.json() | r.text
    response, _, _, status, _ = post_internal(resource='integration_changes',
                                                 payl=payload,
                                                 skip_validation=True)

    return status, response


@NIF.route('/change', methods=['POST'])
#@require_token()
def generate_change_message():
    data = request.get_json()
    print('DATA', data)
    status, response = _gen_change_msg(data['entity_id'], data['entity_type'])
    return eve_response(response, status)
    #return {}, 201

@NIF.route('competences/<int:person_id>', methods=['GET'])
@require_token()
def get_person_competences(person_id):
    ka = KA(KA_USERNAME, KA_PASSWORD)
    status, competences = ka.get_person_competence(person_id)
    return eve_response(competences, status)


@NIF.route('licenses/<int:person_id>', methods=['GET'])
@require_token()
def get_person_licenses(person_id):
    ka = KA(KA_USERNAME, KA_PASSWORD)
    status, licenses = ka.get_person_licenses(person_id)
    return eve_response(licenses, status)
