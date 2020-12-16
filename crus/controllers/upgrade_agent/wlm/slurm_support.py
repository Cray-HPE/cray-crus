"""Supporting functions for Slurm WLM Instances

Copyright 2019, Cray Inc. All rights reserved.
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
