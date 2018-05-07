"""
    Token based Auth
    ================
    
    Also ACL added!!
    
    @attention: Needs tokenmaster to issue tokens
"""

# Atuhentication
from eve.auth import TokenAuth
from flask import current_app as app, request, Response, abort
# from eve.methods.get import getitem as get_internal
# from bson.objectid import ObjectId

class TokenAuth(TokenAuth):
    
    is_auth = False
    user_id = None
    
    
    def check_auth(self, token, allowed_roles, resource, method):
        """Simple token check. Tokens comes in the form of request.authorization['username']
        Token is decoded request.authorization['username']
        """

        stations = {'id': 1,
                    '_id': '5ad2330d26867a2206f135a3',
                    'name': 'hauanveien',
                    'token': '1e26730ea840499295417c74ddd2e052',
                    'client_token': 'MWUyNjczMGVhODQwNDk5Mjk1NDE3Yzc0ZGRkMmUwNTI6'
                    }

        if token == stations['token']:
            return True


        return False
    
    def get_user_id(self):
        return self.user_id
    
    def _set_globals(self, id, _id):
        app.globals.update({'id': id})
        app.globals.update({'_id': "%s" % _id})
    
    def authenticate(self):
        """ Overridden by NOT returning a WWW-Authenticate header
        This makes the browser NOT fire up the basic auth
        """
        resp = Response(None, 401)
        abort(401, description='Please provide proper credentials', response=resp)
