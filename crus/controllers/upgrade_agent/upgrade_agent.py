"""
The definition of the Rolling Compute Upgrade Agent

Copyright 2019-2020 Hewlett Packard Enterprise Development LP
"""
# This is where the heart of Compute Upgrade processing takes place.
# It is implemented as a state machine driven by etcd3_watch events.
# On receipt of an event, the function for the corresponding stage is
# called and runs a simple operation and returns.  The progress of a
# compute upgrade session is tracked by a parallel progress object
# stored in ETCD.  This allows multiple upgrades to be processed in
# parallel, and, since the code itself is stateless (relying on state
# stored in ETCD) allows multiple instances of the controller to
# handle compute upgrades in parallel for scaling.
import time
from queue import Empty
from etcd3_model import UPDATING, DELETING

from ...app import APP
from .errors import ComputeUpgradeError
from .boot_service import BootSession
from .node_group import NodeGroup
from .wlm import get_wlm_handler
from ...models.upgrade_session import (
    UpgradeSession,
    ComputeUpgradeProgress,
    STARTING,
    QUIESCING,
    QUIESCED,
    BOOTING,
    BOOTED,
    WLM_WAITING,
    CLEANUP
)

# A pause time to avoid swamping the system with monitoring of nodes.
# If we are running the unit tests, this is 0.01 seconds.  If we are
# running production it is 10 seconds.  If the upgrade is waiting
# for something, This will be returned from advance functions to tell
# the caller to postpone the next action on this upgrade for that many
# seconds.  Otherwise None is returned.
PAUSE_TIME = 10 if not APP.config['TESTING'] else 0.01

# A timeout value for waiting for WLM nodes to return to service in
# the WLM_WAITING state.  give this plenty of time to let the nodes
# boot and become localized.  10 minutes should be sufficient.
#
# Make it 2 seconds in the testing case so we can reach it in a unit
# test.
WLM_WAIT_TIMEOUT = 10 * 60 if not APP.config['TESTING'] else 2

# Keep track of whether the watcher has been started or not
WATCHER = None


def start_watching():
    """ Set up to watch for upgrade session changes...

    returns a queue and a pending event list.
    """
    global WATCHER  # pylint: disable=global-statement
    if WATCHER:
        return WATCHER

    pending = []
    queue = UpgradeSession.watch()
    WATCHER = (queue, pending)
    UpgradeSession.learn()  # Flow existing upgrade sessions to watchers
    return WATCHER


def watch_sessions():  # pragma no unit test (needs concurrency)
    """Drive the upgrade processing in a forever loop

    """
    queue, pending = start_watching()
    while True:
        process_upgrade(queue, pending)


