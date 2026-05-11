# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""Unit tests for ``common.a2a_event_middleware.workflow_catalog``.

Covers JSON catalog loading and the ``lookup_workflow`` lookup.
"""

from __future__ import annotations

import json

import pytest

from common.a2a_event_middleware import workflow_catalog as wc


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
        assert wf.pattern == "Supervisor-worker"
        assert wf.use_case == "Unit Test"
        assert wf.scenario == "Unit Test"

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
        path.write_text(json.dumps([
            "not an object",
            {"name": "missing pattern"},
            {
                "name": "Good Workflow",
                "pattern": "Supervisor-worker",
                "use_case": "Unit Test",
            },
        ]))
        monkeypatch.setenv("LUNGO_WORKFLOWS_JSON", str(path))
        wc._load_catalog.cache_clear()
        good = wc.lookup_workflow("Good Workflow")
        assert good is not None
        assert good.pattern == "Supervisor-worker"
        assert good.scenario == "Unit Test"
        assert wc.lookup_workflow("missing pattern") is None
