RESOURCE_COLLECTION = 'counties'
_schema = {
    'id': {'type': 'integer',
           'required': True},
    'name': {'type': 'string'},
    'parent_id': {'type': 'integer'},
    'region_no': {'type': 'string'},
    'region_short_no': {'type': 'integer'}
}

definition = {
    'url': 'counties',
    'item_title': 'Counties',
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
    'mongo_indexes': {'county_id': ([('id', 1)], {'background': True}),
                      'parent_id': ([('parent_id', 1)], {'background': True}),
                      'county_name': ([('name', 'text')], {'background': True})
                      },
    'schema': _schema
}

# Search
search_definition = {
    'url': 'counties/search',
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
