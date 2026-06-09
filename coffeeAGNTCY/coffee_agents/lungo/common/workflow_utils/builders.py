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
	PartialEdge,
	PartialNode,
	PartialRegularNode,
	PartialTopology,
	Size,
	Topology,
	Workflow,
	WorkflowInstance,
)

from common.workflow_utils.inflight import (
	RuntimeIdAllocator,
	format_span_id,
	format_trace_id,
)
from common.workflow_utils.workflow_catalog import lookup_workflow

SCHEMA_VERSION = "1.0.0"

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
	node_extras: dict[str, Any] = {}
	if stable_agent_id is not None:
		node_extras["stable_agent_id"] = stable_agent_id
		# Schema requires agent_record_uri on any node with stable_agent_id.
		node_extras["agent_record_uri"] = f"agent-card://{stable_agent_id.removeprefix('agent://')}"
	if extras:
		node_extras.update(extras)
	return PartialRegularNode(
		id=NodeId(node_id),
		operation=operation,
		type=node_type,
		label=label,
		layer_index=layer_index,
		**(dict(size=_DEFAULT_NODE_SIZE) if include_size else {}),
		**node_extras,
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
	extras: dict[str, Any] = {}
	if trace_id is not None:
		extras["trace_id"] = format_trace_id(trace_id)
	if span_id is not None:
		extras["span_id"] = format_span_id(span_id)
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
		**extras,
	)


def build_event(
	*,
	source: str,
	workflow_name: str,
	instance_id: str,
	topology: PartialTopology,
	correlation_id: str,
	event_type: EventType = EventType.STATE_PROGRESS_UPDATE,
	correlation_message: str | None = None,
	trace_id: int | None = None,
	span_id: int | None = None,
) -> Event:
	"""Build an Event for one workflow-instance topology update.

	Looks up descriptive metadata (pattern + use_case) from the catalog at
	emission time so callers only need to carry the workflow name.
	"""
	metadata = lookup_workflow(workflow_name)
	if metadata is None:
		raise RuntimeError(
			f"build_event: workflow_name {workflow_name!r} not in catalog; "
			"intercept() should have rejected this earlier."
		)
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
				metadata.workflow_name: Workflow(
					pattern=metadata.pattern or metadata.workflow_name,
					use_case=metadata.use_case,
					scenario=metadata.scenario,
					name=metadata.workflow_name,
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
