# Copyright 2020 Hewlett Packard Enterprise Development LP

"""
HSM-related BOS limit test helper functions
"""

from common.helpers import debug
from common.hsm import create_hsm_group, delete_hsm_group

def create_hsm_groups(use_api, test_hsm_groups):
    """
    Creates the three necessary HSM groups for CRUS sessions (starting group,
    upgrading group, and failed group). Updates the specified map with mappings
    from each category name to the name of the corresponding HSM group that was
    created.
    """
    for label in [ "starting", "upgrading", "failed" ]:
        debug("Creating %s HSM group for CRUS sessions" % label)
        test_hsm_groups[label] = create_hsm_group(use_api, 
                                                  name_prefix="crus-test-%s" % label, 
                                                  test_name="CMS CRUS integration test")

def delete_hsm_groups(use_api, group_map):
    """
    Delete all HSM groups, removing them from the map as they are deleted.
    """
    key_gname_pairs = list(group_map.items())
    for key, gname in key_gname_pairs:
        debug("Deleting %s HSM group" % gname)
        delete_hsm_group(use_api, gname)
        del group_map[key]
