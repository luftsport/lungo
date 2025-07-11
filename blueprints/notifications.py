import logging

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
from dateutil.parser import parse

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

# Valid operators
SIMPLE_OPERATORS = {
    '=': '$eq',
    '>': '$gt',
    '<': '$lt',
    '>=': '$gte',
    '<=': '$lte',
    '!=': '$ne',
    'in': '$in'
}
MONGO_OPERATORS = list(SIMPLE_OPERATORS.values())
LOGICAL_OPERATORS = ['or', 'and']


def validate_filters(filters, depth=0):
    """
    Validate a filter dictionary or list, supporting or/and and nested filters.
    :param filters: Dict with or/and or list of filter dicts
    :param depth: Recursion depth for logging
    :return: Validated filter structure with parsed values
    """
    indent = "  " * depth
    if isinstance(filters, list):
        # Treat list as implicit and
        filters = {"and": filters}

    if not isinstance(filters, dict):
        logging.error(f"{indent}Filters must be a dictionary or list: {filters}")
        raise ValueError(f"Filters must be a dictionary or list")

    if len(filters) != 1 or list(filters.keys())[0] not in LOGICAL_OPERATORS:
        logging.error(f"{indent}Filters must have a single or or and key: {filters}")
        raise ValueError(f"Filters must have a single or or and key")

    operator = list(filters.keys())[0]
    filter_list = filters[operator]

    if not isinstance(filter_list, list) or not filter_list:
        logging.error(f"{indent}{operator} value must be a non-empty list: {filter_list}")
        raise ValueError(f"{operator} value must be a non-empty list")

    validated_filters = {operator: []}
    required_keys = {'type', 'field', 'value', 'operator'}

    for i, filter_item in enumerate(filter_list):
        if isinstance(filter_item, dict) and any(key in LOGICAL_OPERATORS for key in filter_item):
            # Nested or/and
            validated_filters[operator].append(validate_filters(filter_item, depth + 1))
            logging.info(f"{indent}Validated nested {operator} filter {i} at depth {depth + 1}")
        else:
            # Simple filter dictionary
            if not isinstance(filter_item, dict):
                logging.error(f"{indent}Filter {i} is not a dictionary: {filter_item}")
                raise ValueError(f"Filter {i} must be a dictionary")

            if not all(key in filter_item for key in required_keys):
                missing = required_keys - set(filter_item.keys())
                logging.error(f"{indent}Filter {i} missing required keys: {missing}")
                raise ValueError(f"Filter {i} missing required keys: {missing}")

            if filter_item['type'] not in ['inclusive', 'exclusive']:
                logging.error(f"{indent}Filter {i} invalid type: {filter_item['type']}")
                raise ValueError(f"Filter {i} type must be 'inclusive' or 'exclusive'")

            if not isinstance(filter_item['field'], str) or not filter_item['field']:
                logging.error(f"{indent}Filter {i} invalid field: {filter_item['field']}")
                raise ValueError(f"Filter {i} field must be a non-empty string")

            op = filter_item['operator']
            if op not in SIMPLE_OPERATORS and op not in MONGO_OPERATORS:
                logging.error(f"{indent}Filter {i} invalid operator: {op}")
                raise ValueError(f"Filter {i} operator must be one of {list(SIMPLE_OPERATORS.keys()) + MONGO_OPERATORS}")

            if op in ['in', '$in'] and not isinstance(filter_item['value'], list):
                logging.error(f"{indent}Filter {i} value for 'in' must be a list: {filter_item['value']}")
                raise ValueError(f"Filter {i} value for 'in' must be a list")

            # Validate birth_date
            if filter_item['field'] == 'birth_date':
                try:
                    if op in ['in', '$in']:
                        parsed_values = [parse(val) for val in filter_item['value']]
                        filter_item['value'] = parsed_values
                        logging.info(f"{indent}Parsed birth_date values for filter {i}: {parsed_values}")
                    else:
                        parsed_value = parse(filter_item['value'])
                        filter_item['value'] = parsed_value
                        logging.info(f"{indent}Parsed birth_date value for filter {i}: {parsed_value}")
                except (ValueError, TypeError) as e:
                    logging.error(f"{indent}Filter {i} invalid birth_date value: {filter_item['value']} ({str(e)})")
                    raise ValueError(f"Filter {i} birth_date value must be a valid date/datetime string")

            # Validate age
            if filter_item['field'] == 'age':
                if op in ['in', '$in']:
                    if not all(isinstance(val, int) for val in filter_item['value']):
                        logging.error(f"{indent}Filter {i} age value for 'in' must be a list of integers: {filter_item['value']}")
                        raise ValueError(f"Filter {i} age value for 'in' must be a list of integers")
                else:
                    if not isinstance(filter_item['value'], int):
                        logging.error(f"{indent}Filter {i} age value must be an integer: {filter_item['value']}")
                        raise ValueError(f"Filter {i} age value must be an integer")

            validated_filters[operator].append(filter_item)
            logging.info(f"{indent}Validated filter {i}: {filter_item}")

    return validated_filters


