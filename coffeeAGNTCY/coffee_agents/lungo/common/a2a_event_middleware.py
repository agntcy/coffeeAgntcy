# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""A2A middleware that emits topology discovery ``event_v1`` updates.

Outbound interceptor calls emit ``operation: create`` and inbound consumer
callbacks emit ``operation: update``. Workflow identity is resolved from
``ClientCallContext.state["tool"]`` via a resolver.
"""

from __future__ import annotations

import asyncio
import logging
import os
import uuid as _uuid_mod
from abc import ABC, abstractmethod
from contextvars import ContextVar
from dataclasses import dataclass
from datetime import datetime, timezone
from time import monotonic
from typing import Any, Callable
from uuid import uuid4
from functools import lru_cache

import httpx
from urllib.parse import quote

from a2a.client import ClientEvent
from a2a.client.middleware import ClientCallContext, ClientCallInterceptor
from a2a.types import AgentCard, Message, Task, TaskState

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


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
_SCHEMA_VERSION = "1.0.0"

# Namespace for deriving a stable correlation UUID from an OTel session ID.
_CORRELATION_NS = _uuid_mod.uuid5(_uuid_mod.NAMESPACE_DNS, "lungo.correlation")

# Empty starting topology — the graph is discovered, not declared.
def _init_starting_topology() -> Topology:
    return Topology(nodes=[], edges=[])


def _get_otel_session_id() -> str | None:
    """Return current ``ioa_observe`` session ID, if available."""
    try:
        from ioa_observe.sdk.tracing.context_utils import get_current_session_id
        return get_current_session_id()
    except Exception:
        logger.debug("Could not read OTel session ID", exc_info=True)
        return None


def _correlation_id_from_session(session_id: str) -> str:
    """Derive deterministic ``correlation://UUID`` from a session ID."""
    return f"correlation://{_uuid_mod.uuid5(_CORRELATION_NS, session_id)}"


def _instance_id_from_session(session_id: str, workflow_name: str) -> str:
    """Derive deterministic ``instance://UUID`` from session + workflow."""
    return f"instance://{_uuid_mod.uuid5(_CORRELATION_NS, f'{session_id}::{workflow_name}')}"


# ---------------------------------------------------------------------------
# Interceptor → consumer context propagation
# ---------------------------------------------------------------------------
# The A2A Consumer callback signature is (ClientEvent|Message, AgentCard) —
# it does not receive ClientCallContext.  We use a ContextVar to propagate
# the interceptor's resolved IDs and workflow context so the consumer's
# inbound event correlates with the outbound one.

@dataclass(frozen=True)
class _InterceptorContext:
    """Per-call context propagated from interceptor to consumer."""
    correlation_id: str
    instance_id: str
    workflow_ctx: WorkflowIdentity
    remote_agent_ids: tuple[str, ...]
    transport_label: str
    created_at_monotonic: float
    allocator: _RuntimeIdAllocator

_interceptor_ctx: ContextVar[_InterceptorContext | None] = ContextVar(
    "event_middleware_interceptor_ctx", default=None,
)

# Per-task tracking of which remotes have sent a terminal response in a
# fan-out (broadcast) call.  A ContextVar (not a plain set) so overlapping
# async tasks using the same consumer instance don't cross-contaminate.
_completed_agent_ids_ctx: ContextVar[set[str] | None] = ContextVar(
    "event_middleware_completed_agent_ids", default=None,
)

_fan_out_lock = asyncio.Lock()

@lru_cache(maxsize=1)
def _interceptor_ctx_max_age_seconds() -> float:
    """Return interceptor context max-age in seconds from env."""
    raw = os.getenv("EVENT_MIDDLEWARE_INTERCEPTOR_CTX_MAX_AGE_SECONDS", "300")
    try:
        return float(raw)
    except ValueError:
        logger.warning(
            "Invalid EVENT_MIDDLEWARE_INTERCEPTOR_CTX_MAX_AGE_SECONDS: %r, "
            "falling back to 300s.",
            raw,
        )
        return 300.0


