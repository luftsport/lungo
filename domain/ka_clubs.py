_schema = {
 'AccountId': {'type': 'integer'},
 'AllChildren': {'type': 'string', 'default': ''},
 'AllParents': {'type': 'string', 'default': ''},
 'Children': {'type': 'string', 'default': ''},
 'City': {'type': 'string'},
 'Comment': {'type': 'string'},
 'ContactId': {'type': 'integer'},
 'CountyId': {'type': 'integer'},
 'CountyName': {'type': 'string', 'default': ''},
 'DescribingName': {'type': 'string', 'default': ''},
 'Email': {'type': 'string', 'default': ''},
 'Id': {'type': 'integer', 'unique': True, 'required': True},
 'IsActive': {'type': 'boolean', 'default': False},
 'LocalCouncilId': {'type': 'integer', 'default': -1},
 'LocalCouncilName': {'type': 'integer', 'default': -1},
 'Mobile': {'type': 'string', 'default': ''},
 'Name': {'type': 'string', 'default': ''},
 'NifOrganisationNumber': {'type': 'string', 'required': True},
 'OrgTypeId': {'type': 'integer', 'default': -1},
 'Parents': {'type': 'string', 'default': ''},
 'RegisterAuthorityOrganisationNumber': {'type': 'integer', 'default': -1},
 'SportId': {'type': 'integer', 'default': -1},
 'SportName': {'type': 'string', 'default': ''},
 'Zip': {'type': 'string', 'default': ''},
}

definition = {
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