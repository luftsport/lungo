_schema = {

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
    'total_paid_amount': {'type': 'float'},
    'update_permission': {'type': 'boolean'},
    'id': {'type': 'integer', 'required': True, 'unique': True},
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
    'type_id': {'type': 'integer'},
    'type_name': {'type': 'string'},
    'type_price': {'type': 'float'},
}

definition = {
    'item_title': 'Licenses',
    'datasource': {'source': 'licenses',
                   },
    'additional_lookup': {
        'url': 'regex("[\d{1,9}]+")',
        'field': 'id',
    },
    'extra_response_fields': ['id'],
    'versioning': False,
    'resource_methods': ['GET', 'POST'],
    'item_methods': ['GET', 'PATCH', 'PUT'],

    'schema': _schema
}
