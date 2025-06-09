from flask import Blueprint, current_app as app, request, Response, abort, jsonify, g
from ext.auth.decorators import require_token
from ext.app.eve_helper import eve_response, eve_abort
from eve.methods.get import get_internal, getitem_internal, _perform_aggregation
from eve.methods.post import post_internal
from datetime import datetime
from ext.scf import API_HEADERS, API_BASE_URL
import requests
from uuid import uuid4
import json

Notifications = Blueprint('Notifications', __name__)


def get_person_from_role(role) -> (bool, [int]):
    resp = requests.get(
        '%s/functions?where={"active_in_org_id": %s, "type_id": %s, "is_deleted": false, "is_passive": false}&projection={"person_id": 1}'
        % (API_BASE_URL, role.get('org'), role.get('role')),
        headers=API_HEADERS, verify=app['config'].get('REQUESTS_VERIFY', True))

    if resp.status_code == 200:
        try:
            r = resp.json()
            if '_items' in r:
                if len(r['_items']) == 1:
                    return True, [r['_items'][0]['person_id']]
                elif len(r['_items']) > 1:
                    return True, [i['person_id'] for i in r['_items']]
        except Exception as e:
            pass

    return False, None


def get_person_email(person_id) -> (bool, dict):
    resp = requests.get('{}/persons/{}?projection={{"full_name": 1, "primary_email": 1}}'.format(API_BASE_URL, person_id),
                        headers=API_HEADERS,
                        verify=app['config'].get('REQUESTS_VERIFY', True))

    if resp.status_code == 200:
        try:
            r = resp.json()
            email = r['primary_email']
            name = r.get('full_name', '')
            return True, {'full_name': name, 'email': email}
        except Exception as e:
            pass

    return False, None


def get_org_name(org_id):
    resp = requests.get('{}/{}/{}?projection={{"name": 1}}'.format(API_BASE_URL, 'organizations', org_id),
                        headers=API_HEADERS,
                        verify=app['config'].get('REQUESTS_VERIFY', True))

    if resp.status_code == 200:
        return True, resp.json().get('name', 'Ukjent Klubb')

    return False, 'Ukjent klubb'


def get_person_name(person_id):
    resp = requests.get('{}/{}/{}?projection={{"full_name": 1}}'.format(API_BASE_URL, 'persons', person_id),
                        headers=API_HEADERS,
                        verify=app['config'].get('REQUESTS_VERIFY', True))

    if resp.status_code == 200:
        return True, resp.json().get('full_name', 'Ukjent person')

    return False, 'Ukjent person'


def get_orgs_in_activivity(activity_id, org_type_ids=[6, 14, 19]):
    """
    Aggregation
    :param activity_id:
    :param org_type_ids:
    :return:
    """
    resp = requests.get(
        '{}/organizations/activity?aggregate={{"$activity": {}, "$type_ids": {}}}'.format(API_BASE_URL,
                                                                                          activity_id,
                                                                                          org_type_ids),
        headers=API_HEADERS
    )

    if resp.status_code == 200:
        try:
            return resp.json().get('_items', [{}])[0].get('org_ids', [])
        except IndexError as e:
            pass
        except Exception as e:
            pass

    return []


def get_users_from_role(role):
    """
    Get person_ids from a role
    :param role:
    :return:
    """
    query = ''
    if ('role' and 'org' and 'activity') in role:

        if role['org'] is not None and role['org'] != '*' and role['org'] > 0:
            query = f'where={{"org_id": {role["org"]}, "type_id": {role["role"]}, "is_deleted": false, "is_passive": false}}&projection={{"person_id": 1}}'
        elif role['org'] == '*' and role['activity'] is not None and role['activity'] > 0:
            orgs_from_activity = get_orgs_in_activivity(role['activity'])
            query = f'where={{"org_id": {{"$in": {orgs_from_activity}}}, "type_id": {role["role"]}, "is_deleted": false, "is_passive": false}}&projection={{"person_id": 1}}'
        elif (role['org'] and role['activity']) == '*':
            query = f'where={{"type_id": {role["role"]}, "is_deleted": false, "is_passive": false}}&projection={{"person_id": 1}}'

        resp = requests.get('{}/functions?{}'.format(API_BASE_URL, query), headers=API_HEADERS)  # verify=app['config'].get('REQUESTS_VERIFY', True)

        if resp.status_code == 200:
            try:
                return list(set([item['person_id'] for item in resp.json().get('_items', [])]))
            except IndexError as e:
                pass

    return []


def get_recepient(person_id):
    return get_recepients([person_id])


def get_recepients(recepients):
    persons = []

    try:
        query = 'where={{"id": {{"$in": {} }}}}&projection={{"full_name": 1, "address.email": 1}}'.format(recepients)
        resp = requests.get('{}/{}?{}'.format(API_BASE_URL, 'persons', query), headers=API_HEADERS)

        if resp.status_code == 200:

            for person in resp.json()['_items']:
                if not '_merged_to' in person:
                    try:
                        persons.append({
                            'full_name': person.get('full_name', ''),
                            'email': person.get('address', {}).get('email', [])[0]})
                    except Exception as e:
                        pass

        return list({v['email']: v for v in persons if len(v['email']) > 4}.values())

    except:
        pass

    return persons


