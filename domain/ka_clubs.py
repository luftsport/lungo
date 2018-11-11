_schema = {
    'Id': {'type': 'integer', 'unique': True, 'required': True},
    'AccountId': {'type': 'integer'},
    # 'AllChildren': {'type': 'string', 'default': ''},
    # 'AllParents': {'type': 'string', 'default': ''},
    # 'Children': {'type': 'string', 'default': ''},
    'City': {'type': 'string'},
    'Comment': {'type': 'string'},
    'ContactId': {'type': 'integer'},
    'CountyId': {'type': 'integer'},
    'CountyName': {'type': 'string', 'default': ''},
    'DescribingName': {'type': 'string', 'default': ''},
    'Email': {'type': 'string', 'default': ''},
    'IsActive': {'type': 'boolean', 'default': False},
    'LocalCouncilId': {'type': 'integer'},
    'LocalCouncilName': {'type': 'string'},
    'Mobile': {'type': 'string', 'default': ''},
    'Name': {'type': 'string', 'default': ''},
    'NifOrganisationNumber': {'type': 'string', 'required': True},
    'OrgTypeId': {'type': 'integer'},
    'Parents': {'type': 'string', 'default': ''},
    'RegisterAuthorityOrganisationNumber': {'type': 'integer'},
    'SportId': {'type': 'integer'},
    'SportName': {'type': 'string', 'default': ''},
    'Zip': {'type': 'string', 'default': ''},
}

definition = {
    'url': 'ka/clubs',
    'item_title': 'ka_clubs',
    'datasource': {'source': 'ka_clubs',
                   },
    'additional_lookup': {
        'url': 'regex("[\d{1,9}]+")',
        'field': 'Id',
    },
    'extra_response_fields': ['Id'],
    'versioning': False,
    'resource_methods': ['GET', 'POST'],
    'item_methods': ['GET', 'PATCH'],

    'schema': _schema
}
