_schema = {
 'AccountId': {'type': 'integer'},
 'AllChildren': {'type': '', 'default': None},
 'AllParents': {'type': '', 'default': None},
 'Children': {'type': '', 'default': None},
 'City': {'type': 'string'},
 'Comment': {'type': 'string', 'default': None},
 'ContactId': {'type': 'integer'},
 'CountyId': {'type': 'integer'},
 'CountyName': {'type': 'string', 'default': None},
 'DescribingName': {'type': 'string', 'default': None},
 'Email': {'type': 'string', 'default': None},
 'Id': {'type': 'integer', 'unique': True, 'required': True},
 'IsActive': {'type': 'boolean', 'default': False},
 'LocalCouncilId': {'type': 'integer'},
 'LocalCouncilName': {'type': 'integer'},
 'Mobile': {'type': 'string'},
 'Name': {'type': 'integer'},
 'NifOrganisationNumber': {'type': 'string', 'required': True},
 'OrgTypeId': {'type': 'integer'},
 'Parents': {'type': 'string', 'default': None},
 'RegisterAuthorityOrganisationNumber': {'type': 'integer'},
 'SportId': {'type': 'integer'},
 'SportName': {'type': 'string'},
 'Zip': {'type': 'string'},
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