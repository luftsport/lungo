
_schema = {
 'id': {'type': 'integer', 'unique': True},
 'name': {'type': 'string'},
 'activity_id': {'type': 'integer'},
 'org_type_id': {'type': 'integer'},
}

definition = {
    'url': 'ka/orgs/activity',
    'item_title': 'ka_org_activity',
    'datasource': {'source': 'ka_org_activity',
                   },
    'additional_lookup': {
        'url': 'regex("[\d{1,9}]+")',
        'field': 'id',
    },
    'extra_response_fields': ['id'],
    'versioning': False,
    'resource_methods': ['GET', 'POST'],
    'item_methods': ['GET', 'PATCH', 'PUT'],

    'schema': _schema
}