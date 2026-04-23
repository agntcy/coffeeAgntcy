# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""A2A middleware that emits topology discovery ``event_v1`` updates.

Outbound interceptor calls emit ``operation: create`` and inbound consumer
callbacks emit ``operation: update``. Workflow identity is resolved from
``ClientCallContext.state["tool"]`` via a resolver.

Lifecycle is bound to the caller's OTel span. The interceptor stores
per-trace state keyed by ``trace_id`` and the consumer reads it; a
``SpanProcessor`` evicts state when the owning span ends.
"""

from __future__ import annotations

import asyncio
import logging
import uuid as _uuid_mod
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, timezone
from time import monotonic
from typing import Any, Callable
from uuid import uuid4

import httpx
from urllib.parse import quote

from a2a.client import ClientEvent
from a2a.client.middleware import ClientCallContext, ClientCallInterceptor
from a2a.types import AgentCard, Message, Task, TaskState

from opentelemetry import trace as _otel_trace
from opentelemetry.sdk.trace import ReadableSpan, SpanProcessor

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

from config.config import EMIT_WORKFLOW_EVENTS

logger = logging.getLogger("lungo.common.event_middleware")


# ---------------------------------------------------------------------------
# Tool → workflow identity mapping
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class WorkflowIdentity:
    """Workflow identity values sourced from the workflow catalog."""
    workflow_name: str
    pattern: str
    use_case: str


WorkflowResolver = Callable[[str | None], WorkflowIdentity]


_SCHEMA_VERSION = "1.0.0"

# Stable namespace for deterministic workflow instance IDs.
# Using uuid5(namespace, "<trace_id_hex>::<workflow_name>") ensures:
# - same trace/workflow -> same UUID-shaped instance_id
# - different workflow (or trace) -> different instance_id
_INSTANCE_ID_NS = _uuid_mod.uuid5(_uuid_mod.NAMESPACE_DNS, "lungo.instance_id")

def _init_starting_topology() -> Topology:
    return Topology(nodes=[], edges=[])


# State shared between interceptor and consumer.
# Consumer callbacks do not receive ``ClientCallContext``, so per-call
# state is stored by OTel ``trace_id`` and read back in the consumer.

@dataclass(frozen=True)
class _InterceptionState:
    """Per-interaction state keyed by trace_id."""
    correlation_id: str
    instance_id: str
    workflow_ctx: WorkflowIdentity
    remote_agent_ids: tuple[str, ...]
    transport_label: str
    allocator: _RuntimeIdAllocator
    # Span that owns this interaction; eviction happens when this span ends.
    owner_span_id: int


_in_flight: dict[int, _InterceptionState] = {}
_in_flight_lock = asyncio.Lock()


def _current_trace_id() -> int | None:
    """Return the active OTel trace_id, or None if no valid span is active."""
    ctx = _otel_trace.get_current_span().get_span_context()
    return ctx.trace_id if ctx.is_valid else None


def _format_trace_id(trace_id: int) -> str:
    """Render an OTel trace_id (int) as a hex string for emission."""
    return f"{trace_id:032x}"


def _format_span_id(span_id: int) -> str:
    """Render an OTel span_id (int) as a hex string for emission."""
    return f"{span_id:016x}"


class _InFlightCleanupSpanProcessor(SpanProcessor):
    """Evict ``_in_flight`` entries when their owning span ends."""

    def on_start(self, span, parent_context=None) -> None:  # noqa: D401
        return None

    def on_end(self, span: ReadableSpan) -> None:  # noqa: D401
        span_context = span.get_span_context()
        if span_context is None:
            return
        trace_id = span_context.trace_id
        ending_span_id = span_context.span_id
        state = _in_flight.get(trace_id)
        if state is None:
            return
        # Evict only for the owning span, not every span in the same trace.
        if state.owner_span_id != ending_span_id:
            return
        _in_flight.pop(trace_id, None)
        logger.debug(
            "InFlightCleanup: evicted state for trace_id=%s on owner span end (%s)",
            _format_trace_id(trace_id), span.name,
        )

    def shutdown(self) -> None:  # noqa: D401
        _in_flight.clear()

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
    add_fn(_InFlightCleanupSpanProcessor())
    try:
        setattr(provider, "_lungo_cleanup_registered", True)
    except Exception:
        # Provider may be immutable; registration already succeeded.
        pass
    logger.info("register_cleanup_span_processor: registered on %s",
                type(provider).__name__)


class _RuntimeIdAllocator:
    """Allocate instance-scoped ``node://`` and ``edge://`` IDs."""

    def __init__(self) -> None:
        self._node_cache: dict[str, str] = {}
        self._edge_cache: dict[tuple[str, str], str] = {}
        self._lock = asyncio.Lock()

    async def node_id(self, semantic_key: str) -> str:
        """Return stable runtime ``node://UUID`` for a semantic key."""
        async with self._lock:
            nid = self._node_cache.get(semantic_key)
            if nid is None:
                nid = f"node://{uuid4()}"
                self._node_cache[semantic_key] = nid
            return nid

    async def edge_id(self, source_nid: str, target_nid: str) -> str:
        """Return stable runtime ``edge://UUID`` for source/target pair."""
        async with self._lock:
            key = (source_nid, target_nid)
            eid = self._edge_cache.get(key)
            if eid is None:
                eid = f"edge://{uuid4()}"
                self._edge_cache[key] = eid
            return eid


