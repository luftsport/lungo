RESOURCE_COLLECTION = 'functions'

_schema = {

    'active_in_org_id': {'type': 'integer',
                         'data_relation': {
                             'resource': 'organizations',
                             'field': 'id',
                             'embeddable': True,

                         },
                         },
    'org_id': {'type': 'integer',
               'data_relation': {
                   'resource': 'organizations',
                   'field': 'id',
                   'embeddable': True,

               },
               },
    'org_type_id': {'type': 'integer'},
    'active_in_org_name': {'type': 'string'},
    'contact_id': {'type': 'integer'},
    'contact_information_id': {'type': 'integer'},
    'fa_function_id': {'type': 'integer'},
    'from_date': {'type': 'datetime'},
    'id': {'type': 'integer',
           'unique': True,
           'required': True},
    'type_id': {'type': 'integer'},
    'type_is_license': {'type': 'boolean'},
    'type_name': {'type': 'string'},
    'type_publish': {'type': 'boolean'},
    'has_paid_membership': {'type': 'boolean'},
    'is_deleted': {'type': 'boolean'},
    'is_passive': {'type': 'boolean'},
    'person_id': {'type': 'integer',
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
    'url': 'functions',
    'item_title': 'functions',
    'datasource': {'source': RESOURCE_COLLECTION,
                   'filter': {
                       # Show only active by default
                       # @TODO move to hook and add filter if not set
                       'is_passive': False,
                       'is_deleted': False
                   }
                   },
    'additional_lookup': {
        'url': 'regex("[\d{1,9}]+")',
        'field': 'id',
    },
    'extra_response_fields': ['id'],
    'versioning': False,
    'resource_methods': ['GET'],
    'item_methods': ['GET'],
    'mongo_indexes': {'function_id': ([('id', 1)], {'background': True}),
                      'person_id': ([('person_id', 1)], {'background': True}),
                      'type_id': ([('type_id', 1)], {'background': True}),
                      'to_date': ([('to_date', 1)], {'background': True}),
                      'active_in_org_id': (
                          [('active_in_org_id', 1), ('org_id', 1), ('org_type_id', 1)], {'background': True}),
                      'has_paid_membership': ([('has_paid_membership', 1)], {'background': True}),
                      'type_name': ([('type_name', 'text')], {'background': True})
                      },
    'schema': _schema
}

# Process resource without data_relations
_schema_process = _schema.copy()
_schema_process['active_in_org_id'] = {'type': 'integer'}
_schema_process['org_id'] = {'type': 'integer'}
_schema_process['person_id'] = {'type': 'integer'}

process_definition = {
    'url': 'functions/process',
    'item_title': 'Functions Process',
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

# Aggregation
from bson import SON, ObjectId

agg_get_persons_by_type_and_orgs = {
    'url': 'functions/persons',
    'item_title': 'Functions Types Count',
    'pagination': False,
    'datasource': {
        'source': RESOURCE_COLLECTION,
        'aggregation': {
            'pipeline':
                [
                    {
                        "$match": {
                            "type_id": "$type_id",  # type_id - integer
                            "org_id": {"$in": "$org_ids"},  # org_ids - [integer,..]
                            "is_deleted": False,
                            "is_passive": False
                        }
                    },
                    {
                        "$group": {
                            "_id": "$type_id",
                            "person_ids": {
                                "$addToSet": "$person_id"
                            }
                        }
                    }
                ]
        }
    }
}

## STATS ###
agg_count_types = {
    'url': 'functions/types/count',
    'item_title': 'Functions Types Count',
    'pagination': False,
    'datasource': {
        'source': RESOURCE_COLLECTION,
        'aggregation': {
            'pipeline': [
                {"$group": {"_id": {"type_id": "$type_id", "name": "$type_name"}, "count": {"$sum": 1}}},
                {"$sort": SON([("count", -1), ("_id", -1)])}
            ]
        }
    }
}

agg_count_types_org = {
    'url': 'functions/types/org/count',
    'item_title': 'Functions Types Count',
    'pagination': False,
    'datasource': {
        'source': RESOURCE_COLLECTION,
        'aggregation': {
            'pipeline': [
                {"$match": {"active_in_org_id": "$org_id"}},
                {"$group": {"_id": {"type_id": "$type_id", "name": "$type_name"}, "count": {"$sum": 1}}},
                {"$sort": SON([("count", -1), ("_id", -1)])}
            ]
        }
    }
}

agg_count_types_activity = {
    'url': 'functions/types/activity/count',
    'item_title': 'Functions Types Count',
    'pagination': False,
    'datasource': {
        'source': RESOURCE_COLLECTION,
        'aggregation': {
            'pipeline': [
                {"$match": {"active_in_org_id": {"$in": "$org_ids"}}},
                {"$group": {"_id": {"type_id": "$type_id", "name": "$type_name"}, "count": {"$sum": 1}}},
                {"$sort": SON([("count", -1), ("_id", -1)])}
            ]
        }
    }
}
