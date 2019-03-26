
RESOURCE_COLLECTION = 'licenses'

_schema = {
    'id': {'type': 'integer',
           'required': True,
           'unique': True},
    'type_id': {'type': 'integer'},
    'type_name': {'type': 'string'},
    'type_price': {'type': 'number'},
    'account_number': {'type': 'integer'},
    'competitor_id': {'type': 'integer'},
    'invoice_type_id': {'type': 'integer'},
    'invoice_type_name': {'type': 'string'},
    'kid': {'type': 'string'},
    'online_payment': {'type': 'boolean'},
    'org_id_owner': {'type': 'integer'},
    'person_id': {'type': 'integer'},
    'print_date': {'type': 'datetime'},
    'registered_date': {'type': 'datetime'},
    'total_paid_amount': {'type': 'number'},
    'paid_date': {'type': 'datetime'},
    'update_permission': {'type': 'boolean'},
    'period_from_date': {'type': 'datetime'},
    'period_function_type_count': {'type': 'integer'},
    'period_id': {'type': 'integer'},
    'period_name': {'type': 'string'},
    'period_owner_account_id': {'type': 'integer'},
    'period_owner_contact_id': {'type': 'integer'},
    'period_owner_org_id': {'type': 'integer'},
    'period_owner_org_name': {'type': 'string'},
    'period_to_date': {'type': 'datetime'},
    'status_date': {'type': 'datetime'},
    'status_id': {'type': 'integer'},
    'status_text': {'type': 'string'},

}

definition = {
    'url': 'licenses',
    'item_title': 'Licenses',
    'datasource': {'source': RESOURCE_COLLECTION,
                   },
    'additional_lookup': {
        'url': 'regex("[\d{1,9}]+")',
        'field': 'id',
    },
    'extra_response_fields': ['id'],
    'versioning': False,
    'resource_methods': ['GET'],
    'item_methods': ['GET'],
    'mongo_indexes': {'license_id': ([('id', 1)], {'background': True}),
                      'type_id': ([('type_id', 1)], {'background': True}),
                      'person_id': ([('person_id', 1)], {'background': True}),
                      'org_id_owner': ([('org_id_owner', 1)], {'background': True}),
                      'period_to_date': ([('period_to_date', 1)], {'background': True}),
                      'period_from_date': ([('period_from_date', 1)], {'background': True}),
                      'period_owner_org_id': ([('period_owner_org_id', 1)], {'background': True}),
                      'text': ([('period_name', 'text'), ('type_name', 'text')], {'background': True}),
                      },
    'schema': _schema
}

# Process resource without data_relations
_schema_process = _schema.copy()
_schema_process['type_id'] = {'type': 'integer'}
_schema_process['qualifications'] = {'type': 'list'}

process_definition = {
    'url': 'licenses/process',
    'item_title': 'Licenses Process',
    'datasource': {'source': RESOURCE_COLLECTION,
                   },
    'additional_lookup': {
        'url': 'regex("[\d{1,9}]+")',
        'field': 'id',
    },
    'pagination': False,
    'extra_response_fields': ['id'],
    'versioning': False,
    'resource_methods': ['GET', 'POST', 'DELETE'],
    'item_methods': ['GET', 'PATCH', 'PUT'],
    'schema': _schema_process
}
