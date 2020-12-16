"""
Set up the elements of an app for CRUS

Copyright 2019, Cray Inc. All rights reserved.
"""
import os

from flask import Flask
from flask_swagger_ui import get_swaggerui_blueprint
from flask_marshmallow import Marshmallow
from apispec import APISpec
from apispec.ext.flask import FlaskPlugin
from apispec.ext.marshmallow import MarshmallowPlugin
import urllib3
import etcd3_model
from .version import VERSION, API_VERSION  # pylint: disable=unused-import


def configure_app(application):
    """ Set config values based on environment

    """
    config = {
        "development": "crus.config.DevelopmentConfig",
        "testing": "crus.config.TestingConfig",
        "prod": "crus.config.ProductionConfig",
        "default": "crus.config.DefaultConfig"
    }
    config_name = os.getenv('CRUS_CONFIGURATION', 'default')
    application.config.from_object(config[config_name])


def add_paths(path_list):
    """ Add paths to the swagger definition

    """
    with APP.app_context():
        for path in path_list:
            SPEC.add_path(view=path)


def install_swagger():
    """ Install the swagger UI in the app

    """
    swaggerui_blueprint = get_swaggerui_blueprint(
        "/docs",
        "/docs/swagger.json"
    )
    APP.register_blueprint(swaggerui_blueprint, url_prefix="/docs")


# Create the app and configure it
APP = Flask(__name__)
print("configuring the application")
configure_app(APP)
print("done configuring")
MA = Marshmallow(APP)  # Set up Marshmallow for APP
ETCD = etcd3_model.create_instance()

# A convenient place to define HTTP headers for API requests...
HEADERS = {
    'Content-Type': 'application/json',
    'Accept': 'application/json'
}
HTTPS_VERIFY = True
if not APP.config['HTTPS_VERIFY']:
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    HTTPS_VERIFY = False
API_URI = APP.config['API_URI']

# Create Spec
SPEC = APISpec(
    title='Compute Rolling Upgrade Service',
    openapi_version="3.0.2",
    version=VERSION,
    info={
        'description': "Administrative Front End for Compute Rolling Upgrades"
    },
    servers=[
        {
            'url': "/apis/crus",
            'description': "Cluster External API access"
        },
        {
            'url': "/",
            'description': "Cluster Internal API access"
        }
    ],
    plugins=[
        FlaskPlugin(),
        MarshmallowPlugin(),
    ]
)
