"""Data Model and Schemas for the 'upgrade_session' model of CRUS

Copyright 2019, Cray Inc. All rights reserved.

"""
from marshmallow import fields, post_load
from etcd3_model import (
    Etcd3Model,
    Etcd3Attr,
    clean_desc,
    STATE_DESCRIPTION,
    MESSAGES_DESCRIPTION
)
from ..version import API_VERSION
from ..app import APP, SPEC, ETCD, MA

# Stage name constants for ComputeUpgradeProgress
STARTING = "STARTING"
QUIESCING = "QUIESCING"
QUIESCED = "QUIESCED"
BOOTING = "BOOTING"
BOOTED = "BOOTED"
WLM_WAITING = "WLM_WAITING"
CLEANUP = "CLEANUP"


def _no_upgrade_id():  # pragma should never happen
    """Default for upgrade_id, raises an exception because instantiating a
    ComputeUpgradeProgress without an Upgrade ID is not permitted.

    """
    reason = "'upgrade_id' must be specified in constructor of "\
        "ComputeUpgradeProgress objects"
    raise AttributeError(reason)


class ComputeUpgradeProgress(Etcd3Model):
    """An ETCD persisted object to track the progress of (and state of)
    ComputeUpgradeSessions.

    Fields:

    upgrade_id

        The Upgrade ID of the associated Upgrade Session.  This is the
        Object ID.

    step

        The current step number of the rolling upgrade, used to track
        progress through the rolling part of the upgrade.

    stage

        The current stage of an upgrade the associated session is in,
        used to drive the upgrade forward each time the session
        triggers a watch.  There are stages within a step and stages
        before and after all of the steps.  This is interpreted in the
        context that is appropriate.

    boot_complete_time

        The numeric time at which the boot session completed, used to
        determine when to give up on WLM nodes coming back into
        service.

    completed_nodes

        The list of nodes in a step that have come back into service
        in the WLM.

    """
    etcd_instance = ETCD
    model_prefix = "%s/%s" % (APP.config['ETCD_PREFIX'], "upgrade_progress")

    upgrade_id = Etcd3Attr(is_object_id=True, default=_no_upgrade_id)
    step = Etcd3Attr(default=0)
    stage = Etcd3Attr(default=STARTING)
    boot_complete_time = Etcd3Attr(default=None)
    completed_nodes = Etcd3Attr(default=[])


class UpgradeSession(Etcd3Model):
    """
    Upgrade Session Model

        Fields:
            upgrade_id: the (UUID) id of the upgrade session
            kind: "ComputeUpgradeSession"
            api_version: the api version of for this session parameter set
            starting_label: the node label on the set of nodes to be upgraded
            upgrading_label: the node label used to boot each step of nodes
                             in the rolling upgrade.
            failed_label: the node label to apply to nodes that fail to upgrade
            workload_manager_type: the name of the workload manager controlling
                                   the nodes with the starting label.
            upgrade_step_size: a positive integer specifying the number of
                               nodes to upgrade at a time.
            upgrade_template_id: The Boot Orchestration Service (BOS) Boot
                                 Session Template ID (UUID) to be used for
                                 this upgrade.  The Node Groups label in
                                 this template must exactly match the
                                 value of 'upgrading_label' above.
            completed: A boolean indicating whether processing on this
                       Upgrade Session has completed or not.  Internally
                       set but externally visible for convenience.
    """
    etcd_instance = ETCD
    model_prefix = "%s/%s" % (APP.config['ETCD_PREFIX'], "session")

    # The Object ID used to locate each Tenant instance
    upgrade_id = Etcd3Attr(is_object_id=True)  # Read only

    # The kind of object that the data here represent.  Should always
    # contain "ComputeUpgradeSession".  Protects against stray data
    # types.
    kind = Etcd3Attr(default="ComputeUpgradeSession")  # Read only

    # The API version corresponding to this upgrade session's data.
    # Will always be equal to the API version under which the data
    # were stored in ETCD.  Protects against incompatible upgrade
    # session.
    api_version = Etcd3Attr(default=API_VERSION)  # Read only

    # The node label on the set of nodes to be upgraded
    starting_label = Etcd3Attr(default=None)

    # The node label of the intermediate group used for booting nodes
    # in each ste of the rolling upgrade
    upgrading_label = Etcd3Attr(default=None)

    # The node label to apply to nodes that fail to upgrade
    failed_label = Etcd3Attr(default=None)

    # The name of the workload manager controlling the nodes with the
    # starting label.
    workload_manager_type = Etcd3Attr(default="slurm")

    # A positive integer specifying the number of nodes to upgrade at
    # a time.
    upgrade_step_size = Etcd3Attr(default=1)

    # The Boot Service (BOS) Boot Session Template ID of the Boot
    # Session Template to be used for this upgrade.  The group section
    # of this template must exactly match the label in
    # 'upgrading_label'.
    upgrade_template_id = Etcd3Attr(default=None)

    # A boolean indicating whether processing on this Upgrade Session
    # has completed or not.  Internally set but externally visible for
    # convenience.
    completed = Etcd3Attr(default=False)


