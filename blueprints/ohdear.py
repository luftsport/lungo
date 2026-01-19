import json
from flask import Blueprint, current_app as app, request, Response, abort, jsonify
from eve.methods.post import post_internal
from ext.app.eve_blueprint_helper import SwaggerBlueprint, format_response  # parse_request, format_response,
from ext.auth.decorators import require_token
from ext.app.eve_helper import eve_response, eve_abort
import time
from bson.json_util import dumps
from ext.scf import SIO_URL, CHECK_SOCKETIO, CHECK_SYSTEMD_SERVICES, CHECK_SERVICES, CHECK_SERVER_HEALTH
from ext.app.ohdear import check_systemd_service_ohdear, check_service_health_ohdear, server_health_ohdear, check_mongo, find_process_by_filename, get_socket_ohdear_response, get_socket_ohdear_multi_response, SocketIOHealthChecker

Ohdear = SwaggerBlueprint('Ohdear resources', __name__, url_prefix='ohdear')



def clean_mongo_keys(doc):
    """
    Recursively replaces invalid characters in dictionary keys
    - $ → _dollar_
    - . → _dot_
    """
    if isinstance(doc, dict):
        new_doc = {}
        for key, value in doc.items():
            # Replace invalid chars
            new_key = key.replace('$', '_dollar_').replace('.', '_dot_')
            new_doc[new_key] = clean_mongo_keys(value)
        return new_doc

    elif isinstance(doc, list):
        return [clean_mongo_keys(item) for item in doc]

    else:
        return doc


@Ohdear.route('/api-doc', methods=['GET'])
@require_token()
def get_paths():
    resp = [str(p) for p in app.url_map.iter_rules() if str(p).startswith('/api/v1/ohdear')]
    return eve_response(resp)


@Ohdear.route("/", methods=['GET'])
@require_token(ohdear_allowed=True)
def check():
    result = {
        "checkResults": [
        ]
    }

    # @TODO add try except logic with fail messages
    # 1. systemd
    for systemd_service in CHECK_SYSTEMD_SERVICES:
        result['checkResults'].append(check_systemd_service_ohdear(service_name=systemd_service))

    # 2. daemons
    for service in CHECK_SERVICES.copy():
        checked = None
        if 'pid' in service and service['pid'] is None:
            try:
                process = find_process_by_filename(service['label'])
                if len(process) > 0:
                    service['pid'] = process[0]['pid']
                else:
                    service.pop('pid')

            except Exception as e:
                service.pop('pid')
                app.logger.exception(f'Error checking for service {service} by pid: {e}')

        checked = check_service_health_ohdear(**service)

        # If resync is running, don't fail integration sync
        if checked['status'] != 'ok' and service['name'] == 'Integration Syncronization':
            process = find_process_by_filename('resync')
            if len(process) > 0:
                service['pid'] = process[0]['pid']
                checked = check_service_health_ohdear(**service)
        result['checkResults'].append(checked)

    # 3. Server
    for server in CHECK_SERVER_HEALTH.copy():
        result['checkResults'].append(server_health_ohdear(**server))

    result['checkResults'].append(check_mongo())

    # 4. Scoket.io
    try:
        if CHECK_SOCKETIO is True:
            checker = SocketIOHealthChecker(SIO_URL)
            socket_results = [get_socket_ohdear_response(checker)]
            # socket_results = get_socket_ohdear_multi_response(checker)
            for item in socket_results:
                result['checkResults'].append(item)
            checker.close()

    except Exception as e:
        app.logger.exception(f'Error running the socket checks!')
        try:
            checker.close()
        except Exception as e:
            app.logger.exception(f'Error closing checker: {e}')

    # Done, add timestamp now
    result['finishedAt'] = f'{int(time.time())}'

    # Finally, we store the snapshot locally too
    try:
        response, _, _, status, _ = post_internal(resource='ohdear_snapshots',
                                                  payl=clean_mongo_keys(json.loads(dumps(result))),
                                                  skip_validation=True)
    except Exception as e:
        app.logger.exception(f'[Ohdear] Error post_interal result {e}')

    return jsonify(json.loads(dumps(result))), 200  # ,status_code=200,) #json.dumps(result, cls=EveJSONEncoder)
