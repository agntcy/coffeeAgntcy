# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""A2A client middleware for emitting workflow topology events.

This module contains outbound interceptor and inbound consumer logic
for A2A transport. Shared event builders and sinks live in workflow_utils.
"""

from __future__ import annotations

import logging
import re as _re
from time import monotonic
from typing import Any, Mapping

from a2a.client import ClientEvent
from a2a.client.middleware import ClientCallContext, ClientCallInterceptor
from a2a.types import AgentCard, Message, Task, TaskState
from opentelemetry import trace as _otel_trace

from common.stable_agent_id import stable_agent_id_for_name as _stable_agent_id
from common.workflow_utils.builders import build_event, make_edge, make_node
from common.workflow_utils.event_sink import WorkflowAPIEventSink
from common.workflow_utils.inflight import (
	RuntimeIdAllocator,
	current_trace_id,
	read_trace_context,
	resolve_consumer_state,
	resolve_correlation_id,
	upsert_in_flight_state,
)
from common.workflow_utils.workflow_catalog import lookup_workflow
from config.config import EMIT_WORKFLOW_EVENTS
from schema.types import (
	Operation,
	PartialTopology,
	TopologyEdgeItem,
	TopologyNodeItem,
)

from schema.types.event import _INSTANCE_ID_REGEX as INSTANCE_ID_REGEX

logger = logging.getLogger("lungo.common.event_middleware")

_INSTANCE_ID_PATTERN = _re.compile(INSTANCE_ID_REGEX)


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
	workflow_name: str,
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
		workflow_name=workflow_name,
		remote_agent_ids=remote_agent_ids,
		transport_label=transport_label,
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
		make_node(
			caller_node,
			operation=Operation.CREATE,
			node_type="customNode",
			label=caller_agent_id,
			layer_index=layer_index,
			stable_agent_id=_stable_agent_id(caller_agent_id),
		),
		make_node(
			transport_node,
			operation=Operation.CREATE,
			node_type="transportNode",
			label=transport_label,
			layer_index=layer_index + 1,
		),
	]
	edges: list[TopologyEdgeItem] = [
		await make_edge(
			caller_node,
			transport_node,
			operation=Operation.CREATE,
			allocator=allocator,
		),
	]

	for agent_id in remote_agent_ids:
		remote_node = await allocator.node_id(f"agent-{agent_id}")
		nodes.append(
			make_node(
				remote_node,
				operation=Operation.CREATE,
				node_type="customNode",
				label=agent_id,
				layer_index=layer_index + 2,
				stable_agent_id=_stable_agent_id(agent_id),
			),
		)
		edges.append(
			await make_edge(
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
			make_node(
				remote_node,
				operation=Operation.UPDATE,
				node_type="customNode",
				label=remote_agent_id,
				layer_index=layer_index + 2,
				include_size=False,
				stable_agent_id=_stable_agent_id(remote_agent_id),
			),
			make_node(
				transport_node,
				operation=Operation.UPDATE,
				node_type="transportNode",
				label=transport_label,
				layer_index=layer_index + 1,
				include_size=False,
			),
			make_node(
				caller_node,
				operation=Operation.UPDATE,
				node_type="customNode",
				label=caller_agent_id,
				layer_index=layer_index,
				include_size=False,
				stable_agent_id=_stable_agent_id(caller_agent_id),
			),
		],
		edges=[
			await make_edge(
				transport_node,
				remote_node,
				operation=Operation.UPDATE,
				allocator=allocator,
			),
			await make_edge(
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
		agent_call_graph_layer: int = 0,
	) -> None:
		self._caller_agent_id = caller_card.name
		self._source = _slugify_source(caller_card)
		self._agent_call_graph_layer = agent_call_graph_layer

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

		trace_ctx = read_trace_context()
		if trace_ctx.trace_id is None:
			logger.warning(
				"EventEmittingInterceptor [%s]: no active OTel span for method '%s'. "
				"Falling back to random correlation IDs; consumer callbacks will not "
				"correlate. Ensure ioa_observe is instrumenting the caller.",
				self._source,
				method_name,
			)

		# Workflow identity comes from baggage propagated via OTel context
		# (set at supervisor request entry from the Agentic Workflows API).
		# Both workflow_name (catalog hit) and workflow_instance_id are
		# required; if either is missing or malformed, skip emission.
		propagated_name = trace_ctx.workflow.workflow_name
		propagated_instance_id = trace_ctx.workflow.instance_id

		metadata = lookup_workflow(propagated_name)
		if metadata is None:
			logger.warning(
				"EventEmittingInterceptor [%s]: no catalog match for propagated "
				"workflow_name=%r on method '%s'; skipping event emission.",
				self._source,
				propagated_name,
				method_name,
			)
			return request_payload, http_kwargs

		if not propagated_instance_id or not _INSTANCE_ID_PATTERN.match(propagated_instance_id):
			logger.warning(
				"EventEmittingInterceptor [%s]: missing or malformed propagated "
				"workflow_instance_id=%r on method '%s'; skipping event emission.",
				self._source,
				propagated_instance_id,
				method_name,
			)
			return request_payload, http_kwargs

		workflow_name = metadata.workflow_name
		instance_id = propagated_instance_id
		logger.debug(
			"workflow_name=%s pattern=%s use_case=%s scenario=%s tool=%s",
			workflow_name,
			metadata.pattern,
			metadata.use_case,
			metadata.scenario,
			ctx_state.get("tool", "unknown"),
		)

		correlation_id = resolve_correlation_id(
			ctx_state=ctx_state,
			trace_id=trace_ctx.trace_id,
		)

		# 2) Build/update trace-scoped state and topology fragment.
		remote_agent_ids = _collect_remote_agent_ids(ctx_state, agent_card)

		active_transport = agent_card.preferred_transport or "Transport"

		allocator = await _bind_outbound_interaction_state(
			trace_id=trace_ctx.trace_id,
			owner_span_id=trace_ctx.owner_span_id,
			correlation_id=correlation_id,
			instance_id=instance_id,
			workflow_name=workflow_name,
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
					make_node(
						caller_node,
						operation=Operation.CREATE,
						node_type="customNode",
						label=self._caller_agent_id,
						layer_index=self._agent_call_graph_layer,
						stable_agent_id=_stable_agent_id(
							self._caller_agent_id
						),
					)
				],
				edges=[],
			)
			correlation_msg = f"outbound {method_name} to unknown"

		event = build_event(
			source=self._source,
			workflow_name=workflow_name,
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

		if logger.isEnabledFor(logging.DEBUG):
			logger.debug(
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
	agent_call_graph_layer: int = 0,
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
			source=_source,
		)
		if consumer_state is None:
			return
		correlation_id, instance_id, workflow_name, allocator = consumer_state

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

		event_obj = build_event(
			source=_source,
			workflow_name=workflow_name,
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

		if logger.isEnabledFor(logging.DEBUG):
			logger.debug(
				"event_emitting_consumer [%s]: response from %s (status=%s) (processing time=%.3fs)\n%s",
				_source,
				remote_agent_id,
				status_label,
				monotonic() - t_receive_start,
				event_obj.model_dump_json(indent=2, exclude_none=True),
			)

	return event_emitting_consumer
