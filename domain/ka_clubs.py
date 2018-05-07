_schema = {
    'id': {'type': 'integer'},
    'name': {'type': 'string'},
}

definition = {
    'item_title': 'ka_clubs',
    'datasource': {'source': 'ka_clubs',
                   },

    'versioning': False,
    'resource_methods': ['GET', 'POST'],
    'item_methods': ['GET', 'PATCH'],

    'schema': _schema
}