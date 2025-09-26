import json
import requests
from ext.scf import TMS_URL, TMS_LICENSE_PATH, TMS_USERNAME, TMS_PASSWORD
from flask import Blueprint, current_app as app, request, Response, abort, jsonify
from ext.app.eve_blueprint_helper import SwaggerBlueprint # parse_request, format_response,
from ext.auth.decorators import require_token
from ext.app.eve_helper import eve_response, eve_abort
from datetime import datetime
from dateutil import parser

Tms = SwaggerBlueprint('TMS resources', __name__, url_prefix='tms')

class TMSAPI:

    def __init__(self, username=TMS_USERNAME, password=TMS_PASSWORD):
        self.base_url = TMS_URL
        self.license_path = TMS_LICENSE_PATH
        self.username = username
        self.password = password

    def _get(self, url, headers=None, params=None):
        response = requests.get(url, headers=headers, params=params, auth=(self.username, self.password))
        if response.status_code == 200:
            return response.status_code, response.json()

        return response.status_code, response.text

    def get_license(self, tms_id):
        url = f'{self.base_url}{self.license_path}/{tms_id}'
        status, response = self._get(url)
        return status, response

    def get_licenses(self, params=None):
        url = self.base_url + self.license_path
        status, response = self._get(url, params=params)
        return status, response


@Tms.route('/api-doc', methods=['GET'])
@require_token()
def get_paths():
    resp = [str(p) for p in app.url_map.iter_rules() if str(p).startswith('/api/v1/tms')]
    return eve_response(resp)

@Tms.route("/licenses", methods=['GET'])
@require_token()
def get_licenses():
    status, result = TMSAPI().get_licenses(params=request.args.to_dict())
    if status == 200:
        return eve_response(result)
    return eve_abort(status, result)

@Tms.route("/licenses/<int:license_id>", methods=['GET'])
@require_token()
def get_license(license_id):
    status, result = TMSAPI().get_license(license_id)
    if status == 200:
        return eve_response(result)
    return eve_abort(status, result)