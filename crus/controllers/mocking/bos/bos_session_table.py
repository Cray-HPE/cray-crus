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
Mock Boot Session Table

"""
from .bos_template_table import BootTemplateTable


class BootSession:
    """A class representing a Boot Session

    """
    def __init__(self, session_id, data):
        """Constructor - session_id is the ID of the Boot Session, data is a
        dictionary containing the data provided by the caller.

        """
        self.session_id = session_id
        self.operation = data.get('operation', "")
        self.template_uuid = data.get('templateUuid', None)
        self.job_id = data.get('jobId')

    def get(self):
        """Retrieve the contents of the boot session as a dictionary.

        """
        ret = {
            'links': [
                {
                    'href': self.session_id,
                    'jobId': self.job_id,
                    'rel': "session",
                    'type': "GET",
                    'operation': self.operation,
                    'templateUuid': self.template_uuid,
                }
            ]
        }
        return ret

    def boot(self):
        """ Mock boot the session.

        """
        BootTemplateTable.boot(self.template_uuid)


class BootSessionTable:
    """A static class that manages boot sessions.

    """
    _boot_sessions = {}

    @classmethod
    def create(cls, session_id, data):
        """Create the boot set specified by name with the contents specified
        in data.  Return the boot set data.

        """
        cls._boot_sessions[session_id] = BootSession(session_id, data)
        return cls._boot_sessions[session_id].get()

    @classmethod
    def boot(cls, session_id):
        """Mock boot the boot session identified by session_id.

        """
        boot_session = cls._boot_sessions.get(session_id, None)
        if boot_session:
            boot_session.boot()