KIND_DESCRIPTION = clean_desc(
    """
    The kind of object that the data here represent.  Should always
    contain "ComputeUpgradeSession".  Protects against stray data
    types.
    """
)

API_VERSION_DESCRIPTION = clean_desc(
    """
    The API version corresponding to this upgrade session's data.
    Will always be equal to the API version under which the data
    were stored in ETCD.  Protects against incompatible upgrade
    session.
    """
)


STARTING_LABEL_DESCRIPTION = clean_desc(
    """
    The node label on the set of nodes to be upgraded.
    """
)

UPGRADING_LABEL_DESCRIPTION = clean_desc(
    """
    The node label used to identify the empty node group that will be
    used to boot and reconfigure each step of the rolling upgrade.
    This must exactly match the node label specified in the Boot
    Session Template configured for this upgrade.
    """
)

FAILED_LABEL_DESCRIPTION = clean_desc(
    """
    The node label to apply to nodes that fail to upgrade.
    """
)

WORKLOAD_MGR_TYPE_DESC = clean_desc(
    """
    The name of the workload manager controlling the nodes with the
    starting label.  Currently supported value: 'slurm'.
    """
)

UPGRADE_STEP_SIZE_DESC = clean_desc(
    """
    A positive integer specifying the number of nodes to upgrade at
    a time.
    """
)

UPGRADE_TEMPLATE_ID_DESC = clean_desc(
    """
    The Boot Orchestration Service (BOS) Boot Session Template ID
    (UUID) used to identify the Boot Session Template used to reboot
    and reconfigure nodes during this rolling upgrade.  The single
    node group label configured in this Boot Session Template must
    exactly match the 'upgrading_label' in this Upgrade Session.
    """
)
SAMPLE_UPGRADE_TEMPLATE_ID = "a4cfe939-6057-4137-94b6-3de46157cb53"

COMPLETED_DESC = clean_desc(
    """
    A boolean indicating whether processing on this Upgrade Session
    has completed or not.  Internally set but externally visible for
    convenience.
    """
)


# pylint: disable=too-many-ancestors
class UpgradeSessionSchema(MA.Schema):
    """
    Schema for an upgrade session
    """
    upgrade_id = fields.Str(description="The (UUID) id of the upgrade session",
                            required=False)

    kind = fields.Str(description=KIND_DESCRIPTION,
                      example="ComputeUpgradeSession",
                      required=False)

    api_version = fields.Str(description=API_VERSION_DESCRIPTION,
                             example=API_VERSION,
                             required=False)

    starting_label = fields.Str(description=STARTING_LABEL_DESCRIPTION,
                                example="slurm-nodes",
                                validate=(
                                    lambda l: isinstance(l, str) and l
                                ),
                                required=True)

    upgrading_label = fields.Str(description=UPGRADING_LABEL_DESCRIPTION,
                                 example="upgrading-slurm-nodes",
                                 validate=(
                                     lambda l: isinstance(l, str) and l
                                 ),
                                 required=True)

    failed_label = fields.Str(description=FAILED_LABEL_DESCRIPTION,
                              example="failed-slurm-nodes",
                              validate=(
                                  lambda l: isinstance(l, str) and l
                              ),
                              required=True)

    workload_manager_type = fields.Str(description=WORKLOAD_MGR_TYPE_DESC,
                                       example="slurm",
                                       required=True)

    upgrade_step_size = fields.Int(description=UPGRADE_STEP_SIZE_DESC,
                                   example=50,
                                   validate=(
                                       lambda x: isinstance(x, int) and x > 0
                                   ),
                                   required=True)

    upgrade_template_id = fields.Str(description=UPGRADE_TEMPLATE_ID_DESC,
                                     example=SAMPLE_UPGRADE_TEMPLATE_ID,
                                     required=True)

    completed = fields.Bool(description=COMPLETED_DESC,
                            example=False,
                            required=False)

    state = fields.Str(description=STATE_DESCRIPTION)

    messages = fields.List(fields.Str(description=MESSAGES_DESCRIPTION))

    @post_load
    def make_obj(self, data):
        """ Deserialize to a Partition
        """
        upgrade_session = UpgradeSession(**data)
        return upgrade_session

    class Meta:
        """Add back the 'partition_id' field to the fields accessed through
        this schema, good for displaying the partition.

        """
        strict = True
        fields = (
            'upgrade_id',
            'kind',
            'api_version',
            'starting_label',
            'upgrading_label',
            'failed_label',
            'workload_manager_type',
            'upgrade_step_size',
            'upgrade_template_id',
            'completed',
            'state',
            'messages',
        )
        dump_only = (
            'upgrade_id',
            'kind',
            'api_version',
            'completed',
            'state',
            'messages',
        )


UPGRADE_SESSIONS_SCHEMA = UpgradeSessionSchema(many=True)
UPGRADE_SESSION_SCHEMA = UpgradeSessionSchema()
SPEC.definition('upgrade_session', schema=UPGRADE_SESSION_SCHEMA)
