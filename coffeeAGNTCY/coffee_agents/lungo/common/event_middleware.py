# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""A2A middleware that emits ``event_v1`` topology-discovery events.

The interceptor (outbound, ``operation: create``) and consumer (inbound,
``operation: update``) each emit a ``PartialTopology`` that progressively
reveals the service graph as agents communicate.  ``starting_topology`` is
left empty, the graph is discovered, not declared.

Workflow identity is resolved from a ``tool_workflow_map``; callers only
pass ``"tool"`` in ``ClientCallContext.state``.
"""

from __future__ import annotations

import logging
import uuid as _uuid_mod
from abc import ABC, abstractmethod
from contextvars import ContextVar
from dataclasses import dataclass
from datetime import datetime, timezone
from time import monotonic
from typing import Any
from uuid import uuid4

from a2a.client import ClientEvent
from a2a.client.middleware import ClientCallContext, ClientCallInterceptor
from a2a.types import AgentCard, Message

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

logger = logging.getLogger("lungo.common.event_middleware")


# ---------------------------------------------------------------------------
# Tool → workflow identity mapping
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class ToolWorkflowMapping:
    """Maps a tool to its catalog workflow identity.

    Values must match the catalog's ``starting_workflows.json`` entries
    (see ``api/agentic_workflows/``).  Ideally these should be pulled
    from (or validated against) the catalog's workflow entries at startup
    so that ``workflow_name``, ``pattern``, and ``use_case`` stay
    consistent as the catalog evolves.
    """
    workflow_name: str
    pattern: str
    use_case: str


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
_SCHEMA_VERSION = "1.0.0"

# Namespace for deterministic UUIDs (uuid5) derived from labels.
# TODO: Consider deriving from AgentCard.url instead of name for
# guaranteed stability across label renames.
_NODE_NS = _uuid_mod.uuid5(_uuid_mod.NAMESPACE_DNS, "lungo.nodes")

# Namespace for deriving a stable correlation UUID from an OTel session ID.
_CORRELATION_NS = _uuid_mod.uuid5(_uuid_mod.NAMESPACE_DNS, "lungo.correlation")

# Empty starting topology — the graph is discovered, not declared.
_EMPTY_STARTING_TOPOLOGY = Topology(nodes=[], edges=[])


# ---------------------------------------------------------------------------
# OTel / ioa-observe session context
# ---------------------------------------------------------------------------

def _get_otel_session_id() -> str | None:
    """Read the current ``ioa_observe`` session ID from OTel context.

    Returns ``None`` when no tracing session is active (e.g. in tests
    or when ``OTEL_SDK_DISABLED=true``).
    """
    try:
        from ioa_observe.sdk.tracing.context_utils import get_current_session_id
        return get_current_session_id()
    except Exception:
        return None


def _correlation_id_from_session(session_id: str) -> str:
    """Derive a deterministic ``correlation://UUID`` from a session ID.

    Uses ``uuid5`` so the same session always produces the same
    correlation, and different sessions never collide.
    """
    return f"correlation://{_uuid_mod.uuid5(_CORRELATION_NS, session_id)}"


def _instance_id_from_session(session_id: str, workflow_name: str) -> str:
    """Derive a deterministic ``instance://UUID`` from session + workflow.

    The workflow name is included so that two workflows triggered in the
    same session get distinct instance IDs.
    """
    return f"instance://{_uuid_mod.uuid5(_CORRELATION_NS, f'{session_id}::{workflow_name}')}"


# ---------------------------------------------------------------------------
# Interceptor → consumer context propagation
# ---------------------------------------------------------------------------
# The A2A Consumer callback signature is (ClientEvent|Message, AgentCard) —
# it does not receive ClientCallContext.  We use a ContextVar to propagate
# the interceptor's resolved IDs and workflow mapping so the consumer's
# inbound event correlates with the outbound one.

@dataclass(frozen=True)
class _InterceptorContext:
    """Snapshot of per-call state set by the interceptor for the consumer."""
    correlation_id: str
    instance_id: str
    mapping: ToolWorkflowMapping
    remote_names: tuple[str, ...]
    transport_label: str
    created_at_monotonic: float

_interceptor_ctx: ContextVar[_InterceptorContext | None] = ContextVar(
    "event_middleware_interceptor_ctx", default=None,
)

_INTERCEPTOR_CTX_MAX_AGE_SECONDS = 300.0


# ---------------------------------------------------------------------------
# Deterministic ID helpers
# ---------------------------------------------------------------------------

def agent_node_id(card: AgentCard) -> str:
    """Deterministic ``node://UUID`` for an agent, derived from its card name.

    Accepts an ``AgentCard`` so callers don't need to know which field
    drives identity — the same function can be reused anywhere an agent
    node ID is needed (topology builders, starting topology generation,
    validation, etc.).

    .. todo:: The generated IDs must be validated against the event_v1 JSON
       Schema (``NodeId`` pattern) and aligned with the node IDs in the
       catalog's ``starting_workflows.json`` so that runtime topology
       updates match the starting topology nodes.
    """
    return f"node://{_uuid_mod.uuid5(_NODE_NS, f'agent-{card.name}')}"


def _agent_node_id_from_name(agent_name: str) -> str:
    """Internal shorthand — derive node ID from a plain name string.

    Prefer :func:`agent_node_id` (card-based) for new code.
    """
    return f"node://{_uuid_mod.uuid5(_NODE_NS, f'agent-{agent_name}')}"


def _transport_node_id(caller_name: str, transport_label: str) -> str:
    """Deterministic ``node://UUID`` for a transport hop.

    Keyed on ``(caller_name, transport_label)`` so every call from the
    same caller through the same transport type shares one node.
    Both the interceptor and consumer can compute this independently
    from the AgentCard.

    .. todo:: The generated IDs must be validated against the event_v1 JSON
       Schema (``NodeId`` pattern) and aligned with the transport node IDs
       in the catalog's ``starting_workflows.json``.
    """
    key = f"{caller_name}::{transport_label}"
    return f"node://{_uuid_mod.uuid5(_NODE_NS, f'transport-{key}')}"


def _edge_id(source_nid: str, target_nid: str) -> str:
    """Deterministic ``edge://UUID`` derived from the two node IDs it connects.

    .. todo:: The generated IDs must be validated against the event_v1 JSON
       Schema (``EdgeId`` pattern) and aligned with the edge IDs in the
       catalog's ``starting_workflows.json``.
    """
    return f"edge://{_uuid_mod.uuid5(_NODE_NS, f'{source_nid}->{target_nid}')}"


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


def _make_edge(
    source_nid: str,
    target_nid: str,
    *,
    operation: Operation,
) -> PartialEdge:
    """Create a ``PartialEdge`` for a topology discovery event.

    Edge ``type`` is ``"custom"`` to match the catalog starting topology
    convention and the frontend's registered ReactFlow ``edgeTypes``
    (``"custom"`` and ``"branching"``).  ``bidirectional`` is ``False``
    — edges are directed; the bidirectional nature of request/response
    is captured by separate outbound and inbound events.
    """
    kwargs: dict[str, Any] = dict(
        id=EdgeId(_edge_id(source_nid, target_nid)),
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
    correlation_id: str | None = None,
    correlation_message: str | None = None,
) -> Metadata:
    cid = correlation_id or f"correlation://{uuid4()}"

    return Metadata(
        timestamp=datetime.now(timezone.utc),
        schema_version=_SCHEMA_VERSION,
        id=EventId(f"event://{uuid4()}"),
        type=event_type,
        source=source,
        correlation=Correlation(
            id=CorrelationId(cid),
            message=correlation_message,
        ),
    )


def _build_event(
    *,
    source: str,
    workflow_name: str,
    workflow_use_case: str,
    instance_id: str | None,
    topology: PartialTopology,
    pattern: str | None = None,
    event_type: EventType = EventType.STATE_PROGRESS_UPDATE,
    correlation_id: str | None = None,
    correlation_message: str | None = None,
) -> Event:
    """Assemble a full ``Event`` with one workflow instance update.

    ``starting_topology`` is always empty — the partial topology in each
    instance *is* the discovery payload.

    The ``Event.data.workflows`` dict is keyed by ``workflow_name`` (the
    catalog workflow name) so events can be correlated with catalog entries
    served by ``GET /agentic-workflows/{workflow_name}/``.

    *pattern* is the catalog architectural pattern (e.g.
    ``"Supervisor-worker"``).  Defaults to *workflow_name* when not provided.
    """
    iid = instance_id or f"instance://{uuid4()}"

    return Event(
        metadata=_build_metadata(
            source=source,
            event_type=event_type,
            correlation_id=correlation_id,
            correlation_message=correlation_message,
        ),
        data=Data(
            workflows={
                workflow_name: Workflow(
                    pattern=pattern or workflow_name,
                    use_case=workflow_use_case,
                    name=workflow_name,
                    starting_topology=_EMPTY_STARTING_TOPOLOGY,
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

# NOTE: The outbound interceptor is stateless — it always emits
# operation=CREATE because it cannot know whether a node/edge was emitted
# in a prior request cycle.  The inbound consumer, however, can truthfully
# emit operation=UPDATE because a response guarantees the outbound
# interceptor already fired CREATE for the same path within the same
# request/response cycle.
#
# For the outbound side, correct CRUD lifecycle (CREATE on first sight,
# UPDATE thereafter) should be resolved by the component that owns
# topology state.  Two approaches:
#
#   a) The workflow API / state aggregator normalises CREATE → UPDATE when the
#      node/edge ID already exists in its store.  This is the preferred path:
#      it keeps the middleware simple and pushes lifecycle semantics to the
#      single stateful layer that already aggregates events.
#
#   b) The middleware reads back from the event store (EventSinkRegistry) or
#      tracks a local seen-set (self._seen_ids) to decide CREATE vs UPDATE.
#      This adds coupling/state to the middleware and doesn't survive restarts
#      or multi-instance deployments.

def _outbound_topology(
    caller_name: str,
    remote_names: list[str],
    transport_label: str = "Transport",
    layer_index: int = 0,
) -> PartialTopology:
    """Build the partial topology for outbound A2A call(s).

    Handles both point-to-point (single remote) and fan-out (multiple
    remotes) with one code path.  A single shared transport node is
    always created.  Nodes/edges use ``operation: create``; the state
    middleware deduplicates by ID.
    """
    caller_node = _agent_node_id_from_name(caller_name)
    transport_node = _transport_node_id(caller_name, transport_label)

    nodes: list[TopologyNodeItem] = [
        _make_node(caller_node, operation=Operation.CREATE, node_type="customNode",
                   label=caller_name, layer_index=layer_index),
        _make_node(transport_node, operation=Operation.CREATE, node_type="transportNode",
                   label=transport_label, layer_index=layer_index + 1),
    ]
    edges: list[TopologyEdgeItem] = [
        _make_edge(caller_node, transport_node, operation=Operation.CREATE),
    ]

    for name in remote_names:
        remote_node = _agent_node_id_from_name(name)
        nodes.append(
            _make_node(remote_node, operation=Operation.CREATE, node_type="customNode",
                       label=name, layer_index=layer_index + 2),
        )
        edges.append(
            _make_edge(transport_node, remote_node, operation=Operation.CREATE),
        )

    return PartialTopology(nodes=nodes, edges=edges)


def _inbound_topology(
    caller_name: str,
    remote_name: str,
    transport_label: str = "Transport",
    layer_index: int = 0,
) -> PartialTopology:
    """Build the partial topology for an inbound A2A response.

    Uses ``operation: update`` because the inbound consumer only fires
    when a response arrives — the outbound interceptor is guaranteed to
    have already emitted ``operation: create`` for these same nodes and
    edges within the same request/response cycle.

    The transport node ID is derived from ``(caller_name, transport_label)``
    so it matches the outbound topology without needing the full
    participant list.
    """
    caller_node = _agent_node_id_from_name(caller_name)
    transport_node = _transport_node_id(caller_name, transport_label)
    remote_node = _agent_node_id_from_name(remote_name)

    return PartialTopology(
        nodes=[
            _make_node(remote_node, operation=Operation.UPDATE, node_type="customNode",
                       label=remote_name, layer_index=layer_index + 2, include_size=False),
            _make_node(transport_node, operation=Operation.UPDATE, node_type="transportNode",
                       label=transport_label, layer_index=layer_index + 1, include_size=False),
            _make_node(caller_node, operation=Operation.UPDATE, node_type="customNode",
                       label=caller_name, layer_index=layer_index, include_size=False),
        ],
        edges=[
            _make_edge(transport_node, remote_node, operation=Operation.UPDATE),
            _make_edge(caller_node, transport_node, operation=Operation.UPDATE),
        ],
    )


# ---------------------------------------------------------------------------
# A2A Middleware: Interceptor (outbound requests)
# ---------------------------------------------------------------------------

class EventEmittingInterceptor(ClientCallInterceptor):
    """Intercepts outbound A2A requests and emits a ``StateProgressUpdate``
    that discovers the caller -> transport -> remote agent path in the
    A2A service graph.

    Caller identity is derived from ``caller_card`` — the same ``AgentCard``
    that describes the caller agent.  ``card.name`` is used as the topology
    node label (and slugified as ``Metadata.source``), consistent with how
    remote agents are identified from their cards.

    Workflow identity (``workflow_name``, ``pattern``, ``use_case``) is
    resolved from ``tool_workflow_map`` using the ``"tool"`` key in
    ``ClientCallContext.state``.  Tools never need to know about catalog
    taxonomy — only this mapping does.

    Instantiate per caller::

        from agents.supervisors.auction.card import AUCTION_SUPERVISOR_CARD

        interceptor = EventEmittingInterceptor(
            caller_card=AUCTION_SUPERVISOR_CARD,
            tool_workflow_map=tool_map,
        )
    """

    def __init__(
        self,
        *,
        caller_card: AgentCard,
        tool_workflow_map: dict[str, ToolWorkflowMapping],
        agent_call_graph_layer: int = 0,
        event_sink: EventSinkRegistry | None = None,
        verbose: bool = False,
    ) -> None:
        if not tool_workflow_map:
            raise ValueError("tool_workflow_map must contain at least one mapping")
        self._caller_label = caller_card.name
        self._source = caller_card.name.lower().replace(" ", "_")
        self._tool_workflow_map = tool_workflow_map
        self._agent_call_graph_layer = agent_call_graph_layer
        self._event_sink = event_sink
        self._verbose = verbose

    def _resolve_workflow(self, tool_name: str | None) -> ToolWorkflowMapping:
        """Look up workflow identity for *tool_name*.

        Falls back to the first entry in the map when the tool name is
        unknown or missing, so events are never silently dropped.
        """
        if tool_name and tool_name in self._tool_workflow_map:
            return self._tool_workflow_map[tool_name]
        fallback = next(iter(self._tool_workflow_map.values()))
        if tool_name:
            logger.warning(
                "EventEmittingInterceptor [%s]: tool %r not in tool_workflow_map, "
                "falling back to %r",
                self._source, tool_name, fallback.workflow_name,
            )
        return fallback

    async def intercept(
        self,
        method_name: str,
        request_payload: dict[str, Any],
        http_kwargs: dict[str, Any],
        agent_card: AgentCard | None,
        context: ClientCallContext | None,
    ) -> tuple[dict[str, Any], dict[str, Any]]:

        # if agent_card is None, log an error and skip event emission to avoid crashes
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

        remote_name = agent_card.name
        preferred_transport = agent_card.preferred_transport or "Transport"
        ctx_state = (context.state if context and context.state else {}) or {}

        # -- Resolve workflow identity from the tool → workflow map --
        mapping = self._resolve_workflow(ctx_state.get("tool"))
        workflow_name = mapping.workflow_name
        pattern = mapping.pattern
        use_case = mapping.use_case
        logger.info("workflow_name=%s pattern=%s use_case=%s tool=%s",
                    workflow_name, pattern, use_case,
                    ctx_state.get("tool", "unknown"))

        # -- Extract threaded IDs from context if the caller set them --
        # Precedence: explicit context value → OTel session → fresh UUID.
        # The fallback UUID is generated once and shared with the ContextVar
        # so the consumer's inbound event uses the same IDs.
        session_id = _get_otel_session_id()
        if not session_id:
            logger.debug(
                "EventEmittingInterceptor [%s]: no OTel session active, "
                "correlation/instance IDs will be random UUIDs.",
                self._source,
            )

        correlation_id: str = (
            ctx_state.get("correlation_id")
            or (_correlation_id_from_session(session_id) if session_id else None)
            or f"correlation://{uuid4()}"
        )
        instance_id: str = (
            ctx_state.get("instance_id")
            or (_instance_id_from_session(session_id, workflow_name) if session_id else None)
            or f"instance://{uuid4()}"
        )

        logger.debug(
            "EventEmittingInterceptor [%s]: correlation_id=%s instance_id=%s "
            "source=%s",
            self._source, correlation_id, instance_id,
            "otel_session" if session_id else "context" if ctx_state.get("correlation_id") else "fallback_uuid",
        )

        # -- Collect all target agents (single or fan-out) --
        extra_cards: list[AgentCard] | None = ctx_state.get("additional_agent_cards")
        if extra_cards:
            discovered_names: list[str] = []
            for card in extra_cards:
                if card is None:
                    logger.warning(
                        "EventEmittingInterceptor [%s]: ignoring None entry in additional_agent_cards",
                        self._source,
                    )
                    continue
                card_name = getattr(card, "name", None)
                if card_name:
                    discovered_names.append(card_name)

            remote_names = list(dict.fromkeys(discovered_names))
            # Ensure the primary agent_card target is included
            if remote_name and remote_name not in remote_names:
                remote_names.insert(0, remote_name)
        else:
            remote_names = [remote_name] if remote_name else []

        # Stash resolved state so the consumer can read it (it doesn't
        # receive ClientCallContext).
        _interceptor_ctx.set(_InterceptorContext(
            correlation_id=correlation_id,
            instance_id=instance_id,
            mapping=mapping,
            remote_names=tuple(remote_names),
            transport_label=preferred_transport,
            created_at_monotonic=monotonic(),
        ))

        # -- Build topology --
        if remote_names:
            topology = _outbound_topology(
                self._caller_label,
                remote_names,
                transport_label=preferred_transport,
                layer_index=self._agent_call_graph_layer,
            )
            targets = ", ".join(remote_names)
            correlation_msg = f"outbound {method_name} to [{targets}]"
        else:
            # Unknown remote — emit just the caller node as discovered
            caller_node = _agent_node_id_from_name(self._caller_label)
            topology = PartialTopology(
                nodes=[_make_node(
                    caller_node,
                    operation=Operation.CREATE,
                    node_type="customNode",
                    label=self._caller_label,
                    layer_index=self._agent_call_graph_layer,
                )],
                edges=[],
            )
            correlation_msg = f"outbound {method_name} to unknown"

        event = _build_event(
            source=self._source,
            workflow_name=workflow_name,
            workflow_use_case=use_case,
            instance_id=instance_id,
            topology=topology,
            correlation_id=correlation_id,
            correlation_message=correlation_msg,
            pattern=pattern,
        )

        if self._event_sink:
            await self._event_sink.emit(event)

        if self._verbose:
            logger.info(
                "EventEmittingInterceptor [%s]: outbound %s -> %s\n%s",
                self._source,
                method_name,
                remote_name or "unknown",
                event.model_dump_json(indent=2, exclude_none=True),
            )

        return request_payload, http_kwargs


# ---------------------------------------------------------------------------
# A2A Middleware: Consumer factory (inbound response events)
# ---------------------------------------------------------------------------

def make_event_emitting_consumer(
    *,
    caller_card: AgentCard,
    tool_workflow_map: dict[str, ToolWorkflowMapping],
    agent_call_graph_layer: int = 0,
    event_sink: EventSinkRegistry | None = None,
    verbose: bool = False,
):
    """Factory that returns an ``event_emitting_consumer`` closure bound
    to a specific caller's config.

    Caller identity is derived from ``caller_card`` — ``card.name`` for
    topology labels (and slugified as ``Metadata.source``), consistent
    with how remote agents are identified from their cards.

    The A2A ``Consumer`` type is
    ``Callable[[ClientEvent | Message, AgentCard], Coroutine]`` — a bare
    async function.  We use a closure so the consumer carries caller
    config without module-level state.

    Correlation ID, instance ID, and per-call workflow identity are read
    from ``_interceptor_ctx`` (a ``ContextVar`` set by the interceptor in
    the same async task).  Falls back to defaults when the interceptor
    hasn't run (e.g. standalone consumer usage).
    """
    if not tool_workflow_map:
        raise ValueError("tool_workflow_map must contain at least one mapping")

    caller_label = caller_card.name
    _source = caller_card.name.lower().replace(" ", "_")
    _default_mapping = next(iter(tool_workflow_map.values()))

    async def event_emitting_consumer(
        event: ClientEvent | Message,
        agent_card: AgentCard,
    ) -> None:
        """Emits a ``StateProgressUpdate`` that updates the
        caller -> transport -> remote path discovered by the outbound call.
        """
        remote_name = agent_card.name if agent_card else "unknown"
        preferred_transport = (
            agent_card.preferred_transport if agent_card else None
        ) or "Transport"

        # -- Determine response status from the event payload --
        # TODO: Map task.status.state (TaskState enum: "completed",
        # "working", "failed", etc.) to a visual node state once the
        # frontend supports it (extra field on PartialNode).
        response_status: str | None = None

        if isinstance(event, Message):
            response_status = "completed"
        elif isinstance(event, tuple):
            task, _update_event = event
            if hasattr(task, "status") and task.status:
                response_status = (
                    str(task.status.state) if task.status.state else None
                )

        topology = _inbound_topology(
            caller_label, remote_name,
            transport_label=preferred_transport,
            layer_index=agent_call_graph_layer,
        )

        # -- Read correlation/instance IDs and workflow mapping from the
        # interceptor's ContextVar (set during the outbound call in this
        # same async task).  Falls back to closure defaults when the
        # interceptor hasn't run.
        ictx = _interceptor_ctx.get()
        should_clear_ctx = False
        if ictx is not None:
            age_seconds = monotonic() - ictx.created_at_monotonic
            if age_seconds > _INTERCEPTOR_CTX_MAX_AGE_SECONDS:
                logger.warning(
                    "event_emitting_consumer [%s]: interceptor context is stale "
                    "(age=%.2fs), ignoring it.",
                    _source,
                    age_seconds,
                )
                ictx = None
            elif ictx.remote_names and remote_name not in ictx.remote_names:
                logger.warning(
                    "event_emitting_consumer [%s]: interceptor context remote mismatch "
                    "(event=%s, expected_any=%s), ignoring it.",
                    _source,
                    remote_name,
                    ",".join(ictx.remote_names),
                )
                ictx = None
            elif ictx.transport_label != preferred_transport:
                logger.warning(
                    "event_emitting_consumer [%s]: interceptor context transport mismatch "
                    "(event=%s, expected=%s), ignoring it.",
                    _source,
                    preferred_transport,
                    ictx.transport_label,
                )
                ictx = None

        if ictx is not None:
            correlation_id = ictx.correlation_id
            instance_id = ictx.instance_id
            mapping = ictx.mapping
        else:
            logger.warning(
                "event_emitting_consumer [%s]: no interceptor context found "
                "— correlation/instance IDs will not match outbound event. "
                "This is expected only for standalone consumer usage.",
                _source,
            )
            correlation_id = None
            instance_id = None
            mapping = _default_mapping

        if response_status in {"completed", "failed", "canceled", "cancelled"}:
            should_clear_ctx = True

        event_obj = _build_event(
            source=_source,
            workflow_name=mapping.workflow_name,
            workflow_use_case=mapping.use_case,
            instance_id=instance_id,
            topology=topology,
            correlation_id=correlation_id,
            correlation_message=f"response from {remote_name}, status={response_status}",
            pattern=mapping.pattern,
        )

        if event_sink:
            await event_sink.emit(event_obj)

        if verbose:
            logger.info(
                "event_emitting_consumer [%s]: response from %s (status=%s)\n%s",
                _source,
                remote_name,
                response_status,
                event_obj.model_dump_json(indent=2, exclude_none=True),
            )

        if should_clear_ctx and _interceptor_ctx.get() is not None:
            _interceptor_ctx.set(None)

    return event_emitting_consumer


# ---------------------------------------------------------------------------
# Event sink abstraction
# ---------------------------------------------------------------------------

class EventSink(ABC):
    """Interface for anything that can receive an emitted ``Event``.

    Implement this to plug in storage backends, HTTP forwarders,
    message queues, etc.
    """

    @abstractmethod
    async def emit(self, event: Event) -> None:
        """Handle *event*.  Implementations should be non-blocking."""


class EventSinkRegistry:
    """Fan-out registry — emits every event to all registered sinks.

    Usage::

        registry = EventSinkRegistry()
        registry.add(InMemoryEventSink())
        registry.add(HttpEventSink(url="http://..."))

        interceptor = EventEmittingInterceptor(..., event_sink=registry)
        consumer    = make_event_emitting_consumer(..., event_sink=registry)
    """

    def __init__(self) -> None:
        self._sinks: list[EventSink] = []

    def add(self, sink: EventSink) -> None:
        self._sinks.append(sink)

    async def emit(self, event: Event) -> None:
        for sink in self._sinks:
            try:
                await sink.emit(event)
            except Exception:
                logger.exception("EventSinkRegistry: sink %s failed", type(sink).__name__)
