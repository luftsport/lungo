RESOURCE_COLLECTION = 'payments'

_schema = {
    'id': {'type': 'integer',
           'required': True,
           'unique': True},
    'account_number': {'type': 'string'},
    'amount': {'type': 'float'},
    'amount_at_payment_time': {'type': 'float'},
    'fa_date_time': {'type': 'datetime'},
    'fee': {'type': 'float'},
    'fee_org': {'type': 'integer'},
    'invoice_id': {'type': 'integer'},
    'invoicing_org': 'Korsvoll Idrettslag',
    'invoicing_org_id': {'type': 'integer'},
    'net_amount': {'type': 'integer'},
    'paid_date': {'type': 'datetime'},
    'method_id': {'type': 'integer'},
    'receiver': {'type': 'string'},
    'receiver_org_id': {'type': 'integer'},
    'product_name': {'type': 'string'},
    'product_type': {'type': 'string'},
    'product_type_id': {'type': 'integer'},
    'person_id': {'type': 'integer'},
    'person_type': {'type': 'integer'},
    'transaction_id': {'type': 'integer'},
    'unit_cost_net': {'type': 'float'},
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
    'mongo_indexes': {'payment_id': ([('id', 1)], {'background': True}),
                      'method_id': ([('method_id', 1)], {'background': True}),
                      'receiver': ([('receiver_org_id', 1)], {'background': True}),
                      'paid_date': ([('paid_date', 1)], {'background': True}),
                      'person_id': ([('person_id', 1)], {'background': True}),
                      'text': ([('product_type', 'text'), ('type_name', 'text')], {'background': True}),
                      },
    'schema': _schema
}

# Process resource without data_relations
_schema_process = _schema.copy()

process_definition = {
    'url': 'payments/process',
    'item_title': 'Payments Process',
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
