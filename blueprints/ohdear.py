import json
from flask import Blueprint, current_app as app, request, Response, abort, jsonify
from ext.app.eve_blueprint_helper import SwaggerBlueprint, format_response  # parse_request, format_response,
from ext.auth.decorators import require_token
from ext.app.eve_helper import eve_response, eve_abort
import time
from bson.json_util import dumps
from ext.scf import SIO_URL
from ext.app.ohdear import check_systemd_service_ohdear, check_service_health_ohdear, server_health_ohdear, check_mongo, find_process_by_filename, get_socket_ohdear_response, get_socket_ohdear_multi_response, SocketIOHealthChecker

Ohdear = SwaggerBlueprint('Ohdear resources', __name__, url_prefix='ohdear')

CHECK_SYSTEMD_SERVICES = ['mongod', 'nginx']
CHECK_SERVICES = [

    {'name': 'Integration Syncronization', 'label': 'integration', 'pid_file': '/home/einar/nif-integration/syncdaemon.pid'},
    {'name': 'Integration Stream', 'label': 'integration', 'pid_file': '/home/einar/nif-integration/streamdaemon.pid'},
    {'name': 'NLF AUTH', 'label': 'auth', 'pid_file': '/home/einar/nlf-auth/gunicorn.pid'},
    {'name': 'Spyne for Elefun', 'label': 'elefun', 'cwd': "/home/einar/spyne", 'cmdline_contains': ['melwin.py'], 'allow_multiple': False},
    # {'name': 'Membership API', 'label': 'lungo', 'cwd': "/www/lungo", 'cmdline_contains': ['/www/lungo/bin/gunicorn', 'run:app'], 'allow_multiple': True},
    {'name': 'Membership API', 'label': 'lungo', 'pid_file': '/www/lungo/gunicorn.pid'},
    {'name': 'Mailchimp Lungo Daemon', 'label': 'mailchimp_daemon.py', 'pid': None, 'allow_multiple': False},
    {'name': 'Melwin Lungo Daemon', 'label': 'melwin_daemon.py', 'pid': None, 'allow_multiple': False},
    {'name': 'Sendgrid Lungo Daemon', 'label': 'sendgrid_daemon.py', 'pid': None, 'allow_multiple': False},
    {'name': 'Notification Daemon (socket.io)', 'label': 'notifications', 'cmdline_contains': ['/www/lungo/bin/gunicorn', 'notification_daemon:app'], 'cwd': '/www/lungo', 'allow_multiple': True},

]
CHECK_SERVER_HEALTH = [
    {'critical_disk_paths': ["/", "/var", "/home"], 'warning_percent': 75, 'critical_percent': 90}
]


@Ohdear.route('/api-doc', methods=['GET'])
@require_token()
def get_paths():
    resp = [str(p) for p in app.url_map.iter_rules() if str(p).startswith('/api/v1/ohdear')]
    return eve_response(resp)


@Ohdear.route("/", methods=['GET'])
@require_token(ohdear_allowed=True)
def check():
    result = {
        "finishedAt": f"{int(time.time())}",
        "checkResults": [
        ]
    }

    # @TODO add try except logic with fail messages
    for systemd_service in CHECK_SYSTEMD_SERVICES:
        result['checkResults'].append(check_systemd_service_ohdear(service_name=systemd_service))

    for service in CHECK_SERVICES:
        if 'pid' in service and service['pid'] is None:
            process = []
            try:
                process = find_process_by_filename(service['label'])
                if len(process) > 0:
                    service['pid'] = process[0]['pid']
                else:
                    service.pop('pid')
            except Exception as e:
                service.pop('pid')
                app.logger.exception(f'Error checking for service {service} by pid: {e}')
        result['checkResults'].append(check_service_health_ohdear(**service))

    for server in CHECK_SERVER_HEALTH:
        result['checkResults'].append(server_health_ohdear(**server))

    result['checkResults'].append(check_mongo())

    try:
        checker = SocketIOHealthChecker(SIO_URL)
        socket_results = [get_socket_ohdear_response(checker)]
        # socket_results = get_socket_ohdear_multi_response(checker)
        for item in socket_results:
            result['checkResults'].append(item)

    except Exception as e:
        app.logger.exception(f'Error running the socket checks!')

    return jsonify(json.loads(dumps(result))), 200  # ,status_code=200,) #json.dumps(result, cls=EveJSONEncoder)
