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
"""WLMInstance sub-class to implement the Slurm WLM

"""

import logging
from ..node_table import NodeTable
from ..errors import ComputeUpgradeError
from .wrap_shell import shell
from .wlm import WLMHandler, wlm_handler
from .slurm_support import parse_show_node

LOGGER = logging.getLogger(__name__)


class SlurmHandler(WLMHandler):
    """Static class that implements a WLM API on the Slurm WLM.

    """

    @staticmethod
    def quiesce(xname):
        """Initiate quiescing the node indicated by 'xname'; for slurm this is
        done by 'draining' the node.

        """
        nidname = NodeTable.get_nidname(xname)
        command = ["scontrol", "update", "NodeName=%s" % nidname,
                   "State=DRAIN", "Reason=rolling-upgrade"]
        LOGGER.debug("SlurmHandler.quiesce(%s): nidname=%s, command=%s", xname, nidname, command)
        drain = shell.shell(command)
        # Comprehension used here to avoid passing the list
        # reference
        #
        # pylint: disable=unnecessary-comprehension
        errors = [error for error in drain.errors()]
        if errors != []:  # pragma should never happen
            # Since we are in an error path, we log more than normal at the info log level
            LOGGER.info("SlurmHandler.quiesce(%s): nidname=%s, lines=\n%s", xname, nidname,
                        '\n'.join([line for line in drain.output()]))
            message = "failed to quiesce slurm node '%s' - %s" % (nidname, str(errors))
            LOGGER.error("SlurmHandler.quiesce(%s): %s", xname, message)
            raise ComputeUpgradeError(message)
        LOGGER.debug("SlurmHandler.quiesce(%s): nidname=%s, lines=\n%s", xname, nidname,
                     '\n'.join([line for line in drain.output()]))

    @staticmethod
    def is_ready(xname):
        """Check whether the node indicated by 'xname' has reached (or is in)
        a 'ready' state as defined by the WLM (i.e. appears to be
        capable of being put into service or is in service).

        """
        nidname = NodeTable.get_nidname(xname)
        command = ["scontrol", "show", "node", nidname]
        LOGGER.debug("SlurmHandler.is_ready(%s): nidname=%s, command=%s", xname, nidname, command)
        show = shell.shell(command)
        # Comprehension used here to avoid passing the list
        # references
        #
        # pylint: disable=unnecessary-comprehension
        lines = [line for line in show.output()]
        # pylint: disable=unnecessary-comprehension
        errors = [error for error in show.errors()]
        if errors != []:  # pragma should never happen
            # Since we are in an error path, we log more than normal at the info log level
            LOGGER.info("SlurmHandler.is_ready(%s): nidname=%s, lines=\n%s", xname, nidname, '\n'.join(lines))
            message = "failed to check slurm node '%s' for idle - %s" % (nidname, str(errors))
            LOGGER.error("SlurmHandler.is_ready(%s): %s", xname, message)
            raise ComputeUpgradeError(message)
        nvps = parse_show_node(lines)
        if 'State' not in nvps:  # pragma should never happen
            # Since we are in an error path, we log more than normal at the info log level
            LOGGER.info("SlurmHandler.is_ready(%s): nidname=%s, lines=\n%s", xname, nidname, '\n'.join(lines))
            LOGGER.info("SlurmHandler.is_ready(%s): nidname=%s, nvps=%s", xname, nidname, nvps)
            message = "'State' not found in scontrol output for slurm node '%s' - %s" % nidname
            LOGGER.error("SlurmHandler.is_ready(%s): %s", xname, message)
            raise ComputeUpgradeError(message)
        LOGGER.debug("SlurmHandler.is_ready(%s): nidname=%s, lines=\n%s", xname, nidname, '\n'.join(lines))
        LOGGER.debug("SlurmHandler.is_ready(%s): nidname=%s, nvps=%s", xname, nidname, nvps)
        # In slurm, a '*' in the State field indicates that the node
        # is compromised in some way and not ready to be in service.
        state = nvps['State']
        LOGGER.debug("SlurmHandler.is_ready(%s): nidname=%s, state=%s", xname, nidname, state)
        return "IDLE" in state and '*' not in state

    @staticmethod
    def is_quiet(xname):
        """Check whether the node indicated by 'xname' has reached a quiet
        state after having started quiescing.

        """
        nidname = NodeTable.get_nidname(xname)
        command = ["scontrol", "show", "node", nidname]
        LOGGER.debug("SlurmHandler.is_quiet(%s): nidname=%s, command=%s", xname, nidname, command)
        show = shell.shell(command)
        # Comprehension used here to avoid passing the list
        # references
        #
        # pylint: disable=unnecessary-comprehension
        lines = [line for line in show.output()]
        # pylint: disable=unnecessary-comprehension
        errors = [error for error in show.errors()]
        if errors != []:  # pragma should never happen
            # Since we are in an error path, we log more than normal at the info log level
            LOGGER.info("SlurmHandler.is_quiet(%s): nidname=%s, lines=\n%s", xname, nidname, '\n'.join(lines))
            message = "failed to check slurm node '%s' for idle - %s" % (nidname, str(errors))
            LOGGER.error("SlurmHandler.is_quiet(%s): %s", xname, message)
            raise ComputeUpgradeError(message)
        nvps = parse_show_node(lines)
        if 'State' not in nvps:  # pragma should never happen
            # Since we are in an error path, we log more than normal at the info log level
            LOGGER.info("SlurmHandler.is_quiet(%s): nidname=%s, lines=\n%s", xname, nidname, '\n'.join(lines))
            LOGGER.info("SlurmHandler.is_quiet(%s): nidname=%s, nvps=%s", xname, nidname, nvps)
            message = "'State' not found in scontrol output for slurm node '%s' - %s" % nidname
            LOGGER.error("SlurmHandler.is_quiet(%s): %s", xname, message)
            raise ComputeUpgradeError(message)
        LOGGER.debug("SlurmHandler.is_quiet(%s): nidname=%s, lines=\n%s", xname, nidname, '\n'.join(lines))
        LOGGER.debug("SlurmHandler.is_quiet(%s): nidname=%s, nvps=%s", xname, nidname, nvps)
        state = nvps['State']
        LOGGER.debug("SlurmHandler.is_quiet(%s): nidname=%s, state=%s", xname, nidname, state)
        return (
            ("IDLE" in state or "DOWN" in state) and
            ("DRAIN" in state)
        )

    @staticmethod
    def resume(xname):
        """Put the node indicated by 'xname' back into service.

        """
        nidname = NodeTable.get_nidname(xname)
        command = ["scontrol", "update", "NodeName=%s" % nidname, "State=RESUME"]
        LOGGER.debug("SlurmHandler.resume(%s): nidname=%s, command=%s", xname, nidname, command)
        resume = shell.shell(command)
        # Comprehension used here to avoid passing the list
        # reference
        #
        # pylint: disable=unnecessary-comprehension
        errors = [error for error in resume.errors()]
        if errors != []:  # pragma should never happen
            # Since we are in an error path, we log more than normal at the info log level
            LOGGER.info("SlurmHandler.resume(%s): nidname=%s, lines=\n%s", xname, nidname,
                        '\n'.join([line for line in resume.output()]))
            message = "failed to resume slurm node '%s' - %s" % (nidname, str(errors))
            LOGGER.error("SlurmHandler.resume(%s): %s", xname, message)
            raise ComputeUpgradeError(message)
        LOGGER.debug("SlurmHandler.resume(%s): nidname=%s, lines=\n%s", xname, nidname,
                     '\n'.join([line for line in resume.output()]))

    @staticmethod
    def fail(xname, reason):
        """Put the node indicated by 'xname' back into a failed state,
        specifying a reason.

        """
        nidname = NodeTable.get_nidname(xname)
        command = ["scontrol", "update", "NodeName=%s" % nidname, "State=FAIL", "Reason=%s" % reason]
        LOGGER.debug("SlurmHandler.fail(%s): nidname=%s, command=%s", xname, nidname, command)
        fail = shell.shell(command)
        # Comprehension used here to avoid passing the list
        # reference
        #
        # pylint: disable=unnecessary-comprehension
        errors = [error for error in fail.errors()]
        if errors != []:  # pragma should never happen
            # Since we are in an error path, we log more than normal at the info log level
            LOGGER.info("SlurmHandler.fail(%s): nidname=%s, lines=\n%s", xname, nidname,
                        '\n'.join([line for line in fail.output()]))
            message = "failed to put slurm node '%s' in failed state - %s" % (nidname, str(errors))
            LOGGER.error("SlurmHandler.fail(%s): %s", xname, message)
            raise ComputeUpgradeError(message)
        LOGGER.debug("SlurmHandler.fail(%s): nidname=%s, lines=\n%s", xname, nidname,
                     '\n'.join([line for line in fail.output()]))


# Register the Slurm handler with WLM
wlm_handler("slurm", SlurmHandler)
