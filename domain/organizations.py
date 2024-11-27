RESOURCE_COLLECTION = 'organizations'

_schema = {

    'account': {'type': 'dict',
                # 'schema': {'AccountId': {'type': 'integer'},
                #           'AccountNo': {'type': 'integer'}}
                },
    # 'ActiveLabel': {'type': 'string'},
    # 'CancellationDate': None,
    # 'CancellationTypeId': None,
    'comment': {'type': 'string', 'default': ''},
    'contact': {'type': 'dict',
                'default': {},
                'schema':
                    {
                        'city': {'type': 'string'},
                        'contact_id': {'type': 'integer'},
                        'contact_information_id': {'type': 'integer'},
                        'country_id': {'type': 'integer'},
                        'email': {'type': 'string'},  # Only difference with persons
                        'fax': {'type': 'string'},
                        'phone_home': {'type': 'string'},
                        'phone_mobile': {'type': 'string'},
                        'phone_work': {'type': 'string'},
                        'secret_address': {'type': 'boolean'},
                        'secret_email': {'type': 'boolean'},
                        'secret_phone_home': {'type': 'boolean'},
                        'secret_phone_mobile': {'type': 'boolean'},
                        'secret_phone_work': {'type': 'boolean'},
                        'street_address': {'type': 'string'},
                        'street_address2': {'type': 'string'},
                        'zip_code': {'type': 'string'},
                        'home_page': {'type': 'string'},
                        'location': {'type': 'dict',
                                     'schema': {'geo': {'type': 'point'},
                                                'score': {'type': 'integer'},
                                                'confidence': {'type': 'integer'},
                                                'quality': {'type': 'string'}
                                                }
                                     },
                    }
                },
    # 'ContactId': {'type': 'integer'},
    'created': {'type': 'datetime'},
    'is_active': {'type': 'boolean'},
    'end_date': {'type': 'datetime'},
    'end_type_id': {'type': 'integer'},
    'describing_name': {'type': 'string', 'default': ''},

    'local_council_id': {'type': 'integer'},
    'local_council_name': {'type': 'string', 'default': ''},
    'modified': {'type': 'datetime'},
    'nif_organization_number': {'type': 'string', 'default': ''},
    'name': {'type': 'string', 'default': ''},
    'id': {'type': 'integer', 'unique': True, 'required': True},
    '_up': {'type': 'list',
            'schema': {'type': 'dict',
                       'schema': {'id': {'type': 'integer'},
                                  'type': {'type': 'integer',
                                           'data_relation': {'resource': 'organizations/types',
                                                             'field': 'org_type_id',
                                                             'embeddable': True,
                                                             }
                                           }
                                  }
                       }
            },
    '_down': {'type': 'list',
              'schema': {'type': 'dict',
                         'schema': {'id': {'type': 'integer'},
                                    'type': {'type': 'integer',
                                             'data_relation': {'resource': 'organizations/types',
                                                               'field': 'org_type_id',
                                                               'embeddable': True,
                                                               }
                                             }
                                    }
                         }
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
    'activities': {'type': 'list',
                   'schema': {
                       'type': 'dict',
                       'schema': {
                           'code': {'type': 'string'},
                           'id': {'type': 'integer'},
                           'name': {'type': 'string'}
                       }
                   }
                   },
    'main_activity': {'type': 'dict',
                      'schema': {'code': {'type': 'string'},
                                 'id': {'type': 'integer'},
                                 'name': {'type': 'string'}
                                 },
                      },
    'logo': {'type': 'media'},
}

definition = {
    'url': 'organizations',
    'item_title': 'organizations',
    'datasource': {'source': RESOURCE_COLLECTION,
                   'projection': {'logo': 0}
                   },
    'additional_lookup': {
        'url': 'regex("[\d{1,9}]+")',
        'field': 'id',
    },
    'extra_response_fields': ['id'],
    'versioning': False,
    'resource_methods': ['GET'],
    'item_methods': ['GET'],
    'mongo_indexes': {'org_id': ([('id', 1)], {'background': True}),
                      'type_id': ([('type_id', 1)], {'background': True}),
                      'activities': ([('activities', 1)], {'background': True}),
                      'main_activity': ([('main_activity', 1)], {'background': True}),
                      'KL Number': ([('nif_organization_number', 1)], {'background': True}),
                      '_up': ([('_up', 1)], {'background': True}),
                      '_down': ([('_down', 1)], {'background': True}),
                      'name': ([('name', 'text'),('describing_name', 'text')], {'background': True}),
                      'location': ([('contact.location.geo', '2dsphere')], {'background': True}),
                      },
    'schema': _schema
}



# Process resource without data_relations
_schema_process = _schema.copy()
_schema_process['_up'] = {'type': 'list',
                          'schema': {'type': 'dict',
                                     'schema': {'id': {'type': 'integer'},
                                                'type': {'type': 'integer'}
                                                }
                                     }
                          }
_schema_process['_down'] = {'type': 'list',
                            'schema': {'type': 'dict',
                                       'schema': {'id': {'type': 'integer'},
                                                  'type': {'type': 'integer'}
                                                  }
                                       }
                            }

process_definition = {
    'url': 'organizations/process',
    'item_title': 'Organizations Process',
    'datasource': {'source': RESOURCE_COLLECTION,
                   'projection': {'logo': 0}
                   },
    'additional_lookup': {
        'url': 'regex("[\d{1,9}]+")',
        'field': 'id',
    },
    'pagination': False,
    'extra_response_fields': ['id'],
    'versioning': False,
    'resource_methods': ['GET', 'POST', 'DELETE'],
    'item_methods': ['GET', 'PATCH', 'PUT'],
    'schema': _schema_process
}

# Search
search_definition = {
    'url': 'organizations/search',
    'item_title': 'Organizations Search',
    'datasource': {'source': RESOURCE_COLLECTION,
                   'projection': {
                       "_score": {"$meta": "textScore"},
                       "name": 1,
                       "id": 1,
                       "_updated": 1,
                       "_created": 1,
                       "_version": 1
                   },
                   'default_sort': [("_score", {"$meta": "textScore"})],
                   #'filter': {'org_id_owner': 376, 'is_valid':True}
                   },
    'additional_lookup': {
        'url': 'regex("[\d{1,9}]+")',
        'field': 'id',
    },
    'extra_response_fields': ['id'],
    'resource_methods': ['GET'],
    'item_methods': [],
    'schema': _schema
}


# Aggregation
from bson import SON, ObjectId

# Orgs by activity
agg_get_org_by_activity_and_org_types = {

    'url': '{}/activity'.format(RESOURCE_COLLECTION),
    'item_title': 'Organizations by activity and type_ids',
    'pagination': False,
    'datasource': {
        'source': RESOURCE_COLLECTION,
        'aggregation': {
            'pipeline':
                [
                    {
                        "$match": {
                            "activities.id": "$activity",  # activity - integer
                            "type_id": {"$in": "$type_ids"}  # type_ids - [integer,..]
                        }
                    },
                    {
                        "$group": {
                            "_id": "$activity",
                            "org_ids": {
                                "$addToSet": "$id"
                            }
                        }
                    }
                ]
        }
    }
}

# ?aggregate={"$org_id": 999999}
agg_get_children = {
    'url': '{}/children'.format(RESOURCE_COLLECTION),
    'item_title': 'Organizations children 3 levels down',
    'pagination': False,
    'datasource': {
        'source': RESOURCE_COLLECTION,
        'aggregation': {
            'pipeline':
                [{"$match": {"id": "$org_id"}},
                 {"$graphLookup": {
                     "from": RESOURCE_COLLECTION,
                     "startWith": "$_down.id",
                     "connectFromField": "_down.id",
                     "connectToField": "id",
                     "as": "children",
                     "maxDepth": 3,
                     "depthField": "depth"
                 }
                 }
                 ]
        }
    }
}

agg_get_parents = {
    'url': '{}/parents'.format(RESOURCE_COLLECTION),
    'item_title': 'Organizations parents 3 levels up',
    'pagination': False,
    'datasource': {
        'source': RESOURCE_COLLECTION,
        'aggregation': {
            'pipeline':
                [{"$match": {"id": "$org_id"}},
                 {"$graphLookup": {
                     "from": RESOURCE_COLLECTION,
                     "startWith": "$_up.id",
                     "connectFromField": "_up.id",
                     "connectToField": "id",
                     "as": "parents",
                     "maxDepth": 3,
                     "depthField": "depth"
                 }
                 }
                 ]
        }
    }
}

agg_count_types = {
    'url': 'organizations/types/count',
    'item_title': 'Organiuzations Types Count',
    'pagination': False,
    'datasource': {
        'source': RESOURCE_COLLECTION,
        'aggregation': {
            'pipeline': [
                {"$group": {"_id": "$type_id", "count": {"$sum": 1}}},
                {"$sort": SON([("count", -1), ("_id", -1)])}
            ]
        }
    }
}

agg_parents = {
    'item_title': 'Content Parents Aggregation',
    'pagination': False,
    'datasource': {
        'source': RESOURCE_COLLECTION,
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

agg_children = {
    'item_title': 'Content Parents Aggregation',
    'pagination': False,
    'datasource': {
        'source': RESOURCE_COLLECTION,
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

agg_siblings = {
    'item_title': 'Content Parents Aggregation',
    'pagination': False,
    'datasource': {
        'source': RESOURCE_COLLECTION,
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