# ---------------------------------------------------------------------------
# Utility helpers
# ---------------------------------------------------------------------------

def _slugify_source(card: AgentCard) -> str:
    """Derive a slug-style ``Metadata.source`` from an agent card name."""
    return card.name.lower().replace(" ", "_")

def agent_id_from_card(card: AgentCard | None) -> str | None:
    """Extract an agent ID from an AgentCard, if possible."""
    if card and card.name:
        return card.name
    return None

def agent_ids_from_cards(
    cards: list[AgentCard | None] | None,
) -> list[str]:
    """Build ordered unique agent IDs from ``AgentCard.name`` values."""
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


# ---------------------------------------------------------------------------
# Low-level node / edge factories
# ---------------------------------------------------------------------------

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
    """Create a ``PartialNode`` with standard defaults."""
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
    allocator: _RuntimeIdAllocator,
) -> PartialEdge:
    """Create a ``PartialEdge`` for discovery events."""
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


# ---------------------------------------------------------------------------
# Event construction helpers
# ---------------------------------------------------------------------------

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
        extras["trace_id"] = _format_trace_id(trace_id)
    if span_id is not None:
        extras["span_id"] = _format_span_id(span_id)
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
    correlation_id: str | None, instance_id: str | None
) -> tuple[str, str]:
    """Return provided IDs or mint new correlation/instance IDs."""
    return (
        correlation_id or f"correlation://{uuid4()}",
        instance_id or f"instance://{uuid4()}",
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
    """Build an ``Event`` for one workflow-instance topology update."""
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


# Topology fragment builders. Outbound uses CREATE and inbound uses UPDATE.

async def _outbound_topology(
    caller_agent_id: str,
    remote_agent_ids: list[str],
    transport_label: str = "Transport",
    layer_index: int = 0,
    *,
    allocator: _RuntimeIdAllocator,
) -> PartialTopology:
    """Build outbound topology for single-target or fan-out calls."""
    caller_node = await allocator.node_id(f"agent-{caller_agent_id}")
    transport_node = await allocator.node_id(f"transport-{caller_agent_id}::{transport_label}")

    nodes: list[TopologyNodeItem] = [
        _make_node(caller_node, operation=Operation.CREATE, node_type="customNode",
                   label=caller_agent_id, layer_index=layer_index),
        _make_node(transport_node, operation=Operation.CREATE, node_type="transportNode",
                   label=transport_label, layer_index=layer_index + 1),
    ]
    edges: list[TopologyEdgeItem] = [
        await _make_edge(caller_node, transport_node, operation=Operation.CREATE, allocator=allocator),
    ]

    for agent_id in remote_agent_ids:
        remote_node = await allocator.node_id(f"agent-{agent_id}")
        nodes.append(
            _make_node(remote_node, operation=Operation.CREATE, node_type="customNode",
                       label=agent_id, layer_index=layer_index + 2),
        )
        edges.append(
            await _make_edge(transport_node, remote_node, operation=Operation.CREATE, allocator=allocator),
        )

    return PartialTopology(nodes=nodes, edges=edges)


async def _inbound_topology(
    caller_agent_id: str,
    remote_agent_id: str,
    transport_label: str = "Transport",
    layer_index: int = 0,
    *,
    allocator: _RuntimeIdAllocator,
) -> PartialTopology:
    """Build inbound topology update for an A2A response."""
    caller_node = await allocator.node_id(f"agent-{caller_agent_id}")
    transport_node = await allocator.node_id(f"transport-{caller_agent_id}::{transport_label}")
    remote_node = await allocator.node_id(f"agent-{remote_agent_id}")

    return PartialTopology(
        nodes=[
            _make_node(remote_node, operation=Operation.UPDATE, node_type="customNode",
                       label=remote_agent_id, layer_index=layer_index + 2, include_size=False),
            _make_node(transport_node, operation=Operation.UPDATE, node_type="transportNode",
                       label=transport_label, layer_index=layer_index + 1, include_size=False),
            _make_node(caller_node, operation=Operation.UPDATE, node_type="customNode",
                       label=caller_agent_id, layer_index=layer_index, include_size=False),
        ],
        edges=[
            await _make_edge(transport_node, remote_node, operation=Operation.UPDATE, allocator=allocator),
            await _make_edge(caller_node, transport_node, operation=Operation.UPDATE, allocator=allocator),
        ],
    )


# ---------------------------------------------------------------------------
# A2A Middleware: Interceptor (outbound requests)
# ---------------------------------------------------------------------------

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
        logger.debug("workflow_name=%s pattern=%s use_case=%s tool=%s",
                    workflow_ctx.workflow_name, workflow_ctx.pattern, workflow_ctx.use_case,
                    ctx_state.get("tool", "unknown"))

        # Precedence: explicit context values -> OTel trace_id -> fresh UUID.
        otel_span = _otel_trace.get_current_span()
        otel_ctx = otel_span.get_span_context()
        trace_id_int = otel_ctx.trace_id if otel_ctx.is_valid else None
        span_id_int = otel_ctx.span_id if otel_ctx.is_valid else None

        # The interceptor runs in a short-lived child span that ends as
        # soon as this method returns — before remote responses arrive.
        # The owning lifetime is the parent (the caller's tool span); fall
        # back to the current span only if there is no parent.
        otel_parent = getattr(otel_span, "parent", None)
        owner_span_id_int = (
            otel_parent.span_id if otel_parent is not None
            else span_id_int
        )

        if trace_id_int is None:
            logger.warning(
                "EventEmittingInterceptor [%s]: no active OTel span for method '%s'. "
                "Falling back to random correlation IDs; consumer callbacks will not "
                "correlate. Ensure ioa_observe is instrumenting the caller.",
                self._source, method_name,
            )

        correlation_id = (
            ctx_state.get("correlation_id")
            or (f"correlation://{_uuid_mod.UUID(int=trace_id_int)}" if trace_id_int else None)
            or f"correlation://{uuid4()}"
        )
        instance_id = (
            ctx_state.get("instance_id")
            or (
                f"instance://{_uuid_mod.uuid5(_INSTANCE_ID_NS, f'{trace_id_int:032x}::{workflow_ctx.workflow_name}')}"
                if trace_id_int else None
            )
            or f"instance://{uuid4()}"
        )

        broadcast_cards: list[AgentCard | None] | None = ctx_state.get("broadcast_agent_cards")
        remote_cards: list[AgentCard | None] = broadcast_cards if broadcast_cards else [agent_card]
        remote_agent_ids = agent_ids_from_cards(remote_cards)

        active_transport = agent_card.preferred_transport or "Transport"

        # Register per-interaction state keyed by trace_id so the consumer
        # (which lacks ClientCallContext) can look it up. Cleanup happens
        # in _InFlightCleanupSpanProcessor.on_end when the tool span ends.
        allocator = _RuntimeIdAllocator()
        if trace_id_int is not None:
            state = _InterceptionState(
                correlation_id=correlation_id,
                instance_id=instance_id,
                workflow_ctx=workflow_ctx,
                remote_agent_ids=tuple(remote_agent_ids),
                transport_label=active_transport,
                allocator=allocator,
                owner_span_id=owner_span_id_int or 0,
            )
            async with _in_flight_lock:
                # Preserve allocator to keep node/edge IDs stable within a trace.
                existing = _in_flight.get(trace_id_int)
                if existing is not None:
                    state = _InterceptionState(
                        correlation_id=existing.correlation_id,
                        instance_id=existing.instance_id,
                        workflow_ctx=existing.workflow_ctx,
                        remote_agent_ids=tuple(
                            dict.fromkeys(
                                list(existing.remote_agent_ids) + list(remote_agent_ids)
                            )
                        ),
                        transport_label=existing.transport_label,
                        allocator=existing.allocator,
                        owner_span_id=existing.owner_span_id,
                    )
                    allocator = existing.allocator
                _in_flight[trace_id_int] = state

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
                nodes=[_make_node(
                    caller_node,
                    operation=Operation.CREATE,
                    node_type="customNode",
                    label=self._caller_agent_id,
                    layer_index=self._agent_call_graph_layer,
                )],
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
            trace_id=trace_id_int,
            span_id=span_id_int,
        )

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


