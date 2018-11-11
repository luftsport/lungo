from datetime import datetime

# time,m_benk,m_driv_bottom,m_driv_top,p,p0,rh,t,t_bottom,t_top,t_internal,fan
_schema = {
    'station_id': {'type': 'objectid',
                   'data_relation': {
                       'resource': 'stations',
                       'field': '_id',
                       'embeddable': True,

                   },
                   'required': True,
                   },
    'time': {'type': 'datetime'},
    't': {'type': 'float'},
    'p': {'type': 'float'},
    'p0': {'type': 'float'},
    'rh': {'type': 'float'},
    't_top': {'type': 'float'},
    't_bottom': {'type': 'float'},
    't_internal': {'type': 'float'},
    'm_bench': {'type': 'float'},
    'm_top': {'type': 'float'},
    'm_bottom': {'type': 'float'},
    'fan': {'type': 'boolean'}
}

definition = {
    'url': 'values',
    'item_title': 'values',
    'datasource': {'source': 'values',
                   },

    # 'additional_lookup': {
    #    'url': 'objectid',
    #    'field': 'station_id',
    # },
    # 'extra_response_fields': ['station_id'],

    'versioning': False,
    'resource_methods': ['GET', 'POST'],
    'item_methods': ['GET'],

    'schema': _schema
}
