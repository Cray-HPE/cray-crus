# Copyright 2020 Hewlett Packard Enterprise Development LP

"""
slurm-related test helper functions
"""

from common.helpers import debug, error, info, raise_test_error, \
                           raise_test_exception_error, run_cmd_list, \
                           sleep
from common.utils import run_command_on_xname_via_ssh, scp_to_xname
import datetime
import os.path
import re
import tempfile
import time

# Our nodes in slurm are named nid######
# Examples:
# - nid000001
# Ranges of nodes can be specified with nid#####[#-#], nid####[##-##], nid###[###-###], nid##[####-####], nid#[#####-#####], nid[######-######]
# Examples:
# - nid0000[02-12]
# - nid[000003-000007]
# Inside brackets, commas can also be used to specify multiple ranges or nids.
# Examples:
# - nid0000[02-12,17,20-29]
# Commas can also be used outside brackets, to join any of the above together
# Examples:
# - nid000005,nid[000007-000010],nid0000[12-22,27,30-39]

# So inside of brackets, there can be a list or a single entry
# Each entry is either a single number, or a range of numbers
# Inside the brackets, every number will have the same number of digits
# Examples of entries:
# 1
# 05
# 11-17

# This is a map for the relevant RE for entries with 1 digit numbers,
# 2 digit numbers, etc, up to the maximum of 6 digit numbers
BRACKET_LIST_ENTRY_RE = {
    1: "[0-9](?:-[0-9])?",
    2: "[0-9]{2}(?:-[0-9]{2})?",
    3: "[0-9]{3}(?:-[0-9]{3})?",
    4: "[0-9]{4}(?:-[0-9]{4})?",
    5: "[0-9]{5}(?:-[0-9]{5})?",
    6: "[0-9]{6}(?:-[0-9]{6})?" }

# This is a map for RE for bracket lists of 1 digit numbers,
# 2 digit numbers, etc
BRACKET_LIST_RE = {
    n: "%s(?:,%s)*" % (BRACKET_LIST_ENTRY_RE[n], BRACKET_LIST_ENTRY_RE[n])
    for n in range(1,7)
}

BRACKET_LIST_RE_PROG = { n: re.compile("^%s$" % BRACKET_LIST_RE[n]) for n in BRACKET_LIST_RE.keys() }

# So at the top level, we can have a single node specification, or a list of them
# Each node specification will follow one of the following patterns:
# nid[6-digit bracket list pattern]
# nid#[5-digit bracket list pattern]
# ...
# nid#####[1-digit bracket list pattern]
# nid######

# This is a map for each node specification list entry RE, mapped from the number
# of digits the numbers in the brackets contain (0 in the case where there are 
# no brackets)
#
# We include capturing parenthesis around the numbers preceding the brackets (if any)
# and the contents of the brackets (if any), to help ourselves with later parsing
BRACKET_DIGITS_TO_NODE_SPEC_ENTRY_RE = {
    0: "nid([0-9]{6})",
    1: "nid([0-9]{5})\[(%s)]" % BRACKET_LIST_RE[1],
    2: "nid([0-9]{4})\[(%s)]" % BRACKET_LIST_RE[2],
    3: "nid([0-9]{3})\[(%s)]" % BRACKET_LIST_RE[3],
    4: "nid([0-9]{2})\[(%s)]" % BRACKET_LIST_RE[4],
    5: "nid([0-9])\[(%s)]" % BRACKET_LIST_RE[5],
    6: "nid\[(%s)]" % BRACKET_LIST_RE[6] }

BRACKET_DIGITS_TO_NODE_SPEC_ENTRY_RE_PROG = {
    n: re.compile("^%s$" % BRACKET_DIGITS_TO_NODE_SPEC_ENTRY_RE[n]) for n in BRACKET_DIGITS_TO_NODE_SPEC_ENTRY_RE.keys() }

# So the combined RE for all possible node specifications
NODE_SPEC_ENTRY_RE = "|".join( [ "(?:%s)" % BRACKET_DIGITS_TO_NODE_SPEC_ENTRY_RE[n] for n in range(0,7) ])

# Finally, this RE is for a node specification list, where each entry must
# match one of our node spec entry patterns
# We capture the first entry of the list to help us with later parsing
NODE_SPEC_LIST_RE = "(%s)(?:,%s)*" % (NODE_SPEC_ENTRY_RE, NODE_SPEC_ENTRY_RE)
NODE_SPEC_LIST_RE_PROG = re.compile("^%s$" % NODE_SPEC_LIST_RE)

