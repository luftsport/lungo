RESOURCE_COLLECTION = 'countries'
_schema = {
    'id': {'type': 'integer',
           'required': True},
    'name': {'type': 'string'},
    'iso_alpha2': {'type': 'string'},
    'iso_alpha3': {'type': 'string'}
}

definition = {
    'url': 'countries',
    'item_title': 'Countries',
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
    'mongo_indexes': {'country_id': ([('id', 1)], {'background': True}),
                      'country_name': ([('name', 'text')], {'background': True})
                      },
    'schema': _schema
}

# Search
search_definition = {
    'url': 'countries/search',
    'item_title': 'Countries Search',
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
                   #'filter': {'org_id_owner': 376, 'is_valid':True}
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