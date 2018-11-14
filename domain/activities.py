_schema = {
    'id': {'type': 'integer',
           'unique': True,
           'required': True},
    'code': {'type': 'integer',
             'required': True},
    'description': {'type': 'string'},
    'name': {'type': 'string'},
    'org_id_owner': {'type': 'integer'},
    'org_name_owner': {'type': 'string'},
    'parent_activity_id': {'type': 'integer'},
}

definition = {
    'url': 'activities',
    'item_title': 'Activities',
    'datasource': {'source': 'activities',
                   },
    'additional_lookup': {
        'url': 'regex("[\d{1,9}]+")',
        'field': 'id',
    },
    'extra_response_fields': ['id'],
    'versioning': False,
    'resource_methods': ['GET', 'POST', 'DELETE'],
    'item_methods': ['GET', 'PATCH', 'PUT'],
    'mongo_indexes': {'type_id': ([('id', 1)], {'background': True}),
                      'org_id_owner': ([('org_id_owner', 1)], {'background': True}),
                      'parent_activity_id': ([('parent_activity_id', 1)], {'background': True}),
                      'name': ([('name', 'text')], {'background': True})
                      },
    'schema': _schema
}