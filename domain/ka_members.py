_schema = {
    'Id': {'type': 'integer'},
    'MelwinId': {'type': 'integer', 'default': None},
    'IsActive': {'type': 'boolean'},
    'MemberFeeStatus': {'type': 'integer'},
    'GenderId': {'type': 'integer'},
    'GenderText': {'type': 'string'},
    'TrainingFeeStatus': {'type': 'integer'},
    'BirthDate': {'type': 'datetime'},
    'Phone': {'type': 'string'},
    'Address': {'type': 'string'},
    'PostNumber': {'type': 'string'},
    'City': {'type': 'string'},
    'FullName': {'type': 'string'},
    'Email': {'type': 'string'},
    'competence': {'type': 'list',
                   'default': []},
    'licenses': {'type': 'list',
                 'default': []},
    'clubs': {'type': 'list',
              'default': []},
    'sections': {'type': 'list',
                 'default': []},
}

definition = {
    'item_title': 'ka_members',
    'datasource': {'source': 'kamembers',
                   },
    'additional_lookup': {
        'url': 'regex("[\d{1,9}]+")',
        'field': 'Id',
    },
    'extra_response_fields': ['Id'],
    'versioning': True,
    'resource_methods': ['GET', 'POST'],
    'item_methods': ['GET', 'PATCH', 'PUT'],

    'schema': _schema
}