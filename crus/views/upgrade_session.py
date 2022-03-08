#
# MIT License
#
# (C) Copyright 2019, 2021-2022 Hewlett Packard Enterprise Development LP
#
# Permission is hereby granted, free of charge, to any person obtaining a
# copy of this software and associated documentation files (the "Software"),
# to deal in the Software without restriction, including without limitation
# the rights to use, copy, modify, merge, publish, distribute, sublicense,
# and/or sell copies of the Software, and to permit persons to whom the
# Software is furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included
# in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
# THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR
# OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,
# ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
# OTHER DEALINGS IN THE SOFTWARE.
#
"""
View implementation for the '/session' and '/session/<id> routes of
the CRUS

"""
from http import HTTPStatus as HS

from flask import request
from marshmallow.exceptions import ValidationError
from ..version import API_VERSION
from ..app import APP
from ..models import (
    UpgradeSession,
    UPGRADE_SESSIONS_SCHEMA,
    UPGRADE_SESSION_SCHEMA
)
from . import errors


# endpoint to get a list of Upgrade Sessions or create a new Upgrade Session
@APP.route("/session", methods=["GET", "POST"])
def upgrade_session_list_route():
    """ GET a List of Upgrade Sessions or POST (add) a new Upgrade Session
    ---
    get:
      summary: Get the list of Upgrade Sessions
      description: Get the list of Upgrade Sessions
      responses:
        200:
          description: OK
          content:
            application/json:
              schema:
                type: array
                items: UpgradeSessionSchema
    post:
      summary: Create a new Upgrade Session
      description: Create a new Upgrade Session
      requestBody:
        content:
          application/json:
            schema: UpgradeSessionSchema
      responses:
        201:
          description: Created
          content:
            application/json:
              schema: UpgradeSessionSchema
        400:
          description: Bad Request
        422:
          description: Unprocessable Entity
    """
    if request.method == "GET":
        all_sessions = UpgradeSession.get_all()
        ret = UPGRADE_SESSIONS_SCHEMA.jsonify(all_sessions), HS.OK
        return ret

    if request.method == "POST":
        json_input = request.get_json()
        errs = None
        try:
            new_session, errs = UPGRADE_SESSION_SCHEMA.load(json_input)
        except ValidationError as exc:
            errs = exc.messages
        if errs:
            raise errors.DataValidationFailure(errors=errs)
        new_session.api_version = API_VERSION
        new_session.kind = "ComputeUpgradeSession"
        new_session.put()
        return UPGRADE_SESSION_SCHEMA.jsonify(new_session), HS.CREATED

    # Something other than GET or POST was received.  Should never
    # happen, but just to be on the safe side...
    raise errors.MethodNotAllowed()  # pragma should never happen


# endpoint to get Upgrade Session detail by Upgrade ID and to delete
# an Upgrade Session.
@APP.route("/session/<upgrade_id>", methods=["GET", "DELETE"])
def specific_upgrade_session_route(upgrade_id):
    """ Get or Delete an Upgrade Session by its ID
    ---
    get:
      summary:  Get a specific Upgrade Session by its ID
      description: Get a specific Upgrade Session by its ID
      parameters:
      - in: path
        name: upgrade_id
        required: true
        schema:
          type: string
      responses:
        200:
          description: OK
          content:
            application/json:
              schema: UpgradeSessionSchema
        404:
          description: Not Found

    delete:
      summary: Delete a specific Upgrade Session by its ID
      description: Delete a specific Upgrade Session by its ID
      parameters:
      - name: upgrade_id
        in: path
        required: true
        schema:
          type: string
      responses:
        200:
          description: OK
          content:
            application/json:
              schema: UpgradeSessionSchema
        404:
          description: Not Found
    """
    # Lock UpgradeSession to avoid races between deletions (delete) of
    # individual UpgradeSession objects here and updates occurring in
    # other instances or in the controllers.
    cur_session = UpgradeSession.get(upgrade_id)
    if cur_session is None:
        raise errors.ResourceNotFound()

    if request.method == "GET":
        ret = UPGRADE_SESSION_SCHEMA.jsonify(cur_session), HS.OK
        return ret

    if request.method == "DELETE":
        # Get the lock so we know no one is processing the
        # session, then set DELETING
        with cur_session.lock():
            cur_session = UpgradeSession.get(upgrade_id)
            cur_session.delete()
        # Do a put outside the lock to prevent the session update
        # from being dropped on the floor.  See the comment in
        # controllers/upgrade_agent/upgrade_agent.py.
        cur_session.put()
        return UPGRADE_SESSION_SCHEMA.jsonify(cur_session), HS.OK

    # Something other than GET or DELETE was received.
    # Should never happen, but just to be on the safe side...
    raise errors.MethodNotAllowed()  # pragma should never happen


PATHS = [
    upgrade_session_list_route,
    specific_upgrade_session_route,
]
