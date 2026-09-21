# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""Unit tests for ``common.workflow_utils.workflow_catalog``.

Covers HTTP catalog loading and the ``lookup_workflow`` lookup.
"""

from __future__ import annotations

from typing import Any

import pytest
from common.a2a_event_middleware import event_sink as shim_es
from common.a2a_event_middleware import inflight as shim_if
from common.a2a_event_middleware import workflow_catalog as shim_wc
from common.workflow_utils import event_sink as es
from common.workflow_utils import inflight as inflight
from common.workflow_utils import workflow_catalog as wc


def _payload_from_entries(entries: list[dict[str, Any]]) -> dict[str, Any]:
    return {entry["name"]: entry for entry in entries}


class TestLookupWorkflow:
    def test_returns_metadata_for_known_name(self):
        wf = wc.lookup_workflow("Test Workflow Alpha")
        assert wf is not None
        assert wf.name == "Test Workflow Alpha"
        assert wf.pattern == "Supervisor"
        assert wf.use_case == "Unit Test"
        assert wf.scenario == "Alpha Scenario"

    def test_returns_none_for_unknown_name(self):
        assert wc.lookup_workflow("Nonexistent") is None

    def test_returns_none_for_empty_name(self):
        assert wc.lookup_workflow(None) is None
        assert wc.lookup_workflow("") is None

    def test_get_failure_returns_none(self, monkeypatch):
        def fetch_none():
            return None

        monkeypatch.setattr(wc, "_fetch_catalog_payload", fetch_none)
        wc._clear_catalog_cache()
        assert wc.lookup_workflow("Test Workflow Alpha") is None

    def test_empty_catalog_returns_none(self, monkeypatch):
        def fetch_empty():
            return {}

        monkeypatch.setattr(wc, "_fetch_catalog_payload", fetch_empty)
        wc._clear_catalog_cache()
        assert wc.lookup_workflow("anything") is None

    def test_malformed_entries_skipped_not_fatal(self, monkeypatch):
        def fetch_partial():
            return {
                "bad": "not an object",
                "missing pattern": {"name": "missing pattern"},
                "Good Workflow": {
                    "name": "Good Workflow",
                    "pattern": "Supervisor",
                    "use_case": "Unit Test",
                    "scenario": "Good Scenario",
                },
            }

        monkeypatch.setattr(wc, "_fetch_catalog_payload", fetch_partial)
        wc._clear_catalog_cache()
        good = wc.lookup_workflow("Good Workflow")
        assert good is not None
        assert good.pattern == "Supervisor"
        assert good.use_case == "Unit Test"
        assert good.scenario == "Good Scenario"
        assert wc.lookup_workflow("missing pattern") is None

    def test_catalog_fetched_once_for_many_lookups(self, monkeypatch):
        calls = {"count": 0}

        def fetch_once():
            calls["count"] += 1
            return _payload_from_entries(
                [
                    {
                        "name": "Test Workflow Alpha",
                        "pattern": "Supervisor",
                        "use_case": "Unit Test",
                        "scenario": "Alpha Scenario",
                    }
                ]
            )

        monkeypatch.setattr(wc, "_fetch_catalog_payload", fetch_once)
        wc._clear_catalog_cache()
        wc.lookup_workflow("Test Workflow Alpha")
        wc.lookup_workflow("Test Workflow Alpha")
        wc.lookup_workflow("missing")
        assert calls["count"] == 1

    def test_failed_get_is_retried_on_next_lookup(self, monkeypatch):
        calls = {"count": 0}

        def fetch_fail_then_ok():
            calls["count"] += 1
            if calls["count"] == 1:
                return None
            return _payload_from_entries(
                [
                    {
                        "name": "Test Workflow Alpha",
                        "pattern": "Supervisor",
                        "use_case": "Unit Test",
                        "scenario": "Alpha Scenario",
                    }
                ]
            )

        monkeypatch.setattr(wc, "_fetch_catalog_payload", fetch_fail_then_ok)
        wc._clear_catalog_cache()
        assert wc.lookup_workflow("Test Workflow Alpha") is None
        recovered = wc.lookup_workflow("Test Workflow Alpha")
        assert recovered is not None
        assert recovered.name == "Test Workflow Alpha"
        wc.lookup_workflow("Test Workflow Alpha")
        assert calls["count"] == 2

    def test_empty_parsed_catalog_is_retried(self, monkeypatch):
        calls = {"count": 0}

        def fetch_empty_then_ok():
            calls["count"] += 1
            if calls["count"] == 1:
                return {}
            return _payload_from_entries(
                [
                    {
                        "name": "Test Workflow Alpha",
                        "pattern": "Supervisor",
                        "use_case": "Unit Test",
                        "scenario": "Alpha Scenario",
                    }
                ]
            )

        monkeypatch.setattr(wc, "_fetch_catalog_payload", fetch_empty_then_ok)
        wc._clear_catalog_cache()
        assert wc.lookup_workflow("Test Workflow Alpha") is None
        recovered = wc.lookup_workflow("Test Workflow Alpha")
        assert recovered is not None
        assert calls["count"] == 2


class TestWorkflowCatalogShim:
    """Shim modules must reference the same callables and cache as canonical."""

    def test_lookup_workflow_is_shim_alias(self):
        assert shim_wc.lookup_workflow is wc.lookup_workflow

    def test_load_catalog_is_shim_alias(self):
        assert shim_wc._load_catalog is wc._load_catalog

    def test_clear_catalog_cache_is_shim_alias(self):
        assert shim_wc._clear_catalog_cache is wc._clear_catalog_cache
        assert shim_wc._load_catalog.cache_clear is wc._clear_catalog_cache


class TestInflightShim:
    """Shim must share module-level in-flight state with canonical inflight."""

    def test_in_flight_is_shim_alias(self):
        assert shim_if.in_flight is inflight.in_flight

    def test_in_flight_lock_is_shim_alias(self):
        assert shim_if.in_flight_lock is inflight.in_flight_lock

    def test_register_cleanup_is_shim_alias(self):
        assert shim_if.register_cleanup_span_processor is (
            inflight.register_cleanup_span_processor
        )


class TestEventSinkShim:
    """Shim must reference the same sink types as canonical event_sink."""

    def test_workflow_api_event_sink_is_shim_alias(self):
        assert shim_es.WorkflowAPIEventSink is es.WorkflowAPIEventSink

    def test_event_sink_is_shim_alias(self):
        assert shim_es.EventSink is es.EventSink
