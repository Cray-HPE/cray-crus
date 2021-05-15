# Copyright 2019, 2021 Hewlett Packard Enterprise Development LP
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

"""Tests of the Mock System used for stand-alone development and unit
testing of the Compute Rolling Upgrade Agent.

"""
from crus.controllers.upgrade_agent.node_table import NodeTable
from crus.controllers.upgrade_agent.wlm.slurm_support import (
    parse_show_node,
    parse_show_all_nodes
)
from crus.controllers.mocking.shared import shell
from crus.controllers.mocking.slurm.slurm_state import SlurmNodeTable

NIDNAMES = [NodeTable.get_nidname(xname)
            for xname in NodeTable.get_all_xnames()]


def test_show_all():
    """Test that 'scontrol show node' shows all of the nodes in the
    configuration.

    """
    cmd = shell.shell(["scontrol", "show", "node"])
    # pylint: disable=unnecessary-comprehension
    lines = [line for line in cmd.output()]
    # pylint: disable=unnecessary-comprehension
    errors = [error for error in cmd.errors()]
    assert errors == []
    nodes = parse_show_all_nodes(lines)
    for nidname in NIDNAMES:
        assert nidname in nodes
        assert 'NodeName' in nodes[nidname]
        assert nodes[nidname]['NodeName'] == nidname
        assert 'State' in nodes[nidname]


def test_show_node():
    """Test that 'scontrol show node nid000001' shows only that node.

    """
    cmd = shell.shell(["scontrol", "show", "node", "nid000001"])
    # pylint: disable=unnecessary-comprehension
    lines = [line for line in cmd.output()]
    # pylint: disable=unnecessary-comprehension
    errors = [error for error in cmd.errors()]
    assert errors == []
    nvps = parse_show_node(lines)
    assert 'NodeName' in nvps
    assert nvps['NodeName'] == "nid000001"


def test_state_transitions():
    """Test that I can inject state transitions into a node and I see the
    state transitions come out in successive shows

    """
    states = ["ALLOCATED", "MIXED", "COMPLETING", "IDLE"]
    for state in states:
        SlurmNodeTable.add_pending_state("nid000001", state)

    for state in states:
        cmd = shell.shell(["scontrol", "show", "node", "nid000001"])
        # pylint: disable=unnecessary-comprehension
        lines = [line for line in cmd.output()]
        # pylint: disable=unnecessary-comprehension
        errors = [error for error in cmd.errors()]
        assert errors == []
        nvps = parse_show_node(lines)
        assert 'NodeName' in nvps
        assert nvps['NodeName'] == "nid000001"
        assert 'State' in nvps
        assert nvps['State'] == state
    SlurmNodeTable.clear_pending_states("nid000001")


def test_update_drain():
    """Test setting a node to DRAIN.

    """
    # Look at the initial status of nid000001
    show = shell.shell(["scontrol", "show", "node", "nid000001"])
    # pylint: disable=unnecessary-comprehension
    lines = [line for line in show.output()]
    # pylint: disable=unnecessary-comprehension
    errors = [error for error in show.errors()]
    assert errors == []
    nvps = parse_show_node(lines)
    assert 'State' in nvps
    assert nvps['State'] == "IDLE"
    assert "Reason" not in nvps

    # Switch to draining
    drain = shell.shell(["scontrol", "update", "NodeName=nid000001",
                         "State=DRAIN", "Reason=draining-test"])
    # pylint: disable=unnecessary-comprehension
    lines = [line for line in drain.output()]
    # pylint: disable=unnecessary-comprehension
    errors = [error for error in drain.errors()]
    assert lines == []
    assert errors == []

    # Now look at the new status
    show = shell.shell(["scontrol", "show", "node", "nid000001"])
    # pylint: disable=unnecessary-comprehension
    lines = [line for line in show.output()]
    # pylint: disable=unnecessary-comprehension
    errors = [error for error in show.errors()]
    assert errors == []
    nvps = parse_show_node(lines)
    assert 'State' in nvps
    assert nvps['State'] == "IDLE+DRAIN"
    assert "Reason" in nvps
    assert "draining-test" in nvps['Reason']

    # Now resume...
    resume = shell.shell(["scontrol", "update", "NodeName=nid000001",
                          "State=RESUME"])
    # pylint: disable=unnecessary-comprehension
    lines = [line for line in resume.output()]
    # pylint: disable=unnecessary-comprehension
    errors = [error for error in resume.errors()]
    assert lines == []
    assert errors == []

    # Look at the final status
    show = shell.shell(["scontrol", "show", "node", "nid000001"])
    # pylint: disable=unnecessary-comprehension
    lines = [line for line in show.output()]
    # pylint: disable=unnecessary-comprehension
    errors = [error for error in show.errors()]
    assert errors == []
    nvps = parse_show_node(lines)
    assert 'State' in nvps
    assert nvps['State'] == "IDLE"
    assert "Reason" not in nvps