def process_upgrade(queue, pending):
    """Watch for upgrade_session changes coming from ETCD and drive those
    events into the state machine.  This also handles scheduling of
    pauses when a session is in a state that may need more time to
    complete.  The 'queue' and 'pending' parameters are taken from a
    return from start_watching() and provide the event queue and the
    scheduled pending updates queue respectively.

    """
    # Set a flag to indicate that a given message is an error and
    # should cause the upgrade_session to pause so we don't beat
    # up the system while the problem is being resolved.
    error_message = False

    # Process the pending queue.  If an upgrade session has
    # reached its scheduled time, remove it from the queue and
    # trigger it.
    while pending and time.time() > pending[0][0]:
        upgrade_id = pending.pop(0)[1]
        upgrade_session = UpgradeSession.get(upgrade_id)
        if not upgrade_session:  # pragma no unit test
            # The session has somehow vanished since I last saw
            # it, nothing to do.
            continue
        # Trigger a watch event on this upgrade session
        upgrade_session.put()

    # Compute a timeout for waiting for more work based on the
    # next pending action.  If there is nothing pending, take a
    # long timeout.
    timeout = pending[0][0] - time.time() if pending else PAUSE_TIME
    # The weird coditional below takes into account that None is
    # not comparable to a number.  It will preserve the None if
    # that is what timeout is, otherwise it makes sure that the
    # timeout is positive or 0.
    timeout = 0 if timeout and timeout < 0 else timeout
    try:
        # Look for an UpgradeSession to do something with
        upgrade_session = queue.get(timeout=timeout)
    except Empty:
        # Timed out looking for something to do, go back and
        # process pending and then try again.
        return
    with upgrade_session.lock(timeout=0) as lock:
        if not lock.is_acquired():  # pragma no unit test
            # We didn't get the lock, so someone else has this one...
            return

        # Looks like we have a live one, start processing it.
        # First, get the actual state under the lock, since
        # something could have changed while it was queued.
        upgrade_id = upgrade_session.upgrade_id
        if [event[1] for event in pending if event[1] == upgrade_id]:
            # This one is currently pending.  Probably a case of
            # an update due to an error or something and we don't
            # want to handle it yet.  Skip it.
            return
        upgrade_session = UpgradeSession.get(upgrade_id)
        if not upgrade_session:  # pragma no unit test
            # Seems to be gone, skip it...
            return

        if upgrade_session.completed and upgrade_session.state != DELETING:
            # Just mark this session ready and be done, there is
            # nothing else to do for update (we want to remove it if
            # it is deleting).  This will happen while we are learning
            # after startup.
            upgrade_session.set_ready()
            return

        # Get the progress state for this upgrade session
        upgrade_progress = ComputeUpgradeProgress.get(upgrade_id)
        if upgrade_progress is None:
            upgrade_progress = ComputeUpgradeProgress(upgrade_id=upgrade_id)
            upgrade_progress.put()

        step_number = upgrade_progress.step
        stage = upgrade_progress.stage
        try:
            # Figure out what nodes (if any) we are working with for
            # this pass.  If we have exhausted the nodes to be
            # upgraded (i.e. copleted the last step), this will be an
            # empty list.
            starting_node_group = NodeGroup(upgrade_session.starting_label)
            upgrade_nodes = starting_node_group.get_members()
            first = step_number * upgrade_session.upgrade_step_size
            last = (step_number + 1) * upgrade_session.upgrade_step_size
            # Unlike regular list references, slices don't have a
            # problem with indices out of range, they just return
            # [] in that case.  So, we are done when we get an
            # empty list.
            step_nodes = upgrade_nodes[first:last]

            # Call the handler function for the current stage
            state = upgrade_session.state
            assert state in [UPDATING, DELETING]
            stage_handler = (
                UPDATE_MAP[stage] if state == UPDATING else DELETE_MAP[stage]
            )
            message = stage_handler(
                upgrade_session,
                upgrade_progress,
                step_nodes
            )
        except ComputeUpgradeError as err:  # pragma no unit test
            error_message = True  # schedule this after reporting error
            # Lint complains because it does not understand what stage
            # is.  Silence it.
            #
            # pylint: disable=bad-string-format-type
            message = "Processing step %d in stage %s failed - %s" % (
                step_number,
                stage,
                str(err)
            )
    # Outside the lock, handle any messages and queuing of pending
    # activities.
    #
    # First, check whether we are posting a message (this needs to
    # be done outside the lock to avoid dropping watch events on
    # the floor in a super-rare case).  The race is, I get the
    # lock and see if I acquired it, you get the lock and see if
    # you acquired it, but George over there was holding the lock
    # when he posted a message (and then dropped it immediately).
    # So you and I both fail to acquire the lock.  In the unlikely
    # case where George dies and is not restarted before
    # re-acquiring the lock, no one handles the event.
    #
    # If the session is completed and the session state is
    # DELETING, then the upgrade session has been removed, so
    # there is nothing to post to.  Protect that case here.
    if message is not None and not (upgrade_session.state == DELETING and
                                    upgrade_session.completed):
        upgrade_session.post_message_once(message)
        if not error_message:
            # Nothing to schedule, go back for more
            return

    # There was either no message or an error message, so we are going
    # to schedule a wait event.  Add the upgrade session to the list
    # of pending sessions which this agent will trigger with a put()
    # after the requested pause.
    schedule = time.time() + PAUSE_TIME
    pending.append((schedule, upgrade_id))
    # Make sure the queue is in ascending time order (there should
    # not be very many items in the queue, so there is no need for
    # fancy sorted lists or anything here)
    pending.sort()


def _fail_nodes(upgrade_session, upgrade_progress, xnames, reason):
    """Utility - go through the supplied list of 'xnames' and fail the
    associated nodes in the WLM supplying the specified reason. Also,
    add the nodes to the failed node group.

    """
    wlm = get_wlm_handler(upgrade_session.workload_manager_type)
    failed_node_group = NodeGroup(upgrade_session.failed_label)
    xnames = [xname for xname in xnames
              if xname not in upgrade_progress.completed_nodes]
    for xname in xnames:
        wlm.fail(xname, reason)
        failed_node_group.add_member(xname)


