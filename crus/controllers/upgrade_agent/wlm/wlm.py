"""Base Class for managing WLMs

Copyright 2019, Cray Inc. All rights reserved.
"""
from ..errors import ComputeUpgradeError
WLM_HANDLERS = {}


class WLMHandler:
    """Base static class for managing nodes in workload managers.
    Provides a generic API for WLM node managment.

    """
    @staticmethod
    def quiesce(xname):  # pragma abstract method
        """Initiate quiescing the node indicated by 'xname' in the WLM

        """
        raise NotImplementedError

    @staticmethod
    def is_ready(xname):  # pragma abstract method
        """Check whether the node indicated by 'xname' has reached (or is in)
        a 'ready' state as defined by the WLM (i.e. appears to be
        capable of being put into service or is in service).

        """
        raise NotImplementedError

    @staticmethod
    def is_quiet(xname):  # pragma abstract method
        """Check whether the node indicated by 'xname' has reached a quiet
        state after having started quiescing.

        """
        raise NotImplementedError

    @staticmethod
    def resume(xname):  # pragma abstract method
        """Put the node indicated by 'xname' back into service.

        """
        raise NotImplementedError

    @staticmethod
    def fail(xname, reason):  # pragma abstract method
        """Put the node indicated by 'xname' back into a failed state,
        specifying a reason.

        """
        raise NotImplementedError


def wlm_handler(wlm_type, handler_class):
    """ Register a WLM Handler...

    """
    WLM_HANDLERS[wlm_type] = handler_class


def get_wlm_handler(wlm_type):
    """Get the handler class for the specified WLM type.

    """
    try:
        return WLM_HANDLERS[wlm_type]
    except KeyError:  # pragma should never happen
        raise ComputeUpgradeError("unknown WLM type '%s'" % wlm_type)
