"""

    Base schemas
    ============
    
    Reusable schemas for resource definitions

"""

acl_role_schema = {
    'type': 'dict',
    'schema': {
        'activity': {'type': 'integer'},
        'org': {'type': 'integer'},
        'role': {'type': 'integer'}
    }
}

acl_type_schema = {
    'type': 'dict',
    'schema': {
        'users': {
            'type': 'list',
            'schema': {'type': 'integer'}  # Already fixed
        },
        'roles': {
            'type': 'list',
            'schema': acl_role_schema  # Reference acl_role_schema directly
        }
    }
}

acl_item_schema = {
    'type': 'dict',
    'readonly': True,
    'schema': {
        'read': acl_type_schema,
        'write': acl_type_schema,
        'execute': acl_type_schema,
        'delete': acl_type_schema
    }
}

labels_schema = {
    'type': 'list',
    'default': []
}

geo_schema = {
    'geo': {'type': 'point'},
    'geo_class': {'type': 'string'},
    'geo_importance': {'type': 'float'},
    'geo_place_id': {'type': 'integer'},
    'geo_type': {'type': 'string'}
}

location_schema = {
    'type': 'dict',
    'schema': {
        'street': {'type': 'string'},
        'zip': {'type': 'string'},
        'city': {'type': 'string'},
        'country': {'type': 'string'}
    }
}

location_geo_schema = {
    'type': 'dict',
    'schema': {
        'street': {'type': 'string'},
        'zip': {'type': 'string'},
        'city': {'type': 'string'},
        'country': {'type': 'string'},
        'geo': {'type': 'point'},
        'geo_class': {'type': 'string'},
        'geo_importance': {'type': 'float'},
        'geo_place_id': {'type': 'integer'},
        'geo_type': {'type': 'string'}
    }
}