def _fail_nodes_and_step(upgrade_session, upgrade_progress, xnames, reason):
    """Utility - go through the supplied list of nodes and fail them (see
    _fail_nodes()).  Also, move the upgrade progress on to the next
    step.

    """
    # First, fail the nodes as appropriate
    _fail_nodes(upgrade_session, upgrade_progress, xnames, reason)

    # Now, move on to the next step. Maybe we will be luckier with
    # that one...
    upgrade_progress.completed_nodes = []
    upgrade_progress.step += 1
    upgrade_progress.stage = STARTING
    upgrade_progress.put()


def _update_starting(upgrade_session, upgrade_progress, step_nodes):
    """Start a rolling upgrade step by requesting that all nodes begin
    quiescing in the WLM (e.g. DRAIN in slurm).

    """
    step = upgrade_progress.step
    failed_nodegroup = NodeGroup(upgrade_session.failed_label)
    members = failed_nodegroup.get_members()
    if step == 0 and members != []:
        # Make sure the Failed node group is empty before we start so
        # we can use the group to indicate recent failures.
        for xname in members:
            failed_nodegroup.remove_member(xname)
        return "Cleared node group '%s'" % upgrade_session.failed_label

    if not step_nodes:
        # We are starting a new step and there are no nodes in this
        # step, so we are actually done with all the steps.  Move to
        # cleanup...
        upgrade_progress.stage = CLEANUP
        upgrade_progress.put()
        # Return a message to post in the upgrade session which will
        # cause a new watch event and drop to cleanup handling.
        return "No nodes in step %d: moving to CLEANUP" % step

    # Have some nodes, start quiescing them...
    wlm = get_wlm_handler(upgrade_session.workload_manager_type)
    for xname in step_nodes:
        wlm.quiesce(xname)
    upgrade_progress.stage = QUIESCING
    upgrade_progress.put()
    # Return a message to post in the upgrade session which will cause
    # a new watch event and and drop to the quiescing stage.
    return "Quiesce requested in step %d: moving to QUIESCING" % step


def _update_quiescing(upgrade_session, upgrade_progress, step_nodes):
    """The nodes are in the process of quiescing in the WLM, wait for them
    all to reach a quiesced state (e.g. IDLE+DRAIN in slurm).

    """
    # Wait until we see all of the nodes quiet, then we can advance to
    # BOOTING.  There might be some optimization possible here if we
    # moved nodes on to BOOTING as they quiesce, but this keeps things
    # simple for now.
    step = upgrade_progress.step
    wlm = get_wlm_handler(upgrade_session.workload_manager_type)
    for xname in step_nodes:
        if not wlm.is_quiet(xname):
            # At least one node is not quiet yet, return None to
            # request a pause and retry.
            return None
    # We got through them all, so they are all quiesced.  Move to
    # QUIESCED.
    upgrade_progress.stage = QUIESCED
    upgrade_progress.put()
    # Return a message to post with the upgrade session which will
    # cause an immediate watch event and drop to the quiesced stage.
    return "All nodes quiesced in step %d: moving to QUIESCED" % step


def _update_quiesced(upgrade_session, upgrade_progress, step_nodes):
    """All nodes are quiesced in the WLM, set up and run the boot session.

    """
    # Now install the nodes in the upgrading node group...
    step = upgrade_progress.step
    upgrading_node_group = NodeGroup(upgrade_session.upgrading_label)

    # First, clear out whatever might have been there before...
    members = upgrading_node_group.get_members()
    for xname in members:
        upgrading_node_group.remove_member(xname)
    # Now add the ones we want.
    for xname in step_nodes:
        upgrading_node_group.add_member(xname)

    # And initiate a boot session to boot into the upgrade.
    boot_session = BootSession(upgrade_session.upgrade_id)
    boot_session.boot(upgrade_session.upgrade_template_id, upgrade_session.upgrading_label)
    upgrade_progress.stage = BOOTING
    upgrade_progress.put()
    # Return a message to post with the upgrade session which will
    # cause an immediate watch event and drop to the booting stage.
    return "Began the boot session for step %d: moving to BOOTING" % step


