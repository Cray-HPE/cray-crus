"""
Mock Node Group Table

Copyright 2019, Cray Inc. All rights reserved.
"""


class NodeGroup:
    """A class representing a Node Group

    """
    def __init__(self, label, data):
        """Constructor - name is the name of the Boot Set, data is a
        dictionary containing the data provided by the caller.

        """
        self.label = label
        self.description = data.get('description', "")
        self.tags = data.get('tags', None)
        self.members = data.get('members', {'ids': []})

    def get(self):
        """Retrieve the contents of the boot set as a dictionary.

        """
        ret = {
            'label': self.label,
            'description': self.description,
            'members': self.members,
        }
        if self.tags:
            ret['tags'] = self.tags
        return ret

    def has_member(self, xname):
        """Check whether the node group has the named member.
        """
        return xname in self.members['ids']

    def add_member(self, xname):
        """Add a member (node) to the node group by XNAME
        """
        if xname not in self.members['ids']:
            self.members['ids'].append(xname)
        return self.get()

    def remove_member(self, xname):
        """Remove a member (node) from the node group by XNAME.
        """
        if xname in self.members['ids']:
            self.members['ids'].remove(xname)
        return self.get()


class NodeGroupTable:
    """A static class that manages node groups.

    """
    _node_groups = {}

    @classmethod
    def create(cls, label, data):
        """Create the boot set specified by name with the contents specified
        in data.  Return the boot set data.

        """
        cls._node_groups[label] = NodeGroup(label, data)
        return cls._node_groups[label].get()

    @classmethod
    def get(cls, label):
        """Get the contents of the Boot Set specified by name.

        """
        node_group = cls._node_groups.get(label, None)
        ret = node_group.get() if node_group else None
        return ret

    @classmethod
    def delete(cls, label):
        """Delete the boot set specified by name and return the contents at
        the time it was deleted.

        """
        node_group = cls._node_groups.get(label, None)
        ret = node_group.get() if node_group else None
        if node_group:
            del cls._node_groups[label]
        return ret

    @classmethod
    def add_member(cls, label, data):
        """Add the node (member) identified by xname to the node group
        identified by label.

        """
        xname = data['id']
        node_group = cls._node_groups.get(label, None)
        ret = (node_group.add_member(xname)
               if node_group and not node_group.has_member(xname)
               else None)
        return ret

    @classmethod
    def remove_member(cls, label, xname):
        """Add the node (member) identified by xname to the node group
        identified by label.

        """
        node_group = cls._node_groups.get(label, None)
        ret = (node_group.remove_member(xname)
               if node_group and node_group.has_member(xname)
               else None)
        return ret
