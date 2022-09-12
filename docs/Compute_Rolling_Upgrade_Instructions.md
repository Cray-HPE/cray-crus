# Introduction

The Compute Rolling Upgrade Service (CRUS) of Shasta permits an
administrator to upgrade a set of compute nodes without the need to take
the entire set of nodes out of service at once.  It manages the workload
management status of nodes, quiescing each node before taking the node
out of service, upgrading the node, rebooting the node into the upgraded
state and then returning the node to service within the workload manager
to which the node belongs.

## Key Concepts

A compute upgrade proceeds in 'steps' of a particular size (number of
nodes).  The nodes in each step are taken out of service in the
workload manager to prevent work from being scheduled, upgraded,
re-booted, and put back into service in the workload manager.  By
working one step at a time, CRUS allows the administrator to limit the
impact on production resulting from an upgrade.

The Compute Rolling Upgrade process is built upon a few basic features
of the Shasta management system:

* Grouping of nodes by label provided by the Hardware State Manager (HSM)
'groups' mechanism,

* Workload management that can gracefully take nodes out of service
(quiesce nodes), declare nodes as failed, and return nodes to service.

* The Boot Orchestration Service (BOS), and, in particular, BOS Boot Session
Templates.

## Procedure Overview
The procedure for running a Compute Rolling Upgrade is as follows:

1. Determine the nature and scope of your upgrade and prepare the
necessary artifacts. Detailed information on this is beyond the scope of
these instructions, but guidance can be found in the
*System Administrator's Guide*.

2. Create an HSM Node Group containing the list of node IDs (X-Names)
that are to be upgraded (see below). This is called the Starting
Node Group (starting label) (see below).

3. Create an empty HSM Node Group for Compute Rolling Upgrade to
use for booting nodes in each step of the upgrade (see below). This is
called the Upgrading Node Group (upgrading label) (see below).

4. Create an empty HSM Node Group for Compute Rolling Upgrade to use
to capture nodes that fail to upgrade for some reason (see below).  This
is called the Failed Node Group (failed label) (see below).

5. Create a Boot Orchestration Service (BOS) Session Template
describing the upgrade.  The details of this are mostly beyond the
scope of these instructions and can be found in **NEED DOCUMENT
NAME**.  One important note is that, for Compute Upgrade, the node
group list in this template must contain **exactly** one node group
label and it must **match** the Upgrading Node Group label in 3 above.
Also there must be **no nodes listed individually in the template.**

6. Create a CRUS session specifying the Starting Node Group by its
label, the upgrade step size (i.e. the number of nodes to be upgraded in
a given step), the workload manager type (currently the only supported
workload manager is 'slurm'), the BOS session template id to be used for
the upgrade and the Failed and Upgrading Node Group labels (see below).

7. Monitor the status of the Upgrade Session until it completes (see
below).

8. If a problem arises that prevents the Upgrade Session from
proceeding, fix the problem.  The Upgrade Session should resume
processing from that point.

9. If a problem arises that results in failed upgrade nodes, identify
and fix the problem and re-run the upgrade on only the nodes in the
Failed Node Group (see below).

10. Once the Upgrade Session has run cleanly to completion, delete the
upgrade session (see below).

# Detailed Procedures

## Create and Populate the Starting Node Group (Starting Label)

To create a Starting Node Group with the label 'slurm-nodes'
use the following CLI command:

```
$ cray hsm groups create --label slurm-nodes --description 'Starting Node Group for my Compute Node upgrade'
```

Here is what the execution will look like:

```
$ cray hsm groups create --label slurm-nodes --description 'Starting Node Group for my Compute Node upgrade'
[[results]]
URI = "/hsm/v1/groups/slurm-nodes"
```

Once the node group is created, you can add members to the group as
follows:

```cray hsm groups members create slurm-nodes --id <xname>```

where `<xname>` is the X-Name of a compute node in the group.  You
should do this with the X-Names of every node you want to upgrade.

