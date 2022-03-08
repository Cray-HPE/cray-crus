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
"""Mock scontrol command to support testing of Rolling Compute Upgrade

"""
import sys
from ..shared import shell
from .slurm_state import SlurmNodeTable

SHOW_FMT = """
NodeName={nodename} Arch=x86_64 CoresPerSocket=4
   CPUAlloc=0 CPUTot=8 CPULoad=0.00
   AvailableFeatures=(null)
   ActiveFeatures=(null)
   Gres=(null)
   NodeAddr={node_addr} NodeHostName={node_host} Version=18.08
   OS=Linux 4.12.14-15.5_8.1.81-cray_shasta_c #1 SMP Mon Apr 29 20:28:40 UTC 2019 (068432c)
   RealMemory=38272 AllocMem=0 FreeMem=37804 Sockets=2 Boards=1
   State={state}{substate}{node_state} ThreadsPerCore=1 TmpDisk=0 Weight=1 Owner=N/A MCS_label=N/A
   Partitions=workq
   BootTime=2019-05-03T01:16:48 SlurmdStartTime=2019-05-03T04:04:20
   CfgTRES=cpu=8,mem=38272M,billing=8
   AllocTRES=
   CapWatts=n/a
   CurrentWatts=0 LowestJoules=0 ConsumedJoules=0
   ExtSensorsJoules=n/s ExtSensorsWatts=0 ExtSensorsTemp=n/s
   {reasonstring}
"""[1:-1]

REASON_FMT = "Reason={reason} [root@{reason_time}]"


class ScontrolCmd(shell.Command):
    """Mock up of the 'scontrol' command.

    """
    def run(self, argv):
        """Run method executes commands like scontrol would.  This is a
        limited scontrol mock-up that supports the following:

        - scontrol show node

        - scontrol show node node_name

        - scontrol update Nodename=<node_name> State=DRAIN|FAIL Reason="<reason>"

        - scontrol update Nodename=<node_name> State=RESUME

        all other commands will fail.
        """
        cmdname = None
        sub_cmd = None
        spec = None
        try:
            err = "empty argv -- should not happen"
            cmdname = argv.pop(0)
            err = "%s: requires sub-command: 'show' or 'update'" % cmdname
            sub_cmd = argv.pop(0)
            if sub_cmd == 'show':
                err = "%s: expected 'node [node_name]" % (cmdname)
                if argv.pop(0) != 'node':
                    # Cheat!!!!
                    raise IndexError("next element was not node")
                spec = argv
            elif sub_cmd == 'update':
                spec = argv
            else:
                # Cheat again!!!
                err = "%s: unknown sub-command '%s'" % (cmdname, sub_cmd)
                raise IndexError(err)
        except IndexError:
            print(err, file=sys.stderr)
            return 1
        if sub_cmd == 'show':
            return self.show(cmdname, spec)
        return self.update(cmdname, spec)

    def show(self, cmdname, spec):  # pylint: disable=unused-argument
        """Implement the 'show' sub-command.

        """
        nodenames = ([spec[0]] if spec else SlurmNodeTable.get_all_names())
        for name in nodenames:
            node_addr = SlurmNodeTable.get_node_addr(name)
            node_host = SlurmNodeTable.get_node_host(name)
            state, substate, node_state = SlurmNodeTable.get_state(name)
            if substate in ['DRAIN', 'FAIL'] or node_state == "*":
                reason, rtime = SlurmNodeTable.get_reason(name)
            else:
                reason = None
                rtime = None
            if node_addr is None:
                # This node was not known, complain and skip
                print("unknown node %s" % name, file=sys.stderr)
                continue
            reason_string = ""
            if substate:
                substate = "+%s" % substate
            else:
                substate = ""
            if reason:
                reason_string = REASON_FMT.format(reason=reason,
                                                  reason_time=rtime)
            show_str = SHOW_FMT.format(nodename=name,
                                       node_addr=node_addr,
                                       node_host=node_host,
                                       state=state,
                                       substate=substate,
                                       node_state=node_state,
                                       reasonstring=reason_string)
            print(show_str)
        return 0

    def update(self, cmdname, spec):
        """Implement the 'update' sub-command.

        """
        nvps = {}
        for item in spec:
            name, value = item.split('=')
            if name.lower() not in ["nodename", "state", "reason"]:
                print("%s: unexpected item in spec: '%s' "
                      "expected nodename, state or reason" % (cmdname, name),
                      file=sys.stderr)
                return 1
            nvps[name.lower()] = value
        if 'nodename' not in nvps:
            print("%s: node name must be present in spec" % (cmdname),
                  file=sys.stderr)
            return 1
        nodename = nvps['nodename']
        if 'state' not in nvps:
            print("%s: state must be present in spec" % (cmdname),
                  file=sys.stderr)
            return 1
        state = nvps['state']
        reason = None
        if state in ['DRAIN', 'FAIL']:
            if 'reason' not in nvps:
                print("%s: reason must be present in spec for FAIL and DRAIN"
                      % (cmdname), file=sys.stderr)
                return 1
            reason = nvps['reason']
        if state == 'RESUME' and 'reason' in nvps:
            print("%s: reason must not be in spec for RESUME"
                  % cmdname, file=sys.stderr)
            return 1
        if state == 'DRAIN':
            SlurmNodeTable.drain(nodename, reason)
        elif state == 'FAIL':
            SlurmNodeTable.fail(nodename, reason)
        elif state == 'RESUME':
            SlurmNodeTable.resume(nodename)
        else:
            print("%s: unexpected state '%s' specified for update" %
                  (cmdname, state), file=sys.stderr)
            return 1
        return 0


def install_scontrol():
    """Install the 'scontrol' mock command in the system

    """
    ScontrolCmd("scontrol")
