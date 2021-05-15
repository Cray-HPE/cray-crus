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
Parses command line arguments for CRUS integration test.

Usage: crus_integration_test.py [--nids <A>[-<B>][,<C>[-<D>]]... ] 
                                [--groups <A>[,<B>...]] 
                                [--xnames <A>[,<B>...]] 
                                [--template <bos_session_template_name>] 
                                [--max-step-size n]
                                [-v] {api|cli}

The nodes to use will be the union of all nodes specified via --nids and --xnames, plus
all nodes belonging to any group specified via --groups.

Examples of legal --nids arguments:
--nids 1
--nids 1,5
--nids 1-3
--nids 1,3,5-10

If no nodes are specified (through any combination of --nids, --groups, and --xnames), 
it will use all compute nodes. At least 3 nodes are required for the test to run.

If no BOS session template is specified, the slurm template will be used.
"""

import argparse
from common.argparse import positive_integer, valid_api_cli, \
                            valid_hsm_group_list, valid_nid_list, \
                            valid_session_template_name, valid_xname_list

def valid_step_size(s):
    """
    argparse argument validation helper function.
    Wrapper for positive_integer with argname set.
    """
    return positive_integer("Step size", s)

def valid_number_of_steps(s):
    """
    argparse argument validation helper function.
    Wrapper for positive_integer with argname set.
    """
    return positive_integer("Number of steps", s)

TEST_DESCRIPTION = [
    "Tests CRUS by using it to reboot sets of nodes, verifying that the right things happen.",
    "Nodes may be specified by any combination of --nids, --groups, and --xnames arguments.",
    "If no nodes are specified, all compute nodes will be used.", 
    "At least 3 nodes are required for the test to run." ]

def parse_args(test_variables):
    """
    Parse the command line arguments and return the specified nids, template, use_api, and verbose 
    parameters (or their default values)
    """
    parser = argparse.ArgumentParser(
        description=" ".join(TEST_DESCRIPTION))
    parser.add_argument("--nids", dest="nids", type=valid_nid_list, 
        help="List or range of nids to use for test", 
        metavar="a[-b][,c[-d]]...", default=list())
    parser.add_argument("--groups", dest="groups", type=valid_hsm_group_list, 
        help="List of HSM group names containing the nodes to use for test", 
        metavar="a[,b]...", default=list())
    parser.add_argument("--max-step-size", dest="max_step_size", type=valid_step_size,
        help="Maximum number of nodes per CRUS step", metavar="#", default=None)
    parser.add_argument("--template", dest="template", type=valid_session_template_name, 
        help="Name of BOS session template to copy for test (default: slurm)",
        metavar="bos_session_template_name", default="slurm")
    parser.add_argument("-v", dest="verbose", action="store_const", const=True, 
        help="Enables verbose output (default: disabled)")
    parser.add_argument("--xnames", dest="xnames", type=valid_xname_list, 
        help="List of node xnames to use for test", 
        metavar="{ a[,b]... }", default=list())
    parser.add_argument("api_or_cli", type=valid_api_cli, metavar="{ api | cli }", 
        help="Specify whether the test should use API or CLI calls")

    args = parser.parse_args()
    test_variables["use_api"] = (args.api_or_cli == 'api')
    test_variables["nids"] = args.nids
    test_variables["groups"] = args.groups
    test_variables["xnames"] = args.xnames
    test_variables["max_step_size"] = args.max_step_size
    test_variables["template"] = args.template
    test_variables["verbose"] = (args.verbose == True)