def person_satisfies_filters(person, filters, depth=0):
    """
    Check if a person satisfies the given filters, supporting or/and.
    """
    indent = "  " * depth
    if isinstance(filters, list):
        filters = {"and": filters}

    operator = list(filters.keys())[0]
    filter_list = filters[operator]

    if operator == 'and':
        for i, filter_item in enumerate(filter_list):
            if any(key in LOGICAL_OPERATORS for key in filter_item):
                if not person_satisfies_filters(person, filter_item, depth + 1):
                    logging.info(f"{indent}Person does not satisfy nested and filter {i}: {filter_item}")
                    return False
            else:
                if not person_satisfies_single_filter(person, filter_item):
                    logging.info(f"{indent}Person does not satisfy and filter {i}: {filter_item}")
                    return False
        return True
    elif operator == 'or':
        for i, filter_item in enumerate(filter_list):
            if any(key in LOGICAL_OPERATORS for key in filter_item):
                if person_satisfies_filters(person, filter_item, depth + 1):
                    logging.info(f"{indent}Person satisfies nested or filter {i}: {filter_item}")
                    return True
            else:
                if person_satisfies_single_filter(person, filter_item):
                    logging.info(f"{indent}Person satisfies or filter {i}: {filter_item}")
                    return True
        return False
    return False


def person_satisfies_single_filter(person, filter_dict):
    """
    Check if a person satisfies a single filter.
    """
    field = filter_dict['field']
    value = filter_dict['value']
    operator = SIMPLE_OPERATORS.get(filter_dict['operator'], filter_dict['operator'])

    if field == 'age':
        if 'birth_date' not in person:
            logging.warning(f"birth_date not found in person for age filter: {person}")
            return False
        try:
            person_value = calculate_age(person['birth_date'])
        except ValueError as e:
            logging.error(f"Error calculating age: {str(e)}")
            return False
    else:
        if field not in person:
            logging.warning(f"Field {field} not found in person: {person}")
            return False
        person_value = person[field]

    if field == 'birth_date' and not isinstance(person_value, datetime):
        logging.error(f"Person's birth_date is not a datetime: {person_value}")
        return False

    result = False
    if operator == '$eq' or operator == '=':
        result = person_value == value
    elif operator == '$gt' or operator == '>':
        result = person_value > value
    elif operator == '$lt' or operator == '<':
        result = person_value < value
    elif operator == '$gte' or operator == '>=':
        result = person_value >= value
    elif operator == '$lte' or operator == '<=':
        result = person_value <= value
    elif operator == '$ne' or operator == '!=':
        result = person_value != value
    elif operator == '$in' or operator == 'in':
        result = person_value in value

    if filter_dict['type'] == 'inclusive':
        return result
    elif filter_dict['type'] == 'exclusive':
        return not result
    return False


def person_satisfies_filters(person, filters):
    """
    Check if a person satisfies the given filters.
    :param person: Dictionary with person data, e.g., {'name': 'John', 'birth_date': datetime, 'email': 'john@example.com'}
    :param filters: List of validated filter dicts
    :return: True if person satisfies all filters, False otherwise
    """
    for filter_dict in filters:
        field = filter_dict['field']
        value = filter_dict['value']
        operator = SIMPLE_OPERATORS.get(filter_dict['operator'], filter_dict['operator'])

        # Ensure field exists in person
        if field not in person:
            app.logger.warning(f"Field {field} not found in person: {person}")
            return False

        person_value = person[field]

        # Handle birth_date comparisons
        if field == 'birth_date' and not isinstance(person_value, datetime):
            app.logger.error(f"Person's birth_date is not a datetime: {person_value}")
            return False

        # Compare values
        result = False
        if operator == '$eq' or operator == '=':
            result = person_value == value
        elif operator == '$gt' or operator == '>':
            result = person_value > value
        elif operator == '$lt' or operator == '<':
            result = person_value < value
        elif operator == '$gte' or operator == '>=':
            result = person_value >= value
        elif operator == '$lte' or operator == '<=':
            result = person_value <= value
        elif operator == '$ne' or operator == '!=':
            result = person_value != value
        elif operator == '$in' or operator == 'in':
            result = person_value in value

        # Apply inclusive/exclusive logic
        if filter_dict['type'] == 'inclusive' and not result:
            app.logger.info(f"Person with field {field} and value {person_value} does not satisfy inclusive filter: {filter_dict}")
            return False
        elif filter_dict['type'] == 'exclusive' and result:
            app.logger.info(f"Person with field {field} and value {person_value} does not satisfy inclusive filter: {filter_dict}")
            return False

    app.logger.info(f"Person satisfies all filters: {person}")
    return True


