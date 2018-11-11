
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
    'url': 'competences/types',
    'item_title': 'competences/types',
    'datasource': {'source': 'ka_orgs',
                   },
    'additional_lookup': {
        'url': 'regex("[\d{1,9}]+")',
        'field': 'Id',
    },
    'extra_response_fields': ['Id'],
    'versioning': False,
    'resource_methods': ['GET', 'POST'],
    'item_methods': ['GET', 'PATCH', 'PUT'],
    #'mongo_indexes': {'type_id': ([('id', 1)], {'background': True}),
    #                  'org_id_owner': ([('org_id_owner', 1)], {'background': True}),
    #                  'is_valid': ([('is_valid', 1)], {'background': True}),
    #                  'name': ([('name', 'text')], {'background': True})
    #                  },
    'schema': _schema
}