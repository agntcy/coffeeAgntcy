# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""Unit tests for ``common.a2a_event_middleware``.

Covers outbound/inbound emission, in-flight lifecycle, cleanup registration,
and retry determinism for correlation, instance, and topology IDs.
"""

from __future__ import annotations

import logging
from types import SimpleNamespace
from typing import Any
from unittest.mock import MagicMock

import pytest
from a2a.client.middleware import ClientCallContext
from a2a.types import Task, TaskState, TaskStatus


# ---------------------------------------------------------------------------
# Local helpers
# ---------------------------------------------------------------------------

def _make_workflow_identity(name: str = "Test Workflow Alpha"):
    from common.a2a_event_middleware import WorkflowIdentity

    return WorkflowIdentity(
        workflow_name=name,
        pattern="Supervisor-worker",
        use_case="Unit Test",
    )


def _resolver_for(name: str = "Test Workflow Alpha"):
    """Resolver that always returns the same workflow, regardless of tool."""
    identity = _make_workflow_identity(name)
    return lambda _tool: identity


def _task(metadata: dict | None = None, state: TaskState = TaskState.completed) -> Task:
    return Task(
        context_id="ctx",
        id="task-1",
        status=TaskStatus(state=state),
        metadata=metadata,
    )


def _client_event(task: Task) -> tuple:
    """Wrap a ``Task`` in the tuple shape expected by the consumer."""
    return (task, None)


def _node_ids(event) -> list[str]:
    """Return node IDs from the single workflow instance in an event."""
    instance = _first_instance(event)
    return [str(n.id) for n in instance.topology.nodes]


def _first_instance(event):
    """Return the first workflow instance from an event payload."""
    workflow = next(iter(event.data.workflows.values()))
    return next(iter(workflow.instances.values()))


def _first_instance_id(event) -> str:
    """Return the first workflow instance ID from an event payload."""
    workflow = next(iter(event.data.workflows.values()))
    return next(iter(workflow.instances.keys()))


def _correlation_id(event) -> str:
    """Return correlation ID from an event payload."""
    cid = event.metadata.correlation.id
    return cid.root if hasattr(cid, "root") else str(cid)


@pytest.fixture
def captured_events(monkeypatch):
    """Patch ``WorkflowAPIEventSink`` and collect emitted events in-memory."""
    from common import a2a_event_middleware as mw

    captured: list[Any] = []

    class _CapturingSink:
        def __init__(self, *_a, **_kw):
            pass

        async def emit(self, event):
            captured.append(event)

        async def aclose(self):
            pass

    monkeypatch.setattr(mw, "WorkflowAPIEventSink", _CapturingSink)
    return captured


# ---------------------------------------------------------------------------
# Runtime ID allocator
# ---------------------------------------------------------------------------

class TestRuntimeIdAllocator:
    async def test_distinct_allocators_yield_distinct_ids(self):
        """Distinct allocators should not share node IDs for the same key."""
        from common.a2a_event_middleware import _RuntimeIdAllocator

        a1 = _RuntimeIdAllocator()
        a2 = _RuntimeIdAllocator()
        assert await a1.node_id("same-key") != await a2.node_id("same-key")


# ---------------------------------------------------------------------------
# Cleanup span processor
# ---------------------------------------------------------------------------

class TestInFlightCleanupSpanProcessor:
    def _seed_state(self, trace_id: int, owner_span_id: int):
        from common import a2a_event_middleware as mw
        from common.a2a_event_middleware import (
            _InterceptionState,
            _RuntimeIdAllocator,
        )

        state = _InterceptionState(
            correlation_id="correlation://x",
            instance_id="instance://x",
            workflow_ctx=_make_workflow_identity(),
            remote_agent_ids=("remote",),
            transport_label="JSONRPC",
            allocator=_RuntimeIdAllocator(),
            owner_span_id=owner_span_id,
        )
        mw._in_flight[trace_id] = state
        return state

    def _fake_span(self, trace_id: int, span_id: int, name: str = "span"):
        ctx = SimpleNamespace(trace_id=trace_id, span_id=span_id)
        return SimpleNamespace(
            name=name,
            get_span_context=lambda: ctx,
        )

    def test_evicts_on_owner_span_end(self):
        from common import a2a_event_middleware as mw
        from common.a2a_event_middleware import _InFlightCleanupSpanProcessor

        self._seed_state(trace_id=0xAAA, owner_span_id=0xBBB)
        processor = _InFlightCleanupSpanProcessor()

        processor.on_end(self._fake_span(trace_id=0xAAA, span_id=0xBBB))

        assert 0xAAA not in mw._in_flight

    def test_sibling_span_does_not_evict(self):
        """A different span in the same trace must not drop the state — only
        the owning span does."""
        from common import a2a_event_middleware as mw
        from common.a2a_event_middleware import _InFlightCleanupSpanProcessor

        self._seed_state(trace_id=0xAAA, owner_span_id=0xBBB)
        processor = _InFlightCleanupSpanProcessor()

        processor.on_end(self._fake_span(trace_id=0xAAA, span_id=0xDEAD))

        assert 0xAAA in mw._in_flight

    async def test_owner_span_round_trip_via_interceptor(
        self, agent_card_factory, otel_span, patch_emit_events, captured_events,
    ):
        """State ownership should be tied to parent span, not child interceptor span."""
        from common import a2a_event_middleware as mw
        from common.a2a_event_middleware import (
            EventEmittingInterceptor,
            _InFlightCleanupSpanProcessor,
        )

        patch_emit_events(True)
        caller_card = MagicMock()
        caller_card.name = "Auction Agent"
        interceptor = EventEmittingInterceptor(
            caller_card=caller_card, workflow_resolver=_resolver_for(),
        )

        remote = agent_card_factory("Brazil Farm")
        ctx = ClientCallContext(state={"tool": "get_farm_yield_inventory"})
        trace_id, interceptor_span_id, parent_span_id = 0xAAA, 0xBBB, 0xCCC

        with otel_span(
            trace_id=trace_id,
            span_id=interceptor_span_id,
            parent_span_id=parent_span_id,
        ):
            await interceptor.intercept(
                "send_message", {}, {}, agent_card=remote, context=ctx,
            )

        assert trace_id in mw._in_flight
        state = mw._in_flight[trace_id]
        assert state.owner_span_id == parent_span_id

        processor = _InFlightCleanupSpanProcessor()

        child_ctx = SimpleNamespace(
            trace_id=trace_id, span_id=interceptor_span_id,
        )
        processor.on_end(SimpleNamespace(
            name="interceptor", get_span_context=lambda: child_ctx,
        ))
        assert trace_id in mw._in_flight

        parent_ctx = SimpleNamespace(
            trace_id=trace_id, span_id=parent_span_id,
        )
        processor.on_end(SimpleNamespace(
            name="tool", get_span_context=lambda: parent_ctx,
        ))
        assert trace_id not in mw._in_flight


class TestRegisterCleanupSpanProcessor:
    def test_idempotent_on_same_provider(self, monkeypatch):
        from common import a2a_event_middleware as mw

        provider = MagicMock()
        del provider._lungo_cleanup_registered  # ensure missing
        monkeypatch.setattr(
            mw._otel_trace, "get_tracer_provider", lambda: provider,
        )

        mw.register_cleanup_span_processor()
        mw.register_cleanup_span_processor()

        assert provider.add_span_processor.call_count == 1

    def test_graceful_when_provider_has_no_add_span_processor(
        self, monkeypatch, caplog,
    ):
        from common import a2a_event_middleware as mw

        provider = SimpleNamespace()
        monkeypatch.setattr(
            mw._otel_trace, "get_tracer_provider", lambda: provider,
        )

        with caplog.at_level(logging.WARNING, logger=mw.logger.name):
            mw.register_cleanup_span_processor()

        assert any(
            "no add_span_processor" in rec.getMessage()
            or "add_span_processor" in rec.getMessage()
            for rec in caplog.records
        )


# ---------------------------------------------------------------------------
# EventEmittingInterceptor
# ---------------------------------------------------------------------------

class TestEventEmittingInterceptor:
    def _build(
        self, *, patch_emit_events, caller="Auction Agent", flag=True,
    ):
        from common.a2a_event_middleware import EventEmittingInterceptor

        patch_emit_events(flag)
        caller_card = MagicMock()
        caller_card.name = caller
        return EventEmittingInterceptor(
            caller_card=caller_card,
            workflow_resolver=_resolver_for(),
        )

    async def test_emits_create_event_with_trace_derived_ids(
        self, agent_card_factory, otel_span, patch_emit_events, captured_events,
    ):
        """Same active trace should produce stable correlation and instance IDs."""
        interceptor = self._build(patch_emit_events=patch_emit_events)

        remote = agent_card_factory("Brazil Farm")
        ctx = ClientCallContext(state={"tool": "get_farm_yield_inventory"})

        with otel_span(trace_id=0xDEADBEEF, span_id=0x1234, parent_span_id=0x9999):
            await interceptor.intercept(
                "send_message", {}, {}, agent_card=remote, context=ctx,
            )
            await interceptor.intercept(
                "send_message", {}, {}, agent_card=remote, context=ctx,
            )

        assert len(captured_events) == 2
        cid_1 = _correlation_id(captured_events[0])
        cid_2 = _correlation_id(captured_events[1])
        assert cid_1 == cid_2  # deterministic across retries
        assert cid_1 == "correlation://00000000-0000-0000-0000-0000deadbeef"

    async def test_reentry_preserves_allocator_node_ids(
        self, agent_card_factory, otel_span, patch_emit_events, captured_events,
    ):
        """Retries in one trace should keep node IDs stable via allocator reuse."""
        interceptor = self._build(patch_emit_events=patch_emit_events)

        remote = agent_card_factory("Brazil Farm")
        ctx = ClientCallContext(state={"tool": "get_farm_yield_inventory"})

        with otel_span(trace_id=0xAAA, span_id=0xBBB, parent_span_id=0xCCC):
            await interceptor.intercept(
                "send_message", {}, {}, agent_card=remote, context=ctx,
            )
            await interceptor.intercept(
                "send_message", {}, {}, agent_card=remote, context=ctx,
            )

        assert sorted(_node_ids(captured_events[0])) == sorted(
            _node_ids(captured_events[1])
        )

    async def test_broadcast_fan_out_includes_every_remote(
        self, agent_card_factory, otel_span, patch_emit_events, captured_events,
    ):
        interceptor = self._build(patch_emit_events=patch_emit_events)

        primary = agent_card_factory("Brazil Farm")
        cards = [
            agent_card_factory("Brazil Farm"),
            agent_card_factory("Colombia Farm"),
            agent_card_factory("Vietnam Farm"),
        ]
        ctx = ClientCallContext(state={
            "tool": "get_all_farms_yield_inventory",
            "broadcast_agent_cards": cards,
        })

        with otel_span(trace_id=0x1, span_id=0x2, parent_span_id=0x3):
            await interceptor.intercept(
                "send_message", {}, {}, agent_card=primary, context=ctx,
            )

        [event] = captured_events
        workflow = next(iter(event.data.workflows.values()))
        instance = next(iter(workflow.instances.values()))
        node_labels = {n.label for n in instance.topology.nodes}
        assert {"Brazil Farm", "Colombia Farm", "Vietnam Farm"} <= node_labels

    async def test_outbound_topology_uses_create_operation(
        self, agent_card_factory, otel_span, patch_emit_events, captured_events,
    ):
        """Outbound topology should emit ``Operation.CREATE`` on all nodes/edges."""
        from schema.types import Operation

        interceptor = self._build(patch_emit_events=patch_emit_events)
        remote = agent_card_factory("Brazil Farm")
        ctx = ClientCallContext(state={"tool": "get_farm_yield_inventory"})

        with otel_span(trace_id=0x1, span_id=0x2, parent_span_id=0x3):
            await interceptor.intercept(
                "send_message", {}, {}, agent_card=remote, context=ctx,
            )

        [event] = captured_events
        instance = _first_instance(event)
        assert instance.topology.nodes, "expected non-empty outbound topology"
        assert instance.topology.edges, "expected non-empty outbound edges"
        assert all(n.operation == Operation.CREATE for n in instance.topology.nodes)
        assert all(e.operation == Operation.CREATE for e in instance.topology.edges)

    async def test_instance_id_is_deterministic_across_retries(
        self, agent_card_factory, otel_span, patch_emit_events, captured_events,
    ):
        """Clearing ``_in_flight`` should still recompute the same instance ID."""
        from common import a2a_event_middleware as mw

        interceptor = self._build(patch_emit_events=patch_emit_events)
        remote = agent_card_factory("Brazil Farm")
        ctx = ClientCallContext(state={"tool": "get_farm_yield_inventory"})

        with otel_span(trace_id=0xFEED, span_id=0xBEEF, parent_span_id=0xCAFE):
            await interceptor.intercept(
                "send_message", {}, {}, agent_card=remote, context=ctx,
            )
            mw._in_flight.clear()
            await interceptor.intercept(
                "send_message", {}, {}, agent_card=remote, context=ctx,
            )

        inst_id_1 = _first_instance_id(captured_events[0])
        inst_id_2 = _first_instance_id(captured_events[1])
        assert inst_id_1 == inst_id_2, (
            "instance_id must be deterministic across retries within a trace"
        )

    async def test_flag_disabled_skips_sink(
        self, agent_card_factory, otel_span, patch_emit_events, captured_events,
    ):
        interceptor = self._build(
            patch_emit_events=patch_emit_events, flag=False,
        )
        remote = agent_card_factory("Brazil Farm")
        ctx = ClientCallContext(state={"tool": "get_farm_yield_inventory"})

        with otel_span(trace_id=0x1, span_id=0x2):
            await interceptor.intercept(
                "send_message", {}, {}, agent_card=remote, context=ctx,
            )

        assert captured_events == []

    async def test_missing_agent_card_is_noop(
        self, otel_span, patch_emit_events, captured_events,
    ):
        """Missing ``agent_card`` should be a safe no-op pass-through."""
        interceptor = self._build(patch_emit_events=patch_emit_events)

        payload, http_kwargs = {}, {}
        with otel_span(trace_id=0x1, span_id=0x2):
            out_payload, out_kwargs = await interceptor.intercept(
                "send_message", payload, http_kwargs,
                agent_card=None, context=None,
            )

        assert out_payload is payload
        assert out_kwargs is http_kwargs
        assert captured_events == []


# ---------------------------------------------------------------------------
# make_event_emitting_consumer
# ---------------------------------------------------------------------------

class TestEventEmittingConsumer:
    def _build_pair(self, *, patch_emit_events, resolver=None):
        from common.a2a_event_middleware import (
            EventEmittingInterceptor,
            make_event_emitting_consumer,
        )

        patch_emit_events(True)
        caller = MagicMock()
        caller.name = "Auction Agent"
        workflow_resolver = resolver or _resolver_for()
        interceptor = EventEmittingInterceptor(
            caller_card=caller, workflow_resolver=workflow_resolver,
        )
        consumer = make_event_emitting_consumer(
            caller_card=caller, workflow_resolver=workflow_resolver,
        )
        return interceptor, consumer

    async def test_reuses_interceptor_state_via_in_flight(
        self, agent_card_factory, otel_span, patch_emit_events, captured_events,
    ):
        """Consumer should reuse interceptor state and keep correlation ID."""
        interceptor, consumer = self._build_pair(
            patch_emit_events=patch_emit_events,
        )

        remote = agent_card_factory("Brazil Farm")
        ctx = ClientCallContext(state={"tool": "get_farm_yield_inventory"})

        with otel_span(trace_id=0xFEED, span_id=0xBEEF, parent_span_id=0xCAFE):
            await interceptor.intercept(
                "send_message", {}, {}, agent_card=remote, context=ctx,
            )
            await consumer(
                _client_event(_task(metadata={"name": "Brazil Farm"})),
                agent_card=remote,
            )

        assert len(captured_events) == 2
        outbound, inbound = captured_events
        assert (
            outbound.metadata.correlation.id == inbound.metadata.correlation.id
        )

    async def test_drops_event_when_no_state_and_no_default(
        self, agent_card_factory, otel_span, patch_emit_events, captured_events,
    ):
        """Without in-flight state or default workflow, consumer should drop."""
        def no_default_resolver(_tool):
            raise KeyError("no default")

        _interceptor, consumer = self._build_pair(
            patch_emit_events=patch_emit_events,
            resolver=no_default_resolver,
        )

        remote = agent_card_factory("Brazil Farm")
        with otel_span(trace_id=0x999, span_id=0x888):
            await consumer(
                _client_event(_task(metadata={"name": "Brazil Farm"})),
                agent_card=remote,
            )

        assert captured_events == []

    async def test_extracts_remote_agent_id_from_task_metadata(
        self, agent_card_factory, otel_span, patch_emit_events, captured_events,
    ):
        """Consumer should prefer ``Task.metadata['name']`` over card name."""
        interceptor, consumer = self._build_pair(
            patch_emit_events=patch_emit_events,
        )

        card = agent_card_factory("Generic Farm")
        ctx = ClientCallContext(state={"tool": "get_farm_yield_inventory"})

        with otel_span(trace_id=0x11, span_id=0x22, parent_span_id=0x33):
            await interceptor.intercept(
                "send_message", {}, {}, agent_card=card, context=ctx,
            )
            await consumer(
                _client_event(_task(metadata={"name": "Colombia Farm"})),
                agent_card=card,
            )

        inbound = captured_events[1]
        labels = {
            n.label
            for wf in inbound.data.workflows.values()
            for inst in wf.instances.values()
            for n in inst.topology.nodes
        }
        assert "Colombia Farm" in labels
        assert "Generic Farm" not in labels
