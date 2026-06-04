# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""Trace-scoped in-flight state for workflow event emission.

Interceptor and consumer callbacks may receive asymmetric context.
This module stores per-trace interaction state when an interceptor runs,
then resolves it from OTel trace_id inside the consumer path. It also owns
runtime node/edge ID allocation and span-end cleanup registration.

Workflow identity (workflow_name + instance_id) is read from
``common.workflow_context_prop`` rather than owned here.

Logger name ``lungo.common.event_middleware`` is intentional (log continuity
after move from ``a2a_event_middleware``).
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from typing import Any, Mapping
from uuid import UUID, uuid4

from opentelemetry import trace as _otel_trace
from opentelemetry.sdk.trace import ReadableSpan, SpanProcessor

from common.workflow_context_prop import WorkflowContext, read_workflow_context

logger = logging.getLogger("lungo.common.event_middleware")


class RuntimeIdAllocator:
	"""Allocate instance-scoped node:// and edge:// IDs."""

	def __init__(self) -> None:
		self._node_cache: dict[str, str] = {}
		self._edge_cache: dict[tuple[str, str], str] = {}
		self._lock = asyncio.Lock()

	async def node_id(self, semantic_key: str) -> str:
		"""Return stable runtime node://UUID for a semantic key."""
		async with self._lock:
			nid = self._node_cache.get(semantic_key)
			if nid is None:
				nid = f"node://{uuid4()}"
				self._node_cache[semantic_key] = nid
			return nid

	async def edge_id(self, source_nid: str, target_nid: str) -> str:
		"""Return stable runtime edge://UUID for source/target pair."""
		async with self._lock:
			key = (source_nid, target_nid)
			eid = self._edge_cache.get(key)
			if eid is None:
				eid = f"edge://{uuid4()}"
				self._edge_cache[key] = eid
			return eid


@dataclass(frozen=True)
class InterceptionState:
	"""Per-interaction state keyed by trace_id."""

	correlation_id: str
	instance_id: str
	workflow_name: str
	remote_agent_ids: tuple[str, ...]
	transport_label: str
	allocator: RuntimeIdAllocator
	owner_span_id: int


@dataclass(frozen=True)
class TraceContext:
	"""OTel identifiers plus propagated workflow identity.

	Workflow values are independent of span validity: callers may set them
	before any span exists, so ``workflow`` may carry data even when
	``trace_id`` is None.
	"""

	trace_id: int | None
	span_id: int | None
	owner_span_id: int | None
	workflow: WorkflowContext = WorkflowContext()


# Shared bridge between interceptor and consumer when callback context is asymmetric.
# Keyed by OTel trace_id so consumer-side emissions can recover interceptor state.
in_flight: dict[int, InterceptionState] = {}
in_flight_lock = asyncio.Lock()


def current_trace_id() -> int | None:
	"""Return the active OTel trace_id, or None if no valid span is active."""
	ctx = _otel_trace.get_current_span().get_span_context()
	return ctx.trace_id if ctx.is_valid else None


def format_trace_id(trace_id: int) -> str:
	"""Render an OTel trace_id (int) as a hex string for emission."""
	return f"{trace_id:032x}"


def format_span_id(span_id: int) -> str:
	"""Render an OTel span_id (int) as a hex string for emission."""
	return f"{span_id:016x}"


def read_trace_context() -> TraceContext:
	"""Read active OTel trace/span IDs and propagated workflow identity."""
	wf_ctx = read_workflow_context()

	otel_span = _otel_trace.get_current_span()
	otel_ctx = otel_span.get_span_context()
	if not otel_ctx.is_valid:
		return TraceContext(
			trace_id=None,
			span_id=None,
			owner_span_id=None,
			workflow=wf_ctx,
		)

	otel_parent = getattr(otel_span, "parent", None)
	owner_span_id = otel_parent.span_id if otel_parent is not None else otel_ctx.span_id
	return TraceContext(
		trace_id=otel_ctx.trace_id,
		span_id=otel_ctx.span_id,
		owner_span_id=owner_span_id,
		workflow=wf_ctx,
	)


