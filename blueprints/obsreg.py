import json
import requests
from urllib.parse import urlencode
import base64
from flask import Blueprint, current_app as app, request, Response, abort, jsonify, g
from ext.app.eve_blueprint_helper import SwaggerBlueprint # parse_request, format_response,
from ext.auth.decorators import require_token
from ext.auth.clients import users as USERS
from ext.scf import OBSREG_API_URL
from ext.app.eve_helper import eve_response, eve_abort, eve_error_response
from eve.methods.get import getitem_internal
from eve.methods.post import post_internal
from eve.methods.patch import patch_internal
from datetime import datetime
from dateutil import parser
from operator import itemgetter

OBSREG = SwaggerBlueprint('OBSREG resources', __name__, url_prefix='obsreg')

@OBSREG.route("/persons/avatar/<int:person_id>", methods=['GET'])
@require_token()
def get_avatar(person_id):
    try:
        headers = {"Authorization": f"Basic {USERS[g.token]['client_token']}"}
        response = requests.get(f'{OBSREG_API_URL}/persons/avatar/{person_id}', headers=headers)
        if response.status_code == 200:
            return eve_response(response.json(), response.status_code)
    except Exception as e:
        app.logger.exception(f'Error fetching avatar for person {person_id}')
    return eve_error_response('Avatar not found', 404)