def slurm_bracket_list_entry_to_nidlist(bracket_list_entry):
    """
    Takes the bracket_list_entry string and returns the list of NID numbers it corresponds to.
    The string will either be a nonnegative integer, or a nonnegative integer range.
    This function assumes the string has already been validated to match one of our REs.
    """
    dash_count = bracket_list_entry.count("-")
    if dash_count > 1:
        error("PROGRAMMING LOGIC ERROR: Our prior regular expression checking should have prevented us from hitting this")
        raise_test_error("Bracket list entry should contain 0-1 dashes, but this contains %d: %s" % (dash_count, bracket_list_entry))
    elif dash_count == 1:
        start_number_str, end_number_str = bracket_list_entry.split('-')
        try:
            start_number = int(start_number_str)
        except ValueError as e:
            error("PROGRAMMING LOGIC ERROR: Our prior regular expression checking should have prevented us from hitting this")
            raise_test_exception_error(e, "to parse first integer (%s) in range (%s)" % (start_number_str, bracket_list_entry))
        try:
            end_number = int(end_number_str)
        except ValueError as e:
            error("PROGRAMMING LOGIC ERROR: Our prior regular expression checking should have prevented us from hitting this")
            raise_test_exception_error(e, "to parse integer (%s) in range (%s)" % (end_number_str, bracket_list_entry))
        if start_number > end_number:
            # Our RE doesn't check for this
            raise_test_error("First number in range must be <= second number. Invalid range: %s" % bracket_list_entry)
        return list(range(start_number, end_number+1))
    # No dashes means it should just be a single nonnegative integer
    try:
        return [ int(bracket_list_entry) ]
    except ValueError as e:
        raise_test_exception_error(e, "to parse bracket list entry as integer (%s)" % bracket_list_entry)

def slurm_bracket_contents_to_nidlist(bracket_contents):
    """
    Takes the bracket_contents string and returns the list of NID numbers it corresponds to.
    The string will be a comma-separated list (possibly with only 1 entry). We will call a helper
    function to handle each entry in the list.
    This function assumes the string has already been validated to match one of our REs.
    """
    nid_list = list()
    for bracket_list_entry in bracket_contents.split(','):
        nid_list.extend( slurm_bracket_list_entry_to_nidlist(bracket_list_entry) )
    return nid_list

def slurm_list_entry_to_nidlist(node_spec_list_entry):
    """
    Takes the node_spec_list_entry string and returns the list of NID numbers it corresponds to.
    This function assumes the string has already been validated to match one of our REs.
    """
    # Let's examine the list entry, checking for the different possible number of digits the
    # numbers inside the brackets have (0-6)
    for n in range(0,7):
        m = BRACKET_DIGITS_TO_NODE_SPEC_ENTRY_RE_PROG[n].match(node_spec_list_entry)
        if not m:
            continue
        if n == 0:
            # The numbers inside the brackets have 0 digits, meaning
            # this list entry is just a single nid, without any brackets
            # e.g. nid000020
            # In this case, the matching group is just the nid number
            debug("Node spec list entry \"%s\" appears to be a single node" % node_spec_list_entry)
            nid_str = m.group(1)
            debug("Node spec list entry yields NID string \"%s\"" % nid_str)
            try:
                return [ int(nid_str) ]
            except ValueError as e:
                error("PROGRAMMING LOGIC ERROR: Our prior regular expression checking should have prevented us from hitting this")
                raise_test_exception_error(e, "to parse integer (%s) from node spec list entry (%s)" % (nid_str, node_spec_list_entry))
        elif n == 6:
            # This is an entry where the numbers inside the brackets have 6 digits, so there are no digits before the brackets.
            # e.g. nid[000300-000310,000555]
            # So we just parse the contents of the brackets, and that's our answer.
            # In this case, the matching group is the bracket contents.
            debug("Node spec list entry \"%s\" appears to have no digits before the brackets" % node_spec_list_entry)
            bracket_contents = m.group(1)
            debug("Node spec list entry yields bracket contents \"%s\"" % bracket_contents)
            return slurm_bracket_contents_to_nidlist(bracket_contents)
        # Finally, there are the cases where there are n digit numbers inside the brackets and 6-n digits outside the brackets,
        # for 1 <= n <= 5
        # In this case, the first matching group is the digits before the brackets, and the second matching group
        # is the bracket contents
        debug("Node spec list entry \"%s\" appears to have %d digits before the brackets" % (6-n, node_spec_list_entry))
        prefix_digits_str = m.group(1)
        bracket_contents = m.group(2)
        debug("Node spec list entry yields prefix digits \"%s\" and bracket contents \"%s\"" % (
              prefix_digits_str, bracket_contents))
        try:
            prefix_digits = int(prefix_digits_str)
        except ValueError as e:
            error("PROGRAMMING LOGIC ERROR: Our prior regular expression checking should have prevented us from hitting this")
            raise_test_exception_error(e, "to parse prefix digits (%s) from node spec list entry (%s)" % (prefix_digits, node_spec_list_entry))
        # If the entry is nid0001[09-11], then this specified nodes 109-111
        # So to arrive at the node numbers, every number that we get from the brackets needs to have a number added to it based on the
        # prefix digits:
        add_to_nids = prefix_digits * pow(10,n)
        debug("Based on the prefix digits, we will be adding %d to NIDs we get from the bracket contents" % add_to_nids)
        bracket_nidlist = slurm_bracket_contents_to_nidlist(bracket_contents)
        debug("The bracket contents yielded nidlist = %s" % str(bracket_nidlist))
        adjusted_nidlist = [ add_to_nids+n for n in bracket_nidlist ]
        debug("So the node spec list entry ultimately yields nidlist = %s" % str(adjusted_nidlist))
        return adjusted_nidlist
    raise_test_error("PROGRAMMING LOGIC ERROR: No pattern matched slurm node spec list entry: %s" % node_spec_list_entry)

