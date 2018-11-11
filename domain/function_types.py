_schema = {
    'description': {'type': 'string'},
    'category_id': {'type': 'integer'},
    'category_name': {'type': 'string'},
    'id': {'type': 'integer', 'unique': True},
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
    'item_title': 'function types',
    'datasource': {'source': 'types',
                   },
    'additional_lookup': {
        'url': 'regex("[\d{1,9}]+")',
        'field': 'id',
    },
    'extra_response_fields': ['type_id'],
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
