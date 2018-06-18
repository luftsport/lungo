_schema = {

    'IsLegal': {'type': 'boolean'},
    'OrgTypeId': {'type': 'integer', 'unique': True},
    'OrgTypeNo': {'type': 'string', 'unique': True},
    'OrgTypeText': {'type': 'string'}
}

definition = {
    'item_title': 'organization/types',
    'datasource': {'source': 'organization_types',
                   },
    'additional_lookup': {
        'url': 'regex("[\d{1,9}]+")',
        'field': 'OrgTypeId',
    },
    'extra_response_fields': ['OrgTypeId'],
    'versioning': False,
    'resource_methods': ['GET', 'POST'],
    'item_methods': ['GET', 'PATCH', 'PUT'],

    'schema': _schema
}