def get_recipients_from_roles(roles):
    persons = []

    try:
        for role in roles:
            resp = requests.get(
                '{}/functions?where={{"org_id": {}, "type_id": {}, "is_deleted": false, "is_passive": false }}&projection={{"person_id": 1}}'.format(
                    API_BASE_URL, role.get('org', 0), role.get('role', 0)),
                headers=API_HEADERS)

            if resp.status_code == 200:
                for item in resp.json().get('_items', []):
                    persons.append(item.get('person_id', 0))

        return get_recepients(list(set([i for i in persons if i > 0])))
    except:
        pass

    return persons


def get_users_from_competences(competences):
    persons = []

    try:
        for competence in competences:
            resp = requests.get(
                '{}/competences?where={{"type_id": {}, "passed": true, "valid_until": {{"$gte": "{}" }} }}&projection={{"person_id": 1}}'.format(
                    API_BASE_URL, competence, datetime.utcnow().isoformat()),
                headers=API_HEADERS)

            if resp.status_code == 200:
                return list(set([item['person_id'] for item in resp.json().get('_items', [])]))
    except:
        pass

    return persons


@Notifications.route('/notify', methods=['POST'])
@require_token()
def notify():
    """Get a list of recipients (static), recipients as a result of functions, competences etc (dynamic or static)
    Add to notifications, then a stream handler will act upon the generated notifications
    - choose given or best suited channel
    - apply status when applicable
    - similar to obsreg's notifications"""
    pass


@Notifications.route('/smtp', methods=['POST'])
@require_token()
def email2notification():
    """Get a list of recipients (static), recipients as a result of functions, competences etc (dynamic or static)
    Add to notifications, then a stream handler will act upon the generated notifications
    - choose given or best suited channel
    - apply status when applicable
    - similar to obsreg's notifications"""
    data = request.get_json()

    if not data or 'recipients' not in data or 'subject' not in data or 'message' not in data:
        print(data)
        return eve_abort(400, "Invalid request data")

    if ('roles' and 'competences' and 'users') in data['recipients'].keys():
        recipients = data['recipients']['users']

        for role in data['recipients']['roles']:
            print(role)
            recipients.extend(get_users_from_role(role))

        for competence in data['recipients']['competences']:
            recipients.extend(get_users_from_competences(competence))

    elif 'users' in data['recipients']:
        recipients = data['recipients']['users']
    else:
        return eve_abort(400, "Invalid recipients format")

    recipients = list(set(recipients))
    if 'from' not in data:
        data['from'] = 0  # Default sender is the current user
    # Build message:
    subject = data['subject']
    message = data['message']

    payload = {
        'type': 'email',
        'uuid': None,  # Will be generated by the system
        'data': {
            'subject': subject,
            'message': message
        },
        'recipient': None,  # Will be set for each recipient
        'sender': data['from'],  # The sender's user ID
        'event_id': data.get('event_id', str(uuid4())),  # Optional event ID if applicable
        'event_created': datetime.utcnow(),
        'event_from': data.get('event_from', 'smtp_notification'),  # The source of the event
        'event_from_id': data.get('event_from_id', str(uuid4())),  # Optional ID of the event source
        'dismissible': False,  # Can the notification be dismissed?
        'dismissed': False,  # Will be set when the notification is dismissed
        'transport': 'email',  # The transport method
        'transport_mode': 'immediate',  # How the notification is sent
        'status': 'created',  # Initial status of the notification
        'acl': {
            'read': {'users': [], 'roles': []},
            'write': {'users': [], 'roles': []},
            'create': {'users': [], 'roles': []},
            'delete': {'users': [], 'roles': []},
        }
    }

    for recipient in list(set(recipients)):
        if isinstance(recipient, int):
            # If recipient is a user ID, fetch their email
            pld = payload.copy()
            pld['recipient'] = recipient
            pld['uuid'] = str(uuid4())  # Generate a unique UUID for the notification
            pld['acl']['read']['users'] = [recipient]

            response, _, _, status, _ = post_internal(resource='notifications',
                                                      payl=pld,
                                                      skip_validation=True)
            pld = None
            # resp = requests.post('{}/notifications/smtp'.format(API_BASE_URL), data=json.dumps(payload, cls=EveJSONEncoder), headers=API_HEADERS)
            if status not in [200, 201]:
                app.logger.error(f"Failed to create notification for recipient {recipient}: {response}")
                return eve_abort(404, "Error happened")

    # Here you would typically send the email using your email service
    # For now, we just return a success response
    return jsonify({"status": "success", "id": payload['event_id'], "message": f"Notifications created successfully for the following users: {recipients}"}), 201
