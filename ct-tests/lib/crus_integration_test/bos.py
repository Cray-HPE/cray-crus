# Copyright 2020-2021 Hewlett Packard Enterprise Development LP
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

"""
BOS-related test helper functions for CRUS integration test
"""

from common.bos import create_bos_session_template, \
                       describe_bos_session_template
from common.helpers import any_dict_value, debug, error, info
from common.vcs import create_vcs_branch
import copy
import datetime
import random
import re

CLE_BST_RD_RETRY_PARAM_PATTERN = "^.*(rd[.]retry=([0-9][0-9]*))[^0-9].*$"
CLE_BST_RD_RETRY_PARAM_RE_PROG =  re.compile(CLE_BST_RD_RETRY_PARAM_PATTERN)

def create_bos_session_templates(use_api, template_objects, base_template_name, upgrading_group_name, xnames, 
                                 test_template_names, test_vcs_branches, vcs_repo_dir, num_to_create):
    """
    Create the specified number of new bos session templates, which are clones of "base_template_name"
    with the following changes:
    1) The kernel parameters are changed to have a different rd.retry value
    2) The template name is based on that value
    3) A new vcs branch is created in which the node motd includes this template name, and the
       cfs branch for the new template points to this new vcs branch
    4) The node_list, node_groups, or node_roles_groups fields in the bootset are replaced.
        - The first template will have it replaced with node_list of all our xnames.
        - The rest will have node_groups set to our upgrading group
    The test_template_names list is populated with the new template names.
    The test_vcs_branches list is populated with the new vcs branch names.
    The template_objects map is updated to include the new templates.
    """
    used_rd_retry_values = set()
    def get_next_unused_retry_value(v):
        while v in used_rd_retry_values:
            v+=1
        return v

    for tname, tobject in template_objects.items():
        if tname == base_template_name:
            base_template_object = copy.deepcopy(tobject)
            base_cfs_branch = tobject["cfs"]["branch"]
        for bootset in tobject["boot_sets"].values():
            results = CLE_BST_RD_RETRY_PARAM_RE_PROG.match(bootset["kernel_parameters"])
            if results:
                used_rd_retry_values.add(int(results.group(2)))
                if tname == base_template_name:
                    base_template_retry_string = results.group(1)
            elif tname == base_template_name:
                base_template_retry_string = None
    retry_val = 10
    base_template_object['description'] = "Template for CRUS integration test, based on %s template" % base_template_name
    # We have previously verified that base_template_object has just 1 boot set
    bootset = any_dict_value(base_template_object["boot_sets"])
    for f in [ 'node_list', 'node_groups', 'node_roles_groups' ]:
        try:
            del bootset[f]
        except KeyError:
            pass
    for i in range(num_to_create):
        retry_val = get_next_unused_retry_value(retry_val)
        new_tname = "crus-test-r%d-%s" % (retry_val, datetime.datetime.utcnow().strftime("%Y%m%d-%H%M%S.%f"))
        create_vcs_branch(vcs_repo_dir, new_tname, base_branch=base_cfs_branch)
        test_vcs_branches.append(new_tname)
        new_retry_string = "rd.retry=%d" % retry_val
        retry_val+=1
        new_test_template_object = copy.deepcopy(base_template_object)
        new_test_template_object["cfs"]["branch"] = new_tname
        new_test_template_object["name"] = new_tname
        # We have previously verified that base_template_object has just 1 boot set
        bootset = any_dict_value(new_test_template_object["boot_sets"])
        if i == 0:
            bootset_xname_list = list(xnames)
            random.shuffle(bootset_xname_list)
            bootset["node_list"] = bootset_xname_list
        else:
            bootset["node_groups"] = [ upgrading_group_name ]
        if base_template_retry_string:
            bootset["kernel_parameters"] = bootset["kernel_parameters"].replace(base_template_retry_string, new_retry_string)
        else:
            bootset["kernel_parameters"] = "%s %s" % (bootset["kernel_parameters"], new_retry_string)
        create_bos_session_template(use_api, new_test_template_object)
        test_template_names.append(new_tname)

        # retrieve our new template to verify it was created successfully
        template_objects[new_tname] = describe_bos_session_template(use_api, new_tname)
