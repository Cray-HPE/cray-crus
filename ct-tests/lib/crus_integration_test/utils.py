# Copyright 2020 Hewlett Packard Enterprise Development LP

"""
CRUS integration test helper functions that involve multiple services
"""

from common.bos import describe_bos_session, describe_bos_session_status, list_bos_sessions, \
                       perform_bos_session
from common.capmc import get_capmc_node_status
from common.crus import describe_crus_session
from common.hsm import list_hsm_group_members
from common.helpers import any_dict_value, debug, error, get_bool_field_from_obj, \
                           get_field_from_obj, get_list_field_from_obj, \
                           get_str_field_from_obj, info, raise_test_error, sleep
from common.utils import ssh_command_passes_on_xname, is_xname_pingable
import time

def verify_node_states(use_api, xname_template_map, template_objects, xname_to_nid):
    """
    Verify that all nodes look like they are booted using the correct BOS session template.
    """
    def get_kernel_parameters(bst):
        # We know our test templates only have a single bootset
        bst_bootset = any_dict_value(bst["boot_sets"])
        return bst_bootset["kernel_parameters"]

    show_kernel_cmd = "dmesg | grep 'Kernel command line:'"
    def kernel_parameters_okay(xn, bst):
        boot_verification_cmd = "dmesg | grep -q '%s'" % get_kernel_parameters(bst)
        if ssh_command_passes_on_xname(xn, boot_verification_cmd):
            debug("%s appears to be booted using the expected kernel parameters" % xn)
            return True
        error("%s appears to have the wrong kernel parameters" % xn)
        ssh_command_passes_on_xname(xn, show_kernel_cmd)
        return False

    show_motd_cmd = "tail -1 /etc/motd"
    def motd_okay(xn, tname):
        motd_verification_cmd = "tail -1 /etc/motd | grep -q 'branch=%s$'" % tname
        if ssh_command_passes_on_xname(xn, motd_verification_cmd):
            debug("%s appears to be configured as we expected" % xn)
            return True
        error("%s is not configured as we expected, based on its motd" % xn)
        ssh_command_passes_on_xname(xn, show_motd_cmd)
        return False

    error_map = dict()
    def nid_error(nid, errmsg):
        try:
            error_map[errmsg].append(str(nid))
        except KeyError:
            error_map[errmsg] = [str(nid)]
    nid_to_capmc_status = get_capmc_node_status(use_api=use_api, nids=list(xname_to_nid.values()))
    for xname, nid in xname_to_nid.items():
        power_ping_ok=True
        if nid_to_capmc_status[nid] != "on":
            nid_error(nid, "CAPMC state is %s not on" % nid_to_capmc_status[nid])
            power_ping_ok=False
        if not is_xname_pingable(xname):
            nid_error(nid, "Not pingable")
            power_ping_ok=False
        if not power_ping_ok:
            continue
        elif not ssh_command_passes_on_xname(xname, "date"):
            nid_error(nid, "Unable to reach via ssh")
            continue
        tname = xname_template_map[xname]
        debug("Expected BOS session template for nid %d (xname %s) is %s" % (nid, xname, tname))
        bst = template_objects[tname]
        if not kernel_parameters_okay(xname, bst):
            nid_error(nid, "Unexpected kernel parameters")
        if not motd_okay(xname, tname):
            nid_error(nid, "Unexpected CFS configuration")
    if error_map:
        for errmsg, nidlist in error_map.items():
            error("%s: %s" % (errmsg, ", ".join(nidlist)))
        raise_test_error("At least one error found when verifying node statuses and configurations")

def bos_reboot_nodes(use_api, template_objects, template_name, xname_to_nid, xname_template_map):
    """
    Perform a BOS session reboot operation on the target nodes and verify that this results in the state we expect.
    """
    perform_bos_session(use_api, template_name, "reboot")
    for x in xname_to_nid.keys():
        xname_template_map[x] = template_name
    verify_node_states(use_api, xname_template_map, template_objects, xname_to_nid)
    info("Target node(s) have been rebooted as requested")

# Workaround for CASMCMS-5740
_bos_in_progress_value_map = {
    "": False,
    None: False,
    False: False,
    True: True }
def _get_bos_session_in_progress(bos_session_info):
    """
    Returns the in_progress field from the specified
    BOS session object
    """
    in_progress = get_field_from_obj(bos_session_info, "in_progress", noun="BOS session response object",
                                     null_okay=True)
    try:
        return _bos_in_progress_value_map[in_progress]
    except KeyError:
        raise_test_error("Invalid value for in_progress field: %s (type %s)" % (
                         str(in_progress), str(type(in_progress))))