def test_update_fail():
    """Test setting a node to FAIL.

    """
    # Look at the initial status of nid000001
    show = shell.shell(["scontrol", "show", "node", "nid000001"])
    # pylint: disable=unnecessary-comprehension
    lines = [line for line in show.output()]
    # pylint: disable=unnecessary-comprehension
    errors = [error for error in show.errors()]
    assert errors == []
    nvps = parse_show_node(lines)
    assert 'State' in nvps
    assert nvps['State'] == "IDLE"
    assert "Reason" not in nvps

    # Switch to draining
    drain = shell.shell(["scontrol", "update", "NodeName=nid000001",
                         "State=FAIL", "Reason=failing-test"])
    # pylint: disable=unnecessary-comprehension
    lines = [line for line in drain.output()]
    # pylint: disable=unnecessary-comprehension
    errors = [error for error in drain.errors()]
    assert lines == []
    assert errors == []

    # Now look at the new status
    show = shell.shell(["scontrol", "show", "node", "nid000001"])
    lines = [line for line in show.output()]
    errors = [error for error in show.errors()]
    assert errors == []
    nvps = parse_show_node(lines)
    assert 'State' in nvps
    assert nvps['State'] == "IDLE+FAIL"
    assert "Reason" in nvps
    assert "failing-test" in nvps['Reason']

    # Now resume...
    resume = shell.shell(["scontrol", "update", "NodeName=nid000001",
                          "State=RESUME"])
    # pylint: disable=unnecessary-comprehension
    lines = [line for line in resume.output()]
    # pylint: disable=unnecessary-comprehension
    errors = [error for error in resume.errors()]
    assert lines == []
    assert errors == []

    # Look at the final status
    show = shell.shell(["scontrol", "show", "node", "nid000001"])
    # pylint: disable=unnecessary-comprehension
    lines = [line for line in show.output()]
    # pylint: disable=unnecessary-comprehension
    errors = [error for error in show.errors()]
    assert errors == []
    nvps = parse_show_node(lines)
    assert 'State' in nvps
    assert nvps['State'] == "IDLE"
    assert "Reason" not in nvps


def test_fail_no_subcommand():
    """Test that 'scontrol' with no sub command produces an error.

    """
    cmd = shell.shell(["scontrol"])
    # pylint: disable=unnecessary-comprehension
    lines = [line for line in cmd.output()]
    assert lines == []
    # pylint: disable=unnecessary-comprehension
    errors = [error for error in cmd.errors()]
    assert errors != []


def test_fail_show_bad_subcommand():
    """Test that 'scontrol wobble' (i.e. an unrecognized sub-command)
    produces an error.

    """
    cmd = shell.shell(["scontrol", "wobble"])
    # pylint: disable=unnecessary-comprehension
    lines = [line for line in cmd.output()]
    assert lines == []
    # pylint: disable=unnecessary-comprehension
    errors = [error for error in cmd.errors()]
    assert errors != []


def test_fail_show_no_node():
    """Test that 'scontrol show' (no 'node') produces an error.

    """
    cmd = shell.shell(["scontrol", "show"])
    # pylint: disable=unnecessary-comprehension
    lines = [line for line in cmd.output()]
    assert lines == []
    # pylint: disable=unnecessary-comprehension
    errors = [error for error in cmd.errors()]
    assert errors != []


def test_fail_show_not_node():
    """Test that 'scontrol show node wobble' (something other than 'node')
    produces an error.

    """
    cmd = shell.shell(["scontrol", "show", "wobble"])
    # pylint: disable=unnecessary-comprehension
    lines = [line for line in cmd.output()]
    assert lines == []
    # pylint: disable=unnecessary-comprehension
    errors = [error for error in cmd.errors()]
    assert errors != []


