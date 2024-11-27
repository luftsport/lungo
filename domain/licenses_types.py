RESOURCE_COLLECTION = 'licenses_types'
_schema = {

    'born_after': {'type': 'datetime'},
    'born_before': {'type': 'datetime'},
    'class_id': {'type': 'integer'},
    'description': {'type': 'string'},
    'gender_id': {'type': 'integer'},
    'is_deleted': {'type': 'boolean'},
    'is_payable': {'type': 'boolean'},
    'is_valid': {'type': 'boolean'},
    'period_id': {'type': 'integer'},
    'id': {'type': 'integer'},
    'price': {'type': 'number'},
    'text': {'type': 'string'},
    'org_id_owner': {'type': 'integer'},
}

definition = {
    'url': 'licenses/types',
    'item_title': 'License Types',
    'datasource': {'source': RESOURCE_COLLECTION,
                   },
    'additional_lookup': {
        'url': 'regex("[\d{1,9}]+")',
        'field': 'id',
    },
    'extra_response_fields': ['id'],
    'versioning': False,
    'resource_methods': ['GET', 'POST', 'DELETE'],
    'item_methods': ['GET', 'PATCH', 'PUT'],
    'mongo_indexes': {'id': ([('id', 1)], {'background': True}),
                      'org_id': ([('org_id_owner', 1)], {'background': True}),
                      'text': ([('text', 'text')], {'background': True})
                      },
    'schema': _schema
}

# Search
search_definition = {
    'url': 'licenses/types/search',
    'item_title': 'Licenses Types Search',
    'datasource': {'source': RESOURCE_COLLECTION,
                   'projection': {
                       "_score": {"$meta": "textScore"},
                       "text": 1,
                       "id": 1,
                       "_updated": 1,
                       "_created": 1,
                       "_version": 1
                   },
                   'default_sort': [("_score", {"$meta": "textScore"})],
                   #'filter': {'org_id_owner': 376, 'is_valid':True}
                   },
    'additional_lookup': {
        'url': 'regex("[\d{1,9}]+")',
        'field': 'id',
    },
    'extra_response_fields': ['id'],
    'resource_methods': ['GET'],
    'item_methods': [],
    'schema': _schema
}
