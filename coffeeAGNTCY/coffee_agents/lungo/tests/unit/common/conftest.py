# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""Shared fixtures for common/* unit tests (workflow registry + A2A event middleware).

Resets module-level state that the middleware keeps between calls:

* ``common.a2a_event_middleware._in_flight`` — the per-trace interaction state
* ``common.workflow_registry._TOOL_WORKFLOW_MAP`` — the decorator-populated map
* ``common.workflow_registry.get_workflow_registry`` — the ``lru_cache`` around
  the JSON catalog loader

Provides helpers for constructing minimal ``AgentCard`` stand-ins and a patched
OTel span context without needing a real tracer.
"""

from __future__ import annotations

import contextlib
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterator
from unittest.mock import MagicMock

import pytest


# ---------------------------------------------------------------------------
# State-reset fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def _reset_in_flight() -> Iterator[None]:
    """Clear the middleware's per-trace in-flight state around every test."""
    try:
        from common import a2a_event_middleware as mw
    except Exception:
        yield
        return
    mw._in_flight.clear()
    try:
        yield
    finally:
        mw._in_flight.clear()


@pytest.fixture(autouse=True)
def _reset_tool_workflow_map() -> Iterator[None]:
    """Clear the decorator-populated tool->workflow map around every test."""
    try:
        from common import workflow_registry as wr
    except Exception:
        yield
        return
    saved = dict(wr._TOOL_WORKFLOW_MAP)
    wr._TOOL_WORKFLOW_MAP.clear()
    try:
        yield
    finally:
        wr._TOOL_WORKFLOW_MAP.clear()
        wr._TOOL_WORKFLOW_MAP.update(saved)


@pytest.fixture(autouse=True)
def _reset_workflow_registry_cache() -> Iterator[None]:
    """Invalidate the ``lru_cache`` wrapping ``get_workflow_registry``."""
    try:
        from common import workflow_registry as wr
    except Exception:
        yield
        return
    wr.get_workflow_registry.cache_clear()
    try:
        yield
    finally:
        wr.get_workflow_registry.cache_clear()


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
        from common import a2a_event_middleware as mw
        monkeypatch.setattr(mw, "EMIT_WORKFLOW_EVENTS", enabled, raising=False)

    return _set


# ---------------------------------------------------------------------------
# Workflow catalog helper
# ---------------------------------------------------------------------------

@pytest.fixture
def workflows_json(tmp_path: Path, monkeypatch) -> Path:
    """Write a minimal workflow catalog to disk and point
    ``LUNGO_WORKFLOWS_JSON`` at it. Returns the path so tests can rewrite it.
    """
    path = tmp_path / "starting_workflows.json"
    path.write_text(json.dumps([
        {
            "name": "Test Workflow Alpha",
            "pattern": "Supervisor-worker",
            "use_case": "Unit Test",
        },
        {
            "name": "Test Workflow Beta",
            "pattern": "Group-chat",
            "use_case": "Unit Test",
        },
    ]))
    monkeypatch.setenv("LUNGO_WORKFLOWS_JSON", str(path))
    return path


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
    """Patch ``common.a2a_event_middleware._otel_trace.get_current_span`` to
    return a deterministic span. ``trace_id=None`` simulates "no active span"
    by setting ``is_valid=False``.
    """
    from common import a2a_event_middleware as mw

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
    monkeypatch.setattr(mw, "_otel_trace", fake_tracer, raising=True)
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
# Module-path helper — keeps ``__init__.py``-less test dirs importable
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session", autouse=True)
def _ensure_lungo_on_path() -> None:
    """Guarantee the lungo package root is importable for ``common.*``."""
    root = Path(__file__).resolve().parents[3]
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
