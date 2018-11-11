_schema = {
    'Id': {'type': 'integer', 'required': True},
    'Code': {'type': 'string', 'required': True},
    'Name': {'type': 'string'},
    'PersonId': {'type': 'integer', 'required': True}
}

definition = {
    'url': 'ka/competences',
    'item_title': 'ka_competence',
    'datasource': {'source': 'ka_competence',
                   },
    'additional_lookup': {
        'url': 'regex("[\w{1}\-\w{1,5}]+")',
        'field': 'Code',
    },
    'extra_response_fields': ['Id'],
    'versioning': False,
    'resource_methods': ['GET', 'POST'],
    'item_methods': ['GET', 'PATCH', 'PUT'],

    'schema': _schema
}
