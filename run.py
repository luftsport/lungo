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

try:
    from eve_swagger import get_swagger_blueprint, add_documentation as add_swagger_documentation

    swagger_blueprint = get_swagger_blueprint()
except Exception as e:
    from eve_swagger import swagger as swagger_blueprint, add_documentation as add_swagger_documentation

from eve_healthcheck import EveHealthCheck
from blueprints.syncdaemon import Syncdaemon
from blueprints.fai import Fai
from blueprints.acl import ACL
from blueprints.html import Html
from blueprints.nif import NIF
from blueprints.tms import Tms
from blueprints.notifications import Notifications
from blueprints.ohdear import Ohdear
import time
from flask import g, request, current_app
import uuid
# Import blueprints
# from blueprints.authentication import Authenticate
# Register custom blueprints
# app.register_blueprint(Authenticate, url_prefix="%s/user" % app.globals.get('prefix'))

# Custom url mappings (for flask)
from ext.app.url_maps import ObjectIDConverter, RegexConverter
# Custom auth extensions
from ext.auth.tokenauth import NlfTokenAuth

# Make sure we are in virtualenv
try:
    if sys.prefix == sys.base_prefix:
        print("Outside virtualenv, aborting....")
        sys.exit(-1)
except:
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
app.config['TEMPLATES_AUTO_RELOAD'] = True
app.debug = True
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

app.register_blueprint(Syncdaemon, url_prefix="%s/syncdaemon" % app.globals.get('prefix'))
app.register_blueprint(Fai, url_prefix=f"{app.globals.get('prefix')}/{Fai.url_prefix}")
app.register_blueprint(ACL, url_prefix=f"{app.globals.get('prefix')}/{ACL.url_prefix}")
app.register_blueprint(NIF, url_prefix=f"{app.globals.get('prefix')}/{NIF.url_prefix}")
app.register_blueprint(Tms, url_prefix=f"{app.globals.get('prefix')}/{Tms.url_prefix}")
app.register_blueprint(Notifications, url_prefix=f"{app.globals.get('prefix')}/{Notifications.url_prefix}")
app.register_blueprint(Ohdear, url_prefix=f"{app.globals.get('prefix')}/{Ohdear.url_prefix}")
# Blueprint returning html
app.register_blueprint(Html, url_prefix=f"{app.globals.get('prefix')}/{Html.url_prefix}")

app.register_blueprint(swagger_blueprint, url_prefix=app.globals.get('prefix'))

from ext.app.eve_blueprint_helper import get_swagger_blueprint_spec

# Integrate with eve-swagger (compatible with v1.1.3)
# Integrate with eve-swagger (v1.1.3)
with app.app_context():
    for blueprint in [Notifications, NIF, Tms, Fai, ACL, Syncdaemon, Html]:  # , Authenticate
        swagger_spec = get_swagger_blueprint_spec(blueprint, resource=blueprint.name.lower())
        for path, operations in swagger_spec.items():
            app.logger.info(f'[Blueprint] adding path {path} to swagger doc')
            add_swagger_documentation(swagger_blueprint, {'paths': {path: operations}})

from ext.app.hooks import (
    on_function_post,
    on_license_post, on_competence_post,
    on_person_after_post, on_person_after_put, on_function_put, on_competence_put, on_license_put, before_delete_person,
    on_organizations_post, on_organizations_put, after_get_person, after_get_persons, on_person_before_put,
    assign_lookup,
    on_payment_before_post, on_payment_after_put, on_payment_after_post, on_payment_before_put,
    on_notifications_delete
)

# Should be able to filter out all merged when doing lookup
# def filter_merged_to(request, lookup):
#    if any(i in lookup for i in ['id', '_id']) is False:
#        lookup['_merged_to'] = {"$exists": False}

# PERSONS
app.on_inserted_persons_process += on_person_after_post
# Deregister person and all competences and functions on DELETE
app.on_delete_item_persons_process += before_delete_person  # Use original values and not _update! For later testing!

# On replace(d) / PUT:
app.on_replace_persons_process += on_person_before_put  # Use original values and not _update! For later testing!
app.on_replaced_persons_process += on_person_after_put  # Rebuild person
# After GET'ing a merged person
app.on_fetched_resource_persons += after_get_persons
app.on_fetched_item_persons += after_get_person
app.on_fetched_resource_persons_knips += after_get_persons
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

