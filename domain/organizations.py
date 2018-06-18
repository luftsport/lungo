_schema = {

    'Account': { 'type': 'dict',
        'schema': {'AccountId': {'type': 'integer'},
                   'AccountNo': {'type': 'integer'}}
    },
    #'ActiveLabel': {'type': 'string'},
    #'CancellationDate': None,
    #'CancellationTypeId': None,
    'Comment': {'type': 'string', 'default': ''},
    'Contact': {'type': 'dict', 'default': {}},
    #'ContactId': {'type': 'integer'},
    'Created': {'type': 'datetime'},
    'DescribingName': {'type': 'string', 'default': ''},
    'IsActive': {'type': 'boolean'},
    'LocalCouncilId': {'type': 'integer'},
    'LocalCouncilName': {'type': 'string', 'default': ''},
    'Modified': {'type': 'datetime'},
    'NIFOrganizationNumber': {'type': 'string', 'default': ''},
    'Name': {'type': 'string', 'default': ''},
    'OrgId': {'type': 'integer', 'unique': True},
    'OrgStructuresDown': {'type': 'list',
                          'schema': {'type': 'dict',
                                     'schema': {'id': {'type': 'integer'},
                                                'type': {'type': 'integer',
                                                         'data_relation': {'resource': 'organization/types',
                                                                           'field': 'OrgTypeId',
                                                                           'embeddable': True
                                                         }}}}
                          },
    'OrgStructuresUp': {'type': 'list',
                        'schema': {'type': 'dict',
                                   'schema': {'id': {'type': 'integer'},
                                              'type': {'type': 'integer'}}}
                          },
    #'data_relation': {
    #    'resource': 'users',
    #    'field': '_id',
    #    'embeddable': True
    #},

    'OrganizationTypeId': {'type': 'integer'},
    'ParentOrganizationId': {'type': 'integer'},
    'RegisterAuthorityOrganizationNumber': {'type': 'string'},
    'ShortName': {'type': 'string'},
    'Activities': {'type': 'list', 'schema': {'type': 'dict', 'schema': {
        'ActivityCode': {'type': 'string'},
        'ActivityId': {'type': 'integer'},
        'Name': {'type': 'string'}

    }}},
    'MainActivity': { 'type': 'dict',
                      'schema': {'ActivityCode': {'type': 'string'},
                                'ActivityId': {'type': 'integer'},
                                'Name': {'type': 'string'}
                                },
    }
}

definition = {
    'item_title': 'organizations',
    'datasource': {'source': 'organizations',
                   },
    'additional_lookup': {
        'url': 'regex("[\d{1,9}]+")',
        'field': 'OrgId',
    },
    'extra_response_fields': ['OrgId'],
    'versioning': False,
    'resource_methods': ['GET', 'POST'],
    'item_methods': ['GET', 'PATCH', 'PUT'],

    'schema': _schema
}
