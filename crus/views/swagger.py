"""
View implementation for the '/swagger.py' and '/api routes of
the CRUS

Copyright 2019, Cray Inc. All rights reserved.

"""
from flask import jsonify

from ..app import APP, SPEC


@APP.route("/docs/swagger.json", methods=["GET"])
def swagger_json():
    """Route to swagger.json description
    ---
    get:
      description: retrieve the API specification as a swagger.json file
      responses:
        200:
          description: Success
    """
    return jsonify(SPEC.to_dict()), 200


PATHS = []
