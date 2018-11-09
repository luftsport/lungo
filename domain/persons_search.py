from domain.persons import _schema

definition = {
    'item_title': 'persons',
    'datasource': {'source': 'persons'},
    'additional_lookup': {
        'url': 'regex("[\d{1,9}]+")',
        'field': 'id',
    },
    'extra_response_fields': ['id'],
    'versioning': True,
    'resource_methods': ['GET'],
    'item_methods': [],
    'allow_unknown': True,
    'schema': _schema
}
