raise Exception

RESOURCE_COLLECTION = 'qualifications'

_schema = {

 'Address': {'type': 'string'},
 'BrregOrgNo': {'type': 'string'},
 'City': {'type': 'string'},
 'County': {'type': 'string'},
 'CountyId': {'type': 'integer'},
 'Email': {'type': 'string'},
 'Id': {'type': 'integer', 'unique': True},
 'Name': {'type': 'string'},
 'NameDescr': {'type': 'string'},
 'OrgType': {'type': 'string'},
 'OrgTypeId': {'type': 'integer'},
 'Url': {'type': 'string'},
 'Zip': {'type': 'string'},
 '_down': {'type': 'list', 'default': []},
 '_up': {'type': 'list', 'default': []},
}

definition = {
    'url': 'qualifications',
    'item_title': 'ka_orgs',
    'datasource': {'source': RESOURCE_COLLECTION,
                   },
    'additional_lookup': {
        'url': 'regex("[\d{1,9}]+")',
        'field': 'Id',
    },
    'extra_response_fields': ['Id'],
    'versioning': False,
    'resource_methods': ['GET', 'POST'],
    'item_methods': ['GET', 'PATCH', 'PUT'],

    'schema': _schema
}