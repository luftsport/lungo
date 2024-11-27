"""
    Token based Auth
    ================
    
    Also ACL added!!
    
    @attention: Needs tokenmaster to issue tokens
"""

# Atuhentication
from eve.auth import TokenAuth
from flask import current_app as app, request, Response, abort, g

# Not in github
from ext.auth.clients import users
import string


# from eve.methods.get import getitem as get_internal
# from bson.objectid import ObjectId

class NlfTokenAuth(TokenAuth):
    is_auth = False
    user_id = None
    resource_lookup = None

    def check_auth(self, token, allowed_roles, resource, method):
        """Simple token check. Tokens comes in the form of request.authorization['username']
        Token is decoded request.authorization['username']
        """
        if resource is None:
            resource = ''

        # if this is not a collection /
        if '_' not in resource and resource[-1:] != '/':

            if resource + '/' in users[token]['resources']:
                resource = resource + '/'

            elif resource not in users[token]['resources'] and resource + '/' not in users[token]['resources']:
                # Remove last part of
                if '/'.join(resource.split('/')[:-1])+'/*' in users[token]['resources']:
                    resource = '/'.join(resource.split('/')[:-1])+'/*'

        try:
            if token in users.keys() and method in users[token]['resources'][resource]['methods']:

                self.resource_lookup = users[token]['resources'][resource]['lookup']
                self.user_id = users[token]['id']

                # globals
                g.client_id = self.user_id
                # X-on-behalf-of => person_id
                try:
                    g.whitelist_secret_contact = users[token].get('whitelist_secret_contact', {})
                except:
                    g.whitelist_secret_contact = {}

                return True
        except:  # Keyerror
            pass

        """
        for app in apps:

            if token == app['token']:
                current_app = app
                return True
        """

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
        # resp = Response(None, 401)
        abort(401)  # , description='Please provide proper credentials', response=resp)
