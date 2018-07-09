_schema = {

    'account': {'type': 'dict',
                # 'schema': {'AccountId': {'type': 'integer'},
                #           'AccountNo': {'type': 'integer'}}
                },
    # 'ActiveLabel': {'type': 'string'},
    # 'CancellationDate': None,
    # 'CancellationTypeId': None,
    'comment': {'type': 'string', 'default': ''},
    'contact': {'type': 'dict', 'default': {}},
    # 'ContactId': {'type': 'integer'},
    'created': {'type': 'datetime'},
    'describing_name': {'type': 'string', 'default': ''},
    'is_active': {'type': 'boolean'},
    'local_council_id': {'type': 'integer'},
    'local_council_name': {'type': 'string', 'default': ''},
    'modified': {'type': 'datetime'},
    'nif_organization_number': {'type': 'string', 'default': ''},
    'name': {'type': 'string', 'default': ''},
    'org_id': {'type': 'integer', 'unique': True},
    '_up': {'type': 'list',
            'schema': {'type': 'dict',
                       'schema': {'id': {'type': 'integer'},
                                  'type': {'type': 'integer',
                                           'data_relation': {'resource': 'organizations/types',
                                                             'field': 'org_type_id',
                                                             'embeddable': True
                                                             }}}}
            },
    '_down': {'type': 'list',
              'schema': {'type': 'dict',
                         'schema': {'id': {'type': 'integer'},
                                    'type': {'type': 'integer',
                                             'data_relation': {'resource': 'organizations/types',
                                                               'field': 'org_type_id',
                                                               'embeddable': True
                                                               }}}}
              },
    # 'data_relation': {
    #    'resource': 'users',
    #    'field': '_id',
    #    'embeddable': True
    # },

    'organization_type_id': {'type': 'integer'},
    'parent_organization_id': {'type': 'integer'},
    'register_authority_organization_number': {'type': 'string'},
    'short_name': {'type': 'string'},
    'activities': {'type': 'list', 'schema': {'type': 'dict', 'schema': {
        'code': {'type': 'string'},
        'id': {'type': 'integer'},
        'name': {'type': 'string'}

    }}},
    'main_activity': {'type': 'dict',
                     'schema': {'code': {'type': 'string'},
                                'id': {'type': 'integer'},
                                'name': {'type': 'string'}
                                },
                     }
}

definition = {
    'item_title': 'organizations',
    'datasource': {'source': 'organizations',
                   },
    'additional_lookup': {
        'url': 'regex("[\d{1,9}]+")',
        'field': 'org_id',
    },
    'extra_response_fields': ['org_id'],
    'versioning': False,
    'resource_methods': ['GET', 'POST', 'DELETE'],
    'item_methods': ['GET', 'PATCH', 'PUT'],

    'schema': _schema
}