```
$ cray hsm groups members create slurm-nodes --id x0c0s28b0n0
[[results]]
URI = "/hsm/v1/groups/slurm-nodes/members/x0c0s28b0n0"
```

## Create the Upgrading Node Group (Upgrading Label)

To create an Upgrading Node Group with the label 'upgrading-nodes'
use the following CLI command:

```
$ cray hsm groups create --label upgrading-nodes --description 'Upgrading Node Group for my Compute Node upgrade'
```

There is no need to add members to this group, since it should be empty
when the Compute Rolling Upgrade Process begins.

## Create the Failed Node Group (Failed Label)

To create a Failed Node Group with the label 'failed-nodes'
use the following CLI command:

```
$ cray hsm groups create --label failed-nodes --description 'Failed Node Group for my Compute Node upgrade'
```

There is no need to add members to this group, since it should be empty
when the Compute Rolling Upgrade Process begins.

## Create the CRUS Upgrade Session

To create your CRUS uprgade session using the node group labels shown
above upgrading 50 nodes at a step, use the following CLI command:

```
$ cray crus session create \
       --starting-label slurm-nodes \
       --upgrading-label upgrading-nodes \
       --failed-label failed-nodes \
       --upgrade-step-size 50 \
       --workload-manager-type slurm \
       --upgrade-template-id=<template-UUID>
```

Where `<template-UUID>` is the ID (UUID) of the boot session template in
BOS that you plan to use for the upgrade.

Here is some sample output:

```
$ cray crus session create --starting-label slurm-nodes --upgrading-label upgrading-nodes --failed-label failed-nodes --upgrade-step-size 50 --workload-manager-type slurm --upgrade-template-id boot-template
api_version = "1.0.0"
completed = false
failed_label = "failed-nodes"
kind = "ComputeUpgradeSession"
messages = []
starting_label = "slurm-nodes"
state = "UPDATING"
upgrade_id = "e0131663-dbee-47c2-aa5c-13fe9b110242"
upgrade_step_size = 50
upgrade_template_id = "boot-template"
upgrading_label = "upgrading-nodes"
workload_manager_type = "slurm"
```

Notice the `upgrade_id` field of this output.  This will be used to
monitor the progress of the upgrade session.

## Monitor the CRUS Upgrade Session Status

To monitor the status of your upgrade session, periodically use the
following CLI command:

```
$ cray crus session describe <upgrade-id>
```

where `<upgrade-id>` is the Upgrade Session ID of the upgrade session you are
monitoring.  Here is some sample output:

```
api_version = "1.0.0"
completed = false
failed_label = "failed-nodes"
kind = "ComputeUpgradeSession"
messages = [ "Quiesce requested in step 0: moving to QUIESCING", "All nodes quiesced in step 0: moving to QUIESCED", "Began the boot session for step 0: moving to BOOTING",]
starting_label = "slurm-nodes"
state = "UPDATING"
upgrade_id = "e0131663-dbee-47c2-aa5c-13fe9b110242"
upgrade_step_size = 50
upgrade_template_id = "boot-template"
upgrading_label = "upgrading-nodes"
workload_manager_type = "slurm"
```

If you don't know what value of `<upgrade-id>` to use, you
can use:

```
$ cray crus session list
```

to list all of the sessions present, and look for the one that matches
your session, then find the `upgrade_id` field in that session.

Here is sample output:

```
$ cray crus session list
[[results]]
api_version = "1.0.0"
completed = false
failed_label = "failed-nodes"
kind = "ComputeUpgradeSession"
messages = [ "Quiesce requested in step 0: moving to QUIESCING", "All nodes quiesced in step 0: moving to QUIESCED", "Began the boot session for step 0: moving to BOOTING",]
starting_label = "slurm-nodes"
state = "UPDATING"
upgrade_id = "e0131663-dbee-47c2-aa5c-13fe9b110242"
upgrade_step_size = 50
upgrade_template_id = "boot-template"
upgrading_label = "upgrading-nodes"
workload_manager_type = "slurm"
```

