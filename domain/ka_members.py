from bson import SON

RESOURCE_COLLECTION = 'ka_members'

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
    '_merged_to': {'type': 'integer'}
}

definition = {
    'url': 'ka/members',
    'item_title': 'ka_members',
    'datasource': {'source': RESOURCE_COLLECTION,
                   },
    'additional_lookup': {
        'url': 'regex("[\d{1,9}]+")',
        'field': 'Id',
    },
    'extra_response_fields': ['Id'],
    'versioning': False,
    'resource_methods': ['GET', 'POST'],
    'item_methods': ['GET', 'PATCH', 'PUT'],
    'mongo_indexes': {'person_id': ([('Id', 1)], {'background': True}),
                      'Melwin': ([('MelwinId', 1)], {'background': True}),
                      '_merged_to': ([('_merged_to', 1)], {'background': True}),
                      },
    'schema': _schema
}

agg_count_activities = {
    'url': 'ka/members/activities',
    'item_title': 'Members activities aggregation',
    'pagination': False,
    'datasource': {
        'source': RESOURCE_COLLECTION,
        'aggregation': {
            'pipeline': [
                {"$unwind": {"path": "$activities"}},
                {"$match": {"activities.OrgTypeId": 14}},
                {"$group": {"_id": "$activities.PathName", "count": {"$sum": 1}}},
                {"$sort": SON([("count", -1), ("_id", -1)])}
            ]
        }
    }
}

agg_count_member_activities = {
    'url': 'ka/members/activities/member',
    'item_title': 'Member activities aggregation',
    'pagination': False,
    'datasource': {
        'source': RESOURCE_COLLECTION,
        'aggregation': {
            'pipeline': [
                {"$unwind": {"path": "$activities"}},
                {"$match": {"Id": "$person_id", "activities.OrgTypeId": 14}},
                {"$group": {"_id": "$activities.PathName", "count": {"$sum": 1}}},
                {"$sort": SON([("count", -1), ("_id", -1)])}
            ]
        }
    }
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
