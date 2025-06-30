from _base import acl_item_schema
from bson import SON, ObjectId
from flask import current_app as app

RESOURCE_COLLECTION = 'notifications_messages'
BASE_URL = 'notifications/messages'

_data = {

}

_schema = {'type': {'type': 'string',
                    'required': True,
                    },
           'uuid': {'type': 'string'},
           'data': { # To build the message!
               'type': 'dict',
               'schema': {
                   'subject': {'type': 'string'},  # Subject of the notification
                   'subject_preamble': {'type': 'string'},  # Preamble of the subject
                   'html_content': {'type': 'string'},  # HTML content of the notification
                   'plain_text_content': {'type': 'string'},  # Plain text content of the notification
                   'reply_to': {
                       'type': 'dict',
                       'schema': {
                           'name': {'type': 'string'},  # Reply to name
                           'email': {'type': 'string'}
                       }},  # Reply to email address
                   'from': {
                       'type': 'dict',
                       'schema': {
                           'name': {'type': 'string'},  # Reply to name
                           'email': {'type': 'string'}
                       }},  # From email address
               },
               'files': {
                   'type': 'list',
                   'schema': {
                       'type': 'ObjectId',
                       'data_relation': {
                           'resource': 'files',
                           'field': '_id',
                           'embeddable': True,
                       }
                   }
               },  # List of files attached to the notification
               'headers': {'type': 'dict'},
               'unsubscribe': {'type': 'string'},  # Unsubscribe link or token
           },
           'recipient': {'type': 'integer'},  # Who's the recepient
           'sender': {'type': 'integer'},  # g.user_id or g.person_id
           # Event information
           'event_id': {'type': 'ObjectId'},
           'event_created': {'type': 'datetime'},
           'event_from': {'type': 'string'},  # ex notifications
           'event_from_id': {'type': 'ObjectId'},  # {'type': 'objectid'},
           # 'event_person_id': {'type': 'integer'}, # Sender
           'dismissible': {'type': 'boolean'},  # Can dimiss?
           'dismissed': {'type': 'datetime', 'nullable': True},
           'transport': {'type': 'string'},  # ['email', 'sms', 'socket',...]
           'transport_mode': {'type': 'string'},  # immediate, aggregate_5m, aggregate_1d osv transport_delay 0 10
           'send_at': {'type': 'datetime'},  # When to send the notification
           'status': {'type': 'string'},  # created, pending, delivered
           'acl': acl_item_schema
           }

definition = {
    'item_title': 'Messages generated from notifications',
    'url': BASE_URL,
    'datasource': {'source': RESOURCE_COLLECTION,
                   },
    'resource_methods': ['GET', 'POST'],
    'item_methods': ['GET'],
    'mongo_indexes': {
        'housekeeping': ([('type', 1), ('dismissible', 1), ('dismissed', 1), ('transports', 1)], {'background': True}),
        'uuid': ([('uuid', 1)], {'background': True}),
        'event': ([('event_from', 1), ('event_from_id', 1), ('event_created', 1)], {'background': True}),
        'recipient': ([('recipient', 1)], {'background': True}),
    },
    'additional_lookup': {
        'url': 'regex("[a-fA-F0-9-]+")',
        'field': 'uuid',
    },
    'schema': _schema

}

# AGGREGATION
agg_events = {
    'url': f'{BASE_URL}/events',
    'item_title': 'Get notifications by event_from_id and event_from grouped by events',
    'pagination': False,
    'datasource': {
        'source': RESOURCE_COLLECTION,
        'aggregation': {
            'pipeline': [
                {
                    "$match": {
                        "event_from": "$event_from",
                        "event_from_id": "$event_from_id",

                    }
                },

                {
                    "$group": {
                        "_id": "$event_id",
                        "type": {
                            "$first": "$type"
                        },
                        "recepients": {
                            "$addToSet": "$recepient"
                        },
                        "sender": {
                            "$first": "$sender"
                        },
                        "event_created": {
                            "$first": "$event_created"
                        },
                        "dimissed": {
                            "$first": "$dismissed"
                        },
                        "transport": {
                            "$first": "$transport"
                        },
                        "status": {
                            "$first": "$status"
                        },
                        "data": {
                            "$first": "$data"
                        }
                    }
                },
                {"$sort": {"event_created": -1}}  # SON([("data.when", -1)])},

            ]
        }
    }
}
