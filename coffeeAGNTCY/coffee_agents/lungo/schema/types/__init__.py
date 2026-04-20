# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""Hand-maintained Pydantic v2 types mirroring ``schema/jsonschemas`` (no version suffix on class names).

Update these modules when ``event_v1.json`` or ``event_type_v1.json`` changes; they are not generated.

When re-validating dumped JSON against the JSON Schema, use ``model_dump(mode="json", exclude_none=True)``
so optional object fields are omitted instead of serialized as JSON ``null`` (the schema uses ``type: string``,
not ``null``).
"""

from schema.types.event import (
    AgentId,
    AgentNode,
    AgentPartialNode,
    Correlation,
    CorrelationId,
    Data,
    Edge,
    EdgeId,
    Event,
    EventId,
    InstanceId,
    Metadata,
    Node,
    NodeId,
    Operation,
    PartialEdge,
    PartialNode,
    PartialTopology,
    Size,
    Topology,
    TopologyEdgeItem,
    TopologyNodeItem,
    Workflow,
    WorkflowInstance,
)
from schema.types.event_type import EventType

__all__ = [
    "AgentId",
    "AgentNode",
    "AgentPartialNode",
    "Correlation",
    "CorrelationId",
    "Data",
    "Edge",
    "EdgeId",
    "Event",
    "EventId",
    "EventType",
    "InstanceId",
    "Metadata",
    "Node",
    "NodeId",
    "Operation",
    "PartialEdge",
    "PartialNode",
    "PartialTopology",
    "Size",
    "Topology",
    "TopologyEdgeItem",
    "TopologyNodeItem",
    "Workflow",
    "WorkflowInstance",
]
