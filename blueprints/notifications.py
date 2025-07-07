from flask import Blueprint, current_app as app, request, Response, abort, jsonify, g
from ext.auth.decorators import require_token
from ext.app.eve_helper import eve_response, eve_abort
from eve.methods.get import get_internal, getitem_internal, _perform_aggregation
from eve.methods.post import post_internal
from eve.methods.patch import patch_internal
from datetime import datetime
from ext.scf import API_HEADERS, API_BASE_URL
import requests
from uuid import uuid4
import json
from io import BytesIO
import json
import base64
from werkzeug.utils import secure_filename
from jinja2 import Template as JT
from bs4 import BeautifulSoup
from bson import ObjectId

Notifications = Blueprint('Notifications', __name__)

from ext.scf import (
    SENDGRID_DEFAULT_FROM,
    SENDGRID_DEFAULT_REPLY_TO,
    SENDGRID_DEFAULT_PREAMBLE,
    SENDGRID_DEFAULT_HEADERS,
    SENDGRID_DEFAULT_UNSUBSCRIBE,
    SENDGRID_DEFAULT_REPLY_TO
)


# DIsable jinja templating cache
# app.config['TEMPLATES_AUTO_RELOAD'] = True

def get_person_from_role(role) -> (bool, [int]):
    resp = requests.get(
        '%s/functions?where={"active_in_org_id": %s, "type_id": %s, "is_deleted": false, "is_passive": false}&projection={"person_id": 1}&max_results={}'
        % (API_BASE_URL, role.get('org'), role.get('role'), 20000),
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

    # role = {key: int(value) for key, value in role.items()}
    if ('role' and 'org' and 'activity') in role:

        if role['org'] is not None and role['org'] != '*' and role['org'] > 0:
            query = f'where={{"org_id": {role["org"]}, "type_id": {role["role"]}, "is_deleted": false, "is_passive": false}}&projection={{"person_id": 1}}'
        elif role['org'] == '*' and role['activity'] is not None and role['activity'] != '*' and role['activity'] > 0:
            orgs_from_activity = get_orgs_in_activivity(role['activity'])
            query = f'where={{"org_id": {{"$in": {orgs_from_activity}}}, "type_id": {role["role"]}, "is_deleted": false, "is_passive": false}}&projection={{"person_id": 1}}'
        elif (role['org'] and role['activity']) == '*':
            query = f'where={{"type_id": {role["role"]}, "is_deleted": false, "is_passive": false}}&projection={{"person_id": 1}}'

        resp = requests.get('{}/functions?{}&max_results={}'.format(API_BASE_URL, query, 20000), headers=API_HEADERS)  # verify=app['config'].get('REQUESTS_VERIFY', True)

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
        query = 'where={{"id": {{"$in": {} }}}}&projection={{"full_name": 1, "address.email": 1}}&max_results={}'.format(recepients)
        resp = requests.get('{}/{}?{}'.format(API_BASE_URL, 'persons', query, 20000), headers=API_HEADERS)

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
                '{}/functions?where={{"org_id": {}, "type_id": {}, "is_deleted": false, "is_passive": false }}&projection={{"person_id": 1}}&max_results={}'.format(
                    API_BASE_URL, role.get('org', 0), role.get('role', 0), 20000),
                headers=API_HEADERS)

            if resp.status_code == 200:
                for item in resp.json().get('_items', []):
                    persons.append(item.get('person_id', 0))

        return get_recepients(list(set([i for i in persons if i > 0])))
    except Exception as e:
        app.logger.error(f"Error fetching users from functions: {e}")

    return persons


def get_users_from_competences(competences):
    persons = []
    try:
        for competence in competences:
            resp = requests.get(
                '{}/competences?where={{"type_id": {}, "passed": true, "valid_until": {{"$gte": "{}Z" }} }}&max_results={}projection={{"person_id": 1}}'.format(
                    API_BASE_URL, competence, datetime.utcnow().isoformat(), 20000),
                headers=API_HEADERS)

            if resp.status_code == 200:
                for item in resp.json().get('_items', []):
                    persons.append(item.get('person_id', 0))

            return list(set([item['person_id'] for item in resp.json().get('_items', [])]))
    except Exception as e:
        app.logger.error(f"Error fetching users from competences: {e}")

    return persons