# pylint: disable=unused-argument
def _update_booting(upgrade_session, upgrade_progress, step_nodes):
    """Wait for the boot session to complete, either successfully or not,
    then move on to check success.

    """
    step = upgrade_progress.step
    # Check whether the boot session has completed yet.  If not, stay
    # in this state and schedule a retry.
    boot_session = BootSession(upgrade_session.upgrade_id)
    booting = boot_session.booting()
    assert booting is not None  # programming error if we get None
    if booting:
        # Still booting, return None to request a pause and retry.
        return None
    # No longer booting, this means we booted...  Move to BOOTED.
    upgrade_progress.stage = BOOTED
    upgrade_progress.put()
    # Return a message to be posted to the upgrade session which will
    # cause an immediate watch event and drop to the BOOTED stage.
    return "The boot session for step %d completed: moving to BOOTED" % step


def _update_booted(upgrade_session, upgrade_progress, step_nodes):
    """The boot session has completed, check its success or failure and
    take appropriate action, then start waiting for the nodes to come
    back in the WLM.

    """
    step = upgrade_progress.step
    boot_session = BootSession(upgrade_session.upgrade_id)
    success = boot_session.success()
    assert success is not None  # programming error if we get None
    if success:
        # All is well, the boot session finished successfully.  This
        # should mean the nodes are coming back to life in the
        # WLM. Move to WLM_WAITING.
        upgrade_progress.stage = WLM_WAITING
        upgrade_progress.boot_complete_time = time.time()
        upgrade_progress.completed_nodes = []
        upgrade_progress.put()
        # Return a message to post to the upgrade session which will
        # cause an immediate watch event and drop to the WLM_WAITING
        # stage.
        return "Step %d boot session succeeded: moving to WLM_WAITING" % step

    # The boot session seems to have failed, so we can't make any
    # guesses about the nodes.  Fail all of the nodes in this step,
    # advance the step and go back to STARTING.
    _fail_nodes_and_step(upgrade_session, upgrade_progress, step_nodes,
                         "upgrading-boot-session-failed")
    # Return a message to be posted to the upgrade session which will
    # cause an immediate watch event and drop to the STARTING stage.
    return "The boot session for step %d failed: marking the nodes " \
        "as failed, advancing to step %d and moving to STARTING" % (
            step,
            step + 1
        )


def _update_wlm_waiting(upgrade_session, upgrade_progress, step_nodes):
    """Wait for nodes to reach a 'Ready' state of some kind in the WLM.

    """
    # Check whether we have timed out waiting for the nodes to come
    # back to life under WLM.
    step = upgrade_progress.step
    wlm = get_wlm_handler(upgrade_session.workload_manager_type)
    elapsed = time.time() - upgrade_progress.boot_complete_time
    if elapsed > WLM_WAIT_TIMEOUT:
        # Ran out of time waiting for the remaining nodes in the
        # waiting nodes list.  Move them to failed, advance the step
        # and go back to STARTING.
        _fail_nodes_and_step(upgrade_session, upgrade_progress, step_nodes,
                             "upgrading-time-out-wlm-waiting")
        # Return a message to be posted to the upgrade session which
        # will cause an immediate watch event and drop to the STARTING
        # stage.
        return "Waiting for WLM nodes timed out in step %d: marking " \
            "remaining nodes as failed, advancing to step %d and " \
            "moving to STARTING" % (step, step + 1)

    # Check on any nodes we are waiting for and, if any of them are
    # back to normal, then add them to the completed_nodes list.
    check_nodes = [xname for xname in step_nodes
                   if xname not in upgrade_progress.completed_nodes]
    if check_nodes:
        for xname in check_nodes:
            if wlm.is_ready(xname):
                # This one is ready, resume it and remove it.
                #
                # NOTE: want to do some more sanity checking here
                # to ensure that we don't get false positives for
                # nodes that never reboot.  The best way to do
                # that would be to check that the WLM start time
                # for the node is newer than it was when we
                # started with it.
                wlm.resume(xname)
                upgrade_progress.completed_nodes.append(xname)
        upgrade_progress.put()
        return "Examined nodes %s for WLM completion" % str(check_nodes)

    # We are out of nodes to wait for.  So, we are done and it all seems
    # to have worked.  Move to the next step.
    upgrade_progress.completed_nodes = []
    upgrade_progress.step += 1
    upgrade_progress.stage = STARTING
    upgrade_progress.put()
    # Return a message to be posted to the upgrade session which
    # will cause an immediate watch event and drop to the STARTING
    # stage.
    return "All WLM returned to ready in step %d: advancing to " \
        "step %d and moving to STARTING" % (step, step + 1)


