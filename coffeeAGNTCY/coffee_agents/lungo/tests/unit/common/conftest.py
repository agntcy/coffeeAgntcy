# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""Shared fixtures for common/* unit tests (workflow registry + A2A event middleware).

Resets module-level state that the middleware keeps between calls:

* ``common.workflow_utils.inflight.in_flight`` - the per-trace interaction state
* ``common.workflow_utils.workflow_catalog._cached_catalog`` - the
  process cache of a successful catalog GET

Provides helpers for constructing minimal ``AgentCard`` stand-ins and a patched
OTel span context without needing a real tracer.
"""

from __future__ import annotations

import contextlib
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterator
from unittest.mock import MagicMock

import pytest

_TEST_CATALOG_PAYLOAD = {
    "Test Workflow Alpha": {
        "name": "Test Workflow Alpha",
        "pattern": "Supervisor",
        "use_case": "Unit Test",
        "scenario": "Alpha Scenario",
    },
    "Test Workflow Beta": {
        "name": "Test Workflow Beta",
        "pattern": "Group-chat",
        "use_case": "Unit Test",
        "scenario": "Beta Scenario",
    },
}

@pytest.fixture(autouse=True)
def _reset_in_flight() -> Iterator[None]:
    """Clear the middleware's per-trace in-flight state around every test."""
    try:
        from common.workflow_utils import inflight as inflight_mod
    except Exception:
        yield
        return
    inflight_mod.in_flight.clear()
    try:
        yield
    finally:
        inflight_mod.in_flight.clear()


@pytest.fixture(autouse=True)
def _reset_workflow_catalog_cache() -> Iterator[None]:
    """Drop the successful-GET catalog cache around every test."""
    try:
        from common.workflow_utils import workflow_catalog as wr
    except Exception:
        yield
        return
    wr._clear_catalog_cache()
    try:
        yield
    finally:
        wr._clear_catalog_cache()


@pytest.fixture(autouse=True)
def _test_workflows_catalog(request, monkeypatch) -> Iterator[None]:
    """Point catalog lookup at a fixed Alpha/Beta GET payload.

    Tests that need a different catalog monkeypatch
    ``_fetch_catalog_payload`` themselves after this fixture.
    """
    if "real_workflow_catalog" in request.fixturenames:
        yield
        return

    def fetch_test_catalog():
        return dict(_TEST_CATALOG_PAYLOAD)

    monkeypatch.setattr(
        "common.workflow_utils.workflow_catalog._fetch_catalog_payload",
        fetch_test_catalog,
    )
    yield


@pytest.fixture
def real_workflow_catalog() -> bool:
    """Opt-out fixture: when requested, the autouse Alpha/Beta test catalog
    is skipped so the production starting_workflows.json is loaded."""
    return True


@pytest.fixture
def no_default_baggage() -> bool:
    """Opt-out fixture: when requested, the autouse default-baggage scope
    becomes a no-op for that test."""
    return True


@pytest.fixture(autouse=True)
def _default_workflow_baggage(request) -> Iterator[None]:
    """Attach baggage workflow_name='Test Workflow Alpha' for every test.

    The middleware now reads workflow identity exclusively from OTel
    context, so every test that drives ``EventEmittingInterceptor.intercept``
    needs baggage set; making it autouse keeps tests focused on what they
    actually assert. Tests that need a different workflow_name attach a
    second scope that wins (last-writer-wins on OTel context). Tests that
    explicitly verify the no-baggage path request the
    ``no_default_baggage`` fixture.
    """
    if "no_default_baggage" in request.fixturenames:
        yield
        return

    from common.workflow_context_prop import (
        attach_workflow_context,
        detach_workflow_context,
    )

    token = attach_workflow_context(
        workflow_instance_id="instance://00000000-0000-4000-8000-000000000001",
        workflow_name="Test Workflow Alpha",
    )
    try:
        yield
    finally:
        detach_workflow_context(token)


