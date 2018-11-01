_schema = {

    'approved_by_org_id': {'type': 'integer'},
    'course_id': {'type': 'integer'},
    'passed': {'type': 'boolean'},
    'person_id': {'type': 'integer'},
    'id': {'type': 'integer', 'required': True, 'unique': True},
    'sald': {'type': 'integer'},
    'title': {'type': 'string'},
    'type_id': {'type': 'integer'},
    'additional_title': {'type': 'string'},
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

    'schema': _schema
}
