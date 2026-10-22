# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""A2A client middleware for emitting workflow topology events.

This module contains the A2A client interceptor: ``before`` emits the
outbound topology event and ``after`` the inbound one, once per response
(once per event for streams). Shared event builders and sinks live in
workflow_utils.
"""

from __future__ import annotations

import logging
from time import monotonic
from typing import Any, Literal, Mapping

from a2a.client import ClientCallContext
from a2a.client.interceptors import AfterArgs, BeforeArgs, ClientCallInterceptor
from a2a.types import AgentCard
from google.protobuf.json_format import MessageToDict
from opentelemetry import trace as _otel_trace
from pydantic import ValidationError

from common.a2a_helpers import (
    message_metadata,
    primary_transport,
    response_message,
    task_state_label,
)
from common.stable_agent_id import stable_agent_id_for_name as _stable_agent_id
from common.workflow_utils.builders import build_event, make_edge, make_node
from common.workflow_utils.node_types import AGENT, TRANSPORT
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
    InstanceId,
    Operation,
    PartialTopology,
    TopologyEdgeItem,
    TopologyNodeItem,
)

logger = logging.getLogger("lungo.common.event_middleware")

# Interceptor method names (a2a-sdk BaseClient and the app-sdk patterns
# client) for the calls that carry a message; other methods emit nothing.
_MESSAGE_METHODS = frozenset({"send_message", "send_message_streaming"})


def _is_valid_instance_id(value: str) -> bool:
    """True when value is a canonical ``instance://<uuid>`` id (schema-validated)."""
    try:
        InstanceId(root=value)
    except ValidationError:
        return False
    return True


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
    broadcast_cards: list[AgentCard | None] | None = ctx_state.get(
        "broadcast_agent_cards"
    )
    remote_cards: list[AgentCard | None] = (
        broadcast_cards if broadcast_cards else [agent_card]
    )
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

    This bridges the outbound call to its inbound ``after`` callbacks, which
    are correlated through the trace (broadcast and group chat replies arrive
    without the per-call state).
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
    transport_node = await allocator.node_id(
        f"transport-{caller_agent_id}::{transport_label}"
    )

    nodes: list[TopologyNodeItem] = [
        make_node(
            caller_node,
            operation=Operation.CREATE,
            node_type=AGENT,
            label=caller_agent_id,
            layer_index=layer_index,
            stable_agent_id=_stable_agent_id(caller_agent_id),
        ),
        make_node(
            transport_node,
            operation=Operation.CREATE,
            node_type=TRANSPORT,
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
                node_type=AGENT,
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


async def _delegation_edge_topology(
    anchor_stable_agent_id: str,
    anchor_label: str,
    remote_agent_ids: list[str],
    layer_index: int,
    *,
    allocator: RuntimeIdAllocator,
) -> PartialTopology:
    """Build recruiter-style delegation: anchor nodes + edges only (no transport).

    Anchor nodes carry ``stable_agent_id`` values so the merge layer reconciles
    them onto existing seeded/discovered nodes instead of creating duplicates.
    """
    anchor_id = await allocator.node_id("delegation-recruiter-anchor")
    nodes: list[TopologyNodeItem] = [
        make_node(
            anchor_id,
            operation=Operation.CREATE,
            node_type=AGENT,
            label=anchor_label,
            layer_index=layer_index,
            stable_agent_id=anchor_stable_agent_id,
        ),
    ]
    edges: list[TopologyEdgeItem] = []
    for agent_id in remote_agent_ids:
        remote_anchor_id = await allocator.node_id(f"delegation-remote-{agent_id}")
        nodes.append(
            make_node(
                remote_anchor_id,
                operation=Operation.CREATE,
                node_type=AGENT,
                label=agent_id,
                layer_index=layer_index + 1,
                stable_agent_id=_stable_agent_id(agent_id),
            ),
        )
        edges.append(
            await make_edge(
                anchor_id,
                remote_anchor_id,
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
    transport_node = await allocator.node_id(
        f"transport-{caller_agent_id}::{transport_label}"
    )
    remote_node = await allocator.node_id(f"agent-{remote_agent_id}")

    return PartialTopology(
        nodes=[
            make_node(
                remote_node,
                operation=Operation.UPDATE,
                node_type=AGENT,
                label=remote_agent_id,
                layer_index=layer_index + 2,
                include_size=False,
                stable_agent_id=_stable_agent_id(remote_agent_id),
            ),
            make_node(
                transport_node,
                operation=Operation.UPDATE,
                node_type=TRANSPORT,
                label=transport_label,
                layer_index=layer_index + 1,
                include_size=False,
            ),
            make_node(
                caller_node,
                operation=Operation.UPDATE,
                node_type=AGENT,
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
    """Emit outbound and inbound topology events for A2A calls.

    ``before`` emits the outbound discovery event; ``after`` emits the inbound
    update for every response (every event of a stream, every broadcast or
    group chat reply). Neither raises: the app-sdk patterns client turns an
    ``after`` failure into a failed broadcast reply, so emission errors are
    logged and swallowed.
    """

    def __init__(
        self,
        *,
        caller_card: AgentCard,
        agent_call_graph_layer: int = 0,
        delegation_mode: Literal["full", "edge_only"] = "full",
        delegation_anchor_stable_agent_id: str | None = None,
        delegation_anchor_label: str = "Agentic Recruiter",
    ) -> None:
        self._caller_agent_id = caller_card.name
        self._source = _slugify_source(caller_card)
        self._agent_call_graph_layer = agent_call_graph_layer
        self._delegation_mode = delegation_mode
        self._delegation_anchor_stable_agent_id = delegation_anchor_stable_agent_id
        self._delegation_anchor_label = delegation_anchor_label

        if delegation_mode == "edge_only" and not delegation_anchor_stable_agent_id:
            msg = "delegation_anchor_stable_agent_id is required when delegation_mode='edge_only'"
            raise ValueError(msg)

        if not EMIT_WORKFLOW_EVENTS:
            logger.warning(
                "EventEmittingInterceptor [%s]: EMIT_WORKFLOW_EVENTS is false, interceptor will not emit events.",
                self._source,
            )
            self._event_sink = None
        else:
            self._event_sink = WorkflowAPIEventSink()

    async def before(self, args: BeforeArgs) -> None:
        """Emit the outbound topology event for a message call."""
        if args.method not in _MESSAGE_METHODS:
            return
        try:
            await self._emit_outbound(args.method, args.agent_card, args.context)
        except Exception:
            logger.exception(
                "EventEmittingInterceptor [%s]: outbound event emission failed for method '%s'.",
                self._source,
                args.method,
            )

    async def after(self, args: AfterArgs) -> None:
        """Emit the inbound topology event for one response or stream event."""
        if args.method not in _MESSAGE_METHODS:
            return
        if self._delegation_mode == "edge_only":
            return
        try:
            await self._emit_inbound(args.result, args.agent_card)
        except Exception:
            logger.exception(
                "EventEmittingInterceptor [%s]: inbound event emission failed for method '%s'.",
                self._source,
                args.method,
            )

    async def _emit_outbound(
        self,
        method_name: str,
        agent_card: AgentCard | None,
        context: ClientCallContext | None,
    ) -> None:
        t_intercept_start = monotonic()

        # 1) Validate call context and resolve workflow identity.

        if agent_card is None:
            logger.error(
                "EventEmittingInterceptor [%s]: Missing agent_card for method '%s', skipping event emission.",
                self._source,
                method_name,
            )
            return
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
                "Falling back to random correlation IDs; inbound (after) callbacks will not "
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
            return

        if not propagated_instance_id or not _is_valid_instance_id(
            propagated_instance_id
        ):
            logger.warning(
                "EventEmittingInterceptor [%s]: missing or malformed propagated "
                "workflow_instance_id=%r on method '%s'; skipping event emission.",
                self._source,
                propagated_instance_id,
                method_name,
            )
            return

        workflow_name = metadata.name
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

        active_transport = primary_transport(agent_card) or "Transport"

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
            if (
                self._delegation_mode == "edge_only"
                and self._delegation_anchor_stable_agent_id is not None
            ):
                topology = await _delegation_edge_topology(
                    self._delegation_anchor_stable_agent_id,
                    self._delegation_anchor_label,
                    remote_agent_ids,
                    layer_index=self._agent_call_graph_layer,
                    allocator=allocator,
                )
            else:
                topology = await _outbound_topology(
                    self._caller_agent_id,
                    remote_agent_ids,
                    transport_label=active_transport,
                    layer_index=self._agent_call_graph_layer,
                    allocator=allocator,
                )
            correlation_msg = (
                f"outbound {method_name} to [{', '.join(remote_agent_ids)}]"
            )
        else:
            caller_node = await allocator.node_id(f"agent-{self._caller_agent_id}")
            topology = PartialTopology(
                nodes=[
                    make_node(
                        caller_node,
                        operation=Operation.CREATE,
                        node_type=AGENT,
                        label=self._caller_agent_id,
                        layer_index=self._agent_call_graph_layer,
                        stable_agent_id=_stable_agent_id(self._caller_agent_id),
                    )
                ],
                edges=[],
            )
            correlation_msg = f"outbound {method_name} to unknown"

        event = build_event(
            source=self._source,
            identity=metadata,
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

    async def _emit_inbound(self, result: Any, agent_card: AgentCard | None) -> None:
        """Emit a StateProgressUpdate for one inbound response."""
        t_receive_start = monotonic()

        agent_id = agent_id_from_card(agent_card) or "unknown"
        active_transport = primary_transport(agent_card) or "Transport"

        trace_id_int = current_trace_id()
        span_id_int = (
            _otel_trace.get_current_span().get_span_context().span_id
            if trace_id_int is not None
            else None
        )

        # 1) Resolve remote identity and correlated interaction state.

        remote_agent_id = _remote_agent_id_from_response(result) or agent_id

        consumer_state = resolve_consumer_state(
            trace_id=trace_id_int,
            remote_agent_id=remote_agent_id,
            source=self._source,
        )
        if consumer_state is None:
            return
        correlation_id, instance_id, workflow_name, allocator = consumer_state

        identity = lookup_workflow(workflow_name)
        if identity is None:
            logger.warning(
                "EventEmittingInterceptor [%s]: no catalog match for workflow_name=%r; "
                "skipping inbound event emission.",
                self._source,
                workflow_name,
            )
            return

        # 2) Build inbound topology update and event payload.
        topology = await _inbound_topology(
            self._caller_agent_id,
            remote_agent_id,
            transport_label=active_transport,
            layer_index=self._agent_call_graph_layer,
            allocator=allocator,
        )

        status_label = task_state_label(_response_task_state(result))

        event_obj = build_event(
            source=self._source,
            identity=identity,
            instance_id=instance_id,
            topology=topology,
            correlation_id=correlation_id,
            correlation_message=f"response from {remote_agent_id}, status={status_label}",
            trace_id=trace_id_int,
            span_id=span_id_int,
        )

        # 3) Emit event and optionally log payload.
        if self._event_sink:
            await self._event_sink.emit(event_obj)

        if logger.isEnabledFor(logging.DEBUG):
            logger.debug(
                "EventEmittingInterceptor [%s]: response from %s (status=%s) (processing time=%.3fs)\n%s",
                self._source,
                remote_agent_id,
                status_label,
                monotonic() - t_receive_start,
                event_obj.model_dump_json(indent=2, exclude_none=True),
            )


def _payload(result: Any) -> str | None:
    """Selected ``payload`` oneof of a SendMessageResponse/StreamResponse."""
    which = getattr(result, "WhichOneof", None)
    return which("payload") if which else None


def _response_task_state(result: Any) -> int | None:
    """Task state carried by a response, or ``None`` for a plain message."""
    which = _payload(result)
    if which == "task":
        return result.task.status.state
    if which == "status_update":
        return result.status_update.status.state
    return None


def _response_metadata(result: Any) -> dict[str, Any]:
    """Metadata of a response: the task or update metadata, else the message's."""
    which = _payload(result)
    holder = None
    if which == "task":
        holder = result.task
    elif which == "status_update":
        holder = result.status_update
    if holder is not None and holder.HasField("metadata"):
        return MessageToDict(holder.metadata)
    return message_metadata(response_message(result))


def _remote_agent_id_from_response(result: Any) -> str | None:
    """Extract the remote agent ID (``metadata.name``) from a response."""
    agent_id = _response_metadata(result).get("name")
    if isinstance(agent_id, str):
        stripped = agent_id.strip()
        if stripped and stripped not in {"None", "null"}:
            return stripped
    return None