# NOTIFICATIONS
app.on_delete_notifications += on_notifications_delete

# AGGREGATION

# Sendgrid webhook
from ext.app.sendgrid_hooks import verify_sendgrid_signature

app.on_insert_sendgrid_webhook += verify_sendgrid_signature

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

    file_handler = RotatingFileHandler('lungo-backend.log', 'a', 25 * 1024 * 1024, 10)
    file_handler.setFormatter(
        logging.Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'))
    app.logger.setLevel(logging.DEBUG)
    file_handler.setLevel(logging.DEBUG)
    app.logger.addHandler(file_handler)
    app.logger.info('Lungo startup on database %s' % app.config['MONGO_DBNAME'])


@app.before_request
def start_timer_and_log_start():
    g.request_id = str(uuid.uuid4())
    g.start_time = time.perf_counter()

    # Optional: skip logging health-checks or static if you have many
    if request.path.startswith(('/_', '/static', '/health')):
        return

    # Build log message base
    msg_parts = [
        f"method={request.method}",
        f"path={request.path}",
    ]

    # Query params (GET/DELETE usually; also ? in POST sometimes)
    if request.args:
        # Convert to str; be careful – mask tokens/passwords in prod!
        params_str = ', '.join(f"{k}={v}" for k, v in request.args.items(multi=True))
        msg_parts.append(f"query_params={{{params_str}}}")

    # Body for POST/PUT/PATCH (JSON or form) – careful with size & secrets
    if request.method in ('POST', 'PUT', 'PATCH'):
        try:
            if request.is_json:
                body = request.get_json(silent=True)
                if body:
                    # Truncate if huge; or just log keys
                    body_preview = str(body)[:500] + '...' if len(str(body)) > 500 else str(body)
                    msg_parts.append(f"body_preview={body_preview}")
            elif request.form:
                form_str = ', '.join(f"{k}={v}" for k, v in request.form.items())
                msg_parts.append(f"form={{{form_str}}}")
            # else: raw data → request.get_data() – usually skip or log length only
        except Exception:
            msg_parts.append("body=[parse-error]")

    msg_parts.insert(0, f"request_id={g.request_id}")
    app.logger.info(" → " + " | ".join(msg_parts))


@app.after_request
def log_completion(response):
    if not hasattr(g, 'start_time'):
        return response

    duration = time.perf_counter() - g.start_time

    # Optional: skip or shorten for health endpoints
    if request.path.startswith(('/_', '/static', '/health')):
        return response

    app.logger.info(
        "request_id=%s |← status=%s | duration=%.4f s | path=%s",
        g.request_id,
        response.status_code,
        duration,
        request.path
    )

    return response


# Run only once
# if app.debug and not os.environ.get("WERKZEUG_RUN_MAIN") == "true":
# run once goes here
def save_resources_to_file(output_file='resources.json'):
    with app.app_context():
        # Access the DOMAIN configuration
        domain_config = app.config['DOMAIN']

        # Log the resources for debugging
        print(f"Found {len(domain_config)} resources: {list(domain_config.keys())}")

        # Convert to JSON-serializable format
        serializable_domain = {}
        for resource, config in domain_config.items():
            try:
                # Copy the config to avoid modifying the original
                serializable_config = config.copy()

                # Handle non-serializable fields
                if 'url' in serializable_config and hasattr(serializable_config['url'], 'pattern'):
                    serializable_config['url'] = str(serializable_config['url'].pattern)

                # Handle other potentially non-serializable fields (e.g., authentication, datasource)
                for key, value in serializable_config.items():
                    if not isinstance(value, (str, int, float, bool, list, dict, type(None))):
                        serializable_config[key] = str(value)  # Convert to string as fallback

                serializable_domain[resource] = serializable_config
            except Exception as e:
                print(f"Error processing resource '{resource}': {e}")
                continue  # Skip problematic resource but continue with others

        # Write to JSON file
        try:
            with open(output_file, 'w') as f:
                json.dump(serializable_domain, f, indent=4, sort_keys=True)
            print(f"All resources saved to {output_file}")
        except Exception as e:
            print(f"Error saving to file: {e}")
            print(f"Error saving resources: {e}")


# save_resources_to_file('resources.json')

if __name__ == '__main__':
    app.run(host=app.config['APP_HOST'], port=app.config['APP_PORT'])
