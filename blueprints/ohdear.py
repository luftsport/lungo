import json
import requests
from urllib.parse import urlencode
import base64
from flask import Blueprint, current_app as app, request, Response, abort, jsonify
from ext.app.eve_blueprint_helper import SwaggerBlueprint, format_response  # parse_request, format_response,
# Not yet commited: from ext.app.eve_jsonencoder import EveJSONEncoder
from ext.auth.decorators import require_token
from ext.app.fids import fid_exists, create_fid, update_fid
from ext.scf import FAI_USERNAME, FAI_PASSWD, FAI_URL, COMPETENCE_FAI_MAPPING_IDS, FAI_ID_MAPPINGS_INV, COMPETENCE_FAI_MAPPING
from ext.app.eve_helper import eve_response, eve_abort
from eve.methods.get import getitem_internal
from eve.methods.post import post_internal
from eve.methods.patch import patch_internal
from datetime import datetime
from dateutil import parser
from operator import itemgetter
import time
from bson.json_util import dumps

Ohdear = SwaggerBlueprint('Ohdear resources', __name__, url_prefix='ohdear')

CHECK_SYSTEMD_SERVICES = ['mongod', 'nginx']
CHECK_SERVICES = [
    {'name': 'Notification Daemon (socket.io)', 'label': 'notifications', 'cmdline_contains': ['/www/lungo/bin/gunicorn', 'notification_daemon:app'], 'cwd': '/www/lungo', 'allow_multiple': True},
    {'name' : 'Integration Syncronization', 'label' : 'integration', 'pid_file' : '/home/einar/nif-integration/syncdaemon.pid'},
    {'name' : 'Integration Stream', 'label' : 'integration', 'pid_file' : '/home/einar/nif-integration/streamdaemon.pid'},
    {'name' : 'Membership API', 'label' : 'lungo', 'pid_file' : '/www/lungo/gunicorn.pid'},
    {'name' : 'NLF AUTH', 'label' : 'auth', 'pid_file' : '/home/einar/nlf-auth/gunicorn.pid'},
    {'name' : 'Spyne for Elefun', 'label' : 'elefun', 'cwd' : "/home/einar/spyne", 'cmdline_contains' : ['melwin.py'], 'allow_multiple' : True},
    {'name':'Membership API', 'label':'lungo', 'cwd':"/www/lungo", 'cmdline_contains':['/www/lungo/bin/gunicorn', 'run:app'], 'allow_multiple':True},
]
CHECK_SERVER_HEALT = [
    {'critical_disk_paths': ["/", "/var", "/home"], 'warning_percent': 75, 'critical_percent': 90}
]

@Ohdear.route('/api-doc', methods=['GET'])
@require_token()
def get_paths():
    resp = [str(p) for p in app.url_map.iter_rules() if str(p).startswith('/api/v1/ohdear')]
    return eve_response(resp)

from ext.app.ohdear import check_systemd_service_ohdear, check_service_health_ohdear, server_health_ohdear, check_mongo, perform_socketio_check, SIO_URL

@Ohdear.route("/", methods=['GET'])
@require_token()
def check():
    result = {
        "finishedAt": f"{int(time.time())}",
        "checkResults": [
        ]
    }

    for systemd_service in CHECK_SYSTEMD_SERVICES:
        result['checkResults'].append(check_systemd_service_ohdear(service_name=systemd_service))

    for service in CHECK_SERVICES:
        result['checkResults'].append(check_service_health_ohdear(**service))

    for server in CHECK_SERVER_HEALT:
        result['checkResults'].append(server_health_ohdear(**server))

    result['checkResults'].append(check_mongo())

    result['checkResults'].append(perform_socketio_check(SIO_URL))

    return jsonify(json.loads(dumps(result))), 200 #,status_code=200,) #json.dumps(result, cls=EveJSONEncoder)