def calculate_age(birth_date, reference_date=None):
    """
    Calculate age from a birth_date (datetime or string).
    :param birth_date: datetime object or string (e.g., '2000-01-01')
    :param reference_date: datetime object for age calculation (default: today, 2025-07-11)
    :return: Age in years (int)
    """
    if reference_date is None:
        reference_date = datetime.utcnow()  # Current date as per context

    # Parse birth_date if it's a string
    if isinstance(birth_date, str):
        try:
            birth_date = parser.parse(birth_date)
        except (ValueError, TypeError) as e:
            raise ValueError(f"Invalid birth_date format: {birth_date} ({str(e)})")

    # Ensure birth_date is a datetime
    if not isinstance(birth_date, datetime):
        raise ValueError(f"birth_date must be a datetime or valid date string: {birth_date}")

    # Calculate age
    age = reference_date.year - birth_date.year
    if (reference_date.month, reference_date.day) < (birth_date.month, birth_date.day):
        age -= 1  # Subtract 1 if birthday hasn't occurred this year

    return age


def build_mongo_query(filters):
    """
    Convert filters to a MongoDB query.
    :param filters: List of validated filter dicts
    :return: MongoDB query dictionary
    """
    query = {}
    for filter_dict in filters:
        field = filter_dict['field']
        value = filter_dict['value']
        operator = SIMPLE_OPERATORS.get(filter_dict['operator'], filter_dict['operator'])

        # Build query for the field
        if field not in query:
            query[field] = {}

        query[field][operator] = value

        # Handle exclusive filters (negate the condition)
        if filter_dict['type'] == 'exclusive':
            query[field] = {'$not': query[field]}

    app.logger.info(f"Built MongoDB query: {query}")
    return query


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
        if role['org'] == '*' and role['activity'] == '*':
            query = f'where={{ "type_id": {role["role"]}, "is_deleted": false, "is_passive": false}}&projection={{"person_id": 1}}'
        elif role['org'] is not None and role['org'] != '*' and role['org'] > 0:
            query = f'where={{"org_id": {role["org"]}, "type_id": {role["role"]}, "is_deleted": false, "is_passive": false}}&projection={{"person_id": 1}}'
        elif role['org'] == '*' and role['activity'] is not None and role['activity'] != '*' and role['activity'] > 0:
            orgs_from_activity = get_orgs_in_activivity(role['activity'])
            query = f'where={{"org_id": {{"$in": {orgs_from_activity}}}, "type_id": {role["role"]}, "is_deleted": false, "is_passive": false}}&projection={{"person_id": 1}}'
        elif (role['org'] and role['activity']) == '*':
            query = f'where={{"org_id": {role["org"]}, "type_id": {role["role"]}, "is_deleted": false, "is_passive": false}}&projection={{"person_id": 1}}'

        resp = requests.get('{}/functions?{}&max_results={}'.format(API_BASE_URL, query, 20000), headers=API_HEADERS)  # verify=app['config'].get('REQUESTS_VERIFY', True)

        if resp.status_code == 200:
            try:
                return list(set([item['person_id'] for item in resp.json().get('_items', [])]))
            except IndexError as e:
                pass

    return []


