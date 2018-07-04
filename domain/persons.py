_schema = {

    'active_clubs': {'type': 'list'},
    'active_functions': {'type': 'list'},
    'address': {'type': 'dict', 'schema':
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
            'zip_code': {'type': 'string'}
        }
                },
    'nationality_id': {'type': 'integer'},
    'birth_date': {'type': 'datetime'},
    'clubs': {'type': 'list'},
    'created_date': {'type': 'datetime'},
    'first_name': {'type': 'string'},
    'full_name': {'type': 'string'},
    'function_applications': {'type': 'list'},
    'functions': {'type': 'list'},
    'gender': {'type': 'string', 'allowed': ["M", "F", "A", "U"]},
    'id': {'type': 'integer', 'unique': True},
    'last_changed_date': {'type': 'datetime'},
    'last_name': {'type': 'string'},
    'passive_functions': {'type': 'list'},
    'qualifications': {'type': 'list'},
    'licenses': {'type': 'list'},
    'competences': {'type': 'list'},
    'settings': {'type': 'dict', 'schema':
        {'approve_marketing': {'type': 'boolean'},
         'approve_publishing': {'type': 'boolean'},
         'automatic_data_cleansing_reservation': {'type': 'boolean'},
         'is_person_info_locked': {'type': 'boolean'},
         'is_validated': {'type': 'boolean'},
         'restricted_address': {'type': 'boolean'}
         }
                 },
    'sport_no': {'type': 'string'},
    'user_id': {'type': 'integer'}
}

definition = {
    'item_title': 'persons',
    'datasource': {'source': 'persons',
                   },
    'additional_lookup': {
        'url': 'regex("[\d{1,9}]+")',
        'field': 'id',
    },
    'extra_response_fields': ['id'],
    'versioning': True,
    'resource_methods': ['GET', 'POST', 'DELETE'],
    'item_methods': ['GET', 'PATCH', 'PUT'],

    'schema': _schema
}