def test_fail_show_bad_node():
    """Test that 'scontrol show node wobble' (unrecognized node) produces
    an error.

    """
    cmd = shell.shell(["scontrol", "show", "node", "wobble"])
    # pylint: disable=unnecessary-comprehension
    lines = [line for line in cmd.output()]
    # pylint: disable=unnecessary-comprehension
    errors = [error for error in cmd.errors()]
    assert lines == []
    assert errors != []


def test_fail_update_no_spec():
    """Test that 'scontrol update' (no specification) produces an error.

    """
    cmd = shell.shell(["scontrol", "update"])
    # pylint: disable=unnecessary-comprehension
    lines = [line for line in cmd.output()]
    assert lines == []
    # pylint: disable=unnecessary-comprehension
    errors = [error for error in cmd.errors()]
    assert errors != []


def test_fail_update_no_node():
    """Test that 'scontrol show update State=RESUME' (no node specified)
    produces an error.

    """
    cmd = shell.shell(["scontrol", "update", "State=RESUME"])
    # pylint: disable=unnecessary-comprehension
    lines = [line for line in cmd.output()]
    assert lines == []
    # pylint: disable=unnecessary-comprehension
    errors = [error for error in cmd.errors()]
    assert errors != []


def test_fail_update_fail_no_reason():
    """Test that 'scontrol update Nodename=nid000001 State=FAIL' (no
    reason) produces an error.

    """
    cmd = shell.shell(["scontrol", "update", "NodeName=nid000001",
                       "State=FAIL"])
    # pylint: disable=unnecessary-comprehension
    lines = [line for line in cmd.output()]
    assert lines == []
    # pylint: disable=unnecessary-comprehension
    errors = [error for error in cmd.errors()]
    assert errors != []


def test_fail_update_drain_no_reason():  # pylint: disable=invalid-name
    """Test that 'scontrol update Nodename=nid000001 State=DRAIN' (no
    reason) produces an error.

    """
    cmd = shell.shell(["scontrol", "update", "NodeName=nid000001",
                       "State=DRAIN"])
    # pylint: disable=unnecessary-comprehension
    lines = [line for line in cmd.output()]
    assert lines == []
    # pylint: disable=unnecessary-comprehension
    errors = [error for error in cmd.errors()]
    assert errors != []


def test_fail_update_resume_reason():
    """Test that

        scontrol update NodeName=nid000001 State=RESUME Reason=wobble

    (a reason with RESUME) produces an error.

    """
    cmd = shell.shell(["scontrol", "update", "NodeName=nid000001",
                       "State=RESUME", "Reason=wobble"])
    # pylint: disable=unnecessary-comprehension
    lines = [line for line in cmd.output()]
    assert lines == []
    # pylint: disable=unnecessary-comprehension
    errors = [error for error in cmd.errors()]
    assert errors != []


def test_fail_update_bad_state():
    """Test that 'scontrol update NodeName=nid000001 State=WOBBLE'
    (unknown state) produces an error.

    """
    cmd = shell.shell(["scontrol", "update", "NodeName=nid000001",
                       "State=WOBBLE"])
    # pylint: disable=unnecessary-comprehension
    lines = [line for line in cmd.output()]
    assert lines == []
    # pylint: disable=unnecessary-comprehension
    errors = [error for error in cmd.errors()]
    assert errors != []


def test_fail_update_no_state():
    """Test that 'sconftrol update NodeName=nid000001' (no State) produces
    an error.

    """
    cmd = shell.shell(["scontrol", "update", "NodeName=nid000001"])
    # pylint: disable=unnecessary-comprehension
    lines = [line for line in cmd.output()]
    assert lines == []
    # pylint: disable=unnecessary-comprehension
    errors = [error for error in cmd.errors()]
    assert errors != []


def test_fail_update_something_else():
    """Test that 'scontrol update NodeName=nid000001 Wobble=Wobble'
    (setting something other than State) produces an error.

    """
    cmd = shell.shell(["scontrol", "update", "NodeName=nid000001",
                       "Wobble=Wobble"])
    # pylint: disable=unnecessary-comprehension
    lines = [line for line in cmd.output()]
    assert lines == []
    # pylint: disable=unnecessary-comprehension
    errors = [error for error in cmd.errors()]
    assert errors != []
