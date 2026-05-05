# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""Generated from ``schema/jsonschemas/event_v1.json``.

Do not edit by hand: regenerate with the ``jsonschema-to-pydantic-lungo`` skill.

Source title and description:
    Event (v1) - Message contract for workflow state progress used as an init
    or reset when fully filled. Used by components capable of emitting any
    kind of change event that needs to be communicated.

The class hierarchy mirrors the ``$defs`` of the source schema:

* ``RegularNode`` / ``Edge`` / ``Topology`` are **not** subclasses of their
  partial counterparts: their fields are repeated as required so JSON Schema
  ``allOf`` + ``required`` semantics are preserved without inheriting optional
  ``| None`` fields (Rule C).
* ``PartialAgentNode`` / ``AgentNode`` correspond to ``$defs.partial_agent_node``
  / ``$defs.agent_node``. They subclass the regular node classes because the
  ``partial_node_agent_extension`` / ``node_agent_extension`` composition only
  *adds* fields (Rule D step 1).
* ``$defs.partial_node`` / ``$defs.node`` are sibling-key-discriminated
  ``anyOf`` unions (Rule D): a callable Pydantic ``Discriminator`` mirrors the
  schema's ``not { required: [...] }`` test and routes inputs to the
  ``regular`` or ``agent`` branch; smart-union picks ``Full`` over ``Partial``
  inside each branch.
* Cross-field constraints not expressible in JSON Schema (e.g.
  ``workflow.instances`` map keys must equal the nested ``id``) are encoded as
  Pydantic validators below.
"""

from __future__ import annotations

from enum import StrEnum
from typing import Annotated, Any, Self, Union
from uuid import UUID

from pydantic import (
    AwareDatetime,
    BaseModel,
    ConfigDict,
    Discriminator,
    Field,
    RootModel,
    Tag,
    model_validator,
)

from schema.types.event_type import EventType


# ---------------------------------------------------------------------------
# ``<prefix>://<UUID>`` id types (one per ``$defs.*_id``)
# ---------------------------------------------------------------------------

_UUID_REGEX = (
    r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}"
)
_EVENT_ID_REGEX = rf"^event://{_UUID_REGEX}$"
_CORRELATION_ID_REGEX = rf"^correlation://{_UUID_REGEX}$"
_INSTANCE_ID_REGEX = rf"^instance://{_UUID_REGEX}$"
_NODE_ID_REGEX = rf"^node://{_UUID_REGEX}$"
_STABLE_AGENT_ID_REGEX = rf"^agent://{_UUID_REGEX}$"
_EDGE_ID_REGEX = rf"^edge://{_UUID_REGEX}$"


class EventId(RootModel[str]):
    """Generated from ``$defs.event_id``: unique id for an event message."""

    root: Annotated[
        str,
        Field(
            pattern=_EVENT_ID_REGEX,
            description="Unique id for an event message.",
        ),
    ]


def event_id_from_uuid(event_uuid: UUID) -> EventId:
    """Build a canonical ``event://<uuid>`` id from a ``UUID`` value."""
    return EventId(root=f"event://{event_uuid!s}")


class CorrelationId(RootModel[str]):
    """Generated from ``$defs.correlation_id``: correlation id for one user
    action or API request."""

    root: Annotated[
        str,
        Field(
            pattern=_CORRELATION_ID_REGEX,
            description="Correlation id for one user action or API request.",
        ),
    ]


def correlation_id_from_uuid(correlation_uuid: UUID) -> CorrelationId:
    """Build a canonical ``correlation://<uuid>`` id from a ``UUID`` value."""
    return CorrelationId(root=f"correlation://{correlation_uuid!s}")


class InstanceId(RootModel[str]):
    """Generated from ``$defs.instance_id``: workflow instance id. Each key in
    ``workflow.instances`` must use this same ``instance://...`` value as the
    nested object ``id`` field."""

    root: Annotated[
        str,
        Field(
            pattern=_INSTANCE_ID_REGEX,
            description=(
                "Workflow instance id. Each key in workflow.instances must use this "
                "same instance://... value as the nested object id field."
            ),
        ),
    ]