# ---------------------------------------------------------------------------
# Config-flag helper
# ---------------------------------------------------------------------------

@pytest.fixture
def patch_emit_events(monkeypatch):
    """Return a setter that toggles ``EMIT_WORKFLOW_EVENTS`` on the middleware
    module. The middleware binds the flag at import-time, so we patch the
    attribute on the module itself rather than re-importing.
    """

    def _set(enabled: bool) -> None:
        from common.a2a_event_middleware import middleware as mw
        monkeypatch.setattr(mw, "EMIT_WORKFLOW_EVENTS", enabled, raising=False)

    return _set


# ---------------------------------------------------------------------------
# AgentCard stand-in
# ---------------------------------------------------------------------------

@dataclass
class _FakeAgentCard:
    """Minimal duck-typed ``AgentCard`` for interceptor/consumer tests.

    Only the attributes read by the middleware are populated.
    """
    name: str
    preferred_transport: str | None = "JSONRPC"


def make_agent_card(
    name: str = "Test Caller Agent",
    preferred_transport: str | None = "JSONRPC",
) -> Any:
    """Build a minimal agent card. Typed as Any so tests can pass it where an
    ``a2a.types.AgentCard`` is expected without pulling the real schema in."""
    return _FakeAgentCard(name=name, preferred_transport=preferred_transport)


@pytest.fixture
def agent_card_factory():
    """Fixture form of ``make_agent_card`` for convenience inside tests."""
    return make_agent_card


# ---------------------------------------------------------------------------
# OTel span-context patching
# ---------------------------------------------------------------------------

@dataclass
class _FakeSpanContext:
    trace_id: int
    span_id: int
    is_valid: bool = True


@dataclass
class _FakeSpan:
    span_context: _FakeSpanContext
    parent: _FakeSpanContext | None = None

    def get_span_context(self) -> _FakeSpanContext:
        return self.span_context


@contextlib.contextmanager
def _patched_current_span(
    monkeypatch,
    *,
    trace_id: int | None,
    span_id: int | None,
    parent_span_id: int | None = None,
):
    """Patch ``inflight_mod._otel_trace.get_current_span`` to return a
    deterministic span. ``trace_id=None`` simulates "no active span" by
    setting ``is_valid=False``.
    """
    from common.workflow_utils import inflight as inflight_mod

    valid = trace_id is not None
    ctx = _FakeSpanContext(
        trace_id=trace_id or 0,
        span_id=span_id or 0,
        is_valid=valid,
    )
    parent_ctx = None
    if parent_span_id is not None:
        parent_ctx = _FakeSpanContext(
            trace_id=trace_id or 0,
            span_id=parent_span_id,
            is_valid=True,
        )
    fake_span = _FakeSpan(span_context=ctx, parent=parent_ctx)

    fake_tracer = MagicMock()
    fake_tracer.get_current_span.return_value = fake_span
    monkeypatch.setattr(inflight_mod, "_otel_trace", fake_tracer, raising=True)
    try:
        yield fake_span
    finally:
        pass  # monkeypatch handles restoration


@pytest.fixture
def otel_span(monkeypatch):
    """Return a context manager factory that patches the active OTel span.

    Usage::

        with otel_span(trace_id=0x1234, span_id=0xAB, parent_span_id=0xCD):
            ...
    """

    def _factory(
        *,
        trace_id: int | None,
        span_id: int | None,
        parent_span_id: int | None = None,
    ):
        return _patched_current_span(
            monkeypatch,
            trace_id=trace_id,
            span_id=span_id,
            parent_span_id=parent_span_id,
        )

    return _factory


# ---------------------------------------------------------------------------
# Module-path helper - keeps ``__init__.py``-less test dirs importable
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session", autouse=True)
def _ensure_lungo_on_path() -> None:
    """Guarantee the lungo package root is importable for ``common.*``."""
    root = Path(__file__).resolve().parents[3]
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
