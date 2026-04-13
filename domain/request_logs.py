RESOURCE_COLLECTION = 'request_logs'
_schema = {
    'request_id': {'type': 'string', },
    'method': {'type': 'string', },
    'path': {'type': 'string', },
    'request_args': {'type': 'string', },
    'status_code': {'type': 'integer', },
    'duration': {'type': 'float', },
    'start_time': {'type': 'float', },
}

definition = {
    'url': 'request/logs',
    'item_title': 'Request logs',
    'datasource': {'source': RESOURCE_COLLECTION,
                   },
    'versioning': False,
    'resource_methods': ['GET', 'POST', 'DELETE'],
    'item_methods': ['GET'],
    'mongo_indexes': {'request': ([('request_id', 1)], {'background': True}),
                      'duration': ([('duration', 1)], {'background': True}),
                      'timestamps': ([('_created', 1), ('_updated', 1)], {'background': True})
                      },
    'schema': _schema
}
