# Introduction

CRUS is the Shasta service that manages Compute Node Rolling Upgrades.
It provides a way to upgrade a set of compute nodes in discrete steps
(i.e. a few nodes at a time) gracefully, coordinating with Workload
Managers and with the Boot Orchestration Service (BOS) to take nodes
out of service, boot them and put them back into service while
minimally impacting the availabilty of nodes to do work under a
workload manager.

Further documentation of how to use CRUS can be found
[here](Compute_Rolling_Upgrade_Instructions.md).

These notes explain the implementation of CRUS and highlight some key
aspects of which developers might need to be aware.

If you want an overview, with pictures, check out the
[Compute Rolling Upgrade Service](https://connect.us.cray.com/confluence/pages/viewpage.action?pageId=145958102)
confluence page as well.

# Implementation Walk Through

CRUS follows the Model / View / Controller (MVC) design pattern in
which the service is divided into three elements: a Model referring to
the data model that defines and drives the abstraction presented by
the service, one or more Views which permit interaction with the model
(e.g. creation of an upgrade session definition), and one or more
Controllers which consume and update the data in the Model while they
drive the changes into the broader system to reflect the desired state
stored in the Model.

The code in CRUS is the final arbiter of what the API presented to
clients will look like and how it will behave, so, instead of building
the CRUS code around an API specification, the API specification grows
organically from the code.  This is accomplished using the tools
provided by the Flask, Marshmallow and APISpec Python libraries and by
careful use of Python DocStrings and description / example metadata in
the CRUS data model.  The API specification is generated on every
commit of the code using git hooks, and, if it changes, updated to
reflect the change.

## The Structure of CRUS as a Service

As noted above, CRUS breaks down logically into Model, View and
Controller elements.  The Model is mostly an abstraction, but it can
be seen to reside in the ETCD based data store that backs CRUS data.
The View is provided by the first of two active processes (each in its
own container, but we will get to that later) that make up the active
elements of CRUS.  It serves CRUD requests on the CRUS REST API.  The
Controller is provided by the second of the active processes (a
different entry point than the View), which monitors changes to ETCD
and drives the upgrade process as dictated by those changes.

### The Model

The CRUS Model is defined by the code in the 'crus/models' directory.
There is one object defined by the CRUS Model: an Upgrade Session.  If
you look in this file, you will find three Python classes, two of
which (`UpgradeSession` and `UpgradeSessionSchema`) are part of the
CRUS model and one of which (`ComputeUpgradeProgress`) is used to hold
onto internal state for the Controller (more on this when I talk about
the Controller).

The `UpgradeSession` class defines the data in terms of an
`Etcd3Model`, which is a base class provided by the Cray developed
etcd3_model Python library.  For more information on `Etcd3Model`
objects and how to define and use them, see the `etd3_model` library
[README](https://github.com/Cray-HPE/etcd3_model/README.md)
file.  The `UpgradeSessionSchema` class defines a Marshmallow (Python
Library) Schema object which wraps around `UpgradeSession` objects and
helps to serialize and deserialize them.  This Marshmallow Schema also
provides the metadata needed to document what an Upgrade Session looks
like in the CRUS API Specification.  This latter part is handled at the end of the file in the following code:

```
UPGRADE_SESSIONS_SCHEMA = UpgradeSessionSchema(many=True)
UPGRADE_SESSION_SCHEMA = UpgradeSessionSchema()
SPEC.definition('upgrade_session', schema=UPGRADE_SESSION_SCHEMA)
```

This provides two instances of the schema, one used for serializing
and deserializing lists of Upgrade Session objects and one used for
serializing and deserializing individual Upgrade Session objects.  It then
registers the individual Upgrade Session schema with the APISpec
library as an `upgrade_session` schema in the API Specification.

For the most part, the code will concern itself with the
`UpgradeSession` class, which contains the actual upgrade data, and
these two schema instances, used to produce and present
`UpgradeSession` objects on the API Server.

### The View

The View is defined by the functions found in
'crus/views/upgrade_session.py' and 'crus/views/swagger.py'.  The
former defines the API for creating, retrieving, and deleting Upgrade
Sessions (there is no update operation because an Upgrade Session runs
to completion and changing it in flight presents an unnecessary risk
of introducing an inconsistency into the upgrade).  The latter
provides an API for retrieving the API specification.

The view is presented by a Flask (Python Library) application which,
in production, runs under 'gunicorn' as a web front-end.  It can also
be run stand-alone as is seen in 'crus/wsgi.py'.

Creation of an Upgrade Session causes an `UpgradeSession` object to be
created in ETCD and indexed by its Object Key, which, in the case of
an `UpgradeSession`, is its `upgrade_id` field (a UUID string)
automatically assigned by the etcd3_model library.  The Upgrade
Session, once created and stored in ETCD will trigger the Controller
(more on this below) to start performing the upgrade.

Retrieval of an Upgrade Session either takes the form of listing all
available Upgrade Sessions (when no `upgrade-id` is specified in the
request) or retrieving a single upgrade session by its `upgrade-id`.
This entails a call to either `UpgradeSession.get_all()` which
retrieves all `UpgradeSession` objects from ETCD, or
`UpgradeSession.get()` which retrieves a single `UpgradeSession` object
from ETCD.

Deletion of an Upgrade Session sets a `DELETING` state in the
UpgradeSession object in ETCD, which triggers the Controller to drive
the session to the point where all resources have been cleaned up and
the object can be deleted.  Once the object reaches that point, the
Controller deletes it.

The request 'route' functions defined in these two files contain both
the code to perform API operations and the API documentation in the
form of function DocStrings.  They are registered with the APISpec
library through a three stage process, starting in the Python file
where they are defined, where they are gathered into a list called
PATHS at the end of the file:

```
PATHS = [
    upgrade_session_list_route,
    specific_upgrade_session_route,
]
```

These lists are then picked up by the __init__.py file for
'crus/views' as follows:

```
from ..app import add_paths, install_swagger
from . import upgrade_session
from . import swagger

# Set swagger paths
add_paths(swagger.PATHS)
add_paths(upgrade_session.PATHS)
```

and installed in the API Specification using the `add_paths()` calls
shown above.

### The Controller

The Controller is centered in
'crus/controllers/upgrade_agent/upgrade_agent.py' but the code for the
Controller is everything under the 'crus/controllers' directory.

The heart of the controller is a watcher loop: `watch_sessions()`, the
actual watcher: `process_upgrade()`, and a state machine that handles
execution and deletion of `UpgradeSession` objects.  The etcd3_model
library provides a method for registering for 'watch' events at the
`Etcd3Model` derived class (e.g. `UpgradeSession`) level.  In CRUS,
the Controller calls `UpgradeSession.watch()` to obtain a watch queue,
then calls `UpgradeSession.learn()` to trigger an initial flow of
`UpgradeSession` objects to the watcher.  From there the watcher
processes incoming events in the form of `UpgradeSession` objects as
they are updated in ETCD.

Execution and deletion of Upgrade Sessions progresses through a state
machine that executes the various 'stages' of an upgrade or of cleaning
up an upgrade.  This state machine has two sequences: the Upgrade
Sequence and the Delete Sequence.  At any point in the Ugrade
Sequence, the state machine can detect that an Upgrade Session is in
the `DELETING` state, and switch to the Delete Sequence.  Once in the
Delete Sequence, the Upgrade Session can never go back to the Upgrade
Sequence.

The Upgrade Sequence follows the following stages for each 'step'
(subset of nodes to be upgraded) of an upgrade:

1. `STARTING`: prepare the step for upgrading and begin quiescing the
step nodes in the Workload Manager.  Advance to `QUIESCING`.

2. `QUIESCING`: wait for the step nodes to be quiet in the Workload
Manager. When all step nodes are quiet, advance to `QUIESCED`.

3. `QUIESCED`: initiate boot of the step nodes.  Advance to `BOOTING`.

4. `BOOTING`: wait for the Boot Session for the step to complete.  When
it does, advance to `BOOTED`.

5. `BOOTED`: check success or failure of the Boot Session.  On sucess,
advance to `WLM_WAITING`.  On failure, handle the failure, advance to
the next step (next set of nodes), and return to `STARTING`.

6. `WLM_WAITING`: wait for all step nodes to either return to service
in the WLM or time out returning to service in the WLM.  Handle nodes
that timeout as failed nodes.  In either case, advance to the next
step (next set of nodes) and return to `STARTING`.

7. `CLEANUP`: the entire Upgrade Session has either completed or been
deleted.  Clean up interim resources, in the DELETING case, remove the
Upgrade Session.  In the non-DELETING case, set the Upgrade Session to
Completed and to READY so it will not be processed again until it
enters the `DELETING` state.

When an Upgrade Session enters the `DELETING` state (regardless of the
processing stage it is in) it uses the same stages.  It decides
whether it is deleting *before* or *after* entering the `BOOTING`
stage for the current step.  If it is deleting before enterring
`BOOTING` and the current step is 0, the Upgrade Session simply
advances to the `CLEANUP` stage because there is no further processing
to do on this step or the remaining steps.  If the current step is
greater than 0, then all nodes in all incomplete steps (including this
one) that have not come back into service in the WLM are processed as
failed nodes.  After that, advance to `CLEANUP`.

If the Upgrade Session enters `DELETING` after `BOOTING`, all nodes in
all incomplete steps (including this one) are processed as failed
nodes.  After that advance to `CLEANUP`.

The actual driving of the state machine follows this (simplified)
process:

1. the watcher waits on the watch queue for an Upgrade Session (there
is some magic here relating to scheduling defered updates to Upgrade
Sessions, which we discuss below)

2. the watcher discards any Upgrade Session that does not require
processing (for example, the `completed` field is `True`) or is
scheduled for deferral.

3. the watcher attempts to lock the Upgrade Session using the
distributed locking provided by etcd3_model, if it fails to acquire
the lock, the watcher discards the Upgrade Session (assuming some other
part of CRUS, perhaps another Controller, perhaps an API Server, is
already holding the lock) and goes back to step 1.

4. now that it has the lock, the watcher refreshes its copy of the
Upgrade Session to ensure it has the latest content.

5. The watcher obtains (or creates if it does not yet exist) the
`ComputeUpgradeProgress` object associated with the Ugrade Session.
This is an `Etcd3Model` object defined in 'crus/models/upgrade_session'
which is keyed by the Upgrade Session Upgrade ID and lasts for the
duration of the Upgrade Session execution.  It contains all state
needed to process its associated Upgrade Session.  Because it is
stored in ETCD3, it permits scaling and restart of Controllers (any
CRUS Controller that receives an Upgrade Session watch event can
obtain the lock and process it).

6. From the `ComputeUpgradeProgress` object, the watcher determines
what 'step' and 'stage' the Upgrade Session is in, and chooses the
nodes for that 'step' and the handler function for that 'stage'.

6. The watcher calls the handler function passing in the Upgrade
Session, the `ComputeUpgradeProgress`, and the list of nodes in the
current step.

7. The handler executes a single non-iterative, non-blocking
idempotent increment of the upgrade, updates the
`ComputeUpgradeProgress` with new state, and returns to the
watcher (there are various ways this can happen, which I will get into
below).

8. The watcher releases the lock then updates the Upgrade Session
with, at least, a message indicating what just happened, to trigger a
new watch event to keep the watcher fed (again, there are variations
on this that I will describe below).

9. The watcher goes back to step 1 to wait for another Upgrade Session
object.

This simplified process has a few variations that I have alluded to
above.  Mostly these are driven by the conditions at the end of
processing by a handler.  The following things may happen within a
handler:

1. progress is made with further work to be done (or no progress is
made, but what we are waiting for should not take a long time),

2. no progress is made (i.e. the stage is waiting for completion of
some process) and what we are waiting for will take a while,

3. an exception occurs indicating a failure of some kind in the stage.

4. progress is made resulting in no further work to do (i.e. the
Upgrade Session is complete),


In case #1, the handler returns a non-empty string describing what
progress was made.  This will be used to post a message to the the
`Etcd3Model` object part of the Upgrade Session, informing the client of
what has been done and triggering an immediate watch event on the
Upgrade Session.

In case #2, the handler returns `None`, indicating that the watcher
should hold off on triggering a new watch event on this Upgrade
Session.  In this case the watcher will queue a scheduled update for
this Controller instance.  When the Upgrade Session ID reaches its
scheduled time, it will be updated with a NULL update to trigger a new
watch event.  Non-deletion watch events received by this Controller
Instance on a scheduled Upgrade Session will be discarded (see step 2
of the watcher sequence above) until the scheduled time.  This reduces
load when we are waiting for a longer term event.

In case #3, the exception is caught and translated into a message
which is posted to the Upgrade Session.  The session is then scheduled
for a future update.  The posted message *does* cause a single watch
event to arrive, but, because the Upgrade Session is pending when it
is next seen, it will be discarded (see step 2 of the watcher sequence
above) by this Controller Instance until its appointed time.  This
gives the client a chance to clear the error condition or delete the
Upgrade Session while reducing load from the Controller.

In case #4, the handler sets Upgrade Session `completed` field to
`True`, then sets the Etcd3Model part of the Upgrade Session to READY.
The former means no further processing is needed on this Upgrade
Session, so it can be discarded when learning the Upgrade Sessions in
the future.  The latter shuts off watch events on the Upgrade Session
so the watcher will not see it again until a `learn()` call or
transition to `DELETING` occurs.  The handler then returns a string to
be posted as a message (currently "Upgrade Session Completed").

### Access to Other Shasta Constructs

The Controller drives state out into Shasta and consumes information
from Shasta.  To achieve this, the Controller implements abstractions
of the external Shasta constructs with which it interacts.  The
following sub-sections briefly describe each of these abstractions and
the mechanisms they use.

#### Boot Service Abstraction

The Boot Service Abstraction is found in
'crus/controllers/upgrade_agent/boot_service/boot_session.py'.

The Boot Service Abstraction provides a `BootSession` class that
communicates with the BOS API to instantiate Boot Sessions.  It also
provides methods for monitoring the progress and sucess or failure of
active boot sessions using the Kubernetes Job API.  To keep track of
the session and some state, it uses an `Etcd3Model` derivative
`BootSessionProgress` object indexed to the Upgrade Session Upgrade ID
for Boot Session State.

Currently, the Boot Session abstraction tracks BOA jobs using the
Kubernetes Jobs API to know when a Boot Session completes and whether
it succeeded or failed.  Eventually, that information should be
available through the BOS API directly, at which point the Kubernetes
interaction should be removed.

#### BSS Hosts Abstraction

The BSS Hosts Abstraction is found in
'crus/controllers/upgrade_agent/bss_hosts/bss_hosts.py'.

The BSS Hosts Abstraction provides a `BSSHostTable` class that makes it
easy to interact with host information and do things like translate
between xnames and nids.  It also provides access to attributes of
hosts that can be found in BSS.

The `BSSHostTable` is loaded from BSS using the BSS Hosts API.

#### Node Group Abstraction

The Node Group Abstraction is found in
'crus/controllers/upgrade_agent/node_group/node_group.py'.

The Node Group Abstraction provides a `NodeGroup` class that allows
creation and manipulation of HSM Node Groups by label.  It uses the
HSM Groups API.

#### Node Table Abstraction

The Node Table Abstraction is found in
'crus/controllers/upgrade_agent/node_table/node_table.py'.

The Node Table Abstraction wraps around information from the BSS Hosts
abstraction and provides tools for manipulating and querying node
information.

# Test Driven Development

CRUS is developed with detailed unit testing in mind to make sure that
each step forward is, in fact, a step forward and does not cause
regression.  The keys to this are:

* Fully automated unit testing,

* Simple but robust mocking of relevant elements of the Shasta
environment (including error and other kinds of injection),

* Use of nox for Linting, Style Checking, Testing and Code coverage,

* Use of nox in builds to ensure that builds pass Lint, Style, Tests
and Coverage in the Jenkins pipeline.

## Fully Automated Unit Tests

The tests in CRUS reside in a separate tree from the Python library
code.  This is a 'tests' directory parallel to the 'crus' directory in
the root of the source repository.  The tests run under 'pytest' and
exercise all of the elements of CRUS.

A group of test cases is placed in a python source file with a name
starting with 'test_' anywhere beneath the 'tests' directory.  A test
case is a function with a name beginning with 'test_'.  If the test
runs to completion and returns nothing, it passes.  All of the tests
use 'assert' statements liberally to interrupt the test when a tested
condition is not met.

## Mocking

CRUS uses fairly extensive mocking and simulation of Shasta resources
to permit stand-alone testing of most conditions encountered by CRUS
code.  The simulation built into the mocking is designed to provide an
accurate enough representation of the resource behavior that replacing
the mocked resource with the real resource occurs seamlessly.

In addition to mocking provided by CRUS itself, CRUS takes advantage
of ETCD mocking that is built into the etcd3_model python library to
permit stand alone testing in the absence of an ETCD instance.

### Mocking of Service APIs

CRUS mocks Service APIs by instantiating simulations of their APIs
under a mock 'requests' library.  The mock requests library provides
both an API calling path and a way to tie Python classes in as mock
Service APIs.  This permits each service to be toggled between its
mock version and its real version simply by changing a configuration
setting at run time with no need to vary any production code path.

The mock 'requests' library is found in
'crus/controllers/mocking/shared/requests.py'.

Mock services are found by service name in
'crus/controllers/mocking/<service_name>/<service_name>_api.py'.  For
example, the BSS API mocking is found in
'crus/controllers/mocking/bss/bss_api.py'.

Inside this file you will find a class for each mocked path that
inherits from the `requests.Path` base class, and implements the
necessary methods on that path.  In addition you will find a
`start_service()` function that instantiates the `requests.Path`
derivatives presented by that mock service.

Other supporting files for the mock service can reside in the same
directory and are named as the developer sees fit.

### Mocking of Shell Commands

The CRUS Controller uses some shell commands (most notably Slurm and,
potentially, other WLM commands as part of performing an upgrade.  The
CRUS Controller uses the 'shell' Python library to invoke these
commands and capture their output.  CRUS mocking provides a mock
'shell' library that works similarly to the mock 'requests' library
described above.

The mock 'shell' library is found in
'crus/controllers/mocking/shared/shell.py'.

The only current mock command is 'scontrol' which is found in
'crus/controllers/mocking/slurm/scontrol.py'.  The command is
implemented as an `ScontrolCmd` class which is derived from
`shell.Command` and implements a `run()` method that takes an argument
vector (`argv`).  The `run()` method acts as the main entrypoint for
the mock command.  It then branches out to other methods that
implement specific things within the command as needed.

### Mocking of Kubernetes Jobs

CRUS currently uses Kubernetes to monitor BOA jobs.  This requires
mocking of the Kubernetes Jobs API and simulation of job lifecycles.
This mocking is found in
'crus/controllers/mocking/kubernetes/client.py` and
'crus/controllers/mocking/kubernetes/config.py'.

The BOS Service mocking creates mock BOA jobs in mock Kubernetes, and
mock Kubernetes implements the needed Kubernetes API functions to
simulate that job lifecycle.

### Mocking of ETCD

CRUS uses ETCD for its storage throught the etcd3_model library.  The
etcd3_model library provides its own ETCD mocking to support its own
functions and unit tests, so there is no direct mocking of ETCD in
CRUS.  ETCD mocking is enabled by passing in the correct environment
variable settings to turn on ETCD mocking at run time.

See
[the etcd3_model Stash repo](https://github.com/Cray-HPE/etcd3_model)
for more details.

## Use of nox and pytest For Testing / Linting / Style

CRUS uses nox to orchestrate running of Lint, Style Checking, Unit
Tests and Coverage Reporting on CRUS in a consistent environment.  All
proposed changes to CRUS must pass Lint, Style, all Unit Tests, and a
code coverage of at least 95% to be eligible for release.  The
Dockerfile incorporates a test stage that runs the full nox suite at
build time, so to emerge from the Jenkins build pipeline without a
failure all of the above conditions must be met.

## 100% Unit Test Code Coverage

While the Dockerfile / noxfile permit the code to pass with 95% or
better code coverage, CRUS makes the goal of every potentially
releasable change 100% code coverage with judicious use of coverage
pragmas to handle cases that cannot be tested cost-effectively.  The
benefit of 100% code coverage is that code reviewers can then
concentrate on the sections of code that are covered by coverage
pragmas and high level logic, and developers can be certain that, to
the extent possible, every line of code has been both translated and
executed by Python.  Since runtime errors make up a large part of
Python failures, execution of every statement helps keep the code
solid.

100% coverage does not ensure fully working code.  It is possible to
execute a line of code successfully without yielding the expected
result.  Assurance of code correctness relies on proper testing and
result checking at the unit test level.  100% coverage does, however,
help to prevent obvious runtime failures.

# Deployment Structure

On a Shasta system CRUS is deployed as a Kubernetes Service using
Helm.  Currently the service consists of a single Kubernetes
Deployment containing CRUS specific ETCD instances and a single
'cray-crus' Kubernetes Pod made up of the following containers (in
addition to the sidecars and init containers for istio and ETCD access):

* The cray-crus container which provides the CRUS API server and is
reachable as a REST API.

* the cray-crua container which provides the CRUS Controller (the name
of the container is a throwback to when cray-crua was a separate
Kubernetes Pod invoked by CRUS).

* the munge side-car container which runs 'munge' to provide tokens
for authentication with the 'slurm' Workload Manager controller.

The Kubernetes Deployment could be scaled up to multiple 'cray-crus'
Kubernetes Pods for resiliency or for increased parallelism, though,
because of the way upgrade sessions are processed by the Controller
should permit many parallel upgrades to run without noticable changes
in performance, so parallelism is probably less of a consideration.

The definition of the deployment is found at the top of the source
repository in 'kubernetes/cray-crus/values.yaml'

To support necessary interaction with the Kubernetes Jobs API, there
is also a `cray-crus-actor` ServiceAccount defined that permits the
CRUS Controller to monitor Kubernetes Job status.  The definition of
that ServiceAccount is found in the top of the source repository at
'kubernetes/cray-crus/templates/crus-actor.yaml'.

There is a Confluence Page with pictures of the CRUS Deployment Structure
[here](https://connect.us.cray.com/confluence/pages/viewpage.action?pageId=145958102).
