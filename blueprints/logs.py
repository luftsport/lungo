# blueprints/logs.py
from flask import Blueprint, jsonify, request, current_app as app
from pymongo import MongoClient
from datetime import datetime, timedelta
from ext.app.eve_helper import eve_response
from ext.app.eve_blueprint_helper import parse_request, parsed_to_pymongo
from ext.scf import LOG_URI, LOG_DATABASE, LOG_COLLECTION
from ext.auth.decorators import require_token

Logs = Blueprint('Logs', __name__, url_prefix='logs')


@Logs.route('/api-doc', methods=['GET'])
@require_token()
def get_paths():
    resp = [str(p) for p in app.url_map.iter_rules() if str(p).startswith('/api/v1/logs')]
    return eve_response(resp)


@Logs.route('/', methods=['GET'])
@require_token()
def get_logs_from_mongo():
    logs_client = MongoClient(LOG_URI)
    try:
        args = parse_request(resource=LOG_DATABASE, is_blueprint=True)
    except Exception as e:
        args = {}
        args['page'] = int(request.args.get('page', 1))
        args['max_results'] = int(request.args.get('max_results', 25))

    collection = logs_client.get_database(LOG_DATABASE).get_collection(LOG_COLLECTION)

    cursor = parsed_to_pymongo(parsed=args, collection=collection)

    logs = list(cursor)

    # Convert ObjectIds to strings for JSON
    for log in logs:
        if '_id' in log:
            log['_id'] = str(log['_id'])

    return jsonify({
        '_items': logs,
        '_meta': {
            'page': args['page'],
            'max_results': args['max_results'],
            'total': collection.count_documents(args.get('where') or {})
        }
    })
