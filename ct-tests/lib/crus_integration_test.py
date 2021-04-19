#!/usr/bin/env python3
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

"""
CRUS integration test

See crus_integration_test/argparse.py for command line usage.

### SETUP ###
1 Generate map of xnames, nids, and hostnames for target nodes (by default, 
  all computes)
2 Validate they work with the specified min/max node and step values.
3 Lookup BOS session template
4 Create empty starting, upgrading, and failed HSM groups
5 Create new session template for all target nodes
6 Create new session templates for the upgrading group
7 Use BOS to reboot all target nodes to new BOS session template

### TEST 1 ###
8 Put 1 node into starting group
9 Create CRUS session
10 Verify all goes well & delete CRUS session

### TEST 2 ###
11 Move all nodes into starting group.
Repeat steps 9-10, with step size that results in at least 2 steps

### TEST 3 ###
12 Select 2 nodes
13 Start slurm workload on 1 of them
14 Create CRUS session
15 Verify that CRUS waits while the slurm workloads run
16 Stop the slurm workloads
17 Verify that all goes well & delete CRUS session

### RESTORE NODES ###
18 Create CRUS session to reboot all nodes to base slurm template
19 Verify that all goes well & delete CRUS session

### CLEANUP ###
20 Delete new templates
21 Delete custom vcs branches
22 Delete new hsm groups
"""

from crus_integration_test.argparse import parse_args
from crus_integration_test.crus import verify_crus_waiting_for_quiesce
from crus_integration_test.hsm import create_hsm_groups
from crus_integration_test.slurm import complete_slurm_job, start_slurm_job, \
                                        verify_initial_slurm_state
from crus_integration_test.utils import bos_reboot_nodes, create_bos_session_templates, \
                                        monitor_crus_session, \
                                        verify_results_of_crus_session
from common.bos import bos_session_template_validate_cfs, \
                       list_bos_session_templates, list_bos_sessions
from common.bosutils import delete_bos_session_templates, \
                            delete_cfs_configs, \
                            delete_hsm_groups, \
                            delete_vcs_repo_and_org
from common.cfs import describe_cfs_config
from common.crus import create_crus_session, delete_crus_session
from common.helpers import CMSTestError, create_tmpdir, debug, error_exit, exit_test, \
                           init_logger, info, log_exception_error, raise_test_exception_error, \
                           remove_tmpdir, section, subtest, warn
from common.hsm import set_hsm_group_members
from common.k8s import get_csm_private_key
from common.utils import get_compute_nids_xnames, validate_node_hostnames
from common.vcs import create_and_clone_vcs_repo
import random
import sys

TEST_NAME = "crus_integration_test"

def do_subtest(subtest_name, subtest_func, **subtest_kwargs):
    """
    Log that we are about to run a subtest with the specified name, then call the specified function
    with the specified arguments. Raise exception in case of an error.
    """
    subtest(subtest_name)
    try:
        return subtest_func(**subtest_kwargs)
    except CMSTestError:
        raise
    except Exception as e:
        raise_test_exception_error(e, "%s subtest" % subtest_name)

