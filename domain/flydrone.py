RESOURCE_COLLECTION = 'flydrone'

_schema = {
    'personId': {'type': 'integer'},
    'status': {'type': 'string'},
    'operatorRegistrationNumber': {'type': 'string'},
    'expiredOperatorRegistrationNumberTime': {'type': 'string'}
}

definition = {
    'item_title': 'flydrone',
    'datasource': {'source': RESOURCE_COLLECTION,
                   },
    'url': 'flydrone',
    'additional_lookup': {
        'url': 'regex("[\d{1,9}]+")',
        'field': 'personId',
    },
    # 'pagination': False,
    # 'extra_response_fields': ['personId'],
    'versioning': False,
    # 'internal_resource': True,
    'resource_methods': ['GET', 'POST', 'DELETE'],
    'item_methods': ['GET', 'PATCH', 'PUT'],
    'mongo_indexes': {
        'personId': ([('personId', 1)], {'background': True})
    },
    'schema': _schema
}