The progress of the session through the upgrade process is described
in the `messages` field of your session.  This is a list of messages,
in chronological order, containing information about stage transitions
(see below), step transitions (see below) and other conditions of
interest encountered by your session as it progresses.  It is cleared
once your session completes.

When your session completes, you will see two things:

* the `state` field will contain the word `READY`,

* the `completed` field will be `true`

Here is a sample of a completed session:

```
$ cray crus session describe e0131663-dbee-47c2-aa5c-13fe9b110242
api_version = "1.0.0"
completed = true
failed_label = "failed-nodes"
kind = "ComputeUpgradeSession"
messages = [ "Upgrade Session Completed",]
starting_label = "slurm-nodes"
state = "READY"
upgrade_id = "e0131663-dbee-47c2-aa5c-13fe9b110242"
upgrade_step_size = 50
upgrade_template_id = "boot-template"
upgrading_label = "upgrading-nodes"
workload_manager_type = "slurm"
```

A CRUS session goes through some number of 'steps' (approximately the
number of nodes to be upgraded divided by the requested step size) to
complete an upgrade, and each step moves through the following 'stages'
unless the boot session is interrupted by being deleted:

1. Starting - preparation for the step: initiate WLM quiescing of nodes.

2. Quiescing - waits for all WLM nodes in the step to reach a quiesced
  (i.e. not busy) state.

3. Quiesced - the nodes in the step are all quiesced: initiates booting
  the nodes into the upgraded environment.

4. Booting - waiting for the boot session to complete.

5. Booted - the boot session has completed: check the success or failure
   of the boot session.  Mark all nodes in the step as 'failed' if the
   boot session failed.

6. WLM Waiting - the boot session succeeded: wait for nodes to reach a
   'ready' state in the Workload Manager.  All nodes in the step that fail
   to reach a 'ready' state within 10 minutes of entering this stage are
   marked as failed.

7. Cleanup - the upgrade step has finished: clean up resources to
   prepare for the next step.

When a step moves from one stage to the next, CRUS adds a message to the
`messages` field of the upgrade session to mark the progress.

## Recovering from an Incorrect Upgrade Session

It is possible that your upgrade session may fail to start because you
failed to set up the starting conditions correctly or because you
specified something incorrectly.  If this happens, you have two
choices:

* fix the problem, which will permit the session to resume and complete, or

* delete the session and try again with correct parameters

Here is an example where the user forgot to create the failed node
group label:

```
$ cray crus session describe 2c7fdce6-0047-4421-9676-4301d411d14e
api_version = "1.0.0"
completed = false
failed_label = "failed-node-group"
kind = "ComputeUpgradeSession"
messages = [ "Processing step 0 in stage STARTING failed - failed to obtain Node Group named 'failed-node-group' - {\"type\":\"about:blank\",\"title\":\"Not Found\",\"detail\":\"No such group: failed-node-group\",\"status\":404}\n[404]",]
starting_label = "slurm-nodes"
state = "UPDATING"
upgrade_id = "2c7fdce6-0047-4421-9676-4301d411d14e"
upgrade_step_size = 50
upgrade_template_id = "dummy-boot-template"
upgrading_label = "dummy-node-group"
workload_manager_type = "slurm"
```

Notice in the messages:

```
messages = [ "Processing step 0 in stage STARTING failed - failed to obtain Node Group named 'failed-node-group' - {\"type\":\"about:blank\",\"title\":\"Not Found\",\"detail\":\"No such group: failed-node-group\",\"status\":404}\n[404]",]
```

To fix the problem, the user creates a new node group `failed-node-group`:

```
$ cray hsm groups create --label failed-node-group
[[results]]
URI = "/hsm/v1/groups/failed-node-group"
```

A few seconds later, you can see the session is underway:

