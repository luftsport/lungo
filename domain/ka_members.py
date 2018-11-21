_schema = {
    'Id': {'type': 'integer'},
    'MelwinId': {'type': 'integer'},
    'GenderId': {'type': 'integer'},
    'GenderText': {'type': 'string'},
    'TrainingFeeStatus': {'type': 'integer'},
    'BirthDate': {'type': 'datetime'},
    'Phone': {'type': 'string'},
    'Address': {'type': 'string'},
    'PostNumber': {'type': 'string'},
    'City': {'type': 'string'},
    'FullName': {'type': 'string'},
    'Email': {'type': 'string'},
    'competence': {'type': 'list',
                   'default': []},
    'licenses': {'type': 'list',
                 'default': []},
    'clubs_active': {'type': 'list',
                     'default': []},
    'clubs_inactive': {'type': 'list',
                       'default': []},
    'clubs_payment': {'type': 'list',
                      'default': []},
    'sections': {'type': 'list',
                 'default': []},
    'activities': {'type': 'list',
                   'default': []},
    'Magazines': {'type': 'list',
                  'default': []},
    'Products': {'type': 'list',
                 'default': []},
}

definition = {
    'url': 'ka/members',
    'item_title': 'ka_members',
    'datasource': {'source': 'ka_members',
                   },
    'additional_lookup': {
        'url': 'regex("[\d{1,9}]+")',
        'field': 'Id',
    },
    'extra_response_fields': ['Id'],
    'versioning': False,
    'resource_methods': ['GET', 'POST'],
    'item_methods': ['GET', 'PATCH', 'PUT'],

    'schema': _schema
}

"""
    [
        { 
            "$unwind" : {
                "path" : "$activities"
            }
        }, 
        { 
            "$group" : {
                "_id" : "$activities.OrgId", 
                "count" : {
                    "$sum" : 1.0
                }
            }
        }, 
        { 
            "$sort" : {
                "count" : -1.0
            }
        }
    ]
"""
