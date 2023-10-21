from bson import SON
import datetime

RESOURCE_COLLECTION = 'test'

_schema = {

    'id': {'type': 'integer', 'unique': True},
    'name': {'type': 'string'},
    'memberships': {'type': 'list', 'default': [],
                    'schema': {
                        'club': {'type': 'integer',
                                 'data_relation': {
                                     'resource': 'organizations',
                                     'field': 'id',
                                     'embeddable': True,
                                 }
                                 },
                        'discipline': {'type': 'integer',
                                       'data_relation': {
                                           'resource': 'organizations',
                                           'field': 'id',
                                           'embeddable': True,
                                       }
                                       },
                        'activity': {'type': 'integer',
                                     'data_relation': {
                                         'resource': 'activities',
                                         'field': 'id',
                                         'embeddable': True,
                                     }
                                     },
                    }

                    }
}

definition = {
    'url': 'test',
    'item_title': 'Persons test',
    'datasource': {'source': RESOURCE_COLLECTION,
                   },
    'additional_lookup': {
        'url': 'regex("[\d{1,9}]+")',
        'field': 'id',
    },
    'extra_response_fields': ['id'],
    'versioning': False,
    'resource_methods': ['GET'],
    'item_methods': ['GET'],
    'mongo_indexes': {'person_id': ([('id', 1)], {'background': True}),
                      'clubs': ([('clubs', 1)], {'background': True}),
                      'group': ([('clubs.group', 1)], {'background': True}),
                      'discipline': ([('clubs.discipline', 1)], {'background': True}),
                      'activity': ([('clubs.activity', 1)], {'background': True}),

                      },
    'schema': _schema
}
