from bson import SON

_schema = {
    'id': {'type': 'integer', 'required': True, 'unique': True},
    'approved_by_org_id': {'type': 'integer'},
    'approved_by_person_id': {'type': 'integer'},
    'course_id': {'type': 'integer'},
    'passed': {'type': 'boolean'},
    'person_id': {'type': 'integer'},
    'sald': {'type': 'integer'},
    'title': {'type': 'string'},
    'type_id': {'type': 'integer'},
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
    'item_title': 'Competences',
    'datasource': {'source': 'competences',
                   },
    'additional_lookup': {
        'url': 'regex("[\d{1,9}]+")',
        'field': 'id',
    },
    'extra_response_fields': ['id'],
    'versioning': False,
    'resource_methods': ['GET', 'POST', 'DELETE'],
    'item_methods': ['GET', 'PATCH', 'PUT'],
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


agg_count_codes = {
    'datasource': {
        'source': 'competences',
        'aggregation': {
            'pipeline': [
                {"$group": {"_id": "$title", "count": {"$sum": 1}}},
                {"$sort": SON([("count", -1), ("_id", -1)])}
            ]
        }
    }
}