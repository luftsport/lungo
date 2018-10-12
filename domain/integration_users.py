"""
    '_auth': {
        'type': 'dict',
        'schema': {
            '_auth_username': {'type': 'string'},
            '_auth_password': {'type': 'string'},
            '_auth_club': {'type': 'integer'}
        }
    },
    '_auth_username': {'type': 'string'},
    '_auth_password': {'type': 'string'},
    '_auth_club': {'type': 'integer'},
    'ActiveClubs': {'type': 'list'},
    'ActiveFunctions': {'type': 'list'},
    'Clubs': {'type': 'list'},
    'ExtraAddresses': {'type': 'list'},
    'Functions': {'type': 'list'},
    'HomeAddress': {'type': 'dict'},
    'MyProfileSettings': {'type': 'dict'},
    'Id': {'type': 'integer', 'required': True},
    'IsPersonInfoLocked': {'type': 'boolean'},
    'LastChangedDate': {'type': 'datetime'},
    'LastName': {'type': 'string'},
    'Nationality': {'type': 'integer'},
    'PersonGender': {'type': 'string'},
    'PersonId': {'type': 'integer'},
    'RestrictedAddress': {'type': 'boolean'},
    'SportNo': {'type': 'string'},
    'UserId': {'type': 'integer'},
    'Username': {'type': 'string'},
    'FirstName': {'type': 'string'},
    'FullName': {'type': 'string'},
    'ApproveMarketing': {'type': 'boolean'},
    'ApprovePublishing': {'type': 'boolean'},
    'AutomaticDataCleansingReservation': {'type': 'boolean'},
    'BirthDate': {'type': 'datetime'},
    """
"""
_schema = {

    'active_clubs': {'type': 'list'},
    'active_functions': {'type': 'list'},
    'functions': {'type': 'list'},
    'clubs': {'type': 'list'},
    'club_id': {'type': 'integer', 'required': True, 'unique': True},
    'club_created': {'type': 'datetime'},
    'id': {'type': 'integer', 'required': True},
    'first_name': {'type': 'string'},
    'full_name': {'type': 'string'},
    'login': {'type': 'string'},
    'password': {'type': 'string'},
    'person_id': {'type': 'integer'},
    'user_id': {'type': 'integer'},
    'username': {'type': 'string'},
    'modified': {'type': 'datetime'}
    
}
"""
_schema = {'username': {'type': 'string', 'required': True},
           'password': {'type': 'string', 'required': True},
           'id': {'type': 'integer', 'required': True, 'unique': True},
           'app_id': {'type': 'integer', 'required': True},
           'function_id': {'type': 'integer', 'required': True},
           'club_id': {'type': 'integer', 'required': True, 'unique': True},
           'club_name': {'type': 'string'},
           'club_created': {'type': 'datetime', 'required': True},
           'modified': {'type': 'datetime'}
           }

definition = {
    'item_title': 'integration',
    'datasource': {'source': 'integration', # @TODO - move to integration_users
                   },
    'additional_lookup': {
        'url': 'regex("[\d{1,20}]+")',
        'field': 'club_id',
        #'field': 'id',
    },
    'extra_response_fields': ['club_id'],
    'versioning': False,
    'resource_methods': ['GET', 'POST'],
    'item_methods': ['GET', 'PATCH', 'PUT', 'DELETE'],
    #'mongo_indexes':
    'schema': _schema
}
