RESOURCE_COLLECTION = 'ohdear_snapshots'

_schema = {
}

definition = {
    'url': 'ohdear/snapshots',
    'item_title': 'OhDear Snapshots',
    'datasource': {'source': RESOURCE_COLLECTION,
                   },
    'allow_unknown': True,
    'versioning': False,
    'resource_methods': ['GET', 'POST'],
    'item_methods': ['GET'],
    'mongo_indexes': {
        'timestamps': ([('_created', 1), ('_updated', 1)], {'background': True})
    },
    'schema': _schema
}
