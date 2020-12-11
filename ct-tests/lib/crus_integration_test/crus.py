# Copyright 2020 Hewlett Packard Enterprise Development LP

"""
CRUS-related test helper functions for CRUS integration test
"""

from common.crus import describe_crus_session
from common.helpers import debug, error, info, raise_test_error
import time

QUIESCE_REQUESTED_MESSAGE = "Quiesce requested in step 0: moving to QUIESCING"

def crus_session_waiting_for_quiesce(use_api, crus_session_id, expected_values):
    """
    Describes the specified CRUS session.
    Raises an error if it has been marked completed.
    Returns true if the final status message is our step 0 quiesce request message.
    Raises an error if that message is in the message list, but is not the final one.
    Otherwise returns false.
    """
    crus_session = describe_crus_session(use_api=use_api, upgrade_id=crus_session_id, 
                                         expected_values=expected_values)
    if crus_session["completed"]:
        raise_test_error("CRUS session marked completed before we expected")
    messages = crus_session["messages"]
    if messages:
        if messages[-1] == QUIESCE_REQUESTED_MESSAGE:
            info("Session has requested quiesce")
            return True
        elif QUIESCE_REQUESTED_MESSAGE in messages:
            raise_test_error("CRUS session has progressed beyond step 0 quiesce request before we expected")
    return False

def verify_crus_waiting_for_quiesce(use_api, crus_session_id, expected_values):
    """
    Wait until the CRUS session is waiting for the nodes in step 0 to quiesce.
    Then wait again to make sure that it remains in that state.
    """
    info("Waiting for CRUS session %s to request quiesce of step 0 nodes" % crus_session_id)
    # We will wait for up to 5 minutes for the session to be waiting for step 0
    # nodes to quiesce
    initial_wait_time_minutes = 5
    stop_time = time.time() + initial_wait_time_minutes*60
    while True:
        if crus_session_waiting_for_quiesce(use_api, crus_session_id, expected_values):
            break
        elif time.time() >= stop_time:
            raise_test_error("CRUS session has not reached step 0 quiesce request after %d minute(s)" % initial_wait_time_minutes)
        time.sleep(10)
    no_progress_wait_time_minutes = 3
    info("Wait for %d minute(s) to verify the session does not progress." % no_progress_wait_time_minutes)
    time.sleep(no_progress_wait_time_minutes*60)
    if crus_session_waiting_for_quiesce(use_api, crus_session_id, expected_values):
        info("As expected, the CRUS session is still waiting for quiesce after %d minute(s)" % no_progress_wait_time_minutes)
        return
    raise_test_error("CRUS session previously was waiting for step 0 quiesce, but now that message is gone from the messages list")