class InFlightCleanupSpanProcessor(SpanProcessor):
	"""Evict in_flight entries when their owning span ends."""

	def on_start(self, span, parent_context=None) -> None:  # noqa: D401
		return None

	def on_end(self, span: ReadableSpan) -> None:  # noqa: D401
		span_context = span.get_span_context()
		if span_context is None:
			return
		trace_id = span_context.trace_id
		ending_span_id = span_context.span_id
		state = in_flight.get(trace_id)
		if state is None:
			return
		if state.owner_span_id != ending_span_id:
			return
		in_flight.pop(trace_id, None)
		logger.debug(
			"InFlightCleanup: evicted state for trace_id=%s on owner span end (%s)",
			format_trace_id(trace_id),
			span.name,
		)

	def shutdown(self) -> None:  # noqa: D401
		in_flight.clear()

	def force_flush(self, timeout_millis: int = 30_000) -> bool:  # noqa: D401
		return True


def register_cleanup_span_processor() -> None:
	"""Register the in-flight cleanup processor once on the active provider."""
	provider = _otel_trace.get_tracer_provider()
	add_fn = getattr(provider, "add_span_processor", None)
	if add_fn is None:
		logger.warning(
			"register_cleanup_span_processor: active TracerProvider (%s) has no "
			"add_span_processor; in-flight state will not be auto-evicted. "
			"Ensure ioa_observe/OTel SDK is configured before calling this.",
			type(provider).__name__,
		)
		return
	if getattr(provider, "_lungo_cleanup_registered", False):
		return
	add_fn(InFlightCleanupSpanProcessor())
	try:
		setattr(provider, "_lungo_cleanup_registered", True)
	except Exception:
		pass
	logger.info("register_cleanup_span_processor: registered on %s", type(provider).__name__)


async def upsert_in_flight_state(
	*,
	trace_id: int | None,
	owner_span_id: int | None,
	correlation_id: str,
	instance_id: str,
	workflow_name: str,
	remote_agent_ids: list[str],
	transport_label: str,
) -> RuntimeIdAllocator:
	"""Store trace-scoped state for consumer correlation and ID stability."""
	allocator = RuntimeIdAllocator()
	if trace_id is None:
		return allocator

	state = InterceptionState(
		correlation_id=correlation_id,
		instance_id=instance_id,
		workflow_name=workflow_name,
		remote_agent_ids=tuple(remote_agent_ids),
		transport_label=transport_label,
		allocator=allocator,
		owner_span_id=owner_span_id or 0,
	)
	async with in_flight_lock:
		existing = in_flight.get(trace_id)
		if existing is not None:
			state = InterceptionState(
				correlation_id=existing.correlation_id,
				instance_id=existing.instance_id,
				workflow_name=existing.workflow_name,
				remote_agent_ids=tuple(
					dict.fromkeys(list(existing.remote_agent_ids) + list(remote_agent_ids))
				),
				transport_label=existing.transport_label,
				allocator=existing.allocator,
				owner_span_id=existing.owner_span_id,
			)
			allocator = existing.allocator
		in_flight[trace_id] = state
	return allocator


def resolve_correlation_id(
	*,
	ctx_state: Mapping[str, Any],
	trace_id: int | None,
) -> str:
	"""Resolve correlation_id from ctx override, trace_id, or fresh uuid."""
	return (
		ctx_state.get("correlation_id")
		or (f"correlation://{UUID(int=trace_id)}" if trace_id else None)
		or f"correlation://{uuid4()}"
	)


def resolve_consumer_state(
	*,
	trace_id: int | None,
	remote_agent_id: str,
	source: str,
) -> tuple[str, str, str, RuntimeIdAllocator] | None:
	"""Resolve consumer state from in-flight data; drop event when missing.

	Returns (correlation_id, instance_id, workflow_name, allocator) or None.
	"""
	state = in_flight.get(trace_id) if trace_id is not None else None
	if state is None:
		logger.warning(
			"event_emitting_consumer [%s]: no in-flight state for trace_id=%s; "
			"dropping inbound event for %s",
			source,
			format_trace_id(trace_id) if trace_id else "none",
			remote_agent_id,
		)
		return None
	return (
		state.correlation_id,
		state.instance_id,
		state.workflow_name,
		state.allocator,
	)