# ---------------------------------------------------------------------------
# A2A Middleware: Consumer helpers
# ---------------------------------------------------------------------------

def _extract_task_from_client_event(event: ClientEvent | Message) -> Task | None:
    """Best-effort extraction of ``Task`` from a ``ClientEvent`` payload."""
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


# ---------------------------------------------------------------------------
# A2A Middleware: Consumer factory (inbound response events)
# ---------------------------------------------------------------------------

def make_event_emitting_consumer(
    *,
    caller_card: AgentCard,
    workflow_resolver: WorkflowResolver,
    agent_call_graph_layer: int = 0,
    verbose: bool = False,
):
    """Create consumer closure that emits inbound topology updates."""
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
        """Emit a ``StateProgressUpdate`` for an inbound response."""

        t_receive_start = monotonic()

        agent_id = agent_id_from_card(agent_card) or "unknown"
        active_transport = agent_card.preferred_transport or "Transport"

        # Look up interaction state by the active OTel trace_id. Both the
        # interceptor and this consumer run under the same tool-wrapping span,
        # so they share a trace_id. Eviction happens in
        # _InFlightCleanupSpanProcessor.on_end when that span ends — no
        # response counting, no terminal-state inference.
        trace_id_int = _current_trace_id()
        span_id_int = (
            _otel_trace.get_current_span().get_span_context().span_id
            if trace_id_int is not None else None
        )

        state: _InterceptionState | None = None
        if trace_id_int is not None:
            state = _in_flight.get(trace_id_int)

        # Prefer metadata remote name; fallback to consumer's agent card name.
        remote_agent_id = (
            _extract_remote_agent_id_from_event(event)
            or agent_id
        )

        if state is not None:
            correlation_id = state.correlation_id
            instance_id: str | None = state.instance_id
            workflow_ctx = state.workflow_ctx
            allocator = state.allocator
        else:
            if _default_workflow_ctx is None:
                logger.warning(
                    "event_emitting_consumer [%s]: no in-flight state for trace_id=%s "
                    "and no default workflow — dropping inbound event for %s",
                    _source,
                    _format_trace_id(trace_id_int) if trace_id_int else "none",
                    remote_agent_id,
                )
                return
            logger.warning(
                "event_emitting_consumer [%s]: no in-flight state for trace_id=%s "
                "— minting fresh correlation_id; inbound event will not correlate "
                "with outbound. Expected only for standalone consumer usage.",
                _source,
                _format_trace_id(trace_id_int) if trace_id_int else "none",
            )
            correlation_id = f"correlation://{uuid4()}"
            instance_id = None
            workflow_ctx = _default_workflow_ctx
            allocator = _RuntimeIdAllocator()

        response_status: TaskState | None = None
        task_obj = _extract_task_from_client_event(event)
        if task_obj and task_obj.status and task_obj.status.state:
            response_status = task_obj.status.state

        topology = await _inbound_topology(
            caller_agent_id, remote_agent_id,
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


# ---------------------------------------------------------------------------
# Event sink abstraction
# ---------------------------------------------------------------------------

class EventSink(ABC):
    """Interface for event delivery backends."""

    @abstractmethod
    async def emit(self, event: Event) -> None:
        """Handle ``event``."""

    async def aclose(self) -> None:
        """Release sink resources (default no-op)."""
        return None

class WorkflowAPIEventSink(EventSink):
    """Fire-and-forget sink that POSTs events to the workflow API."""

    _TIMEOUT = 5.0

    def __init__(self, base_url: str | None = None) -> None:
        if base_url is None:
            from config.config import WORKFLOW_API_URL
            self._base_url = WORKFLOW_API_URL
        else:
            self._base_url = base_url

        self._client: httpx.AsyncClient | None = None
        self._pending: set[asyncio.Task] = set()

    def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=self._TIMEOUT)
        return self._client

    _INSTANCE_ID_PREFIX = "instance://"

    async def emit(self, event: Event) -> None:
        """Extract workflow/instance from event and POST in background."""
        try:
            workflow_name = next(iter(event.data.workflows))
            workflow = event.data.workflows[workflow_name]
            instance_id = next(iter(workflow.instances))
        except (StopIteration, AttributeError):
            logger.warning(
                "HttpEventSink: cannot extract workflow/instance from event, dropping."
            )
            return

        # Strip "instance://" prefix to keep URLs concise; the API expects UUID-shaped IDs.
        instance_uuid = instance_id
        if instance_uuid.startswith(self._INSTANCE_ID_PREFIX):
            instance_uuid = instance_uuid[len(self._INSTANCE_ID_PREFIX):]

        url = (
            f"{self._base_url}/agentic-workflows/{quote(workflow_name, safe='')}"
            f"/instances/{quote(instance_uuid, safe='')}/events/"
        )
        body = event.model_dump_json(exclude_none=True)
        task = asyncio.create_task(self._post(url, body))
        self._pending.add(task)
        task.add_done_callback(self._pending.discard)

    async def _post(self, url: str, body: str) -> None:
        """Best-effort POST; errors are logged, never raised."""
        try:
            resp = await self._get_client().post(
                url,
                content=body,
                headers={"Content-Type": "application/json"},
            )
            logger.debug("HttpEventSink: POST %s → %s", url, resp.status_code)
        except Exception:
            logger.warning("HttpEventSink: POST %s failed", url, exc_info=True)

    async def aclose(self) -> None:
        """Drain pending POSTs and close the underlying HTTP client."""
        if self._pending:
            await asyncio.gather(*self._pending, return_exceptions=True)
        if self._client is not None:
            await self._client.aclose()
            self._client = None