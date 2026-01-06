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
    'schema': _schema
}