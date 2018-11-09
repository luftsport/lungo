_schema = {

    'is_legal': {'type': 'boolean'},
    'org_type_id': {'type': 'integer', 'unique': True},
    'org_type_no': {'type': 'string', 'unique': True},
    'org_type_text': {'type': 'string'}
}

definition = {
    'item_title': 'organization/types',
    'datasource': {'source': 'organization_types',
                   },
    'additional_lookup': {
        'url': 'regex("[\d{1,9}]+")',
        'field': 'org_type_id',
    },
    'extra_response_fields': ['org_type_id'],
    'versioning': False,
    'resource_methods': ['GET', 'POST', 'DELETE'],
    'item_methods': ['GET', 'PATCH', 'PUT'],
    'mongo_indexes': {'org_type_id': ([('org_type_id', 1)], {'background': True}),
                      'org_type_text': ([('org_type_text', 'text')], {'background': True})
                      },
    'schema': _schema
}