def slurm_nid_string_to_nidlist(slurm_nid_string):
    """
    First, validate that slurm_nid_string is a node spec list (possibly with just 1 element). If not, raise an error.
    Otherwise, return the corresponding nid list that is specified by the string.
    """
    debug("Parsing slurm NID string \"%s\"" % slurm_nid_string)
    m = NODE_SPEC_LIST_RE_PROG.match(slurm_nid_string)
    if not m:
        raise_test_exception("Specified string does not match the expected format of a slurm nid spec string: %s" % slurm_nid_string)
    # The first match should be the first node spec list entry
    current_list_string = slurm_nid_string
    nid_list = list()
    while True:
        first_entry = m.group(1)
        debug("Parsing node list entry string \"%s\"" % first_entry)
        nid_list.extend( slurm_list_entry_to_nidlist(first_entry) )
        if first_entry == current_list_string:
            # That means we have reached the final entry
            return sorted(nid_list)
        len_entry = len(first_entry)
        if current_list_string[len_entry] != ",":
            raise_test_error("PROGRAMMING LOGIC ERROR: After \"%s\" we expect a comma not \"%s\". Invalid nid spec list string: %s" % (
                first_entry, current_list_string[len_entry], slurm_nid_string))
        elif len(current_list_string) <= len_entry+1:
            raise_test_error("PROGRAMMING LOGIC ERROR: List ends unexpectedly after\"%s\". Invalid nid spec list string: %s" % (
                first_entry, slurm_nid_string))
        current_list_string = current_list_string[len_entry+1:]
        m = NODE_SPEC_LIST_RE_PROG.match(current_list_string)
        if not m:
            raise_test_exception("PROGRAMMING LOGIC ERROR: Substring \"%s\" does not match the expected format. Invalid slurm nid spec string: %s" % (
                                 current_list_string, slurm_nid_string))

def nid_to_slurm_nid_name(nid):
    """
    Return string with slurm nid name for given nid number
    """
    return "nid%06d" % nid

def xname_to_slurm_nid_name(xname, xname_to_nid):
    """
    Wrapper for nid_to_slurm_nid_name
    """
    return nid_to_slurm_nid_name(xname_to_nid[xname])

def nidlist_to_slurm_nid_string(nidlist):
    """
    Returns string that represents the specified nids in slurm
    """
    if not nidlist:
        raise_test_error("PROGRAMMING LOGIC ERROR: Should not call slurm_nid_string with empty list")
    elif len(nidlist) == 1:
        return nid_to_slurm_nid_name(nidlist[0])
    sorted_nidlist = sorted(nidlist)
    nidstrings = list()
    startnid = None
    lastnid = None
    for n in sorted_nidlist:
        if startnid == None:
            startnid = n
        elif n != (lastnid+1):
            if startnid == lastnid:
                nidstrings.append("%06d" % startnid)
            else:
                nidstrings.append("%06d-%06d" % (startnid, lastnid))
            startnid = n
        lastnid = n
    if startnid == lastnid:
        nidstrings.append("%06d" % startnid)
    else:
        nidstrings.append("%06d-%06d" % (startnid, lastnid))
    return "nid[%s]" % ",".join(nidstrings)

