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
"""Slurm node state management used by commands (and tests to set up
initial conditions).  Manages a set of nodes keeping track of what
state each node is in.

"""
import time
from ...upgrade_agent.node_table import NodeTable
from ...upgrade_agent.bss_hosts import BSSHostTable


class SlurmNode:
    """Class to hold the state associated with a Slurm Node.
    """
    def __init__(self, nidname):
        """Constructor

        """
        self.node_name = nidname
        self.xname = NodeTable.get_xname(NodeTable.nidname_to_nid(nidname))
        self.reason = None
        self.reason_time = None
        self.state = 'IDLE'
        self.draining = False
        self.failing = False
        self.pending_states = []

    def get_node_addr(self):
        """Retrieve the node address of the node.

        """
        return "%s-nmn" % self.node_name

    def get_node_host(self):
        """Retrieve the node hostname of the node.

        """
        return self.node_name

    def get_state(self):
        """Retrieve the state of the node.  State is a tuple of a state and an
        optional sub-state which is None if not present.  The
        sub-states can be DRAIN or FAIL.

        """
        if self.pending_states:
            self.state = self.pending_states.pop(0)
        node_state = ""
        host_table = BSSHostTable()
        if host_table.get_state(self.xname) != 'Ready':
            rtime = time.strftime("%Y-%m-%dT%H:%M:%S")
            node_state = "*"
            reason = "Not responding" if self.reason is None else self.reason
            self.reason = reason
            self.reason_time = self.reason_time if self.reason_time else rtime
        if self.draining:
            substate = 'DRAIN'
        elif self.failing:
            substate = 'FAIL'
        else:
            substate = None
        return self.state, substate, node_state

    def get_reason(self):
        """Retrieve the node's 'reason' field if any and the time at which
        that 'reason' was set.

        """
        return self.reason, self.reason_time

    def fail(self, reason):
        """Set the node to FAIL and add a reason, the reason must be supplied.
        This will clear DRAIN if it is set.

        """
        self.draining = False
        self.failing = True
        self.reason = reason
        self.reason_time = time.strftime("%Y-%m-%dT%H:%M:%S")

    def drain(self, reason):
        """Set the node to DRAIN and add a reason, the reason must be supplied.
        This will clear FAIL if it is set.

        """
        self.draining = True
        self.failing = False
        self.reason = reason
        self.reason_time = time.strftime("%Y-%m-%dT%H:%M:%S")

    def resume(self):
        """Clear DRAIN and FAIL states and return the node to operation.

        """
        self.draining = False
        self.failing = False
        self.reason = None
        self.reason_time = None

    def add_pending_state(self, state):
        """Add a new pending state to the node's pending states queue.

        """
        self.pending_states.append(state)

    def clear_pending_states(self):
        """ Clear any pending states that might be in flight.

        """
        self.pending_states = []


class SlurmNodeTable:
    """A class that manages slurm nodes by node group

    """
    _slurm_node_table = None

    def __init__(self):
        """Constructor

        """
        nidnames = [NodeTable.get_nidname(xname)
                    for xname in NodeTable.get_all_xnames()]
        self.nodes = {nidname: SlurmNode(nidname) for nidname in nidnames}

    def get_node(self, nidname):
        """Return the node whose name is 'nidname'

        """
        if nidname in self.nodes:
            return self.nodes[nidname]
        return None

    def all_node_names(self):
        """Retrieve a safe list of all node names in the table.

        """
        # Comprehension used here to avoid returning the list reference
        #
        # pylint: disable=unnecessary-comprehension
        return [key for key in self.nodes]

    @classmethod
    def _node_table(cls):
        """Get / initialize the node table...

        """
        if not cls._slurm_node_table:
            cls._slurm_node_table = SlurmNodeTable()
        return cls._slurm_node_table

    @classmethod
    def get_all_names(cls):
        """Get all of the node names from the slurm node table.

        """
        return cls._node_table().all_node_names()

    @classmethod
    def get_node_addr(cls, name):
        """Retrieve the node address of the named node.

        """
        node = cls._node_table().get_node(name)
        if node:
            return node.get_node_addr()
        return None

    @classmethod
    def get_node_host(cls, name):
        """Retrieve the node hostname of the named node.

        """
        node = cls._node_table().get_node(name)
        if node:
            return node.get_node_host()
        return None

    @classmethod
    def get_state(cls, name):
        """Retrieve the state of the named node.  State is a tuple of a state
        an optional sub-state which is None if not present, and a node
        states suffix which is either '' or '*' deepending on whether
        the node is running or not.

        """
        node = cls._node_table().get_node(name)
        if node:
            return node.get_state()
        return None, None, None

    @classmethod
    def get_reason(cls, name):
        """Retrieve the named node's 'reason' field if any and the time at
        which that 'reason' was set.

        """
        node = cls._node_table().get_node(name)
        if node:
            return node.get_reason()
        return None, None  # pragma should never happen

    @classmethod
    def fail(cls, name, reason):
        """Set the node to FAIL and add a reason, the reason must be supplied.
        This will clear DRAIN if it is set.

        """
        node = cls._node_table().get_node(name)
        if node:
            node.fail(reason)

    @classmethod
    def drain(cls, name, reason):
        """Set the node to DRAIN and add a reason, the reason must be
        supplied.  This will clear FAIL if it is set.

        """
        node = cls._node_table().get_node(name)
        if node:
            node.drain(reason)

    @classmethod
    def resume(cls, name):
        """Clear DRAIN and FAIL states and return the named node to operation.

        """
        node = cls._node_table().get_node(name)
        if node:
            node.resume()

    @classmethod
    def add_pending_state(cls, name, state):
        """Add a new pending state to the named node's pending states queue.

        """
        node = cls._node_table().get_node(name)
        if node:
            node.add_pending_state(state)

    @classmethod
    def clear_pending_states(cls, name):
        """Clear out all pending states in the named node.

        """
        node = cls._node_table().get_node(name)
        if node:
            node.clear_pending_states()