def get_users_from_competence(competence):
    persons = []
    try:
        resp = requests.get(
            '{}/competences?where={{"type_id": {}, "passed": true, "valid_until": {{"$gte": "{}Z" }} }}&max_results={}projection={{"person_id": 1}}'.format(
                API_BASE_URL, competence, datetime.utcnow().isoformat(), 20000),
            headers=API_HEADERS)

        if resp.status_code == 200:
            for item in resp.json().get('_items', []):
                persons.append(item.get('person_id', 0))

        return list(set([item['person_id'] for item in resp.json().get('_items', [])]))
    except Exception as e:
        app.logger.error(f"Error fetching users from competences: {e}")

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


@Notifications.route('/test', methods=['GET'])
@require_token()
def test_notification():
    from eve.utils import parse_request
    print(parse_request('dev').where, parse_request('persons').max_results, parse_request('persons').projection)
    return eve_response(parse_request('notifications').where + str(parse_request('notifications').max_results) + parse_request('notifications').projection)

@Notifications.route('/send/<string:_id>', methods=['POST'])
@require_token()
def send_notification_messages(_id):
    """Send notification messages by ID"""
    print(_id)
    try:
        notification, _, _, status = getitem_internal(resource='notifications', **{'_id': _id})
    except Exception as e:
        print('Error', e)
        return eve_abort(500, "Error fetching notification")

    print("Notification:", status, notification)
    # Check "If-Match" header for optimistic concurrency control
    if status == 200 and notification.get('status', None) == 'generated' and request.headers.get('If-Match', None) == notification.get('_etag', 'nope'):

        notifications = app.data.driver.db['notifications']
        notifications_messages = app.data.driver.db['notifications_messages']
        # Check if the notification is already processed
        n_status = notifications.update_one({'_id': ObjectId(_id)}, {'$set': {'status': 'pending'}})
        if n_status.modified_count == 0:
            return eve_abort(404, "Notification not found or already processed")

        nm_status = notifications_messages.update_many({'event_id': ObjectId(_id)}, {'$set': {'status': 'ready'}})
        if nm_status.modified_count == 0:
            return eve_abort(404, "Notification messages not found or already processed")
        # Update the status of the notification to 'finished'
        nu_status = notifications.update_one({'_id': ObjectId(_id)}, {'$set': {'status': 'finished'}})
        if nu_status.modified_count == 0:
            return eve_abort(404, "Notification not found or already processed")

        return eve_response({"status": "success", "message": f"{nm_status.modified_count} notification messages sent successfully"}, 201)

    return eve_abort(404, "Notification not found or already processed")

