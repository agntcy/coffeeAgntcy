# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""Pydantic v2 models for the event message contract (from ``event_v1.json``).

``Node``, ``Edge``, and ``Topology`` are **not** subclasses of their partial counterparts:
field declarations are repeated with required types so validation matches JSON Schema
``allOf`` + ``required`` without inheriting optional ``| None`` fields.
"""

from __future__ import annotations

import re
from enum import StrEnum
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


class NodeId(RootModel[str]):
    root: Annotated[str, Field(pattern=_NODE_ID_REGEX, description="Graph node id.")]


class EdgeId(RootModel[str]):
    root: Annotated[str, Field(pattern=_EDGE_ID_REGEX, description="Graph edge id.")]


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


class PartialNode(BaseModel):
    """Sparse node (updates); only ``id`` and ``operation`` are required."""

    model_config = ConfigDict(extra="allow")

    id: NodeId
    operation: Operation
    type: Annotated[str, Field(min_length=1)] | None = None
    label: Annotated[str, Field(min_length=1)] | None = None
    size: Size | None = None
    layer_index: float = 0
    agent_record_uri: Annotated[str, Field(min_length=1)] | None = None


class Node(BaseModel):
    """Full node (init/reset); almost all listed fields are required (not a subclass of ``PartialNode``)."""

    model_config = ConfigDict(extra="allow")

    id: NodeId
    operation: Operation
    type: Annotated[str, Field(min_length=1)]
    label: Annotated[str, Field(min_length=1)]
    size: Size
    layer_index: float
    agent_record_uri: Annotated[str, Field(min_length=1)] | None = None


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


TopologyNodeItem = Union[Node, PartialNode]
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
    model_config = ConfigDict(extra="allow")

    workflows: dict[str, Workflow]

    @field_validator("workflows")
    @classmethod
    def _workflows_min_one(cls, v: dict[str, Workflow]) -> dict[str, Workflow]:
        if len(v) < 1:
            raise ValueError("workflows must contain at least one property")
        return v


class Event(BaseModel):
    """Root event message: ``metadata`` and ``data`` required; no extra top-level properties."""

    model_config = ConfigDict(extra="forbid")

    metadata: Metadata
    data: Data
