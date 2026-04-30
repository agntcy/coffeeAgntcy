# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""Pydantic v2 types mirroring ``schema/jsonschemas`` (no version suffix on class
names).

The modules under this package are generated from the JSON schemas with the
``jsonschema-to-pydantic-lungo`` skill. Regenerate them after every change to
``event_v1.json`` or ``event_type_v1.json``.

When re-validating dumped JSON against the JSON Schema, use ``model_dump(mode="json", exclude_none=True)``
so optional object fields are omitted instead of serialized as JSON ``null`` (the schema uses ``type: string``,
not ``null``).
"""

from schema.types.event import (
    AgentNode,
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
    PartialAgentNode,
    PartialEdge,
    PartialNode,
    PartialRegularNode,
    PartialTopology,
    RegularNode,
    Size,
    StableAgentId,
    Topology,
    TopologyEdgeItem,
    TopologyNodeItem,
    Workflow,
    WorkflowInstance,
    correlation_id_from_uuid,
    edge_id_from_uuid,
    event_id_from_uuid,
    instance_id_from_uuid,
    node_id_from_uuid,
    stable_agent_id_from_uuid,
)
from schema.types.event_type import EventType

__all__ = [
    "AgentNode",
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
    "PartialAgentNode",
    "PartialEdge",
    "PartialNode",
    "PartialRegularNode",
    "PartialTopology",
    "RegularNode",
    "Size",
    "StableAgentId",
    "Topology",
    "TopologyEdgeItem",
    "TopologyNodeItem",
    "Workflow",
    "WorkflowInstance",
    "correlation_id_from_uuid",
    "edge_id_from_uuid",
    "event_id_from_uuid",
    "instance_id_from_uuid",
    "node_id_from_uuid",
    "stable_agent_id_from_uuid",
]
