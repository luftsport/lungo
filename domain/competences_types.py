from bson import SON

RESOURCE_COLLECTION = 'competences_types'

_schema = {

    'attributes': {'type': 'dict'},
    'categories': {'type': 'list'},
    'checked_by': {'type': 'string'},  # String?
    'children': {'type': 'list'},
    'code': {'type': 'string'},
    'colorcode': {'type': 'string'},
    'id': {'type': 'integer',
           'required': True,
           'unique': True},
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
    'max_age': {'type': 'integer'},
    'min_age': {'type': 'integer'},
    'modified': {'type': 'string'},
    'organisations': {'type': 'list'},
    'pre_requisites': {'type': 'list'},
    'prequisites_text': {'type': 'string'},
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
                      'type': ([('meta_type', 1)], {'background': True}),
                      'title': ([('title', 'text'), ('description', 'text'), ('sports.name', 'text')], {'background': True})
                      },
    'allow_unknown': True,
    'schema': _schema
}

# Search
search_definition = {
    'url': 'competences/types/search',
    'item_title': 'Functions Types Search',
    'datasource': {'source': RESOURCE_COLLECTION,
                   'projection': {
                       "_score": {"$meta": "textScore"},
                       "title": 1,
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

# Aggregations
agg_count_meta_types = {
    'url': 'competences/types/meta/count',
    'item_title': 'Competences Meta Types',
    'pagination': False,
    'datasource': {
        'source': RESOURCE_COLLECTION,
        'aggregation': {
            'pipeline': [
                {"$group": {"_id": "$meta_type", "count": {"$sum": 1}}},
                {"$sort": SON([("count", -1), ("_id", -1)])}
            ]
        }
    }
}