def check_nif_person(person_id):
    person, _, _, status = getitem_internal(resource='nif_persons', **{'id': person_id})
    if status == 200 and person is not None:
        return True

    return False


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
                '{}/competences?where={{"type_id": {}, "passed": true, "valid_until": {{"$gte": "{}Z" }} }}&max_results={}&projection={{"person_id": 1}}'.format(
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
            '{}/competences?where={{"type_id": {}, "passed": true, "valid_until": {{"$gte": "{}Z" }} }}&max_results={}&projection={{"person_id": 1}}'.format(
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
    return eve_abort(404, "Notify endpoint not implemented yet")


@Notifications.route('/test', methods=['GET'])
@require_token()
def test_notification():
    # from eve.utils import parse_request
    # print(parse_request('dev').where, parse_request('persons').max_results, parse_request('persons').projection)
    # return eve_response(parse_request('notifications').where + str(parse_request('notifications').max_results) + parse_request('notifications').projection)
    return eve_abort(404, "Test endpoint not implemented yet")


@Notifications.route('/send/<string:_id>', methods=['POST'])
@require_token()
def send_notification_messages(_id):
    """Send notification messages by ID"""
    try:
        notification, _, _, status = getitem_internal(resource='notifications', **{'_id': _id})
    except Exception as e:
        app.logger.exception(f"Error fetching notification _id: {_id} status {status} and error {e}")
        return eve_abort(500, "Error fetching notification")

    # Check "If-Match" header for optimistic concurrency control
    if status == 200 and notification.get('status', None) == 'generated' and request.headers.get('If-Match', None) == notification.get('_etag', 'nope'):
        app.logger.info(f"Notification _id: {_id} is ready to be sent, status: {notification.get('status', 'unknown')}")
        notifications = app.data.driver.db['notifications']
        notifications_messages = app.data.driver.db['notifications_messages']
        # Check if the notification is already processed
        n_status = notifications.update_one({'_id': ObjectId(_id)}, {'$set': {'status': 'pending'}})
        if n_status.modified_count == 0:
            app.logger.error(f"Notification _id: {_id} could not update notifications to status pending pymongo status {n_status}")
            return eve_abort(404, "Notification not found or already processed")

        nm_status = notifications_messages.update_many({'event_id': ObjectId(_id)}, {'$set': {'status': 'ready'}})
        if nm_status.modified_count == 0:
            app.logger.error(f"Notification _id: {_id} could not update notification messages pymongo status {nm_status}")
            return eve_abort(404, "Notification messages not found or already processed")
        # Update the status of the notification to 'finished'
        nu_status = notifications.update_one({'_id': ObjectId(_id)}, {'$set': {'status': 'finished'}})
        if nu_status.modified_count == 0:
            app.logger.error(f"Notification _id: {_id} could not update notification template pymongo status {nu_status}")
            return eve_abort(404, "Notification not found or already processed")

        app.logger.info(f"Notification _id: {_id} successfully sent")
        return eve_response({"status": "success", "message": f"{nm_status.modified_count} notification messages sent successfully"}, 201)

    app.logger.error(f"Error notification _id: {_id} etag: {request.headers.get('If-Match', 'nope')} content type: {request.headers.get('Content-Type', 'unknown')} Authorization: {request.headers.get('Authorization', 'unknown')}")
    return eve_abort(404, "Notification not found or already processed")


@Notifications.route('/generate/<string:_id>', methods=['POST', 'GET'])
@require_token()
def generate_notifications(_id):
    try:
        response, _, _, status = getitem_internal(resource='notifications', **{'_id': _id})
    except Exception as e:
        app.logger.exception("Error fetching notification")
        return eve_abort(500, "Error fetching notification")

    # Check "If-Match" header for optimistic concurrency control
    if status == 200 and response.get('status', None) == ('draft' or 'created') and request.headers.get('If-Match', None) == response.get('_etag', 'nope'):
        try:
            r, _, _, pstatus = patch_internal(resource='notifications', payload={'status': 'pending'}, **{'_id': _id})
        except Exception as e:
            app.logger.exception("Error updating notification status to pending")
            return eve_abort(500, "Error updating notification status to pending")

        if pstatus in [200, 201]:

            if 'recipients' not in response or 'subject' not in response.get('data', {}) or ('html_content' not in response.get('data', {}) and 'plain_text_content' not in response.get('data', {})):
                app.logger.error("Invalid request data: missing recipients or subject/content")
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

            # Validate and compile filters if provided
            valid_filters = validate_filters(response['recipients'].get('filters', []))

            for recipient in list(set(recipients)):
                if isinstance(recipient, int):
                    app.logger.debug(f"Processing recipient ID: {recipient}")
                    try:
                        # If recipient is a user ID, fetch their email

                        # Templating the subject and content if needed
                        person = None
                        person, _, _, person_status = getitem_internal(resource='persons', **{'id': recipient})
                        # If status not correct or person is None, we skip this recipient
                        if person_status not in [200, 201] or not person:
                            app.logger.error(f"Failed to fetch person data for recipient {recipient}: {person_status}")
                            failed_recipients.append(recipient)
                            app.logger.error(f"Person data for recipient {recipient} not found or invalid status: {person_status} {person.text if hasattr(person, 'text') else ''}")
                            continue

                        # Make sure to reset every time
                        subject = None
                        html_content = None
                        plain_text_content = None
                        if person_status == 200 and person:

                            # Check if filters are valid else ditch the notification message
                            app.logger.debug(f"Applying filter for recipient {recipient}")
                            # Add special fields:
                            if len(valid_filters) > 0:
                                # Add special fields to the person object for filtering
                                person['age'] = calculate_age(person.get('birth_date', None))
                                if person_satisfies_filters(person, valid_filters) is False:
                                    app.logger.error(f"Person {recipient} does not satisfy the filters, skipping notification.")
                                    continue

                            # Get the email address of the person
                            email = None
                            if payload['transport'] == 'email':
                                app.logger.debug(f"Fetching email for recipient {recipient}")
                                email = person.get('primary_email', person.get('address', {}).get('email', [])[0] if len(person.get('address', {}).get('email', [])) > 0 else None)
                            # Check if the person has memberships in NLF
                            if check_nif_person(person['id']) is False:
                                app.logger.error(f"Person {recipient} has no memberships as reported by /nif/persons, skipping notification.")
                                continue

                            app.logger.debug(f"Processing person data for recipient {recipient}")
                            if 'date_of_death' in person and person['date_of_death'] is not None:
                                app.logger.error(f"Person {recipient} is deceased, skipping notification.")
                                continue
                            if 'subject' in payload['data']:
                                app.logger.debug(f"Rendering subject for recipient {recipient}")
                                subject = subject_template.render(person)
                            if 'html_content' in payload['data']:
                                app.logger.debug(f"Rendering HTML content for recipient {recipient}")
                                html_content = html_content_template.render(person)
                            if 'plain_text_content' in payload['data']:
                                app.logger.debug(f"Rendering plain text content for recipient {recipient}")
                                plain_text_content = plain_text_content_template.render(person)
                            app.logger.debug(f"Finished jinja rendering for recipient {recipient}")

                        # Prepare the payload for the notification message
                        app.logger.debug(f"Preparing payload for recipient {recipient}")
                        pld = payload.copy()
                        pld['data']['subject'] = subject
                        pld['data']['html_content'] = html_content
                        pld['data']['plain_text_content'] = plain_text_content
                        # The rest!
                        pld['recipient'] = {
                            'person_id': recipient,
                            'email': email if email else None,
                            'name': person.get('full_name', '') if person else person.get('first_name', '') + ' ' + person.get('last_name', ''),  # Use full name if available
                            # 'first_name': person.get('first_name', ''),
                            # 'last_name': person.get('last_name', ''),
                        }  # Recipient's person ID and email
                        pld['uuid'] = str(uuid4())  # Generate a unique UUID for the notification
                        pld['acl']['read']['users'] = [recipient]
                        app.logger.debug(f"Payload prepared for recipient {recipient}: {pld}")

                        # Make sure we always supply plain text content
                        if pld['data'].get('html_content', None) is not None and pld['data'].get('plain_text_content', None) is None:
                            # If only HTML content is provided, generate plain text from HTML
                            app.logger.debug(f"Generating plain text content from HTML for recipient {recipient}")
                            soup = BeautifulSoup(pld['data']['html_content'])
                            pld['data']['plain_text_content'] = soup.get_text()
                            app.logger.debug(f"Generated plain text content for recipient {recipient}: {pld['data']['plain_text_content']}")

                        try:
                            app.logger.debug(f"Posting notification message for recipient {recipient}")
                            msg_response, _, _, msg_status, _ = post_internal(resource='notifications_messages',
                                                                              payl=pld,
                                                                              skip_validation=True)
                            app.logger.debug(f"Notification message posted for recipient {recipient}: {msg_status}")
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
            app.logger.debug(f"All recipients processed, total: {len(recipients)}, failed: {len(failed_recipients)}")

            r, _, _, status = patch_internal(resource='notifications', payload={'status': 'generated'}, **{'_id': _id})

            return eve_response({"status": "success", "_id": _id, "_etag": r.get('_etag', None), "message": "Notifications created successfully", "recipients": recipients, "failed": failed_recipients}, 201)

    app.logger.error(f"Notification not found or already processed: {_id}, status: {status}, response: {response.text}, etag: {request.headers.get('If-Match', 'nope')}, expected etag: {response.get('_etag', 'nope')}")
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
