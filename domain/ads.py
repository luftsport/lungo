RESOURCE_COLLECTION = 'ads'

_schema = {
    'id': {'type': 'integer',
           'required': True,
           'unique': True},
    'location': {'type': 'dict',
                 'schema': {'geo': {'type': 'point'}}
                 },
    'altitude': {'type': 'integer'},
    'lat': {'type': 'float'},
    'lng': {'type': 'float'},
    'ground_speed': {'type': 'integer'},
    'vertical_speed': {'type': 'integer'},
    'heading': {'type': 'integer'},

    'code': {'type': 'string'},
    'callsign': {'type': 'integer'},
    'icao24': {'type': 'string'},
    'iata': {'type': 'number'},
    'icao': {'type': 'integer'},
    'flight_no': {'type': 'string'},
    'on_ground': {'type': 'string'},
    'origin_iata': {'type': 'string'},
    'dest_iata': {'type': 'string'},
    'registration': {'type': 'string'},
    'squawk': {'type': 'string'},
    'time': {'type': 'integer'},
}

definition = {
    'url': 'ads',
    'item_title': 'ADS Data',
    'datasource': {'source': RESOURCE_COLLECTION,
                   },
    'allow_unknown': True,
    #'additional_lookup': {
    #    'url': 'regex("[\d{1,9}]+")',
    #    'field': 'id',
    #},
    'extra_response_fields': ['id'],
    'versioning': False,
    'resource_methods': ['GET'],
    'item_methods': ['GET'],
    'mongo_indexes': {'registration': ([('id', 1)], {'background': True}),
                      'location': ([('location.geo', '2dsphere')], {'background': True}),
                      'text': ([('registration', 'text'), ('callsign', 'text'), ('origin_iata', 'text'), ('dest_iata', 'text')], {'background': True}),
                      },
    'schema': _schema
}

# Process resource without data_relations
_schema_process = _schema.copy()

process_definition = {
    'url': 'ads/process',
    'item_title': 'ADS Data Process',
    'datasource': {'source': RESOURCE_COLLECTION,
                   },
    'pagination': False,
    'extra_response_fields': ['id'],
    'versioning': False,
    'resource_methods': ['GET', 'POST', 'DELETE'],
    'item_methods': ['GET', 'PATCH', 'PUT'],
    'schema': _schema_process
}
