from bson import SON
import datetime

RESOURCE_COLLECTION = 'persons'

_schema = {

    'id': {'type': 'integer', 'unique': True},
    'sport_no': {'type': 'string'},
    'user_id': {'type': 'integer'},
    '_merged_to': {'type': 'integer'},
    'created_date': {'type': 'datetime'},
    'last_changed_date': {'type': 'datetime'},
    'first_name': {'type': 'string'},
    'last_name': {'type': 'string'},
    'full_name': {'type': 'string'},
    'gender': {'type': 'string', 'allowed': ['M', 'F', 'A', 'U']},
    'file_upload_id': {'type': 'integer'},
    'birth_date': {'type': 'datetime'},
    'date_of_death': {'type': 'datetime'},
    'nationality_id': {'type': 'integer'},
    'primary_email': {'type': 'string'},
    'clubs': {'type': 'list',
              'schema': {
                  'type': 'integer',
                  'data_relation': {
                      'resource': 'organizations',
                      'field': 'id',
                      'embeddable': True,
                  }
              },
              },
    'memberships': {'type': 'list',
                    'default': [],
                    'schema': {
                        'type': 'dict',
                        'schema': {
                            'id': {
                                'type': 'integer',
                                'data_relation': {
                                    'resource': 'functions',
                                    'field': 'id',
                                    'embeddable': True,
                                }
                            },
                            'club': {
                                'type': 'integer',
                                'data_relation': {
                                    'resource': 'organizations',
                                    'field': 'id',
                                    'embeddable': True,
                                }
                            },
                            'discipline': {
                                'type': 'integer',
                                'data_relation': {
                                    'resource': 'organizations',
                                    'field': 'id',
                                    'embeddable': True,
                                }
                            },
                            'activity': {
                                'type': 'integer',
                                'data_relation': {
                                    'resource': 'activities',
                                    'field': 'id',
                                    'embeddable': True,
                                }
                            },
                            'from_date': {'type': 'datetime'},
                            'payment': {
                                'type': 'dict',
                                'schema': {
                                    'id': {'type': 'integer', 'required': True},
                                    'year': {'type': 'integer'},
                                    'exception': {'type': 'string', 'nullable': True},
                                    'type': {'type': 'string'},
                                    'amount': {'type': 'float'},
                                    'paid': {'type': 'datetime'}
                                }
                            }
                        }
                    }

                    },
    'federation': {'type': 'list'},
    'magazines': {'type': 'list'},
    'functions': {'type': 'list',
                  'schema': {
                      'type': 'integer',
                      'data_relation': {
                          'resource': 'functions',
                          'field': 'id',
                          'embeddable': True,

                      }
                  }
                  },
    # 'qualifications': {'type': 'list'},
    'activities': {'type': 'list',
                   'schema': {
                       'type': 'integer',
                       'data_relation': {
                           'resource': 'activities',
                           'field': 'id',
                           'embeddable': True,
                       }
                   },
                   },
    'licenses': {'type': 'list',
                 'schema': {
                     'type': 'dict',
                     'schema': {
                         'id': {'type': 'integer',
                                'data_relation': {
                                    'resource': 'licenses',
                                    'field': 'id',
                                    'embeddable': True,
                                }
                                },
                         'status_id': {'type': 'integer'},
                         'status_date': {'type': 'datetime'},
                         'expiry': {'type': 'datetime'},
                         'type_id': {'type': 'integer'},
                         'type_name': {'type': 'string'},
                     }}

                 },
    'competences': {
        'type': 'list',
        'schema': {'type': 'dict',
                   'schema': {
                       'id': {'type': 'integer',
                              'data_relation': {
                                  'resource': 'competences',
                                  'field': 'id',
                                  'embeddable': True,
                              }
                              },
                       '_code': {'type': 'integer'},
                       'issuer': {'type': 'integer'},
                       'expiry': {'type': 'datetime'},
                       'paid': {'type': 'datetime'},
                   }}
    },
    'address': {
        'type': 'dict',
        'schema':
            {
                'city': {'type': 'string'},
                'contact_id': {'type': 'integer'},
                'contact_information_id': {'type': 'integer'},
                'country_id': {'type': 'integer'},
                'email': {'type': 'list'},
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

    'settings': {
        'type': 'dict',
        'schema':
            {'approve_marketing': {'type': 'boolean'},
             'approve_publishing': {'type': 'boolean'},
             'automatic_data_cleansing_reservation': {'type': 'boolean'},
             'is_person_info_locked': {'type': 'boolean'},
             'is_validated': {'type': 'boolean'},
             'restricted_address': {'type': 'boolean'}
             }
    },

}

definition = {
    'url': 'persons',
    'item_title': 'Persons',
    'datasource': {'source': RESOURCE_COLLECTION,
                   },
    'additional_lookup': {
        'url': 'regex("[\d{1,9}]+")',
        'field': 'id',
    },
    'projection': False,  # To avoid omitting the _merged_to field
    'extra_response_fields': ['id'],
    'versioning': True,
    'resource_methods': ['GET'],
    'item_methods': ['GET'],
    'mongo_indexes': {'person_id': ([('id', 1)], {'background': True}),
                      # , 'unique': True gives DuplicateKeyError with versioning
                      # 'primary_email': ([('primary_email', 'text')], {'background': True}),
                      'primary_email': ([('primary_email', 1)], {'background': True}),
                      'location': ([('address.location.geo', '2dsphere')], {'background': True}),
                      # 'clubs': ([('clubs', 1)], {'background': True}),
                      'membership': ([('memberships', 1)], {'background': True}),
                      'group': ([('memberships.group', 1)], {'background': True}),
                      'discipline': ([('memberships.discipline', 1)], {'background': True}),
                      'activity': ([('memberships.activity', 1)], {'background': True}),
                      'functions': ([('functions', 1)], {'background': True}),
                      'activities': ([('activities', 1)], {'background': True}),
                      'licenses': ([('licenses', 1)], {'background': True}),
                      'competences': ([('competences', 1)], {'background': True}),
                      'names': ([('full_name', 'text')], {'background': True})
                      },
    'schema': _schema
}

# Process resource without data_relations
_schema_process = _schema.copy()
_schema_process['clubs'] = {'type': 'list'}
_schema_process['memberships'] = {'type': 'list', 'default': [],
                                  'schema': {
                                      'club': {'type': 'integer'},
                                      'discipline': {'type': 'integer'},
                                      'activity': {'type': 'integer'}
                                  }
                                  }

_schema_process['competences'] = {'type': 'list'}
_schema_process['functions'] = {'type': 'list'}
_schema_process['licenses'] = {'type': 'list'}
_schema_process['activities'] = {'type': 'list'}
_schema_process['qualifications'] = {'type': 'list'}

process_definition = {
    'url': 'persons/process',
    'item_title': 'Persons Process',
    'datasource': {'source': RESOURCE_COLLECTION,
                   },
    'additional_lookup': {
        'url': 'regex("[\d{1,9}]+")',
        'field': 'id',
    },
    'pagination': False,
    'extra_response_fields': ['id'],
    'versioning': True,
    'resource_methods': ['GET', 'POST', 'DELETE'],
    'item_methods': ['GET', 'PATCH', 'PUT'],
    'schema': _schema_process
}

# Search
search_definition = {
    'url': 'persons/search',
    'item_title': 'Persons Search',
    'datasource': {'source': RESOURCE_COLLECTION,
                   'projection': {
                       "_score": {"$meta": "textScore"},
                       "full_name": 1,
                       "id": 1,
                       "_updated": 1,
                       "_created": 1,
                       "_version": 1
                   },
                   'default_sort': [("_score", {"$meta": "textScore"})],
                   'filter': {'_merged_to': {'$exists': False}}
                   },
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

# Aggregations
agg_count_gender = {
    'url': 'persons/gender',
    'item_title': 'Persons Gender',
    'pagination': False,
    'datasource': {
        'source': RESOURCE_COLLECTION,
        'aggregation': {
            'pipeline': [
                {'$facet': {
                    'test': [
                        {'$group': {'_id': '$gender', 'count': {'$sum': 1}}},
                        {'$sort': SON([('count', -1), ('_id', -1)])}
                    ],
                    'does': [
                        {'$group': {'_id': '$gender', 'count': {'$sum': 1}}},
                        {'$sort': SON([('count', -1), ('_id', -1)])}
                    ],
                },

                }
            ]
        }
    }
}

# Persons merged from
# http://127.0.0.1:9191/api/v1/persons/merged?aggregate={"$person_id": 7897818}


agg_merged_from = {
    'url': 'persons/merged',
    'item_title': 'Persons merged from',
    'pagination': False,
    'datasource': {
        'source': RESOURCE_COLLECTION,
        'aggregation': {
            'pipeline': [
                {
                    "$match": {
                        "id": "$person_id"
                    }
                },
                {
                    "$project": {
                        "id": 1,
                        "full_name": 1,
                        "_merged_to": 1
                    }
                },
                {
                    "$graphLookup": {
                        "from": "persons",
                        "startWith": "$person_id",
                        "connectFromField": "id",
                        "connectToField": "_merged_to",
                        "as": "merged_from",
                        "maxDepth": 100,
                        "depthField": "depth"
                    }
                },
                {
                    "$project": {
                        "_id": 1,
                        "id": 1,
                        "merged_from": {
                            "$map": {
                                "input": "$merged_from.id",
                                "as": "from_id",
                                "in": "$$from_id"
                            }
                        }
                        # "merged_from.id": 1,
                        # "merged_from._id": 1
                    }
                },
                # {"$unwind": {"$merged_from"}},
                # {"$group": {"_id": {"$push": "id"}}},
                # {"$group": {"_id": "$_id", "merged": {"$push": "$merged_from.id"}}},
                # {"$project": {"merged": 1, "merged_from": -1}}
            ]
        }
    }
}

# {"$unwind": {"merged_from"}},
#                {"$group": {"$merged_from._id": None, "merged": {"$push": "$merged_from.id"}}},
#                {"$project": {"merged": 1, "merged_from": -1}}

# Age aggregation per club
# Should be extended to accomodate multiple dimensions
# ?aggregate={"$club_id": 22976}

"""

@param $org_ids list
@param $activity_ids list off activity ids
"""
agg_age_distribution = {
    'url': 'persons/age',
    'item_title': 'Persons age aggregation',
    'pagination': False,
    'datasource': {
        'source': RESOURCE_COLLECTION,
        'aggregation': {
            'pipeline':
                [
                    {
                        "$match": {"memberships.0": {
                            "$exists": True
                        }
                        }
                    },
                    #
                    #    "$match": "$where",
                    # },
                    {
                        "$match": {

                            "birth_date": {
                                # "$gt": datetime.datetime(1900, 1, 1, 0, 0, 0)
                                "$exists": True

                            },
                            "_merged_to": {
                                "$exists": False
                            },
                            "$or": [
                                {"memberships.club": {"$in": "$org_ids"}},
                                {"memberships.discipline": {"$in": "$org_ids"}},
                                {"memberships.activity": {"$in": "$activity_ids"}}
                            ]

                            # "clubs": {
                            #    "$in": ["$org_id"]
                            # }
                        }

                    },

                    {
                        "$project": {
                            "ageInMillis": {
                                "$subtract": [datetime.datetime.utcnow(), "$birth_date"]
                            }
                        }
                    },
                    {
                        "$project": {
                            "age": {
                                "$divide": ["$ageInMillis", 31558464000]
                            }
                        }
                    },
                    {
                        "$project": {
                            "age": {
                                "$subtract": ["$age", {"$mod": ["$age", 1]}]
                            }
                        }
                    },
                    {
                        "$group": {
                            "_id": "$age",
                            "total": {"$sum": 1}
                        }
                    },
                    {
                        "$sort": {
                            "_id": -1
                        }
                    }
                ]
        }
    }
}

"""
Age distribution for genders in 5 year buckets
$bins?
"""
agg_age_gender_bucket_distribution = {
    'url': 'persons/distribution/pyramid',
    'item_title': 'Persons age and gender aggregation',
    'pagination': False,
    'datasource': {
        'source': RESOURCE_COLLECTION,
        'aggregation': {
            'pipeline':
                [
                    {
                        "$match": {
                            "_merged_to": {
                                "$exists": False
                            },
                            "memberships.0": {
                                "$exists": True
                            },
                            "$or": [
                                {"memberships.club": {"$in": "$org_ids"}},
                                {"memberships.discipline": {"$in": "$org_ids"}},
                                {"memberships.activity": {"$in": "$activity_ids"}}
                            ]
                        }
                    },
                    {
                        "$project": {
                            "date": "$birth_date",
                            "gender": "$gender",
                            "age": {
                                "$divide": [
                                    {"$subtract": [datetime.datetime.utcnow(), "$birth_date"]},
                                    31536000000
                                ]
                            }
                        }
                    },
                    {
                        "$bucket":
                            {
                                "groupBy": "$age",
                                "boundaries": "$bins",
                                # [0, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55, 60, 65, 70, 75, 80, 85, 90, 95, 100, 105],
                                "default": "other",
                                "output":
                                    {
                                        "total": {"$sum": 1},
                                        "male": {
                                            "$sum": {"$cond": {"if": {"$eq": ["$gender", "M"]}, "then": 1, "else": 0}}},
                                        "female": {
                                            "$sum": {"$cond": {"if": {"$eq": ["$gender", "F"]}, "then": 1, "else": 0}}},
                                        "other": {
                                            "$sum": {"$cond": {"if": {"$eq": ["$gender", "U"]}, "then": 1, "else": 0}}},
                                    }
                            }
                    }
                ]
        }
    }
}
