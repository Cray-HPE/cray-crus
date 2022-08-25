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
Tests for the Compute Upgrade Agent

"""
import time
import uuid
from etcd3_model import READY
from crus.controllers.upgrade_agent.upgrade_agent import (
    start_watching,
    process_upgrade
)
from crus import API_VERSION
from crus.controllers.mocking.kubernetes.client import inject_job_conditions
from crus.controllers.mocking.slurm.slurm_state import SlurmNodeTable
from crus.controllers.mocking.bss import BSSNodeTable
from crus.controllers.mocking.bos import BootTemplateTable
from crus.controllers.upgrade_agent.node_group import NodeGroup
from crus.controllers.upgrade_agent.errors import ComputeUpgradeError
from crus.controllers.upgrade_agent.node_table import NodeTable
from crus.models.upgrade_session import (
    UpgradeSession,
    ComputeUpgradeProgress,
    QUIESCED,
    BOOTING,
)


def test_import():
    """ Verify that compute upgrade imported as expected

    """
    help(NodeGroup)
    help(ComputeUpgradeError)
    help(NodeTable)
    help(SlurmNodeTable)
    help(BSSNodeTable)


def setup_nodes(success_nids, fail_nids):
    """ Get the xnames to be upgraded and set the ones that should fail to
    simulate failure.

    """
    success_xnames = [NodeTable.get_xname(nid + 1) for nid in success_nids]
    fail_xnames = [NodeTable.get_xname(nid + 1) for nid in fail_nids]
    for xname in fail_xnames:
        BSSNodeTable.fail_boot(xname)
    return success_xnames, fail_xnames


def restore_nodes(fail_xnames):
    """ Restore the specified nodes to passing boot in BSS.

    """
    for xname in fail_xnames:
        BSSNodeTable.pass_boot(xname)


def initiate_upgrade(xnames):
    """Kick off an upgrade session in which the specified set of xnames
    will be upgraded.

    """

    # Set up the upgrade parameters...
    params = {
        'kind': "ComputeUpgradeSession",
        'api_version': API_VERSION,
        'starting_label': "test-starting",
        'upgrading_label': "test-upgrading",
        'failed_label': "test-failed",
        'workload_manager_type': "slurm",
        'upgrade_step_size': 3,
        'upgrade_template_id': None,
    }
    # Create the starting node group with all of the nodes to be upgraded
    ng_data = {
        'label': params['starting_label'],
        'description': "Simple 10 element starting node group to test upgrade",
        'members': {'ids': xnames}
    }
    assert NodeGroup(ng_data['label'], ng_data)

    # Create the empty upgrading Node Group
    ng_data = {
        'label': params['upgrading_label'],
        'description': "Upgrading node group to test upgrade",
        'members': {'ids': []}
    }
    assert NodeGroup(ng_data['label'], ng_data)

    # Create a boot template based on the upgrading node group label
    template = BootTemplateTable.create(ng_data['label'])
    params['upgrade_template_id'] = template.template_id

    # Create the empty failed Node Group
    ng_data = {
        'label': params['failed_label'],
        'description': "Node group for failed nodes in test upgrade",
        'members': {'ids': []}
    }
    assert NodeGroup(ng_data['label'], ng_data)

    upgrade = UpgradeSession(params)  # Create a session in ETCD
    upgrade.put()  # and commit it to kick off the process
    return upgrade.upgrade_id


def arrived(upgrade, stage, step):
    """Determine whether the supplied session has arrived at either a
    completed state (if stage and step are None) or the requested
    stage / step.

    """
    if stage or step:
        progress = ComputeUpgradeProgress.get(upgrade.upgrade_id)
        if not progress:
            # no progress record yet for session, not there
            return False
        if step and step > progress.step:
            # caller requested a step and we aren't there yet
            return False
        if stage and stage != progress.stage:
            # caller requested a stage and we aren't there yet
            return False
        if not stage and (step + 1) > progress.step:
            # caller requested a step but no stage and we have not
            # reached the next step yet (so the requested step is
            # still completing)
            return False
    elif not upgrade.completed:
        # No step or stage requested, and we have not yet completed
        # the upgrade.
        return False
    return True


def wait_for_upgrade(upgrade_id, queue, pending, stage=None, step=None):
    """Wait for an upgrade to complete (if stage and step are None) or to
    reach the requested stage / step as described in run_upgrade().


    If 'stage' is specified, wait only until the specified
    stage is reached by the upgrade session.

    If 'step' is supplied wait either until the specified 'stage' of the
    specified step number (if 'stage' is supplied), or until the
    specified step number has completed (i.e. the session reaches
    the following step).
    """
    # Wait for the boot to complete...
    timeout = time.time() + 60
    while not arrived(UpgradeSession.get(upgrade_id), stage, step):
        assert time.time() < timeout
        process_upgrade(queue, pending)


def verify_failed_nodes(upgrade_id, fail_xnames):
    """Verify that failed nodes are in the right node group after the
    completion of an upgrade.

    """
    upgrade = UpgradeSession.get(upgrade_id)
    ng_name = upgrade.failed_label
    xname_list = fail_xnames
    print("checking the group '%s'" % ng_name)
    check_ng = NodeGroup(ng_name)
    members = check_ng.get_members()
    # Check that the length of the node group matches what is expected,
    # to eliminate the chance of missing duplicates in either list.
    if len(members) != len(xname_list):  # pragma unit test failure
        print("node group members = %s, expected = %s" % (str(members),
                                                          str(xname_list)))
        assert False
    # Check for strays
    for xname in members:
        assert xname in xname_list
    # Check for missing
    for xname in xname_list:
        assert xname in members


def delete_upgrade(upgrade_id, queue, pending):
    """Set an upgrade_session to deleting and watch it be deleted.  Also
    clean up the node groups associated with the session.

    """
    # Get the upgrade session information and node group labels
    upgrade = UpgradeSession.get(upgrade_id)
    starting_label = upgrade.starting_label
    upgrading_label = upgrade.upgrading_label
    failed_label = upgrade.failed_label

    # Do the delete and wait for it to complete
    upgrade.delete()
    timeout = time.time() + 60
    while UpgradeSession.get(upgrade_id) is not None:
        assert time.time() < timeout
        process_upgrade(queue, pending)

    # Clean up
    starting_ng = NodeGroup(starting_label)
    starting_ng.delete()
    upgrading_ng = NodeGroup(upgrading_label)
    upgrading_ng.delete()
    failed_ng = NodeGroup(failed_label)
    failed_ng.delete()
    BootTemplateTable.delete(upgrade.upgrade_template_id)


def run_upgrade(success_nids, fail_nids):
    """Run a test in which some set of nodes are set to succeed the
    upgrade and others are set to fail the upgrade.  The list of
    (integer) nids in success_nids are expected to succeed, the list
    of (integer) nids in fail_nids are expected to fail and will be
    set up to fail before the upgrade completes.

    Returns None if the session runs to completion and is cleaned up.
    Returns an Upgrade ID (UUID string) if the session is interrupted
    at a step or stage.

    """
    # Start the watcher if it is not already started...
    queue, pending = start_watching()

    # Get the xnames and set the failing nodes to fail in the upgrade
    success_xnames, fail_xnames = setup_nodes(success_nids, fail_nids)

    # Kick off an upgrade and get an upgrade ID
    upgrade_id = initiate_upgrade(success_xnames + fail_xnames)

    # Wait for the upgrade to complete.
    wait_for_upgrade(upgrade_id, queue, pending)

    # Now that we have completed the upgrade, restore the failing nodes
    # to passing again.
    restore_nodes(fail_xnames)

    # Check that the nodes that failed wound up in the failed node group.
    verify_failed_nodes(upgrade_id, fail_xnames)

    # Delete the upgrade session and verify that it gets deleted.
    # Also clean up node groups.
    delete_upgrade(upgrade_id, queue, pending)


def test_simple_upgrade():
    """Test that upgrading 10 nodes with no failures or active states works.

    """
    # Set up the nodes
    success_nids = [nid + 1 for nid in range(0, 10)]
    fail_nids = []
    run_upgrade(success_nids, fail_nids)


def test_simple_upgrade_with_learn():
    """Test that upgrading 10 nodes with no failures or active states
    works. Then cause the controller to re-learn the contents of the
    session before deleting it.  The latter should be a no-op, but
    exercises the learning code.

    """
    # Start the watcher if it is not already started...
    queue, pending = start_watching()

    # Set up the list of nodes to test.
    success_nids = [nid + 1 for nid in range(0, 10)]
    fail_nids = []

    # Get the xnames and set the failing nodes to fail in the upgrade
    success_xnames, fail_xnames = setup_nodes(success_nids, fail_nids)

    # Kick off an upgrade and get an upgrade ID
    upgrade_id = initiate_upgrade(success_xnames + fail_xnames)

    # Wait for the upgrade to complete or reach the designated step /
    # stage.
    wait_for_upgrade(upgrade_id, queue, pending)

    # Now that we have completed the upgrade, restore the failing nodes
    # to passing again.
    restore_nodes(fail_xnames)

    # Check that the nodes that failed wound up in the failed node group.
    verify_failed_nodes(upgrade_id, fail_xnames)

    # Trigger a learn cycle.
    UpgradeSession.learn()

    # Wait for the upgrade to complete.  Since it is already complete,
    # this should take exactly one cycle to absorb the already
    # complete upgrade session and move it to READY.
    count = 0
    timeout = time.time() + 60
    while UpgradeSession.get(upgrade_id).state != READY:
        assert time.time() < timeout
        process_upgrade(queue, pending)
        count += 1
    assert count == 1

    # Delete the upgrade session and verify that it gets deleted.
    # Also clean up node groups.
    delete_upgrade(upgrade_id, queue, pending)


def test_upgrade_half_fail():
    """Test that upgrading 20 nodes in which 10 fail and 10 succeed.

    """
    # Set up the nodes
    success_nids = [nid + 1 for nid in range(0, 10)]
    fail_nids = [nid + 1 for nid in range(10, 20)]
    run_upgrade(success_nids, fail_nids)


def test_upgrade_half_fail_some_busy():  # pylint: disable=invalid-name
    """Test that upgrading 40 nodes in which 10 fail and are idle to
    start, 10 fail and are busy to start and 10 succeed and are idle to
    start and 10 succeed and are busy to start.

    """
    # Set up the nodes
    idle_success_nids = [nid + 1 for nid in range(0, 10)]
    busy_success_nids = [nid + 1 for nid in range(10, 20)]
    idle_fail_nids = [nid + 1 for nid in range(20, 30)]
    busy_fail_nids = [nid + 1 for nid in range(30, 40)]

    # Run all of the busy nodes through 4 states to get to IDLE
    busy_names = [NodeTable.get_nidname(NodeTable.get_xname(nid))
                  for nid in busy_success_nids + busy_fail_nids]
    for name in busy_names:
        SlurmNodeTable.add_pending_state(name, "ALLOCATED")
        SlurmNodeTable.add_pending_state(name, "MIXED")
        SlurmNodeTable.add_pending_state(name, "COMPLETING")
        SlurmNodeTable.add_pending_state(name, "IDLE")

    # Run the test
    run_upgrade(idle_success_nids + busy_success_nids,
                idle_fail_nids + busy_fail_nids)


def test_upgrade_all_boot_sessions_fail():  # pylint: disable=invalid-name
    """Test an upgrade session in which the boot sessions fail.  Verify
    that all nodes get placed in the failed boot set.

    """
    # Start the watcher if it is not already started...
    queue, pending = start_watching()

    boot_fail_nids = [nid + 1 for nid in range(0, 20)]
    fail_nids = []
    # Get the xnames and set the failing nodes to fail in the upgrade
    boot_fail_xnames, fail_xnames = setup_nodes(boot_fail_nids, fail_nids)

    # Inject failures into the K8s jobs
    inject_job_conditions(
        [
            {'type': 'Complete', 'status': 'False'},
            {'type': 'Complete', 'status': 'False'},
            {'type': 'Failed', 'status': 'True'},
        ]
    )

    # Kick off an upgrade and get an upgrade ID
    upgrade_id = initiate_upgrade(boot_fail_xnames + fail_xnames)

    # Wait for the upgrade to complete.
    wait_for_upgrade(upgrade_id, queue, pending)

    # Now that we have completed the upgrade, restore the failing nodes
    # to passing again.
    restore_nodes(fail_xnames)

    # Check that the nodes that failed wound up in the failed node group.
    verify_failed_nodes(upgrade_id, boot_fail_xnames)

    # Delete the upgrade session and verify that it gets deleted.
    # Also clean up node groups.
    delete_upgrade(upgrade_id, queue, pending)
    inject_job_conditions(None)


def test_delete_before_booting():  # pylint: disable=invalid-name
    """Test that deleting a session that is underway and has not yet
    gotten to the booting stage works correctly.

    """
    # Start the watcher if it is not already started...
    queue, pending = start_watching()

    success_nids = [nid + 1 for nid in range(0, 20)]
    fail_nids = []
    # Get the xnames and set the failing nodes to fail in the upgrade
    success_xnames, fail_xnames = setup_nodes(success_nids, fail_nids)

    # Kick off an upgrade and get an upgrade ID
    upgrade_id = initiate_upgrade(success_xnames + fail_xnames)

    # Wait for the upgrade to complete or reach the designated step /
    # stage.
    wait_for_upgrade(upgrade_id, queue, pending, stage=QUIESCED)

    # Delete the upgrade session and verify that it gets deleted.
    # Also clean up node groups.
    delete_upgrade(upgrade_id, queue, pending)


def test_delete_before_booting_second_step():  # pylint: disable=invalid-name
    """Test that deleting a session that is underway and has not yet
    gotten to the booting stage works correctly.

    """
    # Start the watcher if it is not already started...
    queue, pending = start_watching()

    success_nids = [nid + 1 for nid in range(0, 20)]
    fail_nids = []
    # Get the xnames and set the failing nodes to fail in the upgrade
    success_xnames, fail_xnames = setup_nodes(success_nids, fail_nids)

    # Kick off an upgrade and get an upgrade ID
    upgrade_id = initiate_upgrade(success_xnames + fail_xnames)

    # Wait for the upgrade to complete or reach the designated step /
    # stage.
    wait_for_upgrade(upgrade_id, queue, pending, stage=QUIESCED, step=1)

    # Delete the upgrade session and verify that it gets deleted.
    # Also clean up node groups.
    delete_upgrade(upgrade_id, queue, pending)


def test_delete_after_second_step():  # pylint: disable=invalid-name
    """Test that deleting a session that is underway and has not yet
    gotten to the booting stage works correctly.

    """
    # Start the watcher if it is not already started...
    queue, pending = start_watching()

    success_nids = [nid + 1 for nid in range(0, 20)]
    fail_nids = []
    # Get the xnames and set the failing nodes to fail in the upgrade
    success_xnames, fail_xnames = setup_nodes(success_nids, fail_nids)

    # Kick off an upgrade and get an upgrade ID
    upgrade_id = initiate_upgrade(success_xnames + fail_xnames)

    # Wait for the upgrade to complete or reach the designated step /
    # stage.
    wait_for_upgrade(upgrade_id, queue, pending, step=1)

    # Delete the upgrade session and verify that it gets deleted.
    # Also clean up node groups.
    delete_upgrade(upgrade_id, queue, pending)


def test_delete_after_booting():  # pylint: disable=invalid-name
    """Test that deleting a session that is underway but has gotten to the
    booting stage works correctly.

    """
    # Start the watcher if it is not already started...
    queue, pending = start_watching()

    success_nids = [nid + 1 for nid in range(0, 20)]
    fail_nids = []
    # Get the xnames and set the failing nodes to fail in the upgrade
    success_xnames, fail_xnames = setup_nodes(success_nids, fail_nids)

    # Kick off an upgrade and get an upgrade ID
    upgrade_id = initiate_upgrade(success_xnames + fail_xnames)

    # Wait for the upgrade to complete or reach the designated step /
    # stage.
    wait_for_upgrade(upgrade_id, queue, pending, stage=BOOTING)

    # Delete the upgrade session and verify that it gets deleted.
    # Also clean up node groups.
    delete_upgrade(upgrade_id, queue, pending)


def test_upgrade_non_empty_failed_group():  # pylint: disable=invalid-name
    """Test that an upgrade that starts with a non-empty 'failed' node
    group runs correctly to completion.

    """
    # Start the watcher if it is not already started...
    queue, pending = start_watching()

    # Get the xnames and set the failing nodes to fail in the upgrade
    success_nids = [nid + 1 for nid in range(0, 20)]
    fail_nids = []
    success_xnames, fail_xnames = setup_nodes(success_nids, fail_nids)
    xnames = success_xnames + fail_xnames

    # Build and kick off an upgrade that has a non-empty 'failed' node group
    #
    # Set up the upgrade parameters...
    params = {
        'kind': "ComputeUpgradeSession",
        'api_version': API_VERSION,
        'starting_label': "test-starting",
        'upgrading_label': "test-upgrading",
        'failed_label': "test-failed",
        'workload_manager_type': "slurm",
        'upgrade_step_size': 3,
        'upgrade_template_id': str(uuid.uuid4())
    }
    # Create the starting node group with all of the nodes to be upgraded
    ng_data = {
        'label': params['starting_label'],
        'description': "Simple 10 element starting node group to test upgrade",
        'members': {'ids': xnames}
    }
    assert NodeGroup(ng_data['label'], ng_data)

    # Create the empty upgrading Node Group
    ng_data = {
        'label': params['upgrading_label'],
        'description': "Upgrading node group to test upgrade",
        'members': {'ids': []}
    }
    assert NodeGroup(ng_data['label'], ng_data)

    # Create the non-empty failed Node Group
    ng_data = {
        'label': params['failed_label'],
        'description': "Node group for failed nodes in test upgrade",
        'members': {'ids': xnames}
    }
    assert NodeGroup(ng_data['label'], ng_data)

    upgrade = UpgradeSession(params)  # Create a session in ETCD
    upgrade.put()  # and commit it to kick off the process
    upgrade_id = upgrade.upgrade_id

    # Wait for the upgrade to complete or reach the designated step /
    # stage.
    wait_for_upgrade(upgrade_id, queue, pending)

    # Now that we have completed the upgrade, restore the failing nodes
    # to passing again.
    restore_nodes(fail_xnames)

    # Check that the nodes that failed wound up in the failed node group.
    verify_failed_nodes(upgrade_id, fail_xnames)

    # Delete the upgrade session and verify that it gets deleted.
    # Also clean up node groups.
    delete_upgrade(upgrade_id, queue, pending)


def test_upgrade_non_empty_upgrading_group():  # pylint: disable=invalid-name
    """Test that an upgrade that starts with a non-empty 'upgrading' node
    group runs correctly to completion.

    """
    # Start the watcher if it is not already started...
    queue, pending = start_watching()

    # Get the xnames and set the failing nodes to fail in the upgrade
    success_nids = [nid + 1 for nid in range(0, 20)]
    fail_nids = []
    success_xnames, fail_xnames = setup_nodes(success_nids, fail_nids)
    xnames = success_xnames + fail_xnames

    # Build and kick off an upgrade that has a non-empty 'upgrading' node group
    #
    # Set up the upgrade parameters...
    params = {
        'kind': "ComputeUpgradeSession",
        'api_version': API_VERSION,
        'starting_label': "test-starting",
        'upgrading_label': "test-upgrading",
        'failed_label': "test-failed",
        'workload_manager_type': "slurm",
        'upgrade_step_size': 3,
        'upgrade_template_id': str(uuid.uuid4())
    }
    # Create the starting node group with all of the nodes to be upgraded
    ng_data = {
        'label': params['starting_label'],
        'description': "Simple 10 element starting node group to test upgrade",
        'members': {'ids': xnames}
    }
    assert NodeGroup(ng_data['label'], ng_data)

    # Create the non-empty upgrading Node Group
    ng_data = {
        'label': params['upgrading_label'],
        'description': "Upgrading node group to test upgrade",
        'members': {'ids': xnames}
    }
    assert NodeGroup(ng_data['label'], ng_data)

    # Create the empty failed Node Group
    ng_data = {
        'label': params['failed_label'],
        'description': "Node group for failed nodes in test upgrade",
        'members': {'ids': []}
    }
    assert NodeGroup(ng_data['label'], ng_data)

    upgrade = UpgradeSession(params)  # Create a session in ETCD
    upgrade.put()  # and commit it to kick off the process
    upgrade_id = upgrade.upgrade_id

    # Wait for the upgrade to complete or reach the designated step /
    # stage.
    wait_for_upgrade(upgrade_id, queue, pending)

    # Now that we have completed the upgrade, restore the failing nodes
    # to passing again.
    restore_nodes(fail_xnames)

    # Check that the nodes that failed wound up in the failed node group.
    verify_failed_nodes(upgrade_id, fail_xnames)

    # Delete the upgrade session and verify that it gets deleted.
    # Also clean up node groups.
    delete_upgrade(upgrade_id, queue, pending)
