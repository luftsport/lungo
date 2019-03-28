from bson import SON
import datetime

RESOURCE_COLLECTION = 'test'

_schema = {

    'id': {'type': 'integer', 'unique': True},
    'name': {'type': 'string'},
    'clubs': {'type': 'list', 'default': [],
              'schema': {
                  'group': {'type': 'integer'},
                  'discipline': {'type': 'integer'},
                  'activity': {'type': 'integer'},
              }}
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
    'mongo_indexes': {'person id': ([('id', 1)], {'background': True}),
                      'clubs': ([('clubs', 1)], {'background': True}),
                      'group': ([('clubs.group', 1)], {'background': True}),
                      'discipline': ([('clubs.discipline', 1)], {'background': True}),
                      'activity': ([('clubs.activity', 1)], {'background': True}),

                      },
    'schema': _schema
}


