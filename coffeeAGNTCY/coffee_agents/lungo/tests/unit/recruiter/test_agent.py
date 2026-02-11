# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""Unit tests for agents.supervisors.recruiter.agent (select/deselect/send tools, agent structure)."""

from unittest.mock import MagicMock

import pytest

from agents.supervisors.recruiter.agent import (
    root_agent,
    select_agent,
    deselect_agent,
    send_to_agent,
    dynamic_workflow_agent,
    root_runner,
    APP_NAME,
    _find_agent_by_name_or_cid,
)
from agents.supervisors.recruiter.models import (
    STATE_KEY_RECRUITED_AGENTS,
    STATE_KEY_SELECTED_AGENT,
    STATE_KEY_TASK_MESSAGE,
)


# ---------------------------------------------------------------------------
# Agent structure
# ---------------------------------------------------------------------------


class TestAgentStructure:
    def test_root_agent_name(self):
        assert root_agent.name == "recruiter_supervisor"

    def test_root_agent_has_tools(self):
        tool_names = [t.__name__ for t in root_agent.tools]
        assert "recruit_agents" in tool_names
        assert "select_agent" in tool_names
        assert "deselect_agent" in tool_names
        assert "send_to_agent" in tool_names

    def test_root_agent_has_sub_agents(self):
        sub_names = [a.name for a in root_agent.sub_agents]
        assert "dynamic_workflow" in sub_names

    def test_dynamic_workflow_agent_type(self):
        from agents.supervisors.recruiter.dynamic_workflow_agent import (
            DynamicWorkflowAgent,
        )

        assert isinstance(dynamic_workflow_agent, DynamicWorkflowAgent)

    def test_runner_app_name(self):
        assert APP_NAME == "recruiter_supervisor"

    def test_root_agent_has_instruction(self):
        assert root_agent.instruction is not None
        assert len(root_agent.instruction) > 50


# ---------------------------------------------------------------------------
# _find_agent_by_name_or_cid helper
# ---------------------------------------------------------------------------


class TestFindAgentByNameOrCid:
    def test_exact_cid_match(self):
        recruited = {
            "cid_abc123": {"name": "Agent A", "description": "Test agent"},
        }
        cid, record = _find_agent_by_name_or_cid("cid_abc123", recruited)
        assert cid == "cid_abc123"
        assert record["name"] == "Agent A"

    def test_exact_name_match_case_insensitive(self):
        recruited = {
            "cid_abc123": {"name": "Shipping Agent", "description": "Ships things"},
        }
        cid, record = _find_agent_by_name_or_cid("shipping agent", recruited)
        assert cid == "cid_abc123"
        assert record["name"] == "Shipping Agent"

    def test_partial_name_match(self):
        recruited = {
            "cid_abc123": {"name": "Shipping Agent", "description": "Ships things"},
        }
        cid, record = _find_agent_by_name_or_cid("shipping", recruited)
        assert cid == "cid_abc123"

    def test_no_match_returns_none(self):
        recruited = {
            "cid_abc123": {"name": "Shipping Agent", "description": "Ships things"},
        }
        cid, record = _find_agent_by_name_or_cid("accounting", recruited)
        assert cid is None
        assert record is None

    def test_empty_recruited_returns_none(self):
        cid, record = _find_agent_by_name_or_cid("anything", {})
        assert cid is None
        assert record is None


# ---------------------------------------------------------------------------
# select_agent tool
# ---------------------------------------------------------------------------