```
$ cray crus session describe 2c7fdce6-0047-4421-9676-4301d411d14e
api_version = "1.0.0"
completed = false
failed_label = "failed-node-group"
kind = "ComputeUpgradeSession"
messages = [ "Processing step 0 in stage STARTING failed - failed to obtain Node Group named 'failed-node-group' - {\"type\":\"about:blank\",\"title\":\"Not Found\",\"detail\":\"No such group: failed-node-group\",\"status\":404}\n[404]", "Quiesce requested in step 0: moving to QUIESCING", "All nodes quiesced in step 0: moving to QUIESCED", "Began the boot session for step 0: moving to BOOTING",]
starting_label = "slurm-nodes"
state = "UPDATING"
upgrade_id = "2c7fdce6-0047-4421-9676-4301d411d14e"
upgrade_step_size = 50
upgrade_template_id = "dummy-boot-template"
upgrading_label = "dummy-node-group"
workload_manager_type = "slurm"
```

It can take several seconds for a session to resume after a problem
has been fixed, but, if all is well, it will resume.  If there is still a
problem it will show up in the `messages` field.

Suppose the user had instead specified an incorrect starting node group:

```
$ cray crus session create --starting-label slurm-node-group --upgrading-label dummy-node-group --failed-label failed-node-group --upgrade-step-size 50 --workload-manager-type slurm --upgrade-template-id dummy-boot-template
api_version = "1.0.0"
completed = false
failed_label = "failed-node-group"
kind = "ComputeUpgradeSession"
messages = []
starting_label = "slurm-node-group"
state = "UPDATING"
upgrade_id = "d388c6f5-be67-4a31-87a9-819bb4fa804c"
upgrade_step_size = 50
upgrade_template_id = "dummy-boot-template"
upgrading_label = "dummy-node-group"
workload_manager_type = "slurm"
```

A similar problem would show up in `messages`:

```
$ cray crus session describe d388c6f5-be67-4a31-87a9-819bb4fa804c
api_version = "1.0.0"
completed = false
failed_label = "failed-node-group"
kind = "ComputeUpgradeSession"
messages = [ "Processing step 0 in stage STARTING failed - failed to obtain Node Group named 'slurm-node-group' - {\"type\":\"about:blank\",\"title\":\"Not Found\",\"detail\":\"No such group: slurm-node-group\",\"status\":404}\n[404]",]
starting_label = "slurm-node-group"
state = "UPDATING"
upgrade_id = "d388c6f5-be67-4a31-87a9-819bb4fa804c"
upgrade_step_size = 50
upgrade_template_id = "dummy-boot-template"
upgrading_label = "dummy-node-group"
workload_manager_type = "slurm"
```

In this case, it makes more sense to delete and re-create the session:

```
cray crus session delete d388c6f5-be67-4a31-87a9-819bb4fa804c
api_version = "1.0.0"
completed = false
failed_label = "failed-node-group"
kind = "ComputeUpgradeSession"
messages = [ "Processing step 0 in stage STARTING failed - failed to obtain Node Group named 'slurm-node-group' - {\"type\":\"about:blank\",\"title\":\"Not Found\",\"detail\":\"No such group: slurm-node-group\",\"status\":404}\n[404]",]
starting_label = "slurm-node-group"
state = "DELETING"
upgrade_id = "d388c6f5-be67-4a31-87a9-819bb4fa804c"
upgrade_step_size = 50
upgrade_template_id = "dummy-boot-template"
upgrading_label = "dummy-node-group"
workload_manager_type = "slurm"


$ cray crus session create --starting-label slurm-nodes --upgrading-label dummy-node-group --failed-label failed-node-group --upgrade-step-size 50 --workload-manager-type slurm --upgrade-template-id dummy-boot-template
api_version = "1.0.0"
completed = false
failed_label = "failed-node-group"
kind = "ComputeUpgradeSession"
messages = []
starting_label = "slurm-nodes"
state = "UPDATING"
upgrade_id = "135f9667-6d33-45d4-87c8-9b09c203174e"
upgrade_step_size = 50
upgrade_template_id = "dummy-boot-template"
upgrading_label = "dummy-node-group"
workload_manager_type = "slurm"
```

If we look at the new session we see that it is now underway:

```
$ cray crus session describe 135f9667-6d33-45d4-87c8-9b09c203174e
api_version = "1.0.0"
completed = false
failed_label = "failed-node-group"
kind = "ComputeUpgradeSession"
messages = [ "Quiesce requested in step 0: moving to QUIESCING", "All nodes quiesced in step 0: moving to QUIESCED", "Began the boot session for step 0: moving to BOOTING",]
starting_label = "slurm-nodes"
state = "UPDATING"
upgrade_id = "135f9667-6d33-45d4-87c8-9b09c203174e"
upgrade_step_size = 50
upgrade_template_id = "dummy-boot-template"
upgrading_label = "dummy-node-group"
workload_manager_type = "slurm"
```

## Find Failed Nodes and Re-Run the Upgrade on Them

Failed nodes result from three causes:

* Failure of the BOS upgrade session for a given step of the upgrade
  causes all of the nodes in that step to be marked as failed.

* Failure of any given node in a step to reach a 'ready' state in the
  workload manager within 10 minutes of detecting that the BOS boot
  session has completed causes that node to be marked as failed.

* Deletion of a Compute Node Upgrade session while the current step is
  at or beyond the 'Booting' stage causes all of the nodes in that
  step that have not reached a 'ready' state in the workload manager to
  be marked as failed.

When a node is marked as failed, two things happen:

* The node is added to the Failed Node Group associated with the upgrade
  session, and

* The node is marked as 'down' in the workload manager.  If the workload
  manager supports some kind of 'reason' string, that string contains
  the cause of the 'down' status.

Once a session has completed, you can see which nodes failed the
upgrade by listing the contents of the failed node group:

```
$ cray hsm groups describe failed-nodes
```

In this sample output, the node `x0c0s28b0n0` has failed:

```
$ cray hsm groups describe failed-nodes
label = "failed-nodes"
description = ""

[members]
ids = [ "x0c0s28b0n0",]
```

Before re-running an upgrade on failed nodes, determine the cause of the
failed nodes and fix it.  Once the cause has been fixed, you can proceed
to re-run the upgrade.

To re-run an upgrade on failed nodes, create a new (empty) Failed Node
Group with a different name, then construct a new upgrade session
specifying the label of the failed node group as the Starting Label and
using the new Failed Node Group as the Failed Label and using the rest
of the parameters that you used in the original upgrade unchanged.

## Delete the CRUS Upgrade Session

Once you have successfully run a CRUS Upgrade Session it is complete and
cannot be re-used.  You may leave it in place for historical purposes if
you choose, or you may delete it.  If you choose to delete it, use the
following CLI command:

```
$ cray crus session delete <upgrade-id>
```

where `<upgrade-id>` is the Upgrade Session ID of the upgrade session as
described above in *Monitor the CRUS Upgrade Session Status*.

Here is sample output:

```
$ cray crus session delete e0131663-dbee-47c2-aa5c-13fe9b110242
api_version = "1.0.0"
completed = true
failed_label = "failed-nodes"
kind = "ComputeUpgradeSession"
messages = [ "Upgrade Session Completed",]
starting_label = "slurm-nodes"
state = "DELETING"
upgrade_id = "e0131663-dbee-47c2-aa5c-13fe9b110242"
upgrade_step_size = 50
upgrade_template_id = "boot-template"
upgrading_label = "upgrading-nodes"
workload_manager_type = "slurm"
```

Notice that the session sticks around briefly after a delete.  This
allows for orderly cleanup of the session.  When it is gone, you will
see it is gone as follows:

```
(cli_env) C02K2185DKQ2:craycli erl$ cray crus session list
results = []
```

NOTE: if there were more than one session present at the time of the
delete, you would see other sessions, but not the one you created.

You may delete a CRUS session at any time.  If you delete a CRUS session
while it is in progress, the session terminates as soon as it reaches a
point where it can clean up and remove itself.  This results in an
incomplete upgrade, and, possibly, nodes marked as failed.  It is up to
you to do whatever recovery or re-submission of an update is appropriate
at that point.
