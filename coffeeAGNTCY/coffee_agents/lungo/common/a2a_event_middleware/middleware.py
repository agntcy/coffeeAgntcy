# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""A2A client middleware for emitting workflow topology events.

This module contains outbound interceptor and inbound consumer logic,
event/topology builders, and the workflow API sink used to publish
state-progress updates.
"""

from __future__ import annotations

import logging
import uuid as _uuid_mod
from datetime import datetime, timezone
from time import monotonic
from typing import Any, Mapping
from uuid import uuid4

from a2a.client import ClientEvent
from a2a.client.middleware import ClientCallContext, ClientCallInterceptor
from a2a.types import AgentCard, Message, Task, TaskState
from opentelemetry import trace as _otel_trace

from config.config import EMIT_WORKFLOW_EVENTS
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
	PartialTopology,
	Size,
	Topology,
	TopologyEdgeItem,
	TopologyNodeItem,
	Workflow,
	WorkflowInstance,
)

from .inflight import (
	RuntimeIdAllocator,
	current_trace_id,
	format_span_id,
	format_trace_id,
	read_trace_context,
	resolve_consumer_state,
	resolve_interaction_ids,
	upsert_in_flight_state,
)
from .event_sink import WorkflowAPIEventSink
from .workflow_registry import WorkflowIdentity, WorkflowResolver

logger = logging.getLogger("lungo.common.event_middleware")

_SCHEMA_VERSION = "1.0.0"

# Stable namespace for deterministic workflow instance IDs.
# Using uuid5(namespace, "<trace_id_hex>::<workflow_name>") ensures:
# - same trace/workflow -> same UUID-shaped instance_id
# - different workflow (or trace) -> different instance_id
_INSTANCE_ID_NS = _uuid_mod.uuid5(_uuid_mod.NAMESPACE_DNS, "lungo.instance_id")


def _init_starting_topology() -> Topology:
	"""Return an empty starting topology for workflow instances."""
	return Topology(nodes=[], edges=[])


def _slugify_source(card: AgentCard) -> str:
	"""Derive a slug-style Metadata.source from an agent card name."""
	return card.name.lower().replace(" ", "_")


def agent_id_from_card(card: AgentCard | None) -> str | None:
	"""Extract an agent ID from an AgentCard, if possible."""
	if card and card.name:
		return card.name
	return None


def agent_ids_from_cards(
	cards: list[AgentCard | None] | None,
) -> list[str]:
	"""Build ordered unique agent IDs from AgentCard.name values."""
	discovered_ids: list[str] = []

	for card in cards or []:
		aid = agent_id_from_card(card)
		if aid:
			discovered_ids.append(aid)
		else:
			logger.warning(
				"EventEmittingInterceptor: unable to derive agent ID from card with name=%r, skipping it.",
				card.name if card else None,
			)

	return list(dict.fromkeys(discovered_ids))


# long-term: use schema-generated types and add init/build functions there
_DEFAULT_NODE_SIZE = Size(width=1.0, height=1.0)


def _make_node(
	node_id: str,
	*,
	operation: Operation,
	node_type: str,
	label: str,
	layer_index: int,
	include_size: bool = True,
) -> PartialNode:
	"""Create a PartialNode with standard defaults."""
	return PartialNode(
		id=NodeId(node_id),
		operation=operation,
		type=node_type,
		label=label,
		layer_index=layer_index,
		**(dict(size=_DEFAULT_NODE_SIZE) if include_size else {}),
	)


async def _make_edge(
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


def _build_metadata(
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
		schema_version=_SCHEMA_VERSION,
		id=EventId(f"event://{uuid4()}"),
		type=event_type,
		source=source,
		correlation=Correlation(
			id=CorrelationId(correlation_id),
			message=correlation_message,
		),
		**extras,
	)


def _ensure_ids(
	correlation_id: str | None,
	instance_id: str | None,
) -> tuple[str, str]:
	"""Return provided IDs or mint new correlation/instance IDs."""
	return (
		correlation_id or f"correlation://{uuid4()}",
		instance_id or f"instance://{uuid4()}",
	)


def _collect_remote_agent_ids(
	ctx_state: Mapping[str, Any],
	agent_card: AgentCard,
) -> list[str]:
	"""Collect one or more remote agent IDs for the outbound call."""
	broadcast_cards: list[AgentCard | None] | None = ctx_state.get("broadcast_agent_cards")
	remote_cards: list[AgentCard | None] = broadcast_cards if broadcast_cards else [agent_card]
	return agent_ids_from_cards(remote_cards)


async def _bind_outbound_interaction_state(
	*,
	trace_id: int | None,
	owner_span_id: int | None,
	correlation_id: str,
	instance_id: str,
	workflow_ctx: WorkflowIdentity,
	remote_agent_ids: list[str],
	transport_label: str,
) -> RuntimeIdAllocator:
	"""Persist outbound interaction state and return a trace-stable allocator.

	This bridges interceptor context to consumer callbacks, which do not
	receive ClientCallContext.
	"""
	return await upsert_in_flight_state(
		trace_id=trace_id,
		owner_span_id=owner_span_id,
		correlation_id=correlation_id,
		instance_id=instance_id,
		workflow_ctx=workflow_ctx,
		remote_agent_ids=remote_agent_ids,
		transport_label=transport_label,
	)


def _build_event(
	*,
	source: str,
	workflow: WorkflowIdentity,
	instance_id: str | None,
	topology: PartialTopology,
	event_type: EventType = EventType.STATE_PROGRESS_UPDATE,
	correlation_id: str | None = None,
	correlation_message: str | None = None,
	trace_id: int | None = None,
	span_id: int | None = None,
) -> Event:
	"""Build an Event for one workflow-instance topology update."""
	cid, iid = _ensure_ids(correlation_id, instance_id)

	return Event(
		metadata=_build_metadata(
			source=source,
			event_type=event_type,
			correlation_id=cid,
			correlation_message=correlation_message,
			trace_id=trace_id,
			span_id=span_id,
		),
		data=Data(
			workflows={
				workflow.workflow_name: Workflow(
					pattern=workflow.pattern or workflow.workflow_name,
					use_case=workflow.use_case,
					name=workflow.workflow_name,
					starting_topology=_init_starting_topology(),
					instances={
						iid: WorkflowInstance(
							id=InstanceId(iid),
							topology=topology,
						)
					},
				)
			}
		),
	)


async def _outbound_topology(
	caller_agent_id: str,
	remote_agent_ids: list[str],
	transport_label: str = "Transport",
	layer_index: int = 0,
	*,
	allocator: RuntimeIdAllocator,
) -> PartialTopology:
	"""Build outbound topology for single-target or fan-out calls."""
	caller_node = await allocator.node_id(f"agent-{caller_agent_id}")
	transport_node = await allocator.node_id(f"transport-{caller_agent_id}::{transport_label}")

	nodes: list[TopologyNodeItem] = [
		_make_node(
			caller_node,
			operation=Operation.CREATE,
			node_type="customNode",
			label=caller_agent_id,
			layer_index=layer_index,
		),
		_make_node(
			transport_node,
			operation=Operation.CREATE,
			node_type="transportNode",
			label=transport_label,
			layer_index=layer_index + 1,
		),
	]
	edges: list[TopologyEdgeItem] = [
		await _make_edge(
			caller_node,
			transport_node,
			operation=Operation.CREATE,
			allocator=allocator,
		),
	]

	for agent_id in remote_agent_ids:
		remote_node = await allocator.node_id(f"agent-{agent_id}")
		nodes.append(
			_make_node(
				remote_node,
				operation=Operation.CREATE,
				node_type="customNode",
				label=agent_id,
				layer_index=layer_index + 2,
			),
		)
		edges.append(
			await _make_edge(
				transport_node,
				remote_node,
				operation=Operation.CREATE,
				allocator=allocator,
			),
		)

	return PartialTopology(nodes=nodes, edges=edges)


async def _inbound_topology(
	caller_agent_id: str,
	remote_agent_id: str,
	transport_label: str = "Transport",
	layer_index: int = 0,
	*,
	allocator: RuntimeIdAllocator,
) -> PartialTopology:
	"""Build inbound topology update for an A2A response."""
	caller_node = await allocator.node_id(f"agent-{caller_agent_id}")
	transport_node = await allocator.node_id(f"transport-{caller_agent_id}::{transport_label}")
	remote_node = await allocator.node_id(f"agent-{remote_agent_id}")

	return PartialTopology(
		nodes=[
			_make_node(
				remote_node,
				operation=Operation.UPDATE,
				node_type="customNode",
				label=remote_agent_id,
				layer_index=layer_index + 2,
				include_size=False,
			),
			_make_node(
				transport_node,
				operation=Operation.UPDATE,
				node_type="transportNode",
				label=transport_label,
				layer_index=layer_index + 1,
				include_size=False,
			),
			_make_node(
				caller_node,
				operation=Operation.UPDATE,
				node_type="customNode",
				label=caller_agent_id,
				layer_index=layer_index,
				include_size=False,
			),
		],
		edges=[
			await _make_edge(
				transport_node,
				remote_node,
				operation=Operation.UPDATE,
				allocator=allocator,
			),
			await _make_edge(
				caller_node,
				transport_node,
				operation=Operation.UPDATE,
				allocator=allocator,
			),
		],
	)


class EventEmittingInterceptor(ClientCallInterceptor):
	"""Emit outbound topology discovery events for A2A calls."""

	def __init__(
		self,
		*,
		caller_card: AgentCard,
		workflow_resolver: WorkflowResolver,
		agent_call_graph_layer: int = 0,
		verbose: bool = False,
	) -> None:
		self._caller_agent_id = caller_card.name
		self._source = _slugify_source(caller_card)
		self._workflow_resolver = workflow_resolver
		self._agent_call_graph_layer = agent_call_graph_layer
		self._verbose = verbose

		if not EMIT_WORKFLOW_EVENTS:
			logger.warning(
				"EventEmittingInterceptor [%s]: EMIT_WORKFLOW_EVENTS is false, interceptor will not emit events.",
				self._source,
			)
			self._event_sink = None
		else:
			self._event_sink = WorkflowAPIEventSink()

	async def intercept(
		self,
		method_name: str,
		request_payload: dict[str, Any],
		http_kwargs: dict[str, Any],
		agent_card: AgentCard | None,
		context: ClientCallContext | None,
	) -> tuple[dict[str, Any], dict[str, Any]]:
		t_intercept_start = monotonic()

		# 1) Validate call context and resolve workflow identity.

		if agent_card is None:
			logger.error(
				"EventEmittingInterceptor [%s]: Missing agent_card for method '%s', skipping event emission.",
				self._source,
				method_name,
			)
			return request_payload, http_kwargs
		if context is None:
			logger.warning(
				"EventEmittingInterceptor [%s]: Missing context for method '%s'. Context is required for full event emission but will proceed with limited information.",
				self._source,
				method_name,
			)

		ctx_state = (context.state if context and context.state else {}) or {}

		workflow_ctx = self._workflow_resolver(ctx_state.get("tool"))
		logger.debug(
			"workflow_name=%s pattern=%s use_case=%s tool=%s",
			workflow_ctx.workflow_name,
			workflow_ctx.pattern,
			workflow_ctx.use_case,
			ctx_state.get("tool", "unknown"),
		)

		trace_ctx = read_trace_context()
		if trace_ctx.trace_id is None:
			logger.warning(
				"EventEmittingInterceptor [%s]: no active OTel span for method '%s'. "
				"Falling back to random correlation IDs; consumer callbacks will not "
				"correlate. Ensure ioa_observe is instrumenting the caller.",
				self._source,
				method_name,
			)

		correlation_id, instance_id = resolve_interaction_ids(
			ctx_state=ctx_state,
			workflow_ctx=workflow_ctx,
			trace_id=trace_ctx.trace_id,
			instance_id_ns=_INSTANCE_ID_NS,
		)

		# 2) Build/update trace-scoped state and topology fragment.
		remote_agent_ids = _collect_remote_agent_ids(ctx_state, agent_card)

		active_transport = agent_card.preferred_transport or "Transport"

		allocator = await _bind_outbound_interaction_state(
			trace_id=trace_ctx.trace_id,
			owner_span_id=trace_ctx.owner_span_id,
			correlation_id=correlation_id,
			instance_id=instance_id,
			workflow_ctx=workflow_ctx,
			remote_agent_ids=remote_agent_ids,
			transport_label=active_transport,
		)

		if remote_agent_ids:
			topology = await _outbound_topology(
				self._caller_agent_id,
				remote_agent_ids,
				transport_label=active_transport,
				layer_index=self._agent_call_graph_layer,
				allocator=allocator,
			)
			correlation_msg = f"outbound {method_name} to [{', '.join(remote_agent_ids)}]"
		else:
			caller_node = await allocator.node_id(f"agent-{self._caller_agent_id}")
			topology = PartialTopology(
				nodes=[
					_make_node(
						caller_node,
						operation=Operation.CREATE,
						node_type="customNode",
						label=self._caller_agent_id,
						layer_index=self._agent_call_graph_layer,
					)
				],
				edges=[],
			)
			correlation_msg = f"outbound {method_name} to unknown"

		event = _build_event(
			source=self._source,
			workflow=workflow_ctx,
			instance_id=instance_id,
			topology=topology,
			correlation_id=correlation_id,
			correlation_message=correlation_msg,
			trace_id=trace_ctx.trace_id,
			span_id=trace_ctx.span_id,
		)

		# 3) Emit event and optionally log payload.
		if self._event_sink:
			await self._event_sink.emit(event)

		if self._verbose:
			logger.info(
				"EventEmittingInterceptor [%s]: outbound %s -> %s\n%s\nProcessing time: %.3fs",
				self._source,
				method_name,
				", ".join(remote_agent_ids) if remote_agent_ids else "unknown remote",
				event.model_dump_json(indent=2, exclude_none=True),
				monotonic() - t_intercept_start,
			)

		return request_payload, http_kwargs


def _extract_task_from_client_event(event: ClientEvent | Message) -> Task | None:
	"""Best-effort extraction of Task from a ClientEvent payload."""
	if isinstance(event, Message):
		return None

	candidate: Any | None = None

	if isinstance(event, tuple):
		candidate = event[0] if event else None
	elif hasattr(event, "task"):
		candidate = getattr(event, "task", None)
	elif hasattr(event, "__getitem__"):
		try:
			candidate = event[0]  # type: ignore[index]
		except Exception:
			candidate = None

	return candidate if isinstance(candidate, Task) else None


def _extract_remote_agent_id_from_event(
	event: ClientEvent | Message,
) -> str | None:
	"""Extract remote agent ID from response metadata when available."""
	metadata: dict[str, Any] | None = None

	if isinstance(event, Message):
		metadata = event.metadata  # type: ignore[assignment]
	else:
		task_obj = _extract_task_from_client_event(event)
		if task_obj and task_obj.metadata:
			metadata = task_obj.metadata  # type: ignore[assignment]

	if metadata and isinstance(metadata, dict):
		agent_id = metadata.get("name")
		if isinstance(agent_id, str):
			stripped = agent_id.strip()
			if stripped and stripped not in {"None", "null"}:
				return stripped

	return None


def make_event_emitting_consumer(
	*,
	caller_card: AgentCard,
	workflow_resolver: WorkflowResolver,
	agent_call_graph_layer: int = 0,
	verbose: bool = False,
):
	"""Create consumer callback that emits inbound topology updates."""
	if not EMIT_WORKFLOW_EVENTS:
		logger.warning(
			"make_event_emitting_consumer [%s]: EMIT_WORKFLOW_EVENTS is false, consumer will not emit events.",
			_slugify_source(caller_card),
		)
		event_sink = None
	else:
		event_sink = WorkflowAPIEventSink()

	caller_agent_id = caller_card.name
	_source = _slugify_source(caller_card)
	_workflow_resolver = workflow_resolver
	try:
		_default_workflow_ctx = _workflow_resolver(None)
	except KeyError:
		_default_workflow_ctx = None

	async def event_emitting_consumer(
		event: ClientEvent | Message,
		agent_card: AgentCard,
	) -> None:
		"""Emit a StateProgressUpdate for an inbound response."""

		t_receive_start = monotonic()

		agent_id = agent_id_from_card(agent_card) or "unknown"
		active_transport = agent_card.preferred_transport or "Transport"

		trace_id_int = current_trace_id()
		span_id_int = (
			_otel_trace.get_current_span().get_span_context().span_id
			if trace_id_int is not None
			else None
		)

		# 1) Resolve remote identity and correlated interaction state.

		remote_agent_id = _extract_remote_agent_id_from_event(event) or agent_id

		consumer_state = resolve_consumer_state(
			trace_id=trace_id_int,
			remote_agent_id=remote_agent_id,
			default_workflow_ctx=_default_workflow_ctx,
			source=_source,
		)
		if consumer_state is None:
			return
		correlation_id, instance_id, workflow_ctx, allocator = consumer_state

		response_status: TaskState | None = None
		task_obj = _extract_task_from_client_event(event)
		if task_obj and task_obj.status and task_obj.status.state:
			response_status = task_obj.status.state

		# 2) Build inbound topology update and event payload.
		topology = await _inbound_topology(
			caller_agent_id,
			remote_agent_id,
			transport_label=active_transport,
			layer_index=agent_call_graph_layer,
			allocator=allocator,
		)

		status_label = response_status.value if response_status else "unknown"

		event_obj = _build_event(
			source=_source,
			workflow=workflow_ctx,
			instance_id=instance_id,
			topology=topology,
			correlation_id=correlation_id,
			correlation_message=f"response from {remote_agent_id}, status={status_label}",
			trace_id=trace_id_int,
			span_id=span_id_int,
		)

		# 3) Emit event and optionally log payload.
		if event_sink:
			await event_sink.emit(event_obj)

		if verbose:
			logger.info(
				"event_emitting_consumer [%s]: response from %s (status=%s) (processing time=%.3fs)\n%s",
				_source,
				remote_agent_id,
				status_label,
				monotonic() - t_receive_start,
				event_obj.model_dump_json(indent=2, exclude_none=True),
			)

	return event_emitting_consumer
