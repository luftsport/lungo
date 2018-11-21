RESOURCE_COLLECTION = 'competences_types'

_schema = {

    'attributes': {'type': 'list'},
    'categories': {'type': 'list'},
    'checked_by': {'type': 'string'},  # String?
    'children': {'type': 'list'},
    'code': {'type': 'string'},
    'colorcode': {'type': 'string'},
    'id': {'type': 'integer',
           'required': True},
    'meta_type': {'type': 'string'},
    'type_id': {'type': 'integer'},
    'type_sa_id': {'type': 'integer'},
    'description': {'type': 'string'},
    'duration': {'type': 'string'},
    'durations': {'type': 'list'},
    'files': {'type': 'list'},
    'instructors': {'type': 'list'},
    'languages_available': {'type': 'list'},
    'locale': {'type': 'string'},
    'max_age': {'type': 'string'},
    'min_age': {'type': 'string'},
    'modified': {'type': 'string'},
    'organisations': {'type': 'list'},
    'pre_requisites': {'type': 'list'},
    'short_description': {'type': 'string'},
    'sports': {'type': 'list'},
    'title': {'type': 'string'},
    'valid_for': {'type': 'string'},
    'weight': {'type': 'integer'},

}

definition = {
    'url': 'competences/types',
    'item_title': 'Competences Types',
    'datasource': {'source': RESOURCE_COLLECTION,
                   },
    'additional_lookup': {
        'url': 'regex("[\d{1,9}]+")',
        'field': 'id',
    },
    'extra_response_fields': ['id'],
    'versioning': False,
    'resource_methods': ['GET', 'POST'],
    'item_methods': ['GET', 'PATCH', 'PUT'],
    'mongo_indexes': {'type_id': ([('id', 1)], {'background': True}),
                      'title': ([('title', 'text')], {'background': True})
                      },
    'schema': _schema
}
