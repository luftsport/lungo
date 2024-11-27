RESOURCE_COLLECTION = 'function_types'
_schema = {
    'description': {'type': 'string'},
    'category_id': {'type': 'integer'},
    'category_name': {'type': 'string'},
    'id': {'type': 'integer',
           'unique': True,
           'required': True},
    'type_no': {'type': 'string'},
    'is_license': {'type': 'boolean'},
    'is_valid': {'type': 'boolean'},
    'name': {'type': 'string'},
    'org_id_owner': {'type': 'integer'},
    'org_name_owner': {'type': 'string'},
    'publish': {'type': 'boolean'},
}

definition = {
    'url': 'functions/types',
    'item_title': 'Function Types',
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
    'mongo_indexes': {'type_id': ([('id', 1)], {'background': True}),
                      'org_id_owner': ([('org_id_owner', 1)], {'background': True}),
                      'is_valid': ([('is_valid', 1)], {'background': True}),
                      'name': ([('name', 'text')], {'background': True})
                      },
    'schema': _schema
}

# Search
search_definition = {
    'url': 'functions/types/search',
    'item_title': 'Functions Types Search',
    'datasource': {'source': RESOURCE_COLLECTION,
                   'projection': {
                       "_score": {"$meta": "textScore"},
                       "name": 1,
                       "id": 1,
                       "_updated": 1,
                       "_created": 1,
                       "_version": 1
                   },
                   'default_sort': [("_score", {"$meta": "textScore"})],
                   'filter': {'org_id_owner': 376, 'is_valid':True}
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
