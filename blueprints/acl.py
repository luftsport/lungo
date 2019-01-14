from flask import Blueprint, current_app as app, request, Response, abort, jsonify
from ext.auth.decorators import require_token
from ext.app.eve_helper import eve_response, eve_abort
from eve.methods.get import get_internal, getitem_internal, _perform_aggregation
from datetime import datetime
import re

ACL = Blueprint('Acl helpers for the lazy programmer', __name__)

NLF_ORG = {27: 'nlf',
           237: 'mikro',
           238: 'motor',
           109: 'fallskjerm',
           110: 'hps',
           111: 'seil',
           236: 'modell',
           235: 'ballong'
           }


def _acl_from_functions(person_id):
    function_acl = []

    lookup = {'person_id': person_id,
              '$or': [{'to_date': {'$gt': datetime.now().isoformat()}}, {'to_date': {'$exists': False}}]
              }

    functions, _, _, status, _ = get_internal('functions', **lookup)

    if status == 200:

        for f in functions['_items']:

            org, _, _, fstatus = getitem_internal('organizations', **{'id': f['active_in_org_id']})

            if fstatus == 200 and org.get('type_id', 0) in [5, 2, 19]:  # 2 særforbund, 19 seksjon

                function_acl.append({'activity': org.get('main_activity', {'id': 27}).get('id'),
                                     'club': f['active_in_org_id'],
                                     'role': f['type_id'],
                                     'name': f['type_name'],
                                     'func': f['id']})

        return status, function_acl

    return status, function_acl


@ACL.route('/<int:person_id>', methods=['GET'])
@require_token()
def acl(person_id):
    status, function_acl = _acl_from_functions(person_id)

    if status == 200:
        return eve_response(function_acl, 200)

    return eve_abort(status)


@ACL.route('/simple/<int:person_id>', methods=['GET'])
@require_token()
def acl_simple(person_id):
    status, function_acl = _acl_from_functions(person_id)

    if status == 200:

        simple_acl = []
        for a in function_acl:
            if a['activity'] in list(NLF_ORG.keys()):  # and a['role'] in [10000000]:
                simple_acl.append('{}_{}'.format(
                    NLF_ORG[a['activity']],
                    ''.join(re.sub(r'[^a-zæøåA-ZÆØÅ0-9]', '_', a['name']).split()).lower().rstrip('_')))

        return eve_response(list(set(simple_acl)), 200)

    return eve_abort(status)


def acl_simple_all():
    functions, _, _, status, _ = get_internal('functions')

    if status == 200:
        pass


@ACL.route('/activities', methods=['GET'])
@require_token()
def acl_activities():
    return eve_response(NLF_ORG, 200)


@ACL.route('/clubs', methods=['GET'])
@require_token()
def acl_clubs():
    clubs, _, _, status, _ = get_internal('organizations', **{'type_id': {'$in': [5, 2, 19]}})

    if status == 200:
        return eve_response([d['id'] for d in clubs['_items']])

    return eve_response([], status)


@ACL.route('/clubs/activity/<int:activity_id>', methods=['GET'])
@require_token()
def acl_activities_clubs(activity_id):
    clubs, _, _, status, _ = get_internal('organizations',
                                          **{'type_id': {'$in': [5, 2, 19]}, 'main.activity.id': activity_id})

    if status == 200:
        return eve_response(list(set([d['id'] for d in clubs['_items']])), status)

    return eve_response([], status)


@ACL.route('/roles', methods=['GET'])
@require_token()
def acl_roles():
    functions, _, _, status, _ = get_internal('functions_types_count')

    if status == 200:
        funcs = [{'type_id': f['_id'].get('type_id', 0), 'name': f['_id'].get('name', False)} for f in
                 functions['_items']]

        # funcs = list({v['type_id']: v for v in funcs}.values())
        funcs[:] = [d for d in funcs if d.get('name', False) is not False]

        return eve_response(funcs, status)

    return eve_response([], status)


@ACL.route('/roles/activity/<int:activity_id>', methods=['GET'])
@require_token()
def acl_activity_roles(activity_id):
    clubs, _, _, status, _ = get_internal('organizations',
                                          **{'type_id': {'$in': [5, 2, 19]}, 'main_activity.id': activity_id})

    if status == 200:
        clubs = list(set([d['id'] for d in clubs['_items']]))

        resource = 'functions_types_activity_count'
        datasource = app.config['DOMAIN'][resource]['datasource']
        aggregation = datasource.get('aggregation')

        if aggregation:
            aggregation['pipeline'][0]['$match']['active_in_org_id']['$in'] = clubs
            functions, _, _, agg_status, _ = _perform_aggregation(resource, aggregation['pipeline'],
                                                                  aggregation['options'])

            if agg_status == 200:
                funcs = [{'type_id': f['_id'].get('type_id', 0), 'name': f['_id'].get('name', '')} for f in
                         functions['_items']]

                return eve_response(funcs, status)

    return eve_response([], status)


@ACL.route('/roles/club/<int:club_id>', methods=['GET'])
@require_token()
def acl_club_roles(club_id):
    resource = 'functions_types_org_count'
    datasource = app.config['DOMAIN'][resource]['datasource']
    aggregation = datasource.get('aggregation')
    print(aggregation)
    if aggregation:

        aggregation['pipeline'][0]['$match']['active_in_org_id'] = club_id

        functions, _, _, status, _ = _perform_aggregation(resource, aggregation['pipeline'], aggregation['options'])

        if status == 200:
            funcs = [{'type_id': f['_id'].get('type_id', 0), 'name': f['_id'].get('name', '')} for f in
                     functions['_items']]

            return eve_response(funcs, status)

    return eve_response([], status)