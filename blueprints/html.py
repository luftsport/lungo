from flask import Blueprint, current_app as app, request, Response, abort, jsonify
from ext.auth.decorators import require_token
from ext.app.eve_helper import eve_response, eve_abort
from eve.methods.get import get_internal, getitem_internal, _perform_aggregation
from datetime import datetime
from blueprints.member_check import ACTIVITIES

Html = Blueprint('Html blueprint for returning html', __name__)


def _html_page(content):
    return f'<!doctype html><html lang=en-us><head><meta charset=utf-8></head><body>{content}</body></html>'


def _bullet_orgs(orgs):
    r = ''
    for org in orgs:
        r = r + '<li>{} {}</li>'.format(org['id'], org['name'])

    return f'<ul>{r}</ul>'


@Html.route('/list/<string:activity>', methods=['GET'])
def list_orgs(activity):
    if activity in ACTIVITIES.keys():
        lookup = {"type_id": 6, "main_activity.id": ACTIVITIES[activity]}
        orgs, _, _, status, _ = get_internal('organizations', **lookup)

        return _html_page(_bullet_orgs(orgs))
