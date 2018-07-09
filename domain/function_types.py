_schema = {
    'description': {'type': 'string'},
    'function_category_id': {'type': 'integer'},
    'function_category_name': {'type': 'string'},
    'function_type_id': {'type': 'integer', 'unique': True},
    'function_type_no': {'type': 'string'},
    'is_license': {'type': 'boolean'},
    'is_valid': {'type': 'boolean'},
    'name': {'type': 'string'},
    'org_id_owner': {'type': 'integer'},
    'org_name_owner': {'type': 'string'},
    'publish': {'type': 'boolean'},
}

definition = {
    'item_title': 'function types',
    'datasource': {'source': 'function_types',
                   },
    'additional_lookup': {
        'url': 'regex("[\d{1,9}]+")',
        'field': 'function_type_id',
    },
    'extra_response_fields': ['function_type_id'],
    'versioning': False,
    'resource_methods': ['GET', 'POST', 'DELETE'],
    'item_methods': ['GET', 'PATCH', 'PUT'],

    'schema': _schema
}
