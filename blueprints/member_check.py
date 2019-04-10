from flask import Blueprint, current_app as app, request, Response, abort, jsonify
from ext.auth.decorators import require_token
from ext.app.eve_helper import eve_response, eve_abort
from eve.methods.get import get_internal, getitem_internal, _perform_aggregation
from datetime import datetime

MemberCheck = Blueprint('Member check by person id', __name__)

ACTIVITIES = {
    'mikrofly': 237,
    'motorfly': 238,
    'fallskjerm': 109,
    'hps': 110,
    'seilfly': 111,
    'modellfly': 236,
    'ballong': 235
}

ERR = {
    '_status': 'ERR',
    '_error': {
        'code': 404,
        'message': ''
    }
}


@MemberCheck.route('/<string:activity>/<int:person_id>', methods=['GET'])
@require_token()
def member_check(activity, person_id):
    if activity in ACTIVITIES.keys() and person_id > 0:

        lookup = {'activities.PathName': 'Luftsport/{}'.format(activity.capitalize()),
                  'Id': person_id}
        #  '$or': [{'MelwinId': person_id}, {'Id': person_id}]}

        members, _, _, status, _ = get_internal('ka_members', **lookup)

        try:

            if status == 200:
                if '_items' in members and len(members['_items']) == 1:

                    parents = []
                    for a in members['_items'][0]['activities']:
                        if a['PathName'] == "Luftsport/Modellfly":
                            for club in a["ParentOrgIds"]:
                                parents.append(club)

                    parents = list(set(parents))

                    for p in members['_items'][0]['clubs_payment']:

                        if p['PaymentStatus'] == 1 and datetime.datetime.now().month not in [11, 12, 1]:
                            continue

                        if p['ClubId'] in parents and p['PaymentStatus'] in [1, 4]:  # 4 betalt, 1 til forfall

                            return eve_response(
                                {'valid': True,
                                 'full_name': members['_items'][0]['FullName'],
                                 'id': person_id,
                                 'activity': activity,
                                 '_updated': str(members['_items'][0]['_updated'])
                                 # datetime.datetime.fromtimestamp(members['_items'][0]['_updated']['$date'])
                                 }, 200)

                    ERR['_error']['message'] = 'Membership not registered paid'
                    ERR['_error']['code'] = 402
                    return eve_response(ERR, 402)

                elif len(members['_items']) == 0:
                    ERR['_error']['message'] = 'Member not found for activity'
                    ERR['_error']['code'] = 404
                    return eve_response(ERR, 404)
        except:
            pass

    ERR['_error']['message'] = 'You do not have access to the resource'
    ERR['_error']['code'] = 403
    return eve_response(None, 403)

    return eve_response({'valid': False,
                         'full_name': None,
                         'id': person_id,
                         'activity': activity,
                         '_updated': None
                         }, 200)