def do_test(test_variables):
    """
    Main test body. Execute each subtest in turn.
    """

    # =============================
    # =============================
    # SETUP
    # =============================
    # =============================
    use_api = test_variables["use_api"]

    if use_api:
        info("Using API")
    else:
        info("Using CLI")

    # We don't need the CSM private key until it comes time to ssh into the compute nodes, but we'd
    # rather know up front if this fails, to save time
    do_subtest("Get CSM private key (for later use to ssh to computes)", get_csm_private_key)

    nid_to_xname, xname_to_nid = do_subtest("Find compute nids & xnames", 
                                            get_compute_nids_xnames, use_api=use_api, 
                                            nids=test_variables["nids"],
                                            groups=test_variables["groups"],
                                            xnames=test_variables["xnames"],
                                            min_required=3)
    test_variables["nids"] = sorted(list(nid_to_xname.keys()))
    test_variables["xnames"] = sorted(list(nid_to_xname.values()))
    nids = test_variables["nids"]
    xnames = test_variables["xnames"]
    info("nids: %s" % str(nids))

    slurm_nid = random.choice(nids)
    slurm_xname = nid_to_xname[slurm_nid]
    test_nids = [ n for n in nids if n != slurm_nid ]
    test_xnames = [ x for x in xnames if x != slurm_xname ]

    debug("Slurm controller: nid %d (xname %s)" % (slurm_nid, slurm_xname))
    debug("Worker nodes:")
    for test_nid in sorted(test_nids):
        debug("  nid %d (xname %s)" % (test_nid, nid_to_xname[test_nid]))

    max_step_size = len(nids)
    if test_variables["max_step_size"]:
        max_step_size = min(max_step_size, test_variables["max_step_size"])

    do_subtest("Validate node hostnames", validate_node_hostnames, nid_to_xname=nid_to_xname)

    template_objects = do_subtest("List all BOS session templates", list_bos_session_templates, 
                                  use_api=use_api)

    info("BOS session template: %s" % test_variables["template"])
    if test_variables["template"] not in template_objects:
        error_exit("No BOS session template found with name %s" % test_variables["template"])
    else:
        slurm_template_name = test_variables["template"]

    cfs_config_name = do_subtest("Get CFS configuration name from %s BOS session template" % slurm_template_name, 
               bos_session_template_validate_cfs, bst=template_objects[slurm_template_name])
    info("CFS configuration name in %s is %s" % (slurm_template_name, cfs_config_name))
    test_variables["base_cfs_config_name"] = cfs_config_name

    do_subtest("Validate CFS configuration %s" % cfs_config_name, 
               describe_cfs_config, use_api=use_api, name=cfs_config_name)

    test_hsm_groups = test_variables["test_hsm_groups"]
    do_subtest("Create hsm groups", create_hsm_groups, use_api=use_api, test_hsm_groups=test_hsm_groups)

    tmpdir = do_subtest("Create temporary directory", create_tmpdir)
    test_variables["tmpdir"] = tmpdir

    # Always want to make sure that we have a template which does not match any of the others
    # for both cfs branch and kernel parameters.
    num_test_templates = 3

    test_vcs_org = "crus-integration-test-org-%d" % random.randint(0,9999999)
    test_vcs_repo = "crus-integration-test-repo-%d" % random.randint(0,9999999)
    test_variables["test_vcs_org"] = test_vcs_org
    test_variables["test_vcs_repo"] = test_vcs_repo
    
    vcs_repo_dir = do_subtest("Create and clone VCS repo %s in org %s" % (test_vcs_repo, test_vcs_org),
                              create_and_clone_vcs_repo, orgname=test_vcs_org, reponame=test_vcs_repo, 
                              testname=TEST_NAME, tmpdir=tmpdir)
    test_variables["vcs_repo_dir"] = vcs_repo_dir

    do_subtest("Create modified BOS session templates", 
               create_bos_session_templates, 
               num_to_create=num_test_templates, 
               use_api=use_api, 
               template_objects=template_objects, 
               test_variables=test_variables,
               xname_to_nid=xname_to_nid)
    test_template_names = test_variables["test_template_names"]
    base_test_template, test_template1, test_template2 = test_template_names
    debug("Base test template: %s" % base_test_template)
    debug("Test template 1: %s" % test_template1)
    debug("Test template 2: %s" % test_template2)

    # Use BOS to reboot all target nodes to new BOS session template
    xname_template_map = dict()
    do_subtest("Reboot all target nodes to %s template" % base_test_template, bos_reboot_nodes, 
               template_name=base_test_template, use_api=use_api, template_objects=template_objects,
               xname_to_nid=xname_to_nid, xname_template_map=xname_template_map)

    # Verify slurm reports all test nodes as ready
    do_subtest("Verify slurm reports test nodes as ready", verify_initial_slurm_state,
               use_api=use_api, slurm_control_xname=slurm_xname, worker_xnames=test_xnames,
               xname_to_nid=xname_to_nid)

    crus_session_hsm_groups = {
        "failed_label": test_hsm_groups["failed"],
        "starting_label": test_hsm_groups["starting"],
        "upgrading_label": test_hsm_groups["upgrading"] }

    def _set_starting_group(target_xnames):
        """
        Wrapper to call common.hsm.set_hsm_group_members to set our starting
        group's member list to equal the specified xnames
        """
        group_name = crus_session_hsm_groups["starting_label"]
        node_text = ", ".join(sorted(target_xnames))
        if len(target_xnames) > 5:
            info("Setting HSM group %s member list to: %s" % (group_name, node_text))
            subtest_text = "Setting HSM group %s member list to %d test nodes" % (group_name, len(target_xnames))
        else:
            subtest_text = "Setting HSM group %s member list to: %s" % (group_name, node_text)

        do_subtest(subtest_text, set_hsm_group_members, use_api=use_api, group_name=group_name, xname_list=target_xnames)

    def _create_crus_session(target_xnames, step_size, template_name):
        """
        First, makes a list of all current BOS sessions.
        Then creates a CRUS session with the specified values.
        The target_xnames list is just used for test logging purposes, to
        describe the CRUS session.
        Returns the session_id of the CRUS session, a 
        dictionary of the CRUS session values, and the collected
        BOS session list.
        """
        bos_sessions = do_subtest("Getting list of BOS sessions before CRUS session is running", 
                                  list_bos_sessions, use_api=use_api)
        info("BOS session list: %s" % ", ".join(bos_sessions))
        node_text = ", ".join(sorted(target_xnames))
        if len(target_xnames) > 5:
            info("Creating CRUS session with target nodes: %s" % node_text)
            node_text = "%d test nodes" % len(target_xnames)
        subtest_text = "Create CRUS session (template: %s, step size: %d, nodes: %s)" % (template_name, step_size, node_text)
        crus_session_values = {
            "use_api": use_api,
            "upgrade_step_size": step_size,
            "upgrade_template_id": template_name }
        crus_session_values.update(crus_session_hsm_groups)
        response_object = do_subtest(subtest_text, create_crus_session, **crus_session_values)
        crus_session_id = response_object["upgrade_id"]
        return crus_session_id, crus_session_values, bos_sessions

    def _wait_verify_delete_crus_session(crus_session_id, crus_session_values, target_xnames, bos_sessions):
        """
        Wait for CRUS session to be complete.
        Update the xname_template_map to reflect the new expected template for the nodes in the session.
        Verify that the CRUS session results look okay.
        Delete the CRUS session.
        """
        do_subtest("Wait for CRUS session %s to complete" % crus_session_id, monitor_crus_session,
                   use_api=use_api, upgrade_id=crus_session_id, expected_values=crus_session_values,
                   bos_sessions=bos_sessions)
        # Set new expected template for target xnames
        for xn in target_xnames:
            xname_template_map[xn] = crus_session_values["upgrade_template_id"]
        do_subtest("Verify results of CRUS session %s" % crus_session_id, verify_results_of_crus_session,
               use_api=use_api, xname_template_map=xname_template_map, template_objects=template_objects, 
               xname_to_nid=xname_to_nid, target_xnames=list(target_xnames), **crus_session_hsm_groups)
        do_subtest("Delete CRUS session %s" % crus_session_id, delete_crus_session, 
               use_api=use_api, upgrade_id=crus_session_id, max_wait_for_completion_seconds=300)

    # =============================
    # =============================
    # TEST 1
    # =============================
    # =============================

    # Randomly pick 1 xname
    xn = random.choice(test_xnames)
    target_xnames = [xn]
    # Put it into starting HSM group
    _set_starting_group(target_xnames)
    # Pick random step size (since we're only dealing with 1 node, it doesn't matter)
    ssize = random.randint(1, 10000)
    # Create CRUS session
    crus_session_id, crus_session_values, bos_sessions = _create_crus_session(target_xnames, ssize, test_template1)
    # Wait for it to finish, make sure everything looks good, and delete it
    _wait_verify_delete_crus_session(crus_session_id, crus_session_values, target_xnames, bos_sessions)

    # =============================
    # =============================
    # TEST 2
    # =============================
    # =============================

    # Set starting group to all test nodes
    target_xnames = test_xnames
    _set_starting_group(target_xnames)
    # Set step size such that we get at least 2 steps
    ssize = len(target_xnames) // 2
    if (len(target_xnames) % 2) != 0:
        ssize += 1
    ssize = min(ssize, max_step_size)
    # Create CRUS session
    crus_session_id, crus_session_values, bos_sessions = _create_crus_session(target_xnames, ssize, test_template2)
    # Wait for it to finish, make sure everything looks good, and delete it
    _wait_verify_delete_crus_session(crus_session_id, crus_session_values, target_xnames, bos_sessions)

    # =============================
    # =============================
    # TEST 3
    # =============================
    # =============================

    # Randomly select a node for the starting group
    xn = random.choice(test_xnames)
    target_xnames = [xn]
    _set_starting_group(target_xnames)
    # Pick random step size (since we're only dealing with 1 node, it doesn't matter)
    ssize = random.randint(1, 10000)
    # Start slurm workload on node
    slurm_job_id, slurm_job_stopfile = do_subtest("Start slurm workload on %s" % xn, start_slurm_job,
        slurm_control_xname=slurm_xname, worker_xname=xn, xname_to_nid=xname_to_nid, tmpdir=tmpdir)
    # Create CRUS session
    crus_session_id, crus_session_values, bos_sessions = _create_crus_session([xn], ssize, test_template1)
    # Verify that CRUS session is waiting for nodes to quiesce
    do_subtest("Verify CRUS session %s is waiting for nodes to quiesce" % crus_session_id,
               verify_crus_waiting_for_quiesce, use_api=use_api, crus_session_id=crus_session_id, 
                expected_values=crus_session_values)
    # Stop slurm workload on node
    do_subtest("Stop slurm workload on %s" % xn, complete_slurm_job,
        slurm_control_xname=slurm_xname, worker_xname=xn, 
        stopfile_name=slurm_job_stopfile, slurm_job_id=slurm_job_id)
    # Wait for CRUS session to finish, make sure everything looks good, and delete it
    _wait_verify_delete_crus_session(crus_session_id, crus_session_values, target_xnames, bos_sessions)

    # =============================
    # =============================
    # RESTORE NODES
    # =============================
    # =============================

    # Set starting group to all test nodes plus the node we've been using for slurm
    target_xnames = xnames
    _set_starting_group(target_xnames)
    # Create CRUS session
    crus_session_id, crus_session_values, bos_sessions = _create_crus_session(target_xnames, ssize, base_test_template)
    # Wait for it to finish, make sure everything looks good, and delete it
    _wait_verify_delete_crus_session(crus_session_id, crus_session_values, target_xnames, bos_sessions)

    # =============================
    # =============================
    # CLEANUP
    # =============================
    # =============================
    
    section("Cleaning up")

    do_subtest("Delete modified BOS session templates", delete_bos_session_templates, use_api=use_api, 
               template_names=test_template_names)

    do_subtest("Delete VCS repo and org", delete_vcs_repo_and_org, test_variables=test_variables)

    do_subtest("Delete CFS configurations", delete_cfs_configs, use_api=use_api, cfs_config_names=test_variables["test_cfs_config_names"])

    do_subtest("Delete hsm groups", delete_hsm_groups, use_api=use_api, group_map=test_hsm_groups)

    do_subtest("Remove temporary directory", remove_tmpdir, tmpdir=tmpdir)
    test_variables["tmpdir"] = None

    section("Test passed")