class TestSelectAgent:
    @pytest.mark.asyncio
    async def test_select_by_cid(self):
        tool_context = MagicMock()
        tool_context.state = {
            STATE_KEY_RECRUITED_AGENTS: {
                "cid_a": {"name": "Agent A", "description": "Test agent"},
            }
        }

        result = await select_agent(
            agent_identifier="cid_a",
            tool_context=tool_context,
        )

        assert tool_context.state[STATE_KEY_SELECTED_AGENT] == "cid_a"
        assert "Agent A" in result
        assert "✓" in result or "Selected" in result

    @pytest.mark.asyncio
    async def test_select_by_name(self):
        tool_context = MagicMock()
        tool_context.state = {
            STATE_KEY_RECRUITED_AGENTS: {
                "cid_shipping": {"name": "Shipping Agent", "description": "Ships things"},
            }
        }

        result = await select_agent(
            agent_identifier="Shipping Agent",
            tool_context=tool_context,
        )

        assert tool_context.state[STATE_KEY_SELECTED_AGENT] == "cid_shipping"
        assert "Shipping Agent" in result

    @pytest.mark.asyncio
    async def test_select_by_partial_name(self):
        tool_context = MagicMock()
        tool_context.state = {
            STATE_KEY_RECRUITED_AGENTS: {
                "cid_shipping": {"name": "Shipping Agent", "description": "Ships things"},
            }
        }

        result = await select_agent(
            agent_identifier="shipping",
            tool_context=tool_context,
        )

        assert tool_context.state[STATE_KEY_SELECTED_AGENT] == "cid_shipping"

    @pytest.mark.asyncio
    async def test_select_no_match_shows_available(self):
        tool_context = MagicMock()
        tool_context.state = {
            STATE_KEY_RECRUITED_AGENTS: {
                "cid_a": {"name": "Agent A", "description": "Test"},
            }
        }

        result = await select_agent(
            agent_identifier="nonexistent",
            tool_context=tool_context,
        )

        assert "No agent found" in result
        assert "Agent A" in result  # Should show available agents

    @pytest.mark.asyncio
    async def test_select_no_recruited_agents(self):
        tool_context = MagicMock()
        tool_context.state = {}

        result = await select_agent(
            agent_identifier="anything",
            tool_context=tool_context,
        )

        assert "No agents have been recruited" in result


# ---------------------------------------------------------------------------
# deselect_agent tool
# ---------------------------------------------------------------------------


class TestDeselectAgent:
    @pytest.mark.asyncio
    async def test_deselect_when_agent_selected(self):
        tool_context = MagicMock()
        tool_context.state = {
            STATE_KEY_SELECTED_AGENT: "cid_a",
            STATE_KEY_RECRUITED_AGENTS: {
                "cid_a": {"name": "Agent A"},
            },
        }

        result = await deselect_agent(tool_context=tool_context)

        assert tool_context.state[STATE_KEY_SELECTED_AGENT] is None  # Cleared to None
        assert "Deselected" in result
        assert "Agent A" in result

    @pytest.mark.asyncio
    async def test_deselect_when_no_agent_selected(self):
        tool_context = MagicMock()
        tool_context.state = {}

        result = await deselect_agent(tool_context=tool_context)

        assert "No agent was selected" in result


# ---------------------------------------------------------------------------
# send_to_agent tool
# ---------------------------------------------------------------------------


class TestSendToAgent:
    @pytest.mark.asyncio
    async def test_send_when_agent_selected(self):
        tool_context = MagicMock()
        tool_context.state = {
            STATE_KEY_SELECTED_AGENT: "cid_a",
            STATE_KEY_RECRUITED_AGENTS: {
                "cid_a": {"name": "Agent A"},
            },
        }

        result = await send_to_agent(
            message="Hello agent!",
            tool_context=tool_context,
        )

        assert tool_context.state[STATE_KEY_TASK_MESSAGE] == "Hello agent!"
        assert "Agent A" in result
        assert "dynamic_workflow" in result.lower()

    @pytest.mark.asyncio
    async def test_send_when_no_agent_selected(self):
        tool_context = MagicMock()
        tool_context.state = {}

        result = await send_to_agent(
            message="Hello!",
            tool_context=tool_context,
        )

        assert "No agent is currently selected" in result
        assert STATE_KEY_TASK_MESSAGE not in tool_context.state
