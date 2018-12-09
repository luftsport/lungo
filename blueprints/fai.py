import requests
from urllib.parse import urlencode
import base64
from flask import Blueprint, current_app as app, request, Response, abort, jsonify
from ext.auth.decorators import require_token
from ext.auth.clients import FAI_USERNAME, FAI_PASSWD, FAI_URL
from ext.app.eve_helper import eve_response, eve_abort

Fai = Blueprint('FAI resources', __name__)


def make_params():
    params = {'auth_username': FAI_USERNAME,
              'auth_password': base64.b64encode(FAI_PASSWD), 'country': 'NOR'}

@Fai.route("/licenses", methods=['GET'])
@require_token()
def get_licenses():

    response = requests.get('{}?{}'.format(FAI_URL, urlencode(make_params())))

    return eve_response(response.json(), response.status_code)