def monitor_crus_session(use_api, upgrade_id, expected_values, bos_sessions, timeout=45*60, sleeptime=30):
    """
    Wait until the specified CRUS session has completed set to True, or until
    we time out. The sleeptime is how long between checks of the CRUS session status.
    As the session runs, check for new BOS sessions which appear to be from this CRUS session,
    and periodically monitor contents of relevant HSM groups.
    bos_sessions is a list of BOS sessions which existed prior to the start of the CRUS session.
    Units for both timeout and sleeptime is seconds.
    """
    info("Monitoring CRUS session %s until it completes" % upgrade_id)
    stoptime = time.time() + timeout
    errors_found = False
    bos_noun = "BOS session response object"
    myargs = { "noun": "CRUS session response", "null_okay": False }
    previous_bos_sessions = list(bos_sessions)
    upgrading_group = expected_values["upgrading_label"]
    template_name = expected_values["upgrade_template_id"]
    our_bos_sessions = dict()
    our_bos_status = dict()
    while True:
        response_object = describe_crus_session(use_api=use_api, upgrade_id=upgrade_id, 
                                                expected_values=expected_values)
        messages = get_list_field_from_obj(response_object, "messages", member_type=str, **myargs)
        completed = get_bool_field_from_obj(response_object, "completed", **myargs)
        debug("completed=%s" % str(completed))
        for m in messages:
            debug("message: %s" % m, timestamp=False)
        gmembers = list_hsm_group_members(use_api, upgrading_group)
        debug("%s HSM group members: %s" % (upgrading_group, ", ".join(gmembers)))
        current_bos_sessions = list_bos_sessions(use_api)
        new_bos_sessions = [ bsid for bsid in current_bos_sessions if bsid not in previous_bos_sessions ]
        if new_bos_sessions:
            debug("New BOS sessions: %s" % ", ".join(new_bos_sessions))
        else:
            debug("No new BOS sessions found")
        previous_bos_sessions.extend(new_bos_sessions)
        for bsid in new_bos_sessions:
            bos_session_info = describe_bos_session(use_api, bsid)
            bstemplate = get_str_field_from_obj(bos_session_info, "templateUuid", 
                                                noun=bos_noun, min_length=1)
            debug("BOS session ID %s template = %s" % (bsid, bstemplate))
            if bstemplate != template_name:
                continue
            operation = get_str_field_from_obj(bos_session_info, "operation", 
                                               noun=bos_noun, min_length=1)
            debug("BOS session ID %s operation = %s" % (bsid, operation))
            if operation != "reboot":
                continue
            debug("NEW candidate BOS session: %s" % bsid)
            our_bos_sessions[bsid] = bos_session_info
        for bsid, bos_session_info in our_bos_sessions.items():
            # Workaround for CASMCMS-5740
            #in_progress = get_bool_field_from_obj(bos_session_info, "in_progress", noun=bos_noun,
            #                                      null_okay=False)
            in_progress = _get_bos_session_in_progress(bos_session_info)
            if bsid in new_bos_sessions and in_progress:
                continue
            new_session_info = describe_bos_session(use_api, bsid)
            if new_session_info == bos_session_info:
                continue
            debug("BOS session info CHANGED for %s" % bsid)
            our_bos_sessions[bsid] = new_session_info
        for bsid, bos_session_info in our_bos_sessions.items():
            # Workaround for CASMCMS-5740
            #in_progress = get_bool_field_from_obj(bos_session_info, "in_progress", noun=bos_noun,
            #                                      null_okay=False)
            in_progress = _get_bos_session_in_progress(bos_session_info)
            if not in_progress:
                # cannot check status until they are in progress
                continue
            bsstatus = describe_bos_session_status(use_api, bsid)
            try:
                if bsstatus != our_bos_status[bsid]:
                    debug("BOS session status CHANGED for %s" % bsid)                    
            except KeyError:
                debug("NEW BOS session status for %s" % bsid)
            our_bos_status[bsid] = bsstatus
            bootsets = get_list_field_from_obj(bsstatus, "boot_sets", 
                                               noun="BOS session status response object", 
                                               min_length=1, member_type=str)
            for bset in bootsets:
                bootset_status = describe_bos_session_status(use_api, bsid, bset)
                try:
                    if bootset_status != our_bos_status[(bsid, bset)]:
                        debug("BOS session status CHANGED for %s bootset %s" % (bsid, bset))
                except KeyError:
                    debug("NEW BOS session status for %s bootset %s" % (bsid, bset))
                our_bos_status[(bsid, bset)] = bootset_status
        if completed:
            break
        timeleft = stoptime - time.time()
        if timeleft <= 0:
            raise_test_error("Timeout: CRUS session %s not complete after %d seconds" % (upgrade_id, timeout))
        sleep(min(timeleft,sleeptime))
    info("CRUS session %s completed" % upgrade_id)

def verify_results_of_crus_session(use_api, xname_template_map, template_objects, xname_to_nid, target_xnames, 
                                   failed_label, starting_label, upgrading_label):
    """
    Verify the following:
    - The failed_label HSM group is empty
    - The upgrading_label HSM group is empty
    - The starting_label HSM group contains exactly the xnames in target_xnames list
    - Every test xname is booted and configured as expected, based on xname_template_map
    """
    errors_found=False
    debug("Failed HSM group %s should be empty unless nodes failed the upgrade process" % failed_label)
    failed_xnames = list_hsm_group_members(use_api, failed_label)
    if failed_xnames:
        error("Failed HSM group (%s) contains at least one xname: %s" % (failed_label, ", ".join(failed_xnames)))
        errors_found=True
    debug("Upgrading HSM group %s should always be empty after CRUS session is completed" % failed_label)
    upgrading_xnames = list_hsm_group_members(use_api, upgrading_label)
    if failed_xnames:
        error("Upgrading HSM group (%s) should be empty, but it contains at least one xname: %s" % (upgrading_label, ", ".join(upgrading_xnames)))
        errors_found=True
    debug("Starting HSM group (%s) should not be changed by the CRUS session" % starting_label)
    starting_xnames = sorted(list_hsm_group_members(use_api, starting_label))
    target_xnames.sort()
    if starting_xnames != target_xnames:
        info("Before the CRUS session, the starting HSM group (%s) contained the following xname(s): %s" % (
            starting_label, 
            ", ".join(target_xnames)))
        info("After the CRUS session, the starting HSM group (%s) contained the following xname(s): %s" % (
            starting_label, 
            ", ".join(starting_xnames)))
        error("Starting HSM group %s contained different xnames before and after the CRUS session" % starting_label)
        errors_found=True
    verify_node_states(use_api, xname_template_map, template_objects, xname_to_nid)
    info("Everything looks good after CRUS session")
