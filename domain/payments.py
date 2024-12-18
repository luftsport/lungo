from bson import SON

RESOURCE_COLLECTION = 'payments'

_schema = {
    'id': {'type': 'integer',
           'required': True,
           'unique': True},
    'kid': {'type': 'string',
            'unique': False},
    'account_number': {'type': 'string'},
    'amount': {'type': 'float'},
    'amount_at_payment_time': {'type': 'float'},
    # 'fa_date_time': {'type': 'datetime'}, # Rubbish from NIF
    'fee': {'type': 'float'},
    'fee_org': {'type': 'integer'},
    'invoice_id': {'type': 'integer'},
    'invoicing_org': {'type': 'string'},
    'invoicing_org_id': {'type': 'integer'},
    'net_amount': {'type': 'float'},
    'paid_date': {'type': 'datetime'},
    'method_id': {'type': 'integer'},
    'receiver': {'type': 'string'},
    'receiver_org_id': {'type': 'integer'},
    'product_name': {'type': 'string'},
    'product_type': {'type': 'string'},
    'product_type_id': {'type': 'integer'},
    'person_id': {'type': 'integer'},
    'person_type': {'type': 'integer'},
    'payment_id': {'type': 'integer'},
    'unit_cost_net': {'type': 'float'},
    'org_id': {'type': 'integer'}
}

definition = {
    'url': 'payments',
    'item_title': 'Payments',
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
                      'kid_nr': ([('kid', 1)], {'background': True}),
                      'method_id': ([('method_id', 1)], {'background': True}),
                      'receiver': ([('receiver_org_id', 1)], {'background': True}),
                      'paid_date': ([('paid_date', 1)], {'background': True}),
                      'person_id': ([('person_id', 1)], {'background': True}),
                      'text': ([('product_type', 'text'), ('product_name', 'text')], {'background': True}),
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


payments_total_per_year = {
    'url': 'payments/year/total',
    'item_title': 'Aggregates and returns total amount payed for year',
    'pagination': False,
    'datasource': {
        'source': RESOURCE_COLLECTION,
        'aggregation': {
            'pipeline': [
        {'$match': {'paid_date': {'$gte': '$from_date', '$lte': '$to_date'}}},
        {'$group': {"_id": "payments", "amount": {"$sum": '$amount'}, "count": {"$sum": 1}}}

                #{'$project': {'Total': {"$sum": '$amount'}}}
        ]
        }
    }
}

# Aggregations
agg_count_payment_products = {
    'url': 'payments/products/count',
    'item_title': 'Payment Products',
    'pagination': False,
    'datasource': {
        'source': RESOURCE_COLLECTION,
        'aggregation': {
            'pipeline': [
                {"$group": {"_id": {"id": "$product_type_id", "product_type": "$product_name"}, "count": {"$sum": 1}}},
                {"$sort": SON([("count", -1), ("_id", -1)])}
            ]
        }
    }
}