@Notifications.route('/generate/<string:_id>', methods=['POST', 'GET'])
@require_token()
def generate_notifications(_id):
    try:
        response, _, _, status = getitem_internal(resource='notifications', **{'_id': _id})
    except Exception as e:
        return eve_abort(500, "Error fetching notification")

    # Check "If-Match" header for optimistic concurrency control
    if status == 200 and response.get('status', None) == ('draft' or 'created') and request.headers.get('If-Match', None) == response.get('_etag', 'nope'):
        try:
            r, _, _, pstatus = patch_internal(resource='notifications', payload={'status': 'pending'}, **{'_id': _id})
        except Exception as e:
            return eve_abort(500, "Error updating notification status to pending")

        if pstatus in [200, 201]:

            if 'recipients' not in response or 'subject' not in response.get('data', {}) or ('html_content' not in response.get('data', {}) and 'plain_text_content' not in response.get('data', {})):
                return eve_abort(400, "Invalid request data")

            # Get recipients from the request data
            recipients = response['recipients'].get('users', [])

            for role in response['recipients'].get('roles', []):
                recipients.extend(get_users_from_role(role))

            for competence in response['recipients'].get('competences', []):
                recipients.extend(get_users_from_competence(competence))

            if len(recipients) == 0:
                return eve_abort(400, "Invalid recipients format or no recipients found")

            recipients = list(set(recipients))

            # Ensure 'from' field is present, default to current user if not provided
            if 'from' not in response:
                response['from'] = 0  # Default sender is the current user

            data = response.get('data', {})

            payload = {
                'type': response.get('type', 'email_newsletter'),  # Default type if not provided
                'uuid': None,  # Will be generated by the system
                'data': {
                    'subject': data.get('subject', ''),  # Default subject if not provided
                    'subject_preamble': data.get('subject_preamble', SENDGRID_DEFAULT_PREAMBLE),  # Optional subject preamble
                    'html_content': data.get('html_content', data.get('message', None)),  # HTML message content
                    'plain_text_content': data.get('plain_text_content', data.get('message', None)),  # TEXT message content
                    'reply_to': data.get('reply_to', SENDGRID_DEFAULT_REPLY_TO),  # Default reply-to address
                    'from': data.get('from', SENDGRID_DEFAULT_FROM),  # Default from address
                    'files': data.get('files', []),  # List of files attached to the notification
                    'send_at': data.get('send_at', datetime.utcnow().isoformat()),  # When to send the email (sendgrid)
                    'headers': SENDGRID_DEFAULT_HEADERS.update(data.get('headers', {})),  # Optional headers for the email

                },
                'recipient': None,  # Will be set for each recipient
                'sender': response.get('person_id', 0),  # The sender's user ID
                'event_id': _id,  # Optional event ID if applicable
                'event_created': datetime.utcnow(),
                'event_from': response.get('event_from', 'smtp_notification'),  # The source of the event
                'event_from_id': response.get('event_from_id', str(uuid4())),  # Optional ID of the event source
                'dismissible': False,  # Can the notification be dismissed?
                'dismissed': False,  # Will be set when the notification is dismissed
                'transport': 'email',  # The transport method
                'transport_mode': 'immediate',  # How the notification is sent
                'status': 'created',  # Initial status of the notification
                'unsubscribe': response.get('unsubscribe', SENDGRID_DEFAULT_UNSUBSCRIBE),  # Unsubscribe link
                'acl': {
                    'read': {'users': [response['person_id']] if response.get('person_id', 0) > 0 else [], 'roles': []},
                    'write': {'users': [], 'roles': []},
                    'create': {'users': [], 'roles': []},
                    'delete': {'users': [], 'roles': []},
                }
            }

            failed_recipients = []
            subject_template = JT(f"{payload['data'].get('subject', '')}")
            html_content_template = JT(f"{payload['data'].get('html_content', '')}")
            plain_text_content_template = JT(f"{payload['data'].get('plain_text_content', '')}")

            for recipient in list(set(recipients)):
                if isinstance(recipient, int):
                    try:
                        # If recipient is a user ID, fetch their email

                        # Templating the subject and content if needed
                        person = None
                        person, _, _, person_status = getitem_internal(resource='persons', **{'id': recipient})
                        if person_status not in [200, 201]:
                            app.logger.error(f"Failed to fetch person data for recipient {recipient}: {person_status}")
                            failed_recipients.append(recipient)
                            continue
                        # If person is None, we skip this recipient

                        # Get the email address of the person
                        email = None
                        if payload['transport'] == 'email':
                            email = person.get('primary_email', person.get('address', {}).get('email', [])[0] if len(person.get('address', {}).get('email', [])) > 0 else None)

                        # Make sure to reset every time
                        subject = None
                        html_content = None
                        plain_text_content = None
                        if person_status == 200 and person:
                            if 'date_of_death' in person and person['date_of_death'] is not None:
                                app.logger.error(f"Person {recipient} is deceased, skipping notification.")
                                continue
                            if 'subject' in payload['data']:
                                subject = subject_template.render(person)
                            if 'html_content' in payload['data']:
                                html_content = html_content_template.render(person)
                            if 'plain_text_content' in payload['data']:
                                plain_text_content = plain_text_content_template.render(person)

                        pld = payload.copy()
                        pld['data']['subject'] = subject
                        pld['data']['html_content'] = html_content
                        pld['data']['plain_text_content'] = plain_text_content
                        # The rest!
                        pld['recipient'] = {
                            'person_id': recipient,
                            'email': email if email else None,
                            'name': person.get('full_name', '') if person else person.get('first_name', '') + ' ' + person.get('last_name', ''),  # Use full name if available
                            #'first_name': person.get('first_name', ''),
                            #'last_name': person.get('last_name', ''),
                        }  # Recipient's person ID and email
                        pld['uuid'] = str(uuid4())  # Generate a unique UUID for the notification
                        pld['acl']['read']['users'] = [recipient]

                        # Make sure we always supply plain text content
                        if pld['data'].get('html_content', None) is not None and pld['data'].get('plain_text_content', None) is None:
                            # If only HTML content is provided, generate plain text from HTML
                            soup = BeautifulSoup(pld['data']['html_content'])
                            pld['data']['plain_text_content'] = soup.get_text()

                        try:
                            msg_response, _, _, msg_status, _ = post_internal(resource='notifications_messages',
                                                                              payl=pld,
                                                                              skip_validation=True)
                        except Exception as e:
                            app.logger.error(f"Error posting notification message for recipient {recipient}: {e}")
                            # return eve_abort(500, "Error posting notification message")
                        pld = None
                        # resp = requests.post('{}/notifications/smtp'.format(API_BASE_URL), data=json.dumps(payload, cls=EveJSONEncoder), headers=API_HEADERS)
                        if msg_status not in [200, 201]:
                            failed_recipients.append(recipient)
                            app.logger.error(f"Failed to create notification for recipient {recipient}: {msg_response}")
                            # return eve_abort(404, "Error happened")

                    except Exception as e:
                        failed_recipients.append(recipient)
                        app.logger.error(f"Error processing recipient {recipient}: {e}")
                        # return eve_abort(500, "Error processing recipient")

            # Here you would typically send the email using your email service
            # For now, we just return a success response
            r, _, _, status = patch_internal(resource='notifications', payload={'status': 'generated'}, **{'_id': _id})
            return jsonify({"status": "success", "id": payload['event_id'], "message": "Notifications created successfully", "recipients": recipients, "failed": failed_recipients}), 201

    return eve_abort(404, "Notification not found or already processed")


