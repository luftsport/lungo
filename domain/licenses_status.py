_schema = {
    'id': {'type': 'integer',
           'required': True},
    'name': {'type': 'string'},
}

definition = {
    'url': 'licenses/status',
    'item_title': 'License Statuses',
    'datasource': {'source': 'licenses_status',
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
                      'name': ([('name', 'text')], {'background': True})
                      },
    'schema': _schema
}
