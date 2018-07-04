_schema = {

    'ChangeType': {'type': 'string'},
    'Created': {'type': 'datetime'},
    'EntityType': {'type': 'string'},
    'Id': {'type': 'integer'},
    'MergeResultOf': {'type': 'list'},
    'Modified': {'type': 'datetime'},
    'Name': {'type': 'string'},
    'SequenceOrdinal': {'type': 'datetime'},
    'club_id': {'type': 'integer'},
    'ordinal': {'type': 'string', 'unique': True},
    '_status': {'type': 'string'},
    '_issues': {'type': 'dict'}
}

definition = {
    'item_title': 'integration changes stream',
    'datasource': {'source': 'changes_stream',
                   },
    # Can be a time in microseconds
    # 'additional_lookup': {
    #    'url': 'regex("[\d{1,20}]+")',
    #    'field': 'Changes.SequenceOrdinal',
    # },

    'extra_response_fields': ['Id'],
    'versioning': False,
    'resource_methods': ['GET', 'POST', 'DELETE'],
    'item_methods': ['GET', 'PATCH', 'PUT'],

    'schema': _schema
}
