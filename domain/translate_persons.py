RESOURCE_COLLECTION = 'translate_persons'

_schema = {
    'person_id': {'type': 'integer',
                  'required': True,
                  'unique': False},
    'melwin_id': {'type': 'integer',
                  'required': True,
                  'unique': True},
}

definition = {
    'url': 'translate/persons',
    'item_title': 'Translate Persons',
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
    'url': 'translate/persons/process',
    'item_title': 'Translate Persons Process',
    'datasource': {'source': RESOURCE_COLLECTION,
                   },
    'additional_lookup': {
        'url': 'regex("[\d{1,9}]+")',
        'field': 'melwin_id',
    },
    'pagination': False,
    'versioning': False,
    'resource_methods': ['GET', 'POST', 'DELETE'],
    'item_methods': ['GET', 'PATCH', 'PUT'],
    'schema': _schema_process
}