# ---------------------------------------------------------------------------
# Runtime ID allocation
# ---------------------------------------------------------------------------
# IDs are scoped to a workflow instance — the same semantic key yields the
# same runtime ID within one instance (so outbound CREATE and inbound UPDATE
# agree), but different instances produce different IDs even for the same
# agent name.

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
) -> Metadata:
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
) -> Event:
    """Build an ``Event`` for one workflow-instance topology update."""
    cid, iid = _ensure_ids(correlation_id, instance_id)

    return Event(
        metadata=_build_metadata(
            source=source,
            event_type=event_type,
            correlation_id=cid,
            correlation_message=correlation_message,
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


# ---------------------------------------------------------------------------
# Topology fragment builders
# ---------------------------------------------------------------------------
# Outbound interceptor emits CREATE (stateless — can't track prior emissions).
# Inbound consumer emits UPDATE (response guarantees outbound already fired).
# The workflow store upserts by ID, so repeated CREATEs are safe.
# starting_topology is left empty here — the store seeds it from config on
# startup; see the workflow store's merge_event_data docstring for details.

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

        # Precedence: explicit context value -> OTel session -> fresh UUID.
        session_id = _get_otel_session_id()
        if not session_id:
            logger.debug(
                "EventEmittingInterceptor [%s]: no OTel session active, "
                "correlation/instance IDs will be random UUIDs.",
                self._source,
            )

        correlation_id = (
            ctx_state.get("correlation_id")
            or (_correlation_id_from_session(session_id) if session_id else None)
            or f"correlation://{uuid4()}"
        )
        instance_id = (
            ctx_state.get("instance_id")
            or (_instance_id_from_session(session_id, workflow_ctx.workflow_name) if session_id else None)
            or f"instance://{uuid4()}"
        )

        logger.debug(
            "EventEmittingInterceptor [%s]: correlation_id=%s instance_id=%s "
            "source=%s",
            self._source, correlation_id, instance_id,
            "otel_session" if session_id else "context" if ctx_state.get("correlation_id") else "fallback_uuid",
        )

        broadcast_cards: list[AgentCard | None] | None = ctx_state.get("broadcast_agent_cards")
        remote_cards: list[AgentCard | None] = broadcast_cards if broadcast_cards else [agent_card]
        remote_agent_ids = agent_ids_from_cards(remote_cards)

        # Stash state for consumer callbacks (which don't receive call context).
        allocator = _RuntimeIdAllocator()
        _interceptor_ctx.set(_InterceptorContext(
            correlation_id=correlation_id,
            instance_id=instance_id,
            workflow_ctx=workflow_ctx,
            remote_agent_ids=tuple(remote_agent_ids),
            transport_label=agent_card.preferred_transport or "Transport",
            created_at_monotonic=monotonic(),
            allocator=allocator,
        ))
        _completed_agent_ids_ctx.set(None)

        active_transport = agent_card.preferred_transport or "Transport"
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
# A2A Middleware: Consumer context resolution
# ---------------------------------------------------------------------------

_TERMINAL_STATUSES: frozenset[TaskState] = frozenset({
    TaskState.completed,
    TaskState.failed,
    TaskState.canceled,
    TaskState.rejected,
})


def _validate_interceptor_ctx(
    remote_agent_id: str,
    active_transport: str,
    source_label: str,
) -> _InterceptorContext | None:
    """Return validated interceptor context, else ``None``."""
    ictx = _interceptor_ctx.get()
    if ictx is None:
        return None

    age_seconds = monotonic() - ictx.created_at_monotonic
    if age_seconds > _interceptor_ctx_max_age_seconds():
        logger.warning(
            "event_emitting_consumer [%s]: interceptor context is stale "
            "(age=%.2fs), ignoring it.",
            source_label, age_seconds,
        )
        return None

    if ictx.remote_agent_ids and remote_agent_id not in ictx.remote_agent_ids:
        logger.warning(
            "event_emitting_consumer [%s]: interceptor context remote mismatch "
            "(event=%s, expected_any=%s), ignoring it.",
            source_label, remote_agent_id, ",".join(ictx.remote_agent_ids),
        )
        return None

    if ictx.transport_label != active_transport:
        logger.warning(
            "event_emitting_consumer [%s]: interceptor context transport mismatch "
            "(event=%s, expected=%s), ignoring it.",
            source_label, active_transport, ictx.transport_label,
        )
        return None

    return ictx


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
        if agent_id is not None:
            logger.debug(
                "event_emitting_consumer: metadata.name present but unusable (%r); "
                "falling back to round-robin",
                agent_id,
            )

    return None


async def _resolve_fan_out_remote_agent_id(
    agent_id: str,
    event: ClientEvent | Message,
    completed_agent_ids: set[str],
) -> str:
    """Resolve remote agent ID for broadcast response attribution."""
    ictx = _interceptor_ctx.get()
    if ictx is None or len(ictx.remote_agent_ids) <= 1:
        return agent_id

    metadata_name = _extract_remote_agent_id_from_event(event)
    if metadata_name and metadata_name in ictx.remote_agent_ids:
        return metadata_name

    logger.debug(
        "event_emitting_consumer: metadata.name unavailable, "
        "falling back to round-robin attribution for agent_id=%s",
        agent_id,
    )
    async with _fan_out_lock:
        if agent_id in ictx.remote_agent_ids and agent_id not in completed_agent_ids:
            return agent_id

        for name in ictx.remote_agent_ids:
            if name not in completed_agent_ids:
                return name

    logger.warning(
        "event_emitting_consumer: all %d remote_agent_ids already attributed, "
        "surplus response attributed to agent_id=%s",
        len(ictx.remote_agent_ids), agent_id,
    )
    return agent_id


async def _resolve_consumer_context(
    remote_agent_id: str,
    preferred_transport: str,
    response_status: TaskState | None,
    *,
    source_label: str,
    default_workflow_ctx: WorkflowIdentity | None,
    completed_agent_ids: set[str],
) -> tuple[str, str | None, WorkflowIdentity, _RuntimeIdAllocator, bool] | None:
    """Resolve consumer context and lifecycle behavior for a response."""
    ictx = _validate_interceptor_ctx(
        remote_agent_id, preferred_transport, source_label,
    )

    if ictx is not None:
        correlation_id = ictx.correlation_id
        instance_id = ictx.instance_id
        workflow_ctx = ictx.workflow_ctx
        allocator = ictx.allocator
    else:
        if default_workflow_ctx is None:
            logger.warning(
                "event_emitting_consumer [%s]: no interceptor context and no "
                "default workflow — dropping inbound event for %s",
                source_label, remote_agent_id,
            )
            return None
        logger.warning(
            "event_emitting_consumer [%s]: no valid interceptor context "
            "— minting fresh correlation_id; inbound event will not correlate "
            "with outbound. This is expected only for standalone consumer usage.",
            source_label,
        )
        correlation_id = f"correlation://{uuid4()}"
        instance_id = None
        workflow_ctx = default_workflow_ctx
        allocator = _RuntimeIdAllocator()

    should_clear_ctx = False
    if response_status in _TERMINAL_STATUSES:
        if ictx is not None and len(ictx.remote_agent_ids) > 1:
            async with _fan_out_lock:
                completed_agent_ids.add(remote_agent_id)
                if completed_agent_ids >= set(ictx.remote_agent_ids):
                    should_clear_ctx = True
                    logger.debug(
                        "event_emitting_consumer [%s]: all %d remotes responded, "
                        "clearing interceptor context.",
                        source_label, len(ictx.remote_agent_ids),
                    )
        else:
            should_clear_ctx = True

    return correlation_id, instance_id, workflow_ctx, allocator, should_clear_ctx


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

        completed_agent_ids = _completed_agent_ids_ctx.get()
        if completed_agent_ids is None:
            completed_agent_ids = set()
            _completed_agent_ids_ctx.set(completed_agent_ids)

        remote_agent_id = await _resolve_fan_out_remote_agent_id(
            agent_id,
            event,
            completed_agent_ids,
        )

        response_status: TaskState | None = None

        task_obj = _extract_task_from_client_event(event)
        if task_obj and task_obj.status and task_obj.status.state:
            response_status = task_obj.status.state

        resolved = await _resolve_consumer_context(
            remote_agent_id, active_transport, response_status,
            source_label=_source,
            default_workflow_ctx=_default_workflow_ctx,
            completed_agent_ids=completed_agent_ids,
        )
        if resolved is None:
            return
        correlation_id, instance_id, workflow_ctx, allocator, should_clear_ctx = resolved

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

        if should_clear_ctx and _interceptor_ctx.get() is not None:
            _completed_agent_ids_ctx.set(None)
            _interceptor_ctx.set(None)

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