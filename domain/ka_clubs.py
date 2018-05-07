_schema = {
    'id': {'type': 'integer'},
    'name': {'type': 'string'},
}

definition = {
    'item_title': 'ka_clubs',
    'datasource': {'source': 'ka_clubs',
                   },
    'additional_lookup': {
        'url': 'regex("[\d{1,9}]+")',
        'field': 'id',
    },
    'extra_response_fields': ['id'],
    'versioning': False,
    'resource_methods': ['GET', 'POST'],
    'item_methods': ['GET', 'PATCH'],


    'schema': _schema
}