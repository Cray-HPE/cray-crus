"""WLMInstance sub-class to implement the Slurm WLM

Copyright 2019, Cray Inc. All rights reserved.
"""

from ..node_table import NodeTable
from ..errors import ComputeUpgradeError
from .wrap_shell import shell
from .wlm import WLMHandler, wlm_handler
from .slurm_support import parse_show_node


class SlurmHandler(WLMHandler):
    """Static class that implements a WLM API on th the Slurm WLM.

    """
    @staticmethod
    def quiesce(xname):
        """Initiate quiescing the node indicated by 'xname' for slurm this is
        done by 'draining' the node.

        """
        nidname = NodeTable.get_nidname(xname)
        drain = shell.shell(["scontrol", "update", "NodeName=%s" % nidname,
                             "State=DRAIN", "Reason=rolling-upgrade"])
        # Comprehension used here to avoid passing the list
        # reference
        #
        # pylint: disable=unnecessary-comprehension
        errors = [error for error in drain.errors()]
        if errors != []:  # pragma should never happen
            raise ComputeUpgradeError(
                "failed to quiesce slurm node '%s' - %s" %
                (nidname, str(errors))
            )

    @staticmethod
    def is_ready(xname):
        """Check whether the node indicated by 'xname' has reached (or is in)
        a 'ready' state as defined by the WLM (i.e. appears to be
        capable of being put into service or is in service).

        """
        nidname = NodeTable.get_nidname(xname)
        show = shell.shell(["scontrol", "show", "node", nidname])
        # Comprehension used here to avoid passing the list
        # references
        #
        # pylint: disable=unnecessary-comprehension
        lines = [line for line in show.output()]
        # pylint: disable=unnecessary-comprehension
        errors = [error for error in show.errors()]
        if errors != []:  # pragma should never happen
            raise ComputeUpgradeError(
                "failed to check slurm node '%s' for idle - %s" %
                (nidname, str(errors)))
        nvps = parse_show_node(lines)
        if 'State' not in nvps:  # pragma should never happen
            raise ComputeUpgradeError(
                "'State' not found in scontrol output for "
                "slurm node '%s' - %s" % nidname
            )
        # In slurm, a '*' in the State field indicates that the node
        # is compromised in some way and not ready to be in service.
        state = nvps['State']
        return "IDLE" in state and '*' not in state

    @staticmethod
    def is_quiet(xname):
        """Check whether the node indicated by 'xname' has reached a quiet
        state after having started quiescing.

        """
        nidname = NodeTable.get_nidname(xname)
        show = shell.shell(["scontrol", "show", "node", nidname])
        # Comprehension used here to avoid passing the list
        # references
        #
        # pylint: disable=unnecessary-comprehension
        lines = [line for line in show.output()]
        # pylint: disable=unnecessary-comprehension
        errors = [error for error in show.errors()]
        if errors != []:  # pragma should never happen
            raise ComputeUpgradeError(
                "failed to check slurm node '%s' for idle - %s" %
                (nidname, str(errors)))
        nvps = parse_show_node(lines)
        if 'State' not in nvps:  # pragma should never happen
            raise ComputeUpgradeError(
                "'State' not found in scontrol output for "
                "slurm node '%s' - %s" % nidname
            )
        state = nvps['State']
        return (
            ("IDLE" in state or "DOWN" in state) and
            ("DRAIN" in state)
        )

    @staticmethod
    def resume(xname):
        """Put the node indicated by 'xname' back into service.

        """
        nidname = NodeTable.get_nidname(xname)
        resume = shell.shell(["scontrol", "update", "NodeName=%s" % nidname,
                              "State=RESUME"])
        # Comprehension used here to avoid passing the list
        # reference
        #
        # pylint: disable=unnecessary-comprehension
        errors = [error for error in resume.errors()]
        if errors != []:  # pragma should never happen
            raise ComputeUpgradeError(
                "failed to resume slurm node '%s' - %s" %
                (nidname, str(errors))
            )

    @staticmethod
    def fail(xname, reason):
        """Put the node indicated by 'xname' back into a failed state,
        specifying a reason.

        """
        nidname = NodeTable.get_nidname(xname)
        fail = shell.shell(["scontrol", "update", "NodeName=%s" % nidname,
                            "State=FAIL", "Reason=%s" % reason])
        # Comprehension used here to avoid passing the list
        # reference
        #
        # pylint: disable=unnecessary-comprehension
        errors = [error for error in fail.errors()]
        if errors != []:  # pragma should never happen
            raise ComputeUpgradeError(
                "failed to put slurm node '%s' in failed state - %s" %
                (nidname, str(errors))
            )


# Register the Slurm handler with WLM
wlm_handler("slurm", SlurmHandler)
