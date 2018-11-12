_schema = {

    'born_after': {'type': 'datetime'},
    'born_before': {'type': 'datetime'},
    'class_id': {'type': 'integer'},
    'description': {'type': 'string'},
    'gender_id': {'type': 'integer'},
    'is_deleted': {'type': 'boolean'},
    'is_payable': {'type': 'boolean'},
    'is_valid': {'type': 'boolean'},
    'period_id': {'type': 'integer'},
    'id': {'type': 'integer'},
    'price': {'type': 'number'},
    'text': {'type': 'string'},
    'org_id_owner': {'type': 'integer'},
}

definition = {
    'url': 'licenses/types',
    'item_title': 'License Types',
    'datasource': {'source': 'licenses_types',
                   },
    'additional_lookup': {
        'url': 'regex("[\d{1,9}]+")',
        'field': 'id',
    },
    'extra_response_fields': ['id'],
    'versioning': False,
    'resource_methods': ['GET', 'POST'],
    'item_methods': ['GET', 'PATCH', 'PUT'],
    'mongo_indexes': {'id': ([('id', 1)], {'background': True}),
                      'org_id': ([('org_id_owner', 1)], {'background': True}),
                      'text': ([('name', 'text')], {'background': True})
                      },
    'schema': _schema
}