def instance_id_from_uuid(workflow_instance_uuid: UUID) -> InstanceId:
    """Build a canonical ``instance://<uuid>`` id from a ``UUID`` value."""
    return InstanceId(root=f"instance://{workflow_instance_uuid!s}")


class NodeId(RootModel[str]):
    """Generated from ``$defs.node_id``: graph node id used in topology
    definitions."""

    root: Annotated[
        str,
        Field(
            pattern=_NODE_ID_REGEX,
            description="Graph node id. Used in topology definitions.",
        ),
    ]


def node_id_from_uuid(node_uuid: UUID) -> NodeId:
    """Build a canonical ``node://<uuid>`` id from a ``UUID`` value."""
    return NodeId(root=f"node://{node_uuid!s}")


class StableAgentId(RootModel[str]):
    """Generated from ``$defs.stable_agent_id``: stable, agent-scoped
    identifier for a node, independent of its graph node id."""

    root: Annotated[
        str,
        Field(
            pattern=_STABLE_AGENT_ID_REGEX,
            description=(
                "Stable, agent-scoped identifier for a node, independent of its "
                "graph node id."
            ),
        ),
    ]


def stable_agent_id_from_uuid(stable_agent_uuid: UUID) -> StableAgentId:
    """Build a canonical ``agent://<uuid>`` id from a ``UUID`` value."""
    return StableAgentId(root=f"agent://{stable_agent_uuid!s}")


class EdgeId(RootModel[str]):
    """Generated from ``$defs.edge_id``: graph edge id used in topology
    definitions."""

    root: Annotated[
        str,
        Field(
            pattern=_EDGE_ID_REGEX,
            description="Graph edge id. Used in topology definitions.",
        ),
    ]


def edge_id_from_uuid(edge_uuid: UUID) -> EdgeId:
    """Build a canonical ``edge://<uuid>`` id from a ``UUID`` value."""
    return EdgeId(root=f"edge://{edge_uuid!s}")


# ---------------------------------------------------------------------------
# Enumerations
# ---------------------------------------------------------------------------


class Operation(StrEnum):
    """Generated from ``$defs.operation``: entity operation kind."""

    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"


# ---------------------------------------------------------------------------
# ``$defs.size`` (object with ``additionalProperties: false``)
# ---------------------------------------------------------------------------


class Size(BaseModel):
    """Generated from ``$defs.size``: relative layout size vs other nodes.
    Used in topology drawing and layout algorithms."""

    model_config = ConfigDict(extra="forbid")

    width: float = Field(default=1.0)
    height: float = Field(default=1.0)


# ---------------------------------------------------------------------------
# Node hierarchy (``$defs.partial_regular_node`` / ``regular_node`` /
# ``partial_agent_node`` / ``agent_node`` / ``partial_node`` / ``node``).
#
# ``$defs.partial_node_agent_extension`` and ``$defs.node_agent_extension``
# are not emitted as standalone classes: they are only ever referenced by the
# agent-node compositions, so their fields appear directly on
# ``PartialAgentNode`` / ``AgentNode`` (Rule D step 1 + standalone-emission
# rule).
# ---------------------------------------------------------------------------


class PartialRegularNode(BaseModel):
    """Generated from ``$defs.partial_regular_node``: sparse regular node data
    (mainly for updates). ``additionalProperties: true``; agent-extension keys
    live on the ``PartialAgentNode`` subclass and are routed there by the
    ``$defs.partial_node`` / ``$defs.node`` discriminator."""

    model_config = ConfigDict(extra="allow")

    id: NodeId
    operation: Operation
    type: Annotated[str, Field(min_length=1)] | None = None
    label: Annotated[str, Field(min_length=1)] | None = None
    size: Size | None = None
    layer_index: float = 0


class RegularNode(BaseModel):
    """Generated from ``$defs.regular_node``: full regular node data (mainly
    for init/reset). All listed fields are required. Standalone class (not a
    subclass of ``PartialRegularNode``) so optional ``| None`` field types do
    not leak into the required form."""

    model_config = ConfigDict(extra="allow")

    id: NodeId
    operation: Operation
    type: Annotated[str, Field(min_length=1)]
    label: Annotated[str, Field(min_length=1)]
    size: Size
    layer_index: float


