"""
    Lungo - YAMS!
    =============

    @note: Run as development `nohup python run.py >> lungo.log 2>&1&` NB in virtualenv!

    @author:        Einar Huseby
    @copyright:     (c) Norges Luftsportforbund
    @license:       GPLV3, see LICENSE for more details.
"""

import os, sys

from eve import Eve
import json
# Swagger docs
from eve_swagger import swagger
from eve_healthcheck import EveHealthCheck
from blueprints.syncdaemon import Sync
from blueprints.fai import Fai
from blueprints.acl import ACL
from blueprints.member_check import MemberCheck
from blueprints.html import Html

# Import blueprints
# from blueprints.authentication import Authenticate
# Register custom blueprints
# app.register_blueprint(Authenticate, url_prefix="%s/user" % app.globals.get('prefix'))

# Custom url mappings (for flask)
from ext.app.url_maps import ObjectIDConverter, RegexConverter
# Custom auth extensions
from ext.auth.tokenauth import NlfTokenAuth

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
app = Eve(auth=NlfTokenAuth, settings=SETTINGS_PATH)
# app = Eve(settings=SETTINGS_PATH)

""" Define global settings
These settings are mirrored from Eve, but should not be!
@todo: use app.config instead
"""
app.globals = {"prefix": "/api/v1"}

# Healthcheck
hc = EveHealthCheck(app, '/healthcheck')

# Custom url mapping (needed by native flask routes)
app.url_map.converters['objectid'] = ObjectIDConverter
app.url_map.converters['regex'] = RegexConverter

# Register eve-docs blueprint
# app.register_blueprint(eve_docs,        url_prefix="%s/docs" % app.globals.get('prefix'))
app.register_blueprint(swagger, url_prefix=app.globals.get('prefix'))

app.register_blueprint(Sync, url_prefix="%s/syncdaemon" % app.globals.get('prefix'))
app.register_blueprint(Fai, url_prefix="%s/fai" % app.globals.get('prefix'))
app.register_blueprint(ACL, url_prefix="%s/acl" % app.globals.get('prefix'))
app.register_blueprint(MemberCheck, url_prefix="%s/membercheck" % app.globals.get('prefix'))

# Blueprint returning html
app.register_blueprint(Html, url_prefix="%s/html" % app.globals.get('prefix'))

from ext.app.hooks import on_function_post, \
    on_license_post, on_competence_post, \
    on_person_after_post, on_person_after_put, on_function_put, on_competence_put, on_license_put, \
    on_organizations_post, on_organizations_put, after_get_person, on_person_before_put, assign_lookup, \
    on_payment_before_post, on_payment_after_put, on_payment_after_post, on_payment_before_put

# Should be able to filter out all merged when doing lookup
# def filter_merged_to(request, lookup):
#    if any(i in lookup for i in ['id', '_id']) is False:
#        lookup['_merged_to'] = {"$exists": False}

# PERSONS
app.on_inserted_persons_process += on_person_after_post
# On replace(d) / PUT:
app.on_replace_persons_process += on_person_before_put  # Use original values and not _update! For later testing!
app.on_replaced_persons_process += on_person_after_put  # Rebuild person
# After GET'ing a merged person
app.on_fetched_item_persons += after_get_person
app.on_fetched_item_persons_knips += after_get_person

# All get's get through this one!
app.on_pre_GET += assign_lookup

# app.on_pre_GET_persons += filter_merged_to

# Hooks to update person object, database layer, AFTER
# FUNCTIONS
app.on_inserted_functions_process += on_function_post
app.on_replaced_functions_process += on_function_put

# LICENSES
app.on_inserted_licenses_process += on_license_post
app.on_replaced_licenses_process += on_license_put

# COMPETENCES
app.on_inserted_competences_process += on_competence_post
app.on_replaced_competences_process += on_competence_put

# PAYMENTS POST
app.on_insert_payments_process += on_payment_before_post
app.on_inserted_payments_process += on_payment_after_post
# PAYMENTS PUT
app.on_replace_payments_process += on_payment_before_put
app.on_replaced_payments_process += on_payment_after_put


# ORGANIZATIONS
app.on_inserted_organizations_process += on_organizations_post
app.on_replaced_organizations_process += on_organizations_put

# AGGREGATION

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
