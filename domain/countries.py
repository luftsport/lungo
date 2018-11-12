_schema = {
    'id': {'type': 'integer',
           'required': True},
    'name': {'type': 'string'},
    'iso_alpha2': {'type': 'string'},
    'iso_alpha3': {'type': 'integer'}
}

definition = {
    'url': 'countries',
    'item_title': 'Countries',
    'datasource': {'source': 'countries',
                   },
    'additional_lookup': {
        'url': 'regex("[\d{1,9}]+")',
        'field': 'id',
    },
    'extra_response_fields': ['id'],
    'versioning': False,
    'resource_methods': ['GET', 'POST', 'DELETE'],
    'item_methods': ['GET', 'PATCH', 'PUT'],
    'mongo_indexes': {'country_id': ([('id', 1)], {'background': True}),
                      'country_name': ([('name', 'text')], {'background': True})
                      },
    'schema': _schema
}