class PartialAgentNode(PartialRegularNode):
    """Generated from ``$defs.partial_agent_node``: ``partial_regular_node``
    combined with ``partial_node_agent_extension``. ``agent_record_uri`` is
    required by the extension; ``stable_agent_id`` remains optional."""

    agent_record_uri: Annotated[str, Field(min_length=1)]
    stable_agent_id: StableAgentId | None = None


class AgentNode(RegularNode):
    """Generated from ``$defs.agent_node``: ``regular_node`` combined with
    ``node_agent_extension``. Both ``agent_record_uri`` and ``stable_agent_id``
    are required."""

    agent_record_uri: Annotated[str, Field(min_length=1)]
    stable_agent_id: StableAgentId


# ``$defs.partial_node`` and ``$defs.node`` are ``anyOf`` choices between a
# *regular* shape and an *agent_node* shape, distinguished by the presence of
# ``agent_record_uri`` / ``stable_agent_id``. We mirror exactly that single
# decision with a callable Pydantic discriminator and let smart union handle
# the *full vs. partial* sub-choice (which is a pure more-required-fields
# question) inside each branch.

_REGULAR_TAG = "regular"
_AGENT_TAG = "agent"


def _node_kind_discriminator(value: Any) -> str | None:
    """Route to the *regular* or *agent* node branch.

    Returns ``"agent"`` when the input carries any
    ``$defs.partial_node_agent_extension`` key (``agent_record_uri`` or
    ``stable_agent_id``); otherwise ``"regular"``.
    """
    if isinstance(value, (AgentNode, PartialAgentNode)):
        return _AGENT_TAG
    if isinstance(value, (RegularNode, PartialRegularNode)):
        return _REGULAR_TAG
    if not isinstance(value, dict):
        return None
    if "agent_record_uri" in value or "stable_agent_id" in value:
        return _AGENT_TAG
    return _REGULAR_TAG


# Generated from ``$defs.topology_node_item`` (anyOf of partial_node and node).
# Within each tagged branch, smart-union picks the full variant when its extra
# required fields are populated and falls back to the partial variant otherwise.
TopologyNodeItem = Annotated[
    Union[
        Annotated[Union[RegularNode, PartialRegularNode], Tag(_REGULAR_TAG)],
        Annotated[Union[AgentNode, PartialAgentNode], Tag(_AGENT_TAG)],
    ],
    Discriminator(_node_kind_discriminator),
]

# Generated from ``$defs.partial_node`` (anyOf).
PartialNode = Annotated[
    Union[
        Annotated[PartialRegularNode, Tag(_REGULAR_TAG)],
        Annotated[PartialAgentNode, Tag(_AGENT_TAG)],
    ],
    Discriminator(_node_kind_discriminator),
]

# Generated from ``$defs.node`` (anyOf).
Node = Annotated[
    Union[
        Annotated[RegularNode, Tag(_REGULAR_TAG)],
        Annotated[AgentNode, Tag(_AGENT_TAG)],
    ],
    Discriminator(_node_kind_discriminator),
]


# ---------------------------------------------------------------------------
# Edge hierarchy (``$defs.partial_edge`` / ``edge`` / ``topology_edge_item``)
# ---------------------------------------------------------------------------


class PartialEdge(BaseModel):
    """Generated from ``$defs.partial_edge``: sparse edge data (mainly for
    updates). ``additionalProperties: true``."""

    model_config = ConfigDict(extra="allow")

    id: EdgeId
    operation: Operation
    type: Annotated[str, Field(min_length=1)] | None = None
    source: NodeId | None = None
    target: NodeId | None = None
    bidirectional: bool = False
    weight: float = 1.0


class Edge(BaseModel):
    """Generated from ``$defs.edge``: full edge data (mainly for init/reset);
    all fields required. Standalone class (not a subclass of
    ``PartialEdge``)."""

    model_config = ConfigDict(extra="allow")

    id: EdgeId
    operation: Operation
    type: Annotated[str, Field(min_length=1)]
    source: NodeId
    target: NodeId
    bidirectional: bool
    weight: float


# Generated from ``$defs.topology_edge_item`` (anyOf).
TopologyEdgeItem = Union[Edge, PartialEdge]