def test_wrapper():
    test_variables = { 
        "test_template_names": list(),
        "test_cfs_config_names": list(),
        "test_hsm_groups": dict(),
        "tmpdir": None,
        "test_vcs_org": None,
        "test_vcs_repo": None,
        "vcs_repo_dir": None }
    parse_args(test_variables)
    init_logger(test_name=TEST_NAME, verbose=test_variables["verbose"])
    info("Starting test")
    debug("Arguments: %s" % sys.argv[1:])
    debug("test_variables: %s" % str(test_variables))
    use_api = test_variables["use_api"]
    try:
        do_test(test_variables=test_variables)
    except Exception as e:
        # Adding this here to do cleanup when unexpected errors are hit (and to log those errors)
        msg = log_exception_error(e)
        
        section("Attempting cleanup before exiting in failure")
        try:
            test_template_names = test_variables["test_template_names"]
        except KeyError:
            test_template_names = None
        try:
            test_cfs_config_names = test_variables["test_cfs_config_names"]
        except KeyError:
            test_cfs_config_names = None
        try:
            test_hsm_groups = test_variables["test_hsm_groups"]
        except KeyError:
            test_hsm_groups = None
        try:
            tmpdir = test_variables["tmpdir"]
        except KeyError:
            tmpdir = None

        if test_template_names:
            info("Attempting to clean up test BOS session templates before exiting")
            delete_bos_session_templates(use_api=use_api, template_names=test_template_names, error_cleanup=True)

        if test_cfs_config_names:
            delete_cfs_configs(use_api=use_api, cfs_config_names=test_cfs_config_names, error_cleanup=True)

        delete_vcs_repo_and_org(test_variables=test_variables, error_cleanup=True)

        if test_hsm_groups:
            info("Attempting to clean up test HSM groups before exiting")
            delete_hsm_groups(use_api=use_api, group_map=test_hsm_groups, error_cleanup=True)

        if tmpdir != None:
            remove_tmpdir(tmpdir)

        section("Cleanup complete")
        error_exit(msg)

if __name__ == '__main__':
    test_wrapper()
    exit_test()