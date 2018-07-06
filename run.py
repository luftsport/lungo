"""
    WX - Weather API
    ================

    @note: Run as `nohup python run.py >> lungo.log 2>&1&` NB in virtualenv!

    @author:        Einar Huseby
    @copyright:     (c) 2014-2018
    @license:       MIT, see LICENSE for more details. Note that Eve is BSD licensed
"""

import os, sys

from eve import Eve

# Swagger docs
from eve_swagger import swagger

from eve_healthcheck import EveHealthCheck

# Import blueprints
# from blueprints.authentication import Authenticate
# Register custom blueprints
# app.register_blueprint(Authenticate, url_prefix="%s/user" % app.globals.get('prefix'))

# Custom url mappings (for flask)
from ext.app.url_maps import ObjectIDConverter, RegexConverter

# Custom auth extensions
from ext.auth.tokenauth import TokenAuth

# Make sure we are in virtualenv
if not hasattr(sys, 'real_prefix'):
    print("Outside virtualenv, aborting....")
    sys.exit(-1)

# Make sure gunicorn passes settings.py
SETTINGS_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'settings.py')

# Start Eve (and flask)
# Instantiate with custom auth
# app = CustomEve(auth=TokenAuth, settings=SETTINGS_PATH)
# app = Eve(settings=SETTINGS_PATH)
app = Eve(auth=TokenAuth, settings=SETTINGS_PATH)
#app = Eve(settings=SETTINGS_PATH)

# Healthcheck
hc = EveHealthCheck(app, '/healthcheck')

""" Define global settings
These settings are mirrored from Eve, but should not be!
@todo: use app.config instead
"""
app.globals = {"prefix": "/api/v1"}

# Custom url mapping (needed by native flask routes)
app.url_map.converters['objectid'] = ObjectIDConverter
app.url_map.converters['regex'] = RegexConverter

# Register eve-docs blueprint
# app.register_blueprint(eve_docs,        url_prefix="%s/docs" % app.globals.get('prefix'))
app.register_blueprint(swagger)
# You might want to simply update the eve settings module instead.
import json
from flask import redirect, abort, Response

"""
__subclasshook__', '__weakref__', '_ensure_sequence', '_get_mimetype_params', '_on_close', '_status', '_status_code'
, 'accept_ranges', 'add_etag', 'age', 'allow', 'autocorrect_location_header', 'automatically_set_content_length', 'c
ache_control', 'calculate_content_length', 'call_on_close', 'charset', 'close', 'content_encoding', 'content_languag
e', 'content_length', 'content_location', 'content_md5', 'content_range', 'content_type', 'data', 'date', 'default_m
imetype', 'default_status', 'delete_cookie', 'direct_passthrough', 'expires', 'force_type', 'freeze', 'from_app', 'g
et_app_iter', 'get_data', 'get_etag', 'get_wsgi_headers', 'get_wsgi_response', 'headers', 'implicit_sequence_convers
ion', 'is_sequence', 'is_streamed', 'iter_encoded', 'last_modified', 'location', 'make_conditional', 'make_sequence'
, 'mimetype', 'mimetype_params', 'response', 'retry_after', 'set_cookie', 'set_data', 'set_etag', 'status', 'status_
code', 'stream', 'vary', 'www_authenticate']
"""
def after_get_persons(request, response):
    d = json.loads(response.get_data().decode('UTF-8'))

    #print(dir(response))
    if '_items' not in d and '_merged_to' in d:
        #redirect('/persons/%s' % d['_merged_to'], code=302)
        #abort(code=401, description='Permanently moved', response=redirect('/persons/%s' % d['_merged_to'], code=302))
        response.headers['Location'] = '/persons/%s' % d['_merged_to']
        response.status = 'Moved Permanently'
        response.status_code = 301
        response.set_data(json.dumps({'_status': 'ERR',
                                      '_error': '301 Moved permanently',
                                      '_url': '/api/v1/persons/%s' % d['_merged_to']}))

app.on_post_GET_persons += after_get_persons
"""

    START:
    ======

    Start the wsgi server with Eve

    @note: Run development server in background with log as 'nohup python run.py >> nlf.log 2>&1&' 
    @note: Run via gunicorn as 'gunicorn -w 5 -b localhost:8080 run:app'
    @note: Gunicorn should have 2n+1 workers where n is number of cpu cores
    @todo: Config file for gunicorn deployment and -C see http://gunicorn-docs.readthedocs.org/en/latest/settings.html

"""
""" A simple python logger setup
Use app.logger.<level>(<message>) for manual logging
Levels: debug|info|warning|error|critical"""
if 1 == 1 or not app.debug:
    import logging
    from logging.handlers import RotatingFileHandler

    file_handler = RotatingFileHandler('lungo-backend.log', 'a', 1 * 1024 * 1024, 10)
    file_handler.setFormatter(
        logging.Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'))
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('Lungo startup on database %s' % app.config['MONGO_DBNAME'])

# Run only once
# if app.debug and not os.environ.get("WERKZEUG_RUN_MAIN") == "true":
# run once goes here


if __name__ == '__main__':
    app.run(host=app.config['APP_HOST'], port=app.config['APP_PORT'])