def run_slurm_command(cmd_string, slurm_control_xname, retry_wait=1, timeout=20, return_rc=False, **kwargs):
    """
    Runs the specified slurm command. If it fails due to a connection time out, it
    will retry after the specified wait period, up until the specified timeout.
    Returns the stdout of the command, if successful.
    """
    end_time = time.time() + timeout
    while True:
        cmdresp = run_command_on_xname_via_ssh(slurm_control_xname, cmd_string, return_rc=True, **kwargs)
        if cmdresp["rc"] == 0:
            return cmdresp["out"]
        elif any("slurm" in line and "Connection timed out" in line for line in cmdresp["out"].splitlines()):
            debug("slurm command failed due to slurm timeout")
        elif return_rc:
            return cmdresp
        else:
            raise_test_error("slurm command failed on %s: %s" % (slurm_control_xname, cmd_string))
        
        time_left = time.time() - end_time
        if time_left < 0:
            if return_rc:
                return cmdresp
            raise_test_error(
                "slurm command failed on %s due to slurm timeout even after retries: %s" % (slurm_control_xname, cmd_string))
        sleep_time = max( min(time_left, retry_wait), 0.5 )
        sleep(sleep_time)

def verify_initial_slurm_state(use_api, slurm_control_xname, worker_xnames, xname_to_nid):
    """
    Verify that slurm reports all worker nodes as idle
    """
    errors_found = False
    worker_nids = sorted([ xname_to_nid[x] for x in worker_xnames ])
    info("Checking slurm status of worker nids: %s" % str(worker_nids))

    # -h specifies no header
    # -r tells it only to report nodes which are responding
    # -t idle says to only include nodes in the idle state
    sinfo_cmd_base = "sinfo -h -r -t idle"
    # Only report on the following nodes
    nidlist_flag = "-n %s" % nidlist_to_slurm_nid_string(worker_nids)
    # Only output the nodelists which match our parameters
    format_flag = "-o %N"
    sinfo_cmd = " ".join([sinfo_cmd_base, format_flag, nidlist_flag])

    cmdout = run_slurm_command(sinfo_cmd, slurm_control_xname, show_output=True)
    outlines = cmdout.splitlines()

    nids_found = list()
    for nidlist_string in outlines:
        debug("Parsing line: %s" % nidlist_string)
        nodelist = slurm_nid_string_to_nidlist(nidlist_string)
        debug("Resolves to nid list: %s" % str(nodelist))
        unknown_nids = [ n for n in nodelist if n not in worker_nids ]
        if unknown_nids:
            error("One or more unexpected nids reported by sinfo: %s" % str(unknown_nids))
            errors_found = True
        nids_found.extend(nodelist)
    missing_nids = [ n for n in worker_nids if n not in nids_found ]
    if missing_nids:
        error("One or more worker nids were not included in the sinfo output: %s" % str(missing_nids))
        info("Assuming these are valid NIDs for this system, this probably means the nodes are not idle or they are not responding")
        errors_found = True
    if errors_found:
        info("Running a couple slurm commands to collect debugging information")
        run_slurm_command("sinfo --long --Node", slurm_control_xname, show_output=True, return_rc=True)
        run_slurm_command("scontrol show nodes", slurm_control_xname, show_output=True, return_rc=True)
        raise_test_error("Error validating initial slurm states of worker nodes")
    info("All worker nodes appear to be idle in slurm")

CREATE_REMOTE_FILE_COMMAND="""\
python3 -c "import tempfile; print(tempfile.mkstemp(dir='/tmp', prefix='slurm-test-{prefix}-', suffix='{suffix}')[1])"\
"""

def remote_tmpfile(xname, prefix, suffix=".tmp"):
    """
    Create a remote temporary file on xname and returns its full path+filename
    """
    create_remote_file_command = CREATE_REMOTE_FILE_COMMAND.format(prefix=prefix, suffix=suffix)
    cmdresp = run_command_on_xname_via_ssh(xname, create_remote_file_command, return_rc=False)
    return cmdresp["out"].strip()

SBATCH_JOB_SCRIPT="""\
#!/bin/sh
#SBATCH --time=10
srun --nodelist={target_slurm_node_name} bash -c 'while [ -e {stopfile_name} ]; do
sleep 1
done'
"""

SBATCH_RESPONSE_RE = "^Submitted batch job ([0-9][0-9]*)\s*\Z"
SBATCH_RESPONSE_RE_PROG = re.compile(SBATCH_RESPONSE_RE)

def get_slurm_job_state(job_id, slurm_control_xname, **kwargs):
    """
    Returns a string with the state of the specified slurm job
    """
    cmdout = run_slurm_command("sacct -j %d -X -o state -n" % job_id, slurm_control_xname, **kwargs)
    return cmdout.strip()