# pylint: disable=unused-argument
def _cleanup(upgrade_session, upgrade_progress, step_nodes):
    """Clean up after a completed upgrade session (either deleting or
    upgrading)

    """
    # Done with the upgrade, clean everything up.
    upgrading_node_group = NodeGroup(upgrade_session.upgrading_label)
    members = upgrading_node_group.get_members()
    for xname in members:
        upgrading_node_group.remove_member(xname)
    boot_session = BootSession(upgrade_session.upgrade_id)
    boot_session.cleanup()
    upgrade_session.completed = True
    if upgrade_session.state == UPDATING:
        upgrade_session.set_ready()
    elif upgrade_session.state == DELETING:
        upgrade_session.remove()
    upgrade_progress.remove()
    # Return a message to avoid scheduling an update, no further watch
    # events will actually come of this because we have set READY and
    # also set completed on the upgrade_session.
    return "Upgrade Session Completed"


def _delete_before_finished(upgrade_session, upgrade_progress):
    """Move unfinished nodes to Failed when we delete a session before
    finishing.

    """
    step = upgrade_progress.step
    starting_node_group = NodeGroup(upgrade_session.starting_label)
    upgrade_nodes = starting_node_group.get_members()
    first = step * upgrade_session.upgrade_step_size
    last = len(upgrade_nodes)
    nodes = upgrade_nodes[first:last]
    # Move all nodes that haven't already finished upgrading to Failed
    # with a reason indicating that the session was deleted before it
    # completed.
    _fail_nodes(upgrade_session, upgrade_progress, nodes,
                "upgrade-session-deleted-before-completion")

    upgrade_progress.completed_nodes = []
    upgrade_progress.stage = CLEANUP
    upgrade_progress.put()
    return "Upgrade session deleted before completion: moving to cleanup"


def _delete_before_booting(upgrade_session, upgrade_progress, step_nodes):
    """Handle deleting in anything before entering the booting

    """
    if upgrade_session.completed:
        # This is a completed session, just move it to cleanup for
        # removal.
        upgrade_progress.stage = CLEANUP
        upgrade_progress.put()
        return "Deleting after completed: move to CLEANUP for removal"
    step = upgrade_progress.step
    wlm = get_wlm_handler(upgrade_session.workload_manager_type)
    if step == 0:
        # This is a session that never really got started, just resume
        # any quiescing nodes and move them to cleanup for removal.
        for xname in step_nodes:
            wlm.resume(xname)
        upgrade_progress.stage = CLEANUP
        upgrade_progress.put()
        return "Deleting before any updates: move to CLEANUP for removal"

    # Now it gets interesting.  We are deleting after having gotten
    # through step 0.  That means some nodes are upgraded and others
    # are not.  We want to move the ones that have not yet gotten
    # there to Failed and then go to cleanup, leaving the ones that
    # have succeeded alone.
    return _delete_before_finished(upgrade_session, upgrade_progress)


def _delete_after_booting(upgrade_session, upgrade_progress, step_nodes):
    """Handle deleting in anything except cleanup after entering the
    booting stage.

    """
    # All nodes are tainted by the upgrade process at this point, so
    # move anything that has not completed to Failed and go to
    # cleanup.
    return _delete_before_finished(upgrade_session, upgrade_progress)


# Stage handler function mappings
UPDATE_MAP = {
    STARTING: _update_starting,
    QUIESCING: _update_quiescing,
    QUIESCED: _update_quiesced,
    BOOTING: _update_booting,
    BOOTED: _update_booted,
    WLM_WAITING: _update_wlm_waiting,
    CLEANUP: _cleanup,
}

DELETE_MAP = {
    STARTING: _delete_before_booting,
    QUIESCING: _delete_before_booting,
    QUIESCED: _delete_before_booting,
    BOOTING: _delete_after_booting,
    BOOTED: _delete_after_booting,
    WLM_WAITING: _delete_after_booting,
    CLEANUP: _cleanup,
}
