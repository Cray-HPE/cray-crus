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

"""Supporting functions for Slurm WLM Instances

"""
import re


def parse_show_node(lines):
    """Parse the output from an scontrol show node into a dictionary of
    string name value pairs.

    """
    pairs = []
    for line in lines:
        line = re.sub(r"  *$", "", line)  # Remove trailing whitespace
        line = re.sub(r"^  *", "", line)  # Remove leading whitespace
        if not line:
            # Skip empty lines
            continue
        if line.count('=') > 1:
            pairs.extend(line.split())
        else:
            pairs.append(line)
    nvps = {}
    for pair in pairs:
        split = pair.split('=')
        # Pairs that don't parse to a pair are not of interest to us.
        # Slurm has some weird structuring rules, but the fields that
        # use them are not interesting to what we are doing.  Just
        # skip pairs that don't parse well.
        if len(split) == 2:
            name, value = split
            nvps[name] = value
    return nvps


def parse_show_all_nodes(lines):
    """Parse the output from 'scontrol show node' into a dictionary of
    nodes and their settings.

    """
    nodes = {}
    parse_lines = []
    lines.append(None)  # put in a marker for the end...
    for line in lines:
        if line is None or line[0:8] == "NodeName":
            if parse_lines:
                nvps = parse_show_node(parse_lines)
                nodes[nvps['NodeName']] = nvps
            if line is not None:
                parse_lines = [line]
            continue
        parse_lines.append(line)
    return nodes
