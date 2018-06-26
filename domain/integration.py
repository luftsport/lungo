_schema = {
    '_auth': {
        'type': 'dict',
        'schema': {
            'username': {'type': 'string'},
            'password': {'type': 'string'},
            'club': {'type': 'integer'}
        }
    },
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
}

definition = {
    'item_title': 'integration',
    'datasource': {'source': 'integration',
                   },
    'additional_lookup': {
        'url': 'regex("[\d{1,20}]+")',
        'field': '_auth.id',
    },
    'extra_response_fields': ['_auth.id'],
    'versioning': False,
    'resource_methods': ['GET', 'POST'],
    'item_methods': ['GET', 'PATCH', 'PUT'],

    'schema': _schema
}
