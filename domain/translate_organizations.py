RESOURCE_COLLECTION = 'translate_organizations'

_schema = {
    'org_id': {'type': 'integer',
                  'required': True,
                  'unique': True},
    'melwin_id': {'type': 'string',
                  'required': True,
                  'unique': True},
}

definition = {
    'url': 'translate/organizations',
    'item_title': 'Translate Organizations',
    'datasource': {'source': RESOURCE_COLLECTION,
                   },
    'additional_lookup': {
        'url': 'regex("[\d{1,9}]+")',
        'field': 'melwin_id',
    },
    'versioning': False,
    'resource_methods': ['GET'],
    'item_methods': ['GET'],
    'mongo_indexes': {'person_id': ([('person_id', 1)], {'background': True}),
                      'melwin_id': ([('melwin_id', 1)], {'background': True}),
                      },
    'schema': _schema
}

# Process resource without data_relations
_schema_process = _schema.copy()

process_definition = {
    'url': 'translate/organizations/process',
    'item_title': 'Translate Organizations Process',
    'datasource': {'source': RESOURCE_COLLECTION,
                   },
    'additional_lookup': {
        'url': 'regex("[\d{3}\-\w{1}]+")',
        'field': 'melwin_id',
    },
    'pagination': False,
    'versioning': False,
    'resource_methods': ['GET', 'POST', 'DELETE'],
    'item_methods': ['GET', 'PATCH', 'PUT'],
    'schema': _schema_process
}