# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""Unit tests for ``common.workflow_utils.workflow_catalog``.

Covers JSON catalog loading and the ``lookup_workflow`` lookup.
"""

from __future__ import annotations

import json

import pytest
from common.a2a_event_middleware import event_sink as shim_es
from common.a2a_event_middleware import inflight as shim_if
from common.a2a_event_middleware import workflow_catalog as shim_wc
from common.workflow_utils import event_sink as es
from common.workflow_utils import inflight as inflight
from common.workflow_utils import workflow_catalog as wc


class TestLookupWorkflow:
    """The autouse ``_test_workflows_catalog`` fixture in conftest already
    points ``LUNGO_WORKFLOWS_JSON`` at an Alpha/Beta catalog, so happy-path
    tests don't need extra setup. Tests that exercise loader edge cases
    write their own catalog and clear the lru_cache.
    """

    def test_returns_metadata_for_known_name(self):
        wf = wc.lookup_workflow("Test Workflow Alpha")
        assert wf is not None
        assert wf.workflow_name == "Test Workflow Alpha"
        assert wf.pattern == "Supervisor"
        assert wf.use_case == "Unit Test"
        assert wf.scenario == "Alpha Scenario"

    def test_returns_none_for_unknown_name(self):
        assert wc.lookup_workflow("Nonexistent") is None

    def test_returns_none_for_empty_name(self):
        assert wc.lookup_workflow(None) is None
        assert wc.lookup_workflow("") is None

    def test_empty_catalog_raises(self, tmp_path, monkeypatch):
        path = tmp_path / "empty.json"
        path.write_text("[]")
        monkeypatch.setenv("LUNGO_WORKFLOWS_JSON", str(path))
        wc._load_catalog.cache_clear()
        with pytest.raises(RuntimeError):
            wc.lookup_workflow("anything")

    def test_malformed_entries_skipped_not_fatal(self, tmp_path, monkeypatch):
        """Mixed catalogs should load valid entries and skip invalid ones."""
        path = tmp_path / "partial.json"
        path.write_text(
            json.dumps(
                [
                    "not an object",
                    {"name": "missing pattern"},
                    {
                        "name": "Good Workflow",
                        "pattern": "Supervisor",
                        "use_case": "Unit Test",
                        "scenario": "Good Scenario",
                    },
                ]
            )
        )
        monkeypatch.setenv("LUNGO_WORKFLOWS_JSON", str(path))
        wc._load_catalog.cache_clear()
        good = wc.lookup_workflow("Good Workflow")
        assert good is not None
        assert good.pattern == "Supervisor"
        assert good.use_case == "Unit Test"
        assert good.scenario == "Good Scenario"
        assert wc.lookup_workflow("missing pattern") is None


class TestWorkflowCatalogShim:
    """Shim modules must reference the same callables and cache as canonical."""

    def test_lookup_workflow_is_shim_alias(self):
        assert shim_wc.lookup_workflow is wc.lookup_workflow

    def test_load_catalog_is_shim_alias(self):
        assert shim_wc._load_catalog is wc._load_catalog


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
