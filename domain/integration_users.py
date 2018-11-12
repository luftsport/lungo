from bson import SON

_schema = {'username': {'type': 'string',
                        'required': True},
           'password': {'type': 'string',
                        'required': True},
           'id': {'type': 'integer',
                  'required': True,
                  'unique': True},
           'app_id': {'type': 'integer',
                      'required': True},
           'function_id': {'type': 'integer',
                           'required': True},
           'club_id': {'type': 'integer',
                       'required': True,
                       'unique': True},
           'club_name': {'type': 'string'},
           'club_created': {'type': 'datetime',
                            'required': True},
           'modified': {'type': 'datetime'},
           '_realm': {'type': 'string',
                      'allowed': ['DST', 'PROD'],
                      'required': True},
           '_active': {'type': 'boolean',
                       'default': True}
           }

definition = {
    'url': 'integration/users',
    'item_title': 'Integration Users',
    'datasource': {'source': 'integration_users',  # @TODO - move to integration_users
                   },
    'additional_lookup': {
        'url': 'regex("[\d{1,20}]+")',
        'field': 'club_id',
        # 'field': 'id',
    },
    'extra_response_fields': ['club_id'],
    'versioning': False,
    'resource_methods': ['GET', 'POST'],
    'item_methods': ['GET', 'PATCH', 'PUT', 'DELETE'],
    'mongo_indexes': {'id': ([('id', 1)], {'background': True}),
                      'club_id': ([('club_id', 1)], {'background': True}),
                      'username': ([('username', 1)], {'background': True}),
                      'function_id': ([('function_id', 1)], {'background': True}),
                      'app_id': ([('app_id', 1)], {'background': True}),
                      },
    'schema': _schema
}

# Count clubs by club_id
agg_count_clubs = {
    'url': 'integration/users/clubs',
    'datasource': {
        'source': 'integration',
        'aggregation': {
            'pipeline': [
                {"$group": {"_id": "$club_id", "count": {"$sum": 1}}},
                {"$sort": SON([("count", -1), ("_id", -1)])}
            ]
        }
    }
}
