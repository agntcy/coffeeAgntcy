# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""Transport-agnostic builders for workflow topology events (event_v1)."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Mapping
from uuid import uuid4

from schema.types import (
    Correlation,
    CorrelationId,
    Data,
    EdgeId,
    Event,
    EventId,
    EventType,
    InstanceId,
    Metadata,
    NodeId,
    Operation,
    PartialAgentNode,
    PartialBaseNode,
    PartialEdge,
    PartialNode,
    PartialTopology,
    Size,
    StableAgentId,
    Topology,
    Workflow,
    WorkflowInstance,
)

from common.workflow_utils.inflight import (
    RuntimeIdAllocator,
    format_span_id,
    format_trace_id,
)
from common.workflow_utils.workflow_catalog import WorkflowMetadata

SCHEMA_VERSION = "1.2.0"

_DEFAULT_NODE_SIZE = Size(width=1.0, height=1.0)


def init_starting_topology() -> Topology:
    """Return an empty starting topology for workflow instances."""
    return Topology(nodes=[], edges=[])


def make_node(
    node_id: str,
    *,
    operation: Operation,
    node_type: str,
    label: str,
    layer_index: int,
    include_size: bool = True,
    stable_agent_id: str | None = None,
    extras: Mapping[str, Any] | None = None,
) -> PartialNode:
    """Create a PartialNode with standard defaults."""
    extra_kwargs: dict[str, Any] = dict(extras) if extras else {}
    resolved_stable = extra_kwargs.pop("stable_agent_id", None)
    if stable_agent_id is not None:
        resolved_stable = stable_agent_id
    agent_record_uri = extra_kwargs.pop("agent_record_uri", None)
    size_kwargs: dict[str, Any] = {}
    if include_size:
        size_kwargs["size"] = _DEFAULT_NODE_SIZE
    base_kwargs: dict[str, Any] = dict(
        id=NodeId(node_id),
        operation=operation,
        type=node_type,
        label=label,
        layer_index=layer_index,
        **size_kwargs,
        **extra_kwargs,
    )
    if resolved_stable is None and agent_record_uri is None:
        return PartialBaseNode(**base_kwargs)
    if agent_record_uri is None:
        agent_record_uri = (
            f"agent-card://{str(resolved_stable).removeprefix('agent://')}"
        )
    return PartialAgentNode(
        **base_kwargs,
        agent_record_uri=agent_record_uri,
        stable_agent_id=StableAgentId(resolved_stable) if resolved_stable else None,
    )


async def make_edge(
    source_nid: str,
    target_nid: str,
    *,
    operation: Operation,
    allocator: RuntimeIdAllocator,
) -> PartialEdge:
    """Create a PartialEdge for discovery events."""
    kwargs: dict[str, Any] = dict(
        id=EdgeId(await allocator.edge_id(source_nid, target_nid)),
        operation=operation,
        type="custom",
        source=NodeId(source_nid),
        target=NodeId(target_nid),
    )
    if operation == Operation.CREATE:
        kwargs["bidirectional"] = False
        kwargs["weight"] = 1.0
    return PartialEdge(**kwargs)


def build_metadata(
    source: str,
    event_type: EventType,
    correlation_id: str,
    correlation_message: str | None = None,
    trace_id: int | None = None,
    span_id: int | None = None,
) -> Metadata:
    return Metadata(
        timestamp=datetime.now(timezone.utc),
        schema_version=SCHEMA_VERSION,
        id=EventId(f"event://{uuid4()}"),
        type=event_type,
        source=source,
        correlation=Correlation(
            id=CorrelationId(correlation_id),
            message=correlation_message,
        ),
        trace_id=format_trace_id(trace_id) if trace_id is not None else None,
        span_id=format_span_id(span_id) if span_id is not None else None,
    )


def build_event(
    *,
    source: str,
    identity: WorkflowMetadata,
    instance_id: str,
    topology: PartialTopology,
    correlation_id: str,
    event_type: EventType = EventType.STATE_PROGRESS_UPDATE,
    correlation_message: str | None = None,
    trace_id: int | None = None,
    span_id: int | None = None,
) -> Event:
    """Build an Event for one workflow-instance topology update.

    Copies identity fields from ``WorkflowMetadata`` onto the still-flat
    ``Workflow`` wire object.
    """
    return Event(
        metadata=build_metadata(
            source=source,
            event_type=event_type,
            correlation_id=correlation_id,
            correlation_message=correlation_message,
            trace_id=trace_id,
            span_id=span_id,
        ),
        data=Data(
            workflows={
                identity.name: Workflow(
                    pattern=identity.pattern or identity.name,
                    use_case=identity.use_case,
                    scenario=identity.scenario,
                    name=identity.name,
                    starting_topology=init_starting_topology(),
                    instances={
                        instance_id: WorkflowInstance(
                            id=InstanceId(instance_id),
                            topology=topology,
                        )
                    },
                )
            }
        ),
    )
