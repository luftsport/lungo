from bson import SON

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
    'clubs': {'type': 'list',
              'schema': {'type': 'integer',
                         'data_relation': {
                             'resource': 'organizations',
                             'field': 'id',
                             'embeddable': True,
                         }
                         },
              },
    'functions': {'type': 'list',
                  'schema': {'type': 'integer',
                             'data_relation': {
                                 'resource': 'functions',
                                 'field': 'id',
                                 'embeddable': True,

                             }
                             }
                  },
    # 'qualifications': {'type': 'list'},
    'activities': {'type': 'list'},
    'licenses': {'type': 'list'},
    'competences': {'type': 'list'},

    'address': {'type': 'dict',
                'schema':
                    {
                        'city': {'type': 'string'},
                        'contact_id': {'type': 'integer'},
                        'contact_information_id': {'type': 'integer'},
                        'country_id': {'type': 'integer'},
                        'email': {'type': 'string'},
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

    'settings': {'type': 'dict',
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
    'extra_response_fields': ['id'],
    'versioning': True,
    'resource_methods': ['GET'],
    'item_methods': ['GET'],
    'mongo_indexes': {'person id': ([('id', 1)], {'background': True}),
                      # , 'unique': True gives DuplicateKeyError with versioning
                      'location': ([('address.location.geo', '2dsphere')], {'background': True}),
                      'clubs': ([('clubs', 1)], {'background': True}),
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
                   'projection': {"_score": {"$meta": "textScore"}, "full_name": 1, "id": 1},
                   'default_sort': [("_score", {"$meta": "textScore"})]
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
    'datasource': {
        'source': RESOURCE_COLLECTION,
        'aggregation': {
            'pipeline': [
                {'$group': {'_id': '$gender', 'count': {'$sum': 1}}},
                {'$sort': SON([('count', -1), ('_id', -1)])}
            ]
        }
    }
}
