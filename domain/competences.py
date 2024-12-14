from bson import SON

RESOURCE_COLLECTION = 'competences'

_schema = {
    'id': {'type': 'integer',
           'required': True,
           'unique': True},
    'approved_by_org_id': {'type': 'integer'},
    'approved_by_person_id': {'type': 'integer'},
    'course_id': {'type': 'integer'},
    'passed': {'type': 'boolean'},
    'person_id': {'type': 'integer'},
    'sald': {'type': 'integer'},
    'title': {'type': 'string'},
    'type_id': {'type': 'integer',
                'data_relation': {
                    'resource': 'competences_types',
                    'field': 'id',
                    'embeddable': True,
                },
                },
    'additional_title': {'type': 'string'},
    'paid_date': {'type': 'datetime'},
    'date': {'type': 'datetime'},
    'valid_until': {'type': 'datetime'},
    'grade': {'type': 'string'},
    'comments': {'type': 'string'},
    '_section': {'type': 'string'},
    '_code': {'type': 'string'},
    '_name': {'type': 'string'}
}

definition = {
    'url': 'competences',
    'item_title': 'Competences',
    'datasource': {'source': RESOURCE_COLLECTION,
                   },
    'additional_lookup': {
        'url': 'regex("[\d{1,9}]+")',
        'field': 'id',
    },
    'extra_response_fields': ['id'],
    'versioning': False,
    'resource_methods': ['GET'],
    'item_methods': ['GET'],
    'mongo_indexes': {'competence_id': ([('id', 1)], {'background': True}),
                      'person_id': ([('person_id', 1)], {'background': True}),
                      'type_id': ([('type_id', 1)], {'background': True}),
                      'approved': ([('approved_by_person_id', 1)], {'background': True}),
                      'valid_until': ([('valid_until', 1)], {'background': True}),
                      'section': ([('_section', 1)], {'background': True}),
                      'code': ([('_code', 1)], {'background': True}),
                      'title': ([('title', 'text')], {'background': True})
                      },
    'schema': _schema
}

# Process resource without data_relations
_schema_process = _schema.copy()
_schema_process['active_in_org_id'] = {'type': 'integer'}
_schema_process['person_id'] = {'type': 'integer'}

process_definition = {
    'url': 'competences/process',
    'item_title': 'Competences Process',
    'datasource': {'source': RESOURCE_COLLECTION,
                   },
    'additional_lookup': {
        'url': 'regex("[\d{1,9}]+")',
        'field': 'id',
    },
    'pagination': False,
    'extra_response_fields': ['id'],
    'versioning': False,
    'resource_methods': ['GET', 'POST', 'DELETE'],
    'item_methods': ['GET', 'PATCH', 'PUT'],
    'schema': _schema_process
}

# Search
search_definition = {
    'url': 'competences/search',
    'item_title': 'Competences Search',
    'datasource': {'source': RESOURCE_COLLECTION,
                   'projection': {
                       "_score": {"$meta": "textScore"},
                       "title": 1,
                       "type_id": 1,
                       "id": 1,
                       "person_id": 1,
                       "_updated": 1,
                       "_created": 1,
                       "_version": 1
                   },
                   'default_sort': [("_score", {"$meta": "textScore"})],
                   #'filter': {'_merged_to': {'$exists': False}}
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
agg_count_codes = {
    'url': 'competences/codes',
    'item_title': 'Competences Codes',
    'pagination': False,
    'datasource': {
        'source': RESOURCE_COLLECTION,
        'aggregation': {
            'pipeline': [
                {"$group": {"_id": "$title", "count": {"$sum": 1}}},
                {"$sort": SON([("count", -1), ("_id", -1)])}
            ]
        }
    }
}

# Aggregations
agg_count_types = {
    'url': 'competences/types/count',
    'item_title': 'Competences Types',
    'pagination': False,
    'datasource': {
        'source': RESOURCE_COLLECTION,
        'aggregation': {
            'pipeline': [
                {"$group": {"_id": "$type_id", "count": {"$sum": 1}}},
                {"$sort": SON([("count", -1), ("_id", -1)])}
            ]
        }
    }
}

"""
example api/v1/competences/types/count/year?aggregate={"$competences": [66667614, 66667596]}
"""
agg_count_types_by_year = {
    'url': 'competences/types/count/year',
    'item_title': 'Competences Types',
    'pagination': False,
    'datasource': {
        'source': RESOURCE_COLLECTION,
        'aggregation': {
            'pipeline': [
                {'$match': {'type_id': {'$in': '$competences'},
                            "approved_by_org_id": 376,
                            },
                 },
                {'$group': {"_id": {"year": {"$year": "$date"}, "code": "$_code", "type": "$type_id"},
                            "count": {"$sum": 1}}}
            ]
        }
    }
}

# Aggregations
agg_count_persons = {
    'url': 'competences/persons/count',
    'item_title': 'Competences persons',
    'pagination': False,
    'datasource': {
        'source': RESOURCE_COLLECTION,
        'aggregation': {
            'pipeline': [
                {"$group": {"_id": "$person_id", "count": {"$sum": 1}}},
                {"$sort": SON([("count", -1), ("_id", -1)])}
            ]
        }
    }
}
