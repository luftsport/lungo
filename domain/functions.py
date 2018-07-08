_schema = {

    'active_in_org_id': {'type': 'integer'},
    'active_in_org_name': {'type': 'string'},
    'contact_id': {'type': 'integer'},
    'contact_information_id': {'type': 'integer'},
    'fa_function_id': {'type': 'integer'},
    'first_name': {'type': 'string'},
    'from_date': {'type': 'datetime'},
    'function_id': {'type': 'integer', 'unique': True, 'required': True},
    'function_type_id': {'type': 'integer'},
    'function_type_is_license': {'type': 'boolean'},
    'function_type_name': {'type': 'string'},
    'function_type_publish': {'type': 'boolean'},
    'has_paid_membership': {'type': 'boolean'},
    'is_deleted': {'type': 'boolean'},
    'is_passive': {'type': 'boolean'},
    'last_name': {'type': 'string'},
    'person_id': {'type': 'integer'},
    'role_level_id': {'type': 'integer'},
    'to_date': {'type': 'datetime'},
    'update_permission': {'type': 'boolean'},
}

definition = {
    'item_title': 'functions',
    'datasource': {'source': 'functions',
                   },
    'additional_lookup': {
        'url': 'regex("[\d{1,9}]+")',
        'field': 'id',
    },
    'extra_response_fields': ['id'],
    'versioning': False,
    'resource_methods': ['GET', 'POST', 'DELTE'],
    'item_methods': ['GET', 'PATCH', 'PUT'],

    'schema': _schema
}