@Notifications.route('/wqe', methods=['POST'])
@require_token()
def email2notification():
    """Get a list of recipients (static), recipients as a result of functions, competences etc (dynamic or static)
    Add to notifications, then a stream handler will act upon the generated notifications
    - choose given or best suited channel
    - apply status when applicable
    - similar to obsreg's notifications"""
    print('HEADERS', request.headers)
    print('ARGS', request.args)
    print('FORM', request.form)
    try:
        data = json.loads(request.form['data'])  # Deserialize JSON string to dict
    except json.JSONDecodeError as e:
        app.logger.exception(f"Invalid JSON data in request {e}")
        return jsonify({'error': 'Invalid JSON data'}), 400

    if not data or 'recipients' not in data or 'subject' not in data or ('html_content' not in data and 'plain_text_content' not in data):
        return eve_abort(400, "Invalid request data")

    # Get recipients from the request data
    recipients = data['recipients'].get('users', [])

    for role in data['recipients'].get('roles', []):
        recipients.extend(get_users_from_role(role))

    for competence in data['recipients'].get('competences', []):
        recipients.extend(get_users_from_competence(competence))

    if len(recipients) == 0:
        return eve_abort(400, "Invalid recipients format or no recipients found")

    recipients = list(set(recipients))

    # Ensure 'from' field is present, default to current user if not provided
    if 'from' not in data:
        data['from'] = 0  # Default sender is the current user

    # Build message:
    # subject = data['subject']
    # message = data['message']

    # Headers for the email
    # Headers = {}
    # Access file(s)
    files = request.files.getlist('file')  # Get list of files under 'file' field
    # if not files or all(file.filename == '' for file in files):
    #   return jsonify({'error': 'No files uploaded'}), 400
    # Process files for Eve
    processed_files = []
    for file in files:
        if file and file.filename:
            # Read file content into BytesIO
            file_content = BytesIO(file.read())
            filename = secure_filename(file.filename)

            # Option 1: Store as BytesIO (if Eve schema accepts binary data)
            # processed_files.append({'filename': filename, 'content': file_content})

            # Option 2: Store as base64 string (common for embedding files in JSON)
            file_content.seek(0)  # Reset buffer position
            base64_content = base64.b64encode(file_content.read()).decode('utf-8')
            processed_files.append({
                'filename': filename,
                'content': base64_content,
                'content_type': file.content_type
            })
    # files = []
    # if request.files:
    #    if 'file' in request.files and request.files['file']:
    #        files = [request.files['file']]
    #   else:
    #        files = request.files

    payload = {
        'type': 'email',
        'uuid': None,  # Will be generated by the system
        'data': {
            'subject': data.get('subject', ''),  # Default subject if not provided
            'subject_preamble': data.get('subject_preamble', SENDGRID_DEFAULT_PREAMBLE),  # Optional subject preamble
            'html_content': data.get('html_content', data.get('message', None)),  # HTML message content
            'plain_text_content': data.get('plain_text_content', data.get('message', None)),  # TEXT message content
            'reply_to': data.get('reply_to', SENDGRID_DEFAULT_REPLY_TO),  # Default reply-to address
            'from': data.get('from', SENDGRID_DEFAULT_FROM),  # Default from address
            'files': processed_files,
            'send_at': data.get('send_at', datetime.utcnow().isoformat()),  # When to send the email (sendgrid)
            'headers': SENDGRID_DEFAULT_HEADERS.update(data.get('headers', {})),  # Optional headers for the email
            'unsubscribe': data.get('unsubscribe', SENDGRID_DEFAULT_UNSUBSCRIBE)  # Unsubscribe link
        },
        'recipient': None,  # Will be set for each recipient
        'sender': data.get('person_id', 0),  # The sender's user ID
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
            'read': {'users': [data['person_id']] if data.get('person_id', 0) > 0 else [], 'roles': []},
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
