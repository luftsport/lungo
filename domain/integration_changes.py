from bson import SON

_schema = {
    'id': {'type': 'integer'},
    'change_type': {'type': 'string'},
    'created': {'type': 'datetime'},
    'entity_type': {'type': 'string'},
    'merge_result_of': {'type': 'list'},
    'modified': {'type': 'datetime'},
    'name': {'type': 'string'},
    'sequence_ordinal': {'type': 'datetime'},
    '_org_id': {'type': 'integer'},
    '_ordinal': {'type': 'string',
                 'unique': True,
                 'required': True},
    '_status': {'type': 'string'},
    '_issues': {'type': 'dict'},
    '_realm': {'type': 'string',
               'allowed': ['DST', 'PROD'],
               'required': True},

}

definition = {
    'url': 'integration/changes',
    'item_title': 'Integration Changes',
    'datasource': {'source': 'integration_changes',
                   },
    # Can be a time in microseconds
    # 'additional_lookup': {
    #    'url': 'regex("[\d{1,20}]+")',
    #    'field': 'Changes.SequenceOrdinal',
    # },

    'extra_response_fields': ['Id'],
    'versioning': False,
    'resource_methods': ['GET', 'POST', 'DELETE'],
    'item_methods': ['GET', 'PATCH', 'PUT', 'DELETE'],
    'mongo_indexes': {'id': ([('id', 1)], {'background': True}),
                      'created': ([('created', 1)], {'background': True}),
                      '_status': ([('_status', 1)], {'background': True}),
                      '_org_id': ([('_org_id', 1)], {'background': True}),
                      '_updated': ([('_updated', 1)], {'background': True}),
                      'entity_type': ([('_status', 1)], {'background': True}),
                      'change_type': ([('_status', 1)], {'background': True}),
                      },
    'schema': _schema
}

# Aggregations
agg_count_entity_types = {
    'url': 'integration/changes/entity/types',
    'item_title': 'Integration Changes Entity Types',
    'datasource': {
        'source': 'integration_changes',
        'aggregation': {
            'pipeline': [
                {"$group": {"_id": "$entity_type", "count": {"$sum": 1}}},
                {"$sort": SON([("count", -1), ("_id", -1)])}
            ]
        }
    }
}

agg_count_statuses = {
    'url': 'integration/changes/status',
    'item_title': 'Integration Changes Status',
    'datasource': {
        'source': 'integration_changes',
        'aggregation': {
            'pipeline': [
                {"$group": {"_id": "$_status", "count": {"$sum": 1}}},
                {"$sort": SON([("count", -1), ("_id", -1)])}
            ]
        }
    }
}

agg_count_clubs = {
    'url': 'integration/changes/clubs',
    'item_title': 'Integration Changes Clubs',
    'datasource': {
        'source': 'integration_changes',
        'aggregation': {
            'pipeline': [
                {"$group": {"_id": "$_org_id", "count": {"$sum": 1}}},
                {"$sort": SON([("count", -1), ("_id", -1)])}
            ]
        }
    }
}

agg_count_change_types = {
    'url': 'integration/changes/change/types',
    'item_title': 'Integration Changes Types',
    'datasource': {
        'source': 'integration_changes',
        'aggregation': {
            'pipeline': [
                {"$group": {"_id": "$change_type", "count": {"$sum": 1}}},
                {"$sort": SON([("count", -1), ("_id", -1)])}
            ]
        }
    }
}
