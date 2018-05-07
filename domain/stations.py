from datetime import datetime

# time,m_benk,m_driv_bottom,m_driv_top,p,p0,rh,t,t_bottom,t_top,t_internal,fan
_schema = {
    'time': {'type': 'datetime'},
    'name': {'type': 'string'},
    'location': {'type': 'point'},
    'description': {'type': 'string'},
    'active': {'type': 'boolean'},
}

definition = {
    'item_title': 'stations',
    'datasource': {'source': 'stations',
                   },

    'versioning': False,
    'resource_methods': ['GET', 'POST'],
    'item_methods': ['GET', 'PATCH'],

    'schema': _schema
}

