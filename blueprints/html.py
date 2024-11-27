from flask import Blueprint, current_app as app, request, Response, abort, jsonify
from ext.auth.decorators import require_token
from ext.app.eve_helper import eve_response, eve_abort
from eve.methods.get import get_internal, getitem_internal, _perform_aggregation
from datetime import datetime

ACTIVITIES = {
    'mikrofly': 237,
    'sportsfly': 237,
    'motorfly': 238,
    'fallskjerm': 109,
    'hps': 110,
    'seilfly': 111,
    'modellfly': 236,
    'ballong': 235
}

Html = Blueprint('Html blueprint for returning html', __name__)


def _html_page(content):
    return f'<!doctype html><html lang=en-us><head><meta charset=utf-8></head><body>{content}</body></html>'


def _bullet_orgs(orgs):
    r = ''
    for org in orgs:
        r = '{}<li>{} {}</li>'.format(r, org['id'], org['name'])

    return f'<ul>{r}</ul>'


@Html.route('/organizations/list/<string:activity>', methods=['GET'])
def list_orgs(activity):
    if activity in ACTIVITIES.keys():
        lookup = {"type_id": 6, "main_activity.id": ACTIVITIES[activity], "is_active": True}
        orgs, _, _, status, _ = get_internal('organizations', **lookup)

        return _html_page(_bullet_orgs(orgs.get('_items', [])))
