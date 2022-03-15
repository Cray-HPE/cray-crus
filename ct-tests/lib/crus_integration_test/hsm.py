#
# MIT License
#
# (C) Copyright 2020-2022 Hewlett Packard Enterprise Development LP
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
HSM-related BOS limit test helper functions
"""

from common.helpers import debug
from common.hsm import create_hsm_group

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
