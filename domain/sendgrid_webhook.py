RESOURCE_COLLECTION = 'sendgrid_webhook'
BASE_URL = 'sendgrid/webhook'

_data = {

}

_schema = {
    'email': {'type': 'string'},
    'event': {'type': 'string'},
    'timestamp': {'type': 'integer'},
    'sg_event_id': {'type': 'string'},
    'sg_message_id': {'type': 'string'},
}

definition = {
    'item_title': 'Sendgrid webhook for notifications',
    'url': BASE_URL,
    'datasource': {'source': RESOURCE_COLLECTION,
                   },
    'public_methods': ['POST'],
    'resource_methods': ['GET', 'POST'],
    'item_methods': ['GET'],
    'allow_unknown': True,
    'versioning': False,
    'mongo_indexes': {},
    # 'additional_lookup': {
    #    'url': 'regex("[a-fA-F0-9-]+")',
    #    'field': 'uuid',
    # },
    'schema': _schema

}