def show_job_status(job_id, slurm_control_xname, **kwargs):
    """
    Runs a command to show the status of the specified slurm job
    """
    return run_slurm_command("scontrol show job %d" % job_id, slurm_control_xname, **kwargs)

def start_slurm_job(slurm_control_xname, worker_xname, xname_to_nid, tmpdir):
    """
    Starts our slurm job on the specified worker node. Returns the slurm job ID and the
    name of the remote stopfile.
    The job just waits for the stopfile to be removed from the worker node, and then exits.
    """
    info("Launch slurm job on %s" % worker_xname)
    worker_slurm_name = xname_to_slurm_nid_name(xname=worker_xname, xname_to_nid=xname_to_nid)
    debug("worker_slurm_name = %s" % worker_slurm_name)
    debug("Creating temporary stopfile on %s" % worker_xname)
    datestring = datetime.datetime.utcnow().strftime("%Y%m%d-%H%M%S.%f")
    stopfile_name = remote_tmpfile(xname=worker_xname, prefix="stopfile-%s" % datestring)
    debug("Stopfile name on %s is %s" % (worker_xname, stopfile_name))
    sbatch_job_script_contents = SBATCH_JOB_SCRIPT.format(
                                    target_slurm_node_name=worker_slurm_name, 
                                    stopfile_name=stopfile_name)
    sbscript_prefix="slurm-sbatch-job-script-%s" % datestring
    with tempfile.NamedTemporaryFile(mode="wt", delete=False, 
                                     dir=tmpdir, suffix=".sh",
                                     prefix=sbscript_prefix) as sbscript_local_file:
        sbscript_local_name = sbscript_local_file.name
        sbscript_local_file.write(sbatch_job_script_contents)
    debug("Local sbatch script name is %s" % sbscript_local_name)
    run_cmd_list(["chmod", "a+rx", sbscript_local_name], return_rc=False)
    sbscript_remote_name = "/tmp/%s" % os.path.basename(sbscript_local_name)
    scp_to_xname(sbscript_local_name, slurm_control_xname, remote_target="/tmp", scp_arg_list=["-p"])
    debug("Remote sbatch script name on %s is %s" % (slurm_control_xname, sbscript_remote_name))

    cmdout = run_slurm_command("sbatch --nodelist=%s %s" % (worker_slurm_name, sbscript_remote_name), slurm_control_xname)
    job_id_int = None
    for line in cmdout.splitlines():
        m = SBATCH_RESPONSE_RE_PROG.match(line)
        if m:
            if job_id_int != None:
                raise_test_error("Multiple job ID lines found in sbatch command output")
            job_id_str = m.group(1)
            try:
                job_id_int = int(job_id_str)
            except ValueError as e:
                error("PROGRAMMING LOGIC ERROR: Our regular expression should have guaranteed that \"%s\" was an integer string" % job_id_str)
                raise_test_exception_error(e, "to convert slurm job ID (%s) to an integer" % job_id_str)
    if job_id_int == None:
        raise_test_error("No slurm job ID line found in sbatch command output")
    show_job_status(job_id_int, slurm_control_xname)
    # Verify we get to running state. We will wait briefly
    debug("Make sure job goes to running state")
    end_time = time.time() + 30
    while True:
        if get_slurm_job_state(job_id_int, slurm_control_xname) == "RUNNING":
            info("Slurm job %d is running on %s" % (job_id_int, worker_xname))
            break
        elif time.time() > end_time:
            show_job_status(job_id_int, slurm_control_xname, return_rc=True)
            raise_test_error("Slurm job %d still not in running state on %s" % (job_id_int, worker_xname))
        sleep(5)
    return job_id_int, stopfile_name

def complete_slurm_job(slurm_control_xname, worker_xname, stopfile_name, slurm_job_id):
    """
    Removes the specificed stopfile from the worker node and verifies that the slurm job completes
    """
    info("Completing slurm job %d" % slurm_job_id)
    run_command_on_xname_via_ssh(worker_xname, 
                                 "rm %s" % stopfile_name, 
                                 return_rc=False)
    sleep(1)
    timeout_time = time.time() + 60
    while True:
        if get_slurm_job_state(slurm_job_id, slurm_control_xname) == "COMPLETED":
            info("slurm reports that job %d has completed" % slurm_job_id)
            return
        elif time.time() >= timeout_time:
            show_job_status(job_id_int, slurm_control_xname, return_rc=True)
            raise_test_error("slurm job %d not completed after 60 seconds" % slurm_job_id)
        sleep(5)
