from _base import acl_item_schema
from bson import SON, ObjectId
from flask import current_app as app

RESOURCE_COLLECTION = 'notifications'
BASE_URL = 'notifications'

_data = {

}

_schema = {'type': {'type': 'string',
                    'required': True,
                    },
           'uuid': {'type': 'string'},
           'data': {
               'type': 'dict',
               'schema': {
                   'subject': {'type': 'string'},  # Subject of the notification
                   'subject_preamble': {'type': 'string'},  # Preamble of the subject
                   'html_content': {'type': 'string'},  # HTML content of the notification
                   'plain_text_content': {'type': 'string'},  # Plain text content of the notification
                   'from': {
                       'type': 'dict',
                       'schema': {
                           'name': {'type': 'string'},  # Reply to name
                           'email': {'type': 'string'}
                       }},  # From email address
                   'reply_to': {
                       'type': 'dict',
                       'schema': {
                           'name': {'type': 'string'},  # Reply to name
                           'email': {'type': 'string'}
                       }},  # Reply to email address
                   'bounce': {
                       'type': 'dict',
                       'schema': {
                           'email': {'type': 'string'}
                       }},  # Bounce email address used in Return-Path header

                   'files': {
                       'type': 'list',
                       'schema': {
                           'type': 'objectid',
                           'data_relation': {
                               'resource': 'files',
                               'field': '_id',
                               'embeddable': True,
                           }
                       }
                   },  # List of files attached to the notification

                   'headers': {'type': 'dict'},
               },

           },
           'recipients': {'type': 'dict'},  # Who's the recepient
           'recipients_resolved': {'type': 'list'},  # Who's the recepients
           'sender': {'type': 'integer'},  # evt
           """{
                       'type': 'dict',
                       'schema': {
                           'name': {'type': 'string'},  # Reply to name
                           'email': {'type': 'string'}
                       }},  # Reply to email address
           """

           # Event information
           'event_id': {'type': 'objectid'},
           'event_created': {'type': 'datetime'},
           'event_from': {'type': 'string'},  # ex notifications
           'event_from_id': {'type': 'objectid'},
           # 'event_person_id': {'type': 'integer'}, # Sender
           'dismissible': {'type': 'boolean'},  # Can dimiss?
           # Transport information
           'transport': {'type': 'string'},  # ['email', 'sms', 'socket',...]
           'transport_mode': {'type': 'string'},  # immediate, aggregate_5m, aggregate_1d osv transport_delay 0 10
           'status': {'type': 'string', 'required': True, 'default': 'draft'},  # draft created, pending, delivered
           'strategy': {'type': 'string'},  # How to handle the message, e.g. 'immediate', 'aggregate', 'user'
           'send_at': {'type': 'datetime'},  # When to send the notifications
           # Unsubscribe information
           'unsubscribe': {'type': 'string'},  # Unsubscribe link or token
           'acl': acl_item_schema
           }

definition = {
    'item_title': 'Base notifications',
    'url': BASE_URL,
    'datasource': {'source': RESOURCE_COLLECTION,
                   },
    'resource_methods': ['GET', 'POST'],
    'item_methods': ['GET', 'PUT', 'PATCH', 'DELETE'],
    'allow_unknown': True,
    'versioning': True,
    'mongo_indexes': {
        'housekeeping': ([('type', 1), ('dismissible', 1), ('transport', 1)], {'background': True}),
        'uuid': ([('uuid', 1)], {'background': True}),
        'event': ([('event_from', 1), ('event_from_id', 1), ('event_created', 1)], {'background': True}),
        'recipients': ([('recipients', 1)], {'background': True}),
    },
    'additional_lookup': {
        'url': 'regex("[a-fA-F0-9-]+")',
        'field': 'uuid',
    },
    'schema': _schema

}
