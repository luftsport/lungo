RESOURCE_COLLECTION = 'persons_fids'

_schema = {
    'person_id': {'type': 'integer'},
    'fid_type': {'type': 'string'},
    'data': {'type': 'dict'}
}

"""
'flydrone': {
        'type': 'dict',
        'schema': {
            'personId': {'type': 'integer'},
            'status': {'type': 'string'},
            'operatorRegistrationNumber': {'type': 'string'},
            'expiredOperatorRegistrationNumberTime': {'type': 'string'}
        }
    },
    'fai': {
        'type': 'dict',
        'schema': {
            'person_id': {'type': 'integer'},
            'license_id': {'type': 'integer'},
        }
    }
    """
definition = {
    'item_title': 'Foreign ids',
    'datasource': {'source': RESOURCE_COLLECTION,
                   },
    'url': 'persons/fids',
    #'additional_lookup': {
    #    'url': 'regex("[\d{1,9}]+")',
    #    'field': 'person_id',
    #},
    # 'pagination': False,
    # 'extra_response_fields': ['personId'],
    #'versioning': True,
    # 'internal_resource': True, # Only internal?
    'allow_unknown': True,
    'resource_methods': ['GET', 'POST'],
    'item_methods': ['GET', 'PATCH', 'PUT', 'DELETE'],
    'mongo_indexes': {
        'person_id': ([('person_id', 1)], {'background': True}),
        'fid_type': ([('fid_type', 1)], {'background': True})
    },
    'schema': _schema
}
