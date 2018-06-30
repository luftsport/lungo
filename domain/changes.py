_schema = {

    'Changes': {'type': 'list', 'schema':
        {'type': 'dict',
         'schema':
             {
                 'ChangeType': {'type': 'string'},
                 'Created': {'type': 'datetime'},
                 'Id': {'type': 'integer'},
                 'MergeResultOf': {'type': 'list'},
                 'Modified': {'type': 'datetime'},
                 'SequenceOrdinal': {'type': 'datetime'},
             }
         }
                },
    'StartDate': {'type': 'datetime'},
    'EndDate': {'type': 'datetime'},
    'NextStartDate': {'type': 'datetime'},
    'ReportDate': {'type': 'datetime'},
    'club_id': {'type': 'integer'}
}

definition = {
    'item_title': 'integration changes',
    'datasource': {'source': 'changes',
                   },

    'extra_response_fields': ['club_d'],
    'versioning': False,
    'resource_methods': ['GET', 'POST', 'DELETE'],
    'item_methods': ['GET', 'PATCH', 'PUT'],

    'schema': _schema
}
