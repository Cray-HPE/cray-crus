# Copyright 2020-2021 Hewlett Packard Enterprise Development LP
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
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.  IN NO EVENT SHALL
# THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR
# OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,
# ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
# OTHER DEALINGS IN THE SOFTWARE.
#
# (MIT License)

"""
CRUS-related CMS test helper functions
"""

from .api import API_URL_BASE, requests_delete, requests_get, requests_post
from .cli import run_cli_cmd
from .helpers import debug, error, get_bool_field_from_obj, get_int_field_from_obj, \
                     get_list_field_from_obj, get_str_field_from_obj, info, \
                     raise_test_error, sleep
import time

CRUS_URL_BASE = "%s/crus" % API_URL_BASE
CRUS_SESSION_URL_BASE = "%s/session" % CRUS_URL_BASE

def crus_session_url(upgrade_id=None):
    """
    Returns the CRUS API endpoint for either CRUS sessions generally, or the
    specified CRUS session
    """
    if upgrade_id == None:
        return CRUS_SESSION_URL_BASE
    return "%s/%s" % (CRUS_SESSION_URL_BASE, upgrade_id)

CRUS_SESSION_STRING_FIELDS = [ "failed_label", "kind", "workload_manager_type", "api_version", 
                               "state", "starting_label", "upgrade_template_id", "upgrade_id", 
                               "upgrading_label" ]

CRUS_SESSION_FIELDS = CRUS_SESSION_STRING_FIELDS + [ "completed", "upgrade_step_size", "messages" ]

CRUS_SESSION_DEFAULTS = {
    "kind": "ComputeUpgradeSession",
    "workload_manager_type": "slurm" }

def validate_crus_session(session_object, expected_values=None):
    """
    Validates that the CRUS session object has the fields we expect (and that
    those fields have the expected values, if specified)
    """
    if expected_values == None:
        expected_values=dict()
    noun="CRUS session object"
    for field in CRUS_SESSION_STRING_FIELDS:
        try:
            get_str_field_from_obj(session_object, field, noun=noun, exact_value=expected_values[field])
        except KeyError:
            try:
                get_str_field_from_obj(session_object, field, noun=noun, exact_value=CRUS_SESSION_DEFAULTS[field])
            except KeyError:
                get_str_field_from_obj(session_object, field, noun=noun, min_length=1)
    try:
        get_int_field_from_obj(session_object, "upgrade_step_size", noun=noun, exact_value=expected_values["upgrade_step_size"])
    except KeyError:
        get_int_field_from_obj(session_object, "upgrade_step_size", noun=noun, min_value=1)
    try:
        get_bool_field_from_obj(session_object, "completed", noun=noun, exact_value=expected_values["completed"])
    except KeyError:
        get_bool_field_from_obj(session_object, "completed", noun=noun, null_okay=False)
    get_list_field_from_obj(session_object, "messages", noun=noun, member_type=str)
    unknown_fields = [ k for k in session_object.keys() if k not in CRUS_SESSION_FIELDS ]
    if unknown_fields:
        raise_test_error("CRUS session object has unexpected field(s): %s" % ", ".join(unknown_fields))

def describe_crus_session(use_api, upgrade_id, expected_values=None):
    """
    Calls an API GET or CLI describe on the specified CRUS session.
    The CRUS session is extracted from the response, it is validated (for the things we care about,
    anyway), and then it is returned.
    """
    info("Describing CRUS session %s" % upgrade_id)
    if use_api:
        url = crus_session_url(upgrade_id)
        response_object = requests_get(url)
    else:
        cmd_list = ["crus","session","describe",upgrade_id]
        response_object = run_cli_cmd(cmd_list)

    if expected_values == None:
        expected_values = { "upgrade_id": upgrade_id }
    else:
        expected_values["upgrade_id"] = upgrade_id
    validate_crus_session(response_object, expected_values=expected_values)
    return response_object

def list_crus_sessions(use_api):
    """
    Uses the API or CLI to list all CRUS sessions. 
    The response is validated and a mapping of upgrade_ids to CRUS sessions is returned.
    """
    info("Listing CRUS sessions")
    if use_api:
        response_object = requests_get(crus_session_url())
    else:
        response_object = run_cli_cmd("crus session list".split())

    if not isinstance(response_object, list):
        raise_test_error("Response should be a list but it is %s" % str(type(response_object)))

    for cs in response_object:
        validate_crus_session(cs)

    return { cs["upgrade_id"]: cs for cs in response_object }

def create_crus_session(use_api, failed_label, starting_label, upgrade_template_id, upgrade_step_size, 
                        upgrading_label, workload_manager_type="slurm"):
    """
    Creates the specified CRUS session
    """
    info("Creating CRUS session")
    session_values = {
        "failed_label": failed_label,
        "starting_label": starting_label,
        "workload_manager_type": workload_manager_type,
        "upgrade_template_id": upgrade_template_id,
        "upgrade_step_size": upgrade_step_size,
        "upgrading_label": upgrading_label }
    if use_api:
        response_object = requests_post(crus_session_url(), json=session_values)
    else:
        cli_cmd_list = [ "crus", "session", "create",
                         "--failed-label", failed_label,
                         "--starting-label", starting_label,
                         "--upgrade-step-size", str(upgrade_step_size),
                         "--upgrade-template-id", upgrade_template_id,
                         "--upgrading-label", upgrading_label,
                         "--workload-manager-type", workload_manager_type ]
        response_object = run_cli_cmd(cli_cmd_list)
    validate_crus_session(response_object, expected_values=session_values)
    return response_object

def delete_crus_session(use_api, upgrade_id):
    """
    Delete the specified CRUS session
    """
    info("Deleting CRUS session %s" % upgrade_id)
    if use_api:
        url = crus_session_url(upgrade_id)
        # Currently CRUS delete operations return 200 with an object
        # (unlike most services, which return 204 and blank response)
        # This is because (I think) CRUS sessions do not get deleted
        # immediately, but just get marked for deletion.
        return requests_delete(url, expected_sc=200)
    else:
        cli_cmd_list = [ "crus", "session", "delete", upgrade_id ]
        return run_cli_cmd(cli_cmd_list)

def wait_until_crus_session_complete(use_api, upgrade_id, timeout=45*60, sleeptime=30, expected_values=None):
    """
    Wait until the specified CRUS session has completed set to True, or until
    we time out. The sleeptime is how long between checks of the CRUS session status.
    Units for both timeout and sleeptime is seconds.
    """
    info("Waiting for CRUS session %s to complete" % upgrade_id)
    stoptime = time.time() + timeout
    errors_found = False
    noun = "CRUS session response"
    myargs = { "noun": noun, "null_okay": False }
    while True:
        response_object = describe_crus_session(use_api=use_api, upgrade_id=upgrade_id, 
                                                expected_values=expected_values)
        messages = get_list_field_from_obj(response_object, "messages", member_type=str, **myargs)
        completed = get_bool_field_from_obj(response_object, "completed", **myargs)
        debug("completed=%s" % str(completed))
        for m in messages:
            debug("message: %s" % m, timestamp=False)
        if completed:
            break
        timeleft = stoptime - time.time()
        if timeleft <= 0:
            raise_test_error("Timeout: CRUS session %s not complete after %d seconds" % (upgrade_id, timeout))
        sleep(min(timeleft,sleeptime))
    info("CRUS session %s completed" % upgrade_id)