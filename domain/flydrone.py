RESOURCE_COLLECTION = 'flydrone'

_schema = {
    'personId': {'type': 'int', 'unique': True},
    'status': {'type': 'str'},
    'operatorRegistrationNumber': {'type': 'str'},
    'expiredOperatorRegistrationNumberTime': {'type': 'str'}
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
    'extra_response_fields': ['personId'],
    'versioning': True,
    #'internal_resource': True,
    'resource_methods': ['GET', 'POST', 'DELETE'],
    'item_methods': ['GET', 'PATCH', 'PUT'],
    'schema': _schema
}
