_schema = {

    'change_type': {'type': 'string'},
    'created': {'type': 'datetime'},
    'entity_type': {'type': 'string'},
    'id': {'type': 'integer'},
    'merge_result_of': {'type': 'list'},
    'modified': {'type': 'datetime'},
    'name': {'type': 'string'},
    'sequence_ordinal': {'type': 'datetime'},
    '_club_id': {'type': 'integer'},
    '_ordinal': {'type': 'string', 'unique': True},
    '_status': {'type': 'string'},
    '_issues': {'type': 'dict'}
}

definition = {
    'item_title': 'integration changes',
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
    'item_methods': ['GET', 'PATCH', 'PUT'],

    'schema': _schema
}
