# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""Unit tests for ``common.workflow_registry``.

Covers identity key derivation, workflow registration guards, catalog loading,
resolver fallback behavior, and tool-call context construction.
"""

from __future__ import annotations

import json
from types import SimpleNamespace

import pytest


class TestToolIdentityKey:
    @pytest.mark.parametrize(
        "obj,expected",
        [
            (SimpleNamespace(name="from_name", __name__="ignored"), "from_name"),
            (SimpleNamespace(__name__="from_dunder"), "from_dunder"),
            (
                SimpleNamespace(__wrapped__=SimpleNamespace(__name__="from_wrapped")),
                "from_wrapped",
            ),
        ],
        ids=["name_wins", "dunder_fallback", "wrapped_fallback"],
    )
    def test_precedence(self, obj, expected):
        from common.workflow_registry import _tool_identity_key

        assert _tool_identity_key(obj) == expected


class TestRegisterWorkflow:
    def test_rejects_unknown_workflow(self, workflows_json):
        from common.workflow_registry import register_workflow

        with pytest.raises(KeyError):
            @register_workflow("Nonexistent Workflow")
            def my_tool():
                pass

    def test_conflicting_re_registration_raises(self, workflows_json):
        from common.workflow_registry import register_workflow

        @register_workflow("Test Workflow Alpha")
        def my_tool():
            pass

        with pytest.raises(ValueError):
            register_workflow("Test Workflow Beta")(my_tool)


class TestGetWorkflowRegistry:
    def test_loads_valid_catalog(self, workflows_json):
        from common.workflow_registry import get_workflow_registry

        wf = get_workflow_registry().get("Test Workflow Alpha")
        assert wf.workflow_name == "Test Workflow Alpha"
        assert wf.pattern == "Supervisor-worker"
        assert wf.use_case == "Unit Test"

    def test_empty_catalog_raises(self, tmp_path, monkeypatch):
        from common import workflow_registry as wr

        path = tmp_path / "empty.json"
        path.write_text("[]")
        monkeypatch.setenv("LUNGO_WORKFLOWS_JSON", str(path))
        wr.get_workflow_registry.cache_clear()
        with pytest.raises(RuntimeError):
            wr.get_workflow_registry()

    def test_malformed_entries_skipped_not_fatal(self, tmp_path, monkeypatch):
        """Mixed catalogs should load valid entries and skip invalid ones."""
        from common import workflow_registry as wr

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
        wr.get_workflow_registry.cache_clear()
        registry = wr.get_workflow_registry()
        assert registry.get("Good Workflow").pattern == "Supervisor-worker"
        with pytest.raises(KeyError):
            registry.get("missing pattern")


class TestToolWorkflowResolver:
    def _resolver(self, *, default=None, mapping=None):
        from common.workflow_registry import (
            ToolWorkflowResolver,
            WorkflowRegistration,
            get_workflow_registry,
        )

        return ToolWorkflowResolver(
            registry=get_workflow_registry(),
            registration=WorkflowRegistration(
                tool_workflow_map=mapping or {},
                default_workflow_name=default,
            ),
        )

    def test_explicit_tool_mapping(self, workflows_json):
        resolver = self._resolver(mapping={"tool_a": "Test Workflow Alpha"})
        assert resolver.resolve("tool_a").workflow_name == "Test Workflow Alpha"

    def test_default_fallback_when_tool_unmapped(self, workflows_json):
        resolver = self._resolver(
            default="Test Workflow Beta",
            mapping={"tool_a": "Test Workflow Alpha"},
        )
        assert resolver.resolve("tool_unknown").workflow_name == "Test Workflow Beta"

    def test_no_default_and_unknown_raises(self, workflows_json):
        resolver = self._resolver(mapping={"tool_a": "Test Workflow Alpha"})
        with pytest.raises(KeyError):
            resolver.resolve("tool_unknown")


class TestMakeToolCallContext:
    def test_merges_tool_key_with_extras(self):
        from common.workflow_registry import make_tool_call_context

        def my_tool():
            pass

        ctx = make_tool_call_context(
            my_tool,
            correlation_id="correlation://abc",
            broadcast_agent_cards=["card1"],
        )
        assert ctx.state == {
            "tool": "my_tool",
            "correlation_id": "correlation://abc",
            "broadcast_agent_cards": ["card1"],
        }
