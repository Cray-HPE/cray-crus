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

"""Base Class for managing WLMs

"""
import logging
from ..errors import ComputeUpgradeError
WLM_HANDLERS = {}

LOGGER = logging.getLogger(__name__)


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
        message = "unknown WLM type '%s'" % wlm_type
        LOGGER.error("get_wlm_handler: %s", message)
        raise ComputeUpgradeError(message)
