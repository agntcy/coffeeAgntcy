# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""Pydantic v2 models for the event message contract (from ``event_v1.json``).

``Node``, ``Edge``, and ``Topology`` are **not** subclasses of their partial counterparts:
field declarations are repeated with required types so validation matches JSON Schema
``allOf`` + ``required`` without inheriting optional ``| None`` fields.

``AgentNode`` and ``AgentPartialNode`` *are* subclasses of ``Node`` and ``PartialNode``
respectively, extending them with agent-specific fields. Only nodes representing agents carry
these fields; other topology nodes (e.g. transport) do not.
"""

from __future__ import annotations

import re
from enum import StrEnum
from uuid import UUID
from typing import Annotated, Self, Union

from pydantic import (
    AwareDatetime,
    BaseModel,
    ConfigDict,
    Field,
    RootModel,
    field_validator,
    model_validator,
)
from schema.types.event_type import EventType

_UUID_REGEX = (
    r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}"
)
_EVENT_ID_REGEX = rf"^event://{_UUID_REGEX}$"
_CORRELATION_ID_REGEX = rf"^correlation://{_UUID_REGEX}$"
_INSTANCE_ID_REGEX = rf"^instance://{_UUID_REGEX}$"
_NODE_ID_REGEX = rf"^node://{_UUID_REGEX}$"
_EDGE_ID_REGEX = rf"^edge://{_UUID_REGEX}$"
_AGENT_ID_REGEX = rf"^agent://{_UUID_REGEX}$"


class EventId(RootModel[str]):
    root: Annotated[
        str,
        Field(pattern=_EVENT_ID_REGEX, description="Unique id for an event message."),
    ]


class CorrelationId(RootModel[str]):
    root: Annotated[
        str,
        Field(
            pattern=_CORRELATION_ID_REGEX,
            description="Correlation id for one user action or API request.",
        ),
    ]


class InstanceId(RootModel[str]):
    root: Annotated[
        str,
        Field(
            pattern=_INSTANCE_ID_REGEX,
            description="Workflow instance id; map keys under workflow.instances must match nested id.",
        ),
    ]


def instance_id_from_uuid(workflow_instance_uuid: UUID) -> InstanceId:
    """Build canonical ``instance://`` id from a path-segment UUID (see agentic-workflows HTTP routes)."""
    return InstanceId(root=f"instance://{workflow_instance_uuid!s}")


class NodeId(RootModel[str]):
    root: Annotated[str, Field(pattern=_NODE_ID_REGEX, description="Graph node id.")]


class EdgeId(RootModel[str]):
    root: Annotated[str, Field(pattern=_EDGE_ID_REGEX, description="Graph edge id.")]


class AgentId(RootModel[str]):
    root: Annotated[str, Field(pattern=_AGENT_ID_REGEX, description="Stable agent id, invariant across runtime instances of the same agent.")]


class Operation(StrEnum):
    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"


class Size(BaseModel):
    model_config = ConfigDict(extra="forbid")

    width: float = Field(
        default=1.0, description="Relative layout width vs other nodes."
    )
    height: float = Field(
        default=1.0, description="Relative layout height vs other nodes."
    )


_AGENT_SPECIFIC_FIELDS: tuple[str, ...] = ("agent_record_uri", "stable_agent_id")


def _reject_agent_specific_extra_fields(instance: BaseModel) -> None:
    """Reject agent-specific keys if they sneak in via ``extra="allow"``.

    ``Node`` and ``PartialNode`` deliberately do not declare ``agent_record_uri`` or
    ``stable_agent_id``; those belong to the ``AgentNode`` / ``AgentPartialNode``
    subclasses. Because ``extra="allow"`` accepts any extra key with any value,
    without this check an invalid input (e.g. ``agent_record_uri=""`` or
    ``stable_agent_id="not-a-uri"``) would quietly validate as a non-agent node with
    the bogus value in ``__pydantic_extra__``. Rejecting them here forces the
    ``TopologyNodeItem`` union to validate such inputs against the agent subclasses,
    which enforce the format constraints and raise if they are not met.

    Because Agent subclasses declare these as real fields (not extras), this
    validator is a no-op for them.
    """
    extras = instance.__pydantic_extra__
    if extras is None:
        return
    for name in _AGENT_SPECIFIC_FIELDS:
        if name in extras:
            raise ValueError(
                f"{name} is only valid in AgentNode / AgentPartialNode"
            )


class PartialNode(BaseModel):
    """Sparse node (updates); only ``id`` and ``operation`` are required."""

    model_config = ConfigDict(extra="allow")

    id: NodeId
    operation: Operation
    type: Annotated[str, Field(min_length=1)] | None = None
    label: Annotated[str, Field(min_length=1)] | None = None
    size: Size | None = None
    layer_index: float = 0

    @model_validator(mode="after")
    def _no_agent_specific_fields(self) -> Self:
        _reject_agent_specific_extra_fields(self)
        return self


