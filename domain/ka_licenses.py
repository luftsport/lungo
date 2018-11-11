_schema = {
    'Id': {'type': 'integer', 'required': True},
    'Name': {'type': 'string'},
    'PersonId': {'type': 'integer', 'required': True}
}

definition = {
    'url': 'ka/licenses',
    'item_title': 'ka_licenses',
    'datasource': {'source': 'ka_licenses',
                   },
    'additional_lookup': {
        'url': 'regex("[\d{1,9}]+")',
        'field': 'Id',
    },
    'extra_response_fields': ['Id'],
    'versioning': False,
    'resource_methods': ['GET', 'POST'],
    'item_methods': ['GET', 'PATCH', 'PUT'],

    'schema': _schema
}
