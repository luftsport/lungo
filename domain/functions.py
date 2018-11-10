_schema = {

    'active_in_org_id': {'type': 'integer',
                         'nullable': True,
                         'data_relation': {
                             'resource': 'organizations',
                             'field': 'id',
                             'embeddable': True,

                         },
                         },
    'active_in_org_name': {'type': 'string'},
    'contact_id': {'type': 'integer'},
    'contact_information_id': {'type': 'integer'},
    'fa_function_id': {'type': 'integer'},
    'from_date': {'type': 'datetime'},
    'id': {'type': 'integer', 'unique': True, 'required': True},
    'type_id': {'type': 'integer'},
    'type_is_license': {'type': 'boolean'},
    'type_name': {'type': 'string'},
    'type_publish': {'type': 'boolean'},
    'has_paid_membership': {'type': 'boolean'},
    'is_deleted': {'type': 'boolean'},
    'is_passive': {'type': 'boolean'},
    'person_id': {'type': 'integer',
                  'nullable': True,
                  'data_relation': {
                      'resource': 'persons',
                      'field': 'id',
                      'embeddable': True,
                  },
                  },
    'role_level_id': {'type': 'integer'},
    'to_date': {'type': 'datetime'},
    'update_permission': {'type': 'boolean'},
}

definition = {
    'item_title': 'functions',
    'datasource': {'source': 'functions',
                   },
    'additional_lookup': {
        'url': 'regex("[\d{1,9}]+")',
        'field': 'id',
    },
    'extra_response_fields': ['id'],
    'versioning': False,
    'resource_methods': ['GET', 'POST', 'DELETE'],
    'item_methods': ['GET', 'PATCH', 'PUT'],
    'mongo_indexes': {'function_id': ([('id', 1)], {'background': True}),
                      'person_id': ([('person_id', 1)], {'background': True}),
                      'type_id': ([('type_id', 1)], {'background': True}),
                      'to_date': ([('to_date', 1)], {'background': True}),
                      'active_in_org_id': ([('active_in_org_id', 1)], {'background': True}),
                      'has_paid_membership': ([('has_paid_membership', 1)], {'background': True}),
                      # 'type_name': ([('title', 'text')], {'background': True})
                      },
    'schema': _schema
}

# Aggregation
from bson import SON, ObjectId

agg_count_types = {
    'datasource': {
        'source': 'functions',
        'aggregation': {
            'pipeline': [
                {"$group": {"_id": "$type_id", "count": {"$sum": 1}}},
                {"$sort": SON([("count", -1), ("_id", -1)])}
            ]
        }
    }
}
