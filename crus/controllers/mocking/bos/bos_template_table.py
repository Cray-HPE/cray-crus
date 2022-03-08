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
Mock Boot Template Table

"""
import uuid

from ..bss.bss_nodes import BSSNodeTable
from ...upgrade_agent.node_group import NodeGroup


class BootTemplate:
    """A class representing a Boot Template schematically for testing
    purposes.  This short circuits the actual BOS structure which has
    a session template that then points to a boot set.  All we need
    from here is the node group to be booted, so we put it here to
    keep complexity down.

    """
    def __init__(self, node_group_label):
        """Constructor - node_group_label is the label of the node group in
        the (presumptive) boot set used to boot the nodes.

        """
        self.template_id = str(uuid.uuid4())
        self.node_group = node_group_label

    def boot(self):
        """ Mock boot the nodes referenced by the template.

        """
        node_group = NodeGroup(self.node_group)
        if node_group:
            for xname in node_group.get_members():
                BSSNodeTable.boot(xname)


class BootTemplateTable:
    """A static class that manages boot templates.

    """
    _boot_templates = {}

    @classmethod
    def create(cls, node_group_label):
        """Create the boot set specified by name with the contents specified
        in data.  Return the BootTemplate object created.

        """
        template = BootTemplate(node_group_label)
        cls._boot_templates[template.template_id] = template
        return template

    @classmethod
    def delete(cls, template_id):
        """Remove a template by its template id.

        """
        if template_id in cls._boot_templates:
            del cls._boot_templates[template_id]

    @classmethod
    def boot(cls, template_id):
        """ Mock boot a template based on its template ID
        """
        template = cls._boot_templates.get(template_id, None)
        if template:
            template.boot()

    @classmethod
    def create_dummy(cls):
        """Stuff a dummy template into the template table with a
        node_group_label of 'dummy-node-group' for use in manual
        testing in BOS mocking mode.

        """
        if 'dummy-boot-template' not in cls._boot_templates:
            template = BootTemplate('dummy-node-group')
            template.template_id = 'dummy-boot-template'
            cls._boot_templates[template.template_id] = template


# Make a dummy boot template
BootTemplateTable.create_dummy()