# ---------------------------------------------------------------------------
# Topology (``$defs.partial_topology`` / ``$defs.topology``)
# ---------------------------------------------------------------------------


class PartialTopology(BaseModel):
    """Generated from ``$defs.partial_topology``: sparse topology under a
    workflow instance, describing changes compared to starting or previous
    state."""

    model_config = ConfigDict(extra="allow")

    nodes: list[TopologyNodeItem] | None = None
    edges: list[TopologyEdgeItem] | None = None


class Topology(BaseModel):
    """Generated from ``$defs.topology``: full topology data describing an
    initial state. ``nodes`` and ``edges`` are required. Standalone class (not
    a subclass of ``PartialTopology``) so the optional list types do not leak
    into the required form."""

    model_config = ConfigDict(extra="allow")

    nodes: list[TopologyNodeItem]
    edges: list[TopologyEdgeItem]


# ---------------------------------------------------------------------------
# Correlation, Metadata
# ---------------------------------------------------------------------------


class Correlation(BaseModel):
    """Generated from ``$defs.correlation``: correlation data for an event
    message, referencing another event that closely connects to this one."""

    model_config = ConfigDict(extra="allow")

    id: CorrelationId
    message: str | None = None


class Metadata(BaseModel):
    """Generated from ``$defs.metadata``: general metadata for an event
    message, including fields for proper identification."""

    model_config = ConfigDict(extra="allow")

    timestamp: Annotated[
        AwareDatetime,
        Field(description="When the message was produced (RFC 3339)."),
    ]
    schema_version: Annotated[
        str,
        Field(
            min_length=1,
            description="Semantic version of this contract (e.g. 1.0.0).",
        ),
    ]
    correlation: Correlation
    id: EventId
    type: EventType
    source: Annotated[
        str,
        Field(
            min_length=1,
            description="Producer identifier (e.g. agent or adapter name).",
        ),
    ]


# ---------------------------------------------------------------------------
# Workflow tree (``workflow_instance`` / ``workflow`` / ``data`` / root event)
# ---------------------------------------------------------------------------


class WorkflowInstance(BaseModel):
    """Generated from ``$defs.workflow_instance``: workflow instance data. The
    parent object key under ``workflow.instances`` must be identical to ``id``
    (same ``instance://...`` string)."""

    model_config = ConfigDict(extra="allow")

    id: InstanceId
    topology: PartialTopology


class Workflow(BaseModel):
    """Generated from ``$defs.workflow``: workflow data, describing common
    configuration for a specific workflow, and tracking instances of that
    workflow.

    The ``propertyNames`` constraint on ``instances`` (each key must match
    ``$defs.instance_id``) is encoded directly in the dict key annotation.

    The cross-field constraint that each ``instances`` key must equal the
    nested ``workflow_instance.id`` cannot be expressed in JSON Schema, so it
    is enforced by a ``model_validator`` (mirrors
    ``schema.json_schema._enforce_workflow_instance_map_key_id_match``).
    """

    model_config = ConfigDict(extra="allow")

    pattern: Annotated[str, Field(min_length=1)]
    use_case: Annotated[str, Field(min_length=1)]
    name: Annotated[str, Field(min_length=1)]
    starting_topology: Topology
    instances: dict[
        Annotated[str, Field(pattern=_INSTANCE_ID_REGEX)], WorkflowInstance
    ]

    @model_validator(mode="after")
    def _instance_keys_equal_nested_id(self) -> Self:
        for key, inst in self.instances.items():
            if key != inst.id.root:
                raise ValueError(
                    "instances map key must equal workflow_instance.id: "
                    f"key={key!r} id={inst.id.root!r}"
                )
        return self


class Data(BaseModel):
    """Generated from ``$defs.data``: payload data object containing workflow
    configurations and the targeted instances. ``additionalProperties: true``
    so unknown app-level keys are kept."""

    model_config = ConfigDict(extra="allow")

    workflows: dict[str, Workflow]


class Event(BaseModel):
    """Generated from the top-level ``event_v1`` schema. ``additionalProperties:
    false`` so extra top-level keys are rejected."""

    model_config = ConfigDict(extra="forbid")

    metadata: Metadata
    data: Data
