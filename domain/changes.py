_schema = {

    'Changes': {'type': 'list', 'schema':
        {'type': 'dict',
         'schema':
             {
                 'ChangeType': {'type': 'string'},
                 'Created': {'type': 'datetime'},
                 'EntityType': {'type': 'string'},
                 'Id': {'type': 'integer'},
                 'MergeResultOf': {'type': 'list'},
                 'Modified': {'type': 'datetime'},
                 'Name': {'type': 'string'},
                 'SequenceOrdinal': {'type': 'datetime'},
             }
         }
                },
    'StartDate': {'type': 'datetime'},
    'EndDate': {'type': 'datetime'},
    'NextStartDate': {'type': 'datetime'},
    'ReportDate': {'type': 'datetime'},
    'ParentOrgId': {'type': 'integer'},
    'club_id': {'type': 'integer'}
}

definition = {
    'item_title': 'Integration Changes',
    'datasource': {'source': 'changes',
                   },
    # Can be a time in microseconds
    #'additional_lookup': {
    #    'url': 'regex("[\d{1,20}]+")',
    #    'field': 'Changes.SequenceOrdinal',
    #},

    'extra_response_fields': ['club_d'],
    'versioning': False,
    'resource_methods': ['GET', 'POST', 'DELETE'],
    'item_methods': ['GET', 'PATCH', 'PUT'],

    'schema': _schema
}
