_schema = {

    'account': {'type': 'dict',
                # 'schema': {'AccountId': {'type': 'integer'},
                #           'AccountNo': {'type': 'integer'}}
                },
    # 'ActiveLabel': {'type': 'string'},
    # 'CancellationDate': None,
    # 'CancellationTypeId': None,
    'comment': {'type': 'string', 'default': ''},
    'contact': {'type': 'dict', 'default': {}},
    # 'ContactId': {'type': 'integer'},
    'created': {'type': 'datetime'},
    'describing_name': {'type': 'string', 'default': ''},
    'is_active': {'type': 'boolean'},
    'local_council_id': {'type': 'integer'},
    'local_council_name': {'type': 'string', 'default': ''},
    'modified': {'type': 'datetime'},
    'nif_organization_number': {'type': 'string', 'default': ''},
    'name': {'type': 'string', 'default': ''},
    'id': {'type': 'integer', 'unique': True},
    '_up': {'type': 'list',
            'schema': {'type': 'dict',
                       'schema': {'id': {'type': 'integer'},
                                  'type': {'type': 'integer',
                                           'data_relation': {'resource': 'organizations/types',
                                                             'field': 'org_type_id',
                                                             'embeddable': True,
                                                             'validate': False
                                                             }}}}
            },
    '_down': {'type': 'list',
              'schema': {'type': 'dict',
                         'schema': {'id': {'type': 'integer'},
                                    'type': {'type': 'integer',
                                             'data_relation': {'resource': 'organizations/types',
                                                               'field': 'org_type_id',
                                                               'embeddable': True,
                                                               'validate': False
                                                               }}}}
              },
    # 'data_relation': {
    #    'resource': 'users',
    #    'field': '_id',
    #    'embeddable': True
    # },

    'type_id': {'type': 'integer'},
    'parent_id': {'type': 'integer'},
    'authority_id': {'type': 'string'},
    'short_name': {'type': 'string'},
    'activities': {'type': 'list', 'schema': {'type': 'dict', 'schema': {
        'code': {'type': 'string'},
        'id': {'type': 'integer'},
        'name': {'type': 'string'}

    }}},
    'main_activity': {'type': 'dict',
                      'schema': {'code': {'type': 'string'},
                                 'id': {'type': 'integer'},
                                 'name': {'type': 'string'}
                                 },
                      }
}

definition = {
    'item_title': 'organizations',
    'datasource': {'source': 'organizations',
                   },
    'additional_lookup': {
        'url': 'regex("[\d{1,9}]+")',
        'field': 'id',
    },
    'extra_response_fields': ['id'],
    'versioning': False,
    'resource_methods': ['GET', 'POST', 'DELETE'],
    'item_methods': ['GET', 'PATCH', 'PUT'],
    'mongo_indexes': {'org_id': ([('id', 1)], {'background': True}),
                      'type_id': ([('type_id', 1)], {'background': True}),
                      'activities': ([('activities', 1)], {'background': True}),
                      'main_activity': ([('main_activity', 1)], {'background': True}),
                      '_up': ([('_up', 1)], {'background': True}),
                      '_down': ([('_down', 1)], {'background': True}),
                      'name': ([('name', 'text')], {'background': True})
                      },
    'schema': _schema
}

# Aggregation
from bson import SON, ObjectId

agg_count_types = {
    'datasource': {
        'source': 'organizations',
        'aggregation': {
            'pipeline': [
                {"$group": {"_id": "$type_id", "count": {"$sum": 1}}},
                {"$sort": SON([("count", -1), ("_id", -1)])}
            ]
        }
    }
}

parents = {
    'item_title': 'Content Parents Aggregation',
    'datasource': {
        'source': 'organizations',
        'aggregation': {

            'pipeline': [
                {
                    "$match": {
                        "id": "$start_id",
                        "parent": {
                            "$ne": None
                        }
                    }
                },
                {
                    "$project": {
                        "id": 1,
                        "name": 1,
                        "_up": 1,
                        "_down": 1,
                    }
                },
                {
                    "$graphLookup": {
                        "from": "organizations",
                        "startWith": "$_up",
                        "connectFromField": "parent",
                        "connectToField": "_id",
                        "maxDepth": 3,
                        "depthField": "levelAbove",
                        "as": "parents"
                    }
                },
                {
                    "$project": {
                        "parents._id": 1,
                        "parents.title": 1,
                        "parents.slug": 1,
                        "parents.space_key": 1,
                        "parents.levelAbove": 1
                    }
                },
                {
                    "$sort": SON([("parents.levelAbove", -1)])
                },
            ]

        }
    }
}

children = {
    'item_title': 'Content Parents Aggregation',
    'datasource': {
        'source': 'content',
        'aggregation': {

            'pipeline':

                [
                    {
                        "$match": {
                            "_id": "$start_id",
                        }
                    },
                    {
                        "$project": {
                            "_id": 1,
                            "title": 1,
                            "slug": 1,
                            "space_key": 1
                        }
                    },
                    {
                        "$graphLookup": {
                            "from": "content",
                            "startWith": "$_id",
                            "connectFromField": "_id",
                            "connectToField": "parent",
                            "maxDepth": "$max_depth",
                            "depthField": "levelBelove",
                            "as": "children"
                        }
                    },
                    {
                        "$project": {
                            "children._id": 1,
                            "children.title": 1,
                            "children.slug": 1,
                            "children.space_key": 1,
                            "children.levelBelove": 1
                        }
                    },
                    {
                        "$sort": {
                            "children.leveBelove": 1
                        }
                    }
                ]
        }
    }
}

siblings = {
    'item_title': 'Content Parents Aggregation',
    'datasource': {
        'source': 'content',
        'aggregation': {

            'pipeline':

                [
                    {
                        "$match": {
                            "_id": "$parent_id",
                        }
                    },
                    {
                        "$project": {
                            "_id": 1,
                            "title": 1,
                            "slug": 1,
                            "space_key": 1
                        }
                    },
                    {
                        "$graphLookup": {
                            "from": "content",
                            "startWith": "$_id",
                            "connectFromField": "_id",
                            "connectToField": "parent",
                            "maxDepth": 0,
                            "depthField": "levelBelove",
                            "restrictSearchWithMatch": {"_id": {"$ne": "$current_id"}},
                            "as": "siblings"
                        }
                    },
                    {
                        "$project": {
                            "siblings._id": 1,
                            "siblings.title": 1,
                            "siblings.slug": 1,
                            "siblings.space_key": 1,
                            "siblings.levelBelove": 1
                        }
                    },
                    {
                        "$sort": {
                            "siblings.leveBelove": 1
                        }
                    }
                ]
        }
    }
}