class Node(BaseModel):
    """Full node (init/reset); all listed fields are required (not a subclass of ``PartialNode``)."""

    model_config = ConfigDict(extra="allow")

    id: NodeId
    operation: Operation
    type: Annotated[str, Field(min_length=1)]
    label: Annotated[str, Field(min_length=1)]
    size: Size
    layer_index: float

    @model_validator(mode="after")
    def _no_agent_specific_fields(self) -> Self:
        _reject_agent_specific_extra_fields(self)
        return self


class AgentPartialNode(PartialNode):
    """Sparse node representing an agent; extends ``PartialNode``.
    
    At least some fields in this model class need to be required because otherwise
    the validation would fall through to the PartialNode model class and possibly validate as a non-agent node.
    """

    agent_record_uri: Annotated[str, Field(min_length=1)]
    stable_agent_id: AgentId | None = None


class AgentNode(Node):
    """Full node representing an agent; extends ``Node``.
    
    At least some fields in this model class need to be required because otherwise
    the validation would fall through to the Node model class and possibly validate as a non-agent node.
    """

    agent_record_uri: Annotated[str, Field(min_length=1)]
    stable_agent_id: AgentId


class PartialEdge(BaseModel):
    """Sparse edge (updates)."""

    model_config = ConfigDict(extra="allow")

    id: EdgeId
    operation: Operation
    type: Annotated[str, Field(min_length=1)] | None = None
    source: NodeId | None = None
    target: NodeId | None = None
    bidirectional: bool = False
    weight: float = 1.0


class Edge(BaseModel):
    """Full edge (init/reset); all fields required."""

    model_config = ConfigDict(extra="allow")

    id: EdgeId
    operation: Operation
    type: Annotated[str, Field(min_length=1)]
    source: NodeId
    target: NodeId
    bidirectional: bool
    weight: float


TopologyNodeItem = Union[AgentNode, Node, AgentPartialNode, PartialNode]
TopologyEdgeItem = Union[Edge, PartialEdge]


class PartialTopology(BaseModel):
    model_config = ConfigDict(extra="allow")

    nodes: list[TopologyNodeItem] | None = None
    edges: list[TopologyEdgeItem] | None = None


class Topology(BaseModel):
    """Full topology; ``nodes`` and ``edges`` required (standalone, not a subclass of ``PartialTopology``)."""

    model_config = ConfigDict(extra="allow")

    nodes: list[TopologyNodeItem]
    edges: list[TopologyEdgeItem]


class Correlation(BaseModel):
    model_config = ConfigDict(extra="allow")

    id: CorrelationId
    message: str | None = None


class Metadata(BaseModel):
    model_config = ConfigDict(extra="allow")

    timestamp: Annotated[
        AwareDatetime,
        Field(description="When the message was produced (RFC 3339)."),
    ]
    schema_version: Annotated[
        str,
        Field(
            min_length=1, description="Semantic version of this contract (e.g. 1.0.0)."
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


class WorkflowInstance(BaseModel):
    model_config = ConfigDict(extra="allow")

    id: InstanceId
    topology: PartialTopology


class Workflow(BaseModel):
    model_config = ConfigDict(extra="allow")

    pattern: Annotated[str, Field(min_length=1)]
    use_case: Annotated[str, Field(min_length=1)]
    name: Annotated[str, Field(min_length=1)]
    starting_topology: Topology
    instances: dict[str, WorkflowInstance]

    @field_validator("instances")
    @classmethod
    def _instance_keys_are_instance_ids(
        cls, v: dict[str, WorkflowInstance]
    ) -> dict[str, WorkflowInstance]:
        key_re = re.compile(_INSTANCE_ID_REGEX)
        for key in v:
            if not key_re.match(key):
                msg = f"instances map key must match instance id pattern: {key!r}"
                raise ValueError(msg)
        return v

    @model_validator(mode="after")
    def _instance_keys_match_nested_id(self) -> Self:
        for key, inst in self.instances.items():
            if key != inst.id.root:
                msg = (
                    f"instances map key must equal workflow_instance.id: key={key!r} "
                    f"id={inst.id.root!r}"
                )
                raise ValueError(msg)
        return self


class Data(BaseModel):
    """``data`` subtree on the wire and accumulated workflow-instance store state."""

    model_config = ConfigDict(extra="allow")

    workflows: dict[str, Workflow] = Field(default_factory=dict)


class Event(BaseModel):
    """Root event message: ``metadata`` and ``data`` required; no extra top-level properties."""

    model_config = ConfigDict(extra="forbid")

    metadata: Metadata
    data: Data
