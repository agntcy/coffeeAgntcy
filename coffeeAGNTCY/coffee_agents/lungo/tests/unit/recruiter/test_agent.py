# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""Unit tests for agents.supervisors.recruiter.agent (select/deselect/send tools, agent structure)."""

from unittest.mock import MagicMock

import pytest
from agents.supervisors.recruiter.models import (
    STATE_KEY_RECRUITED_AGENTS,
    STATE_KEY_SELECTED_AGENT,
    STATE_KEY_TASK_MESSAGE,
)

# ---------------------------------------------------------------------------
# Agent structure
# ---------------------------------------------------------------------------


class TestAgentStructure:
    def test_root_agent_name(self, recruiter_agent):
        assert recruiter_agent.root_agent.name == "recruiter_supervisor"

    def test_root_agent_has_tools(self, recruiter_agent):
        tool_names = [t.__name__ for t in recruiter_agent.root_agent.tools]
        assert "recruit_agents" in tool_names
        assert "select_agent" in tool_names
        assert "deselect_agent" in tool_names
        assert "send_to_agent" in tool_names

    def test_root_agent_has_sub_agents(self, recruiter_agent):
        sub_names = [a.name for a in recruiter_agent.root_agent.sub_agents]
        assert "dynamic_workflow" in sub_names

    def test_dynamic_workflow_agent_type(self, recruiter_agent):
        from agents.supervisors.recruiter.dynamic_workflow_agent import (
            DynamicWorkflowAgent,
        )

        assert isinstance(recruiter_agent.dynamic_workflow_agent, DynamicWorkflowAgent)

    def test_runner_app_name(self, recruiter_agent):
        assert recruiter_agent.APP_NAME == "recruiter_supervisor"

    def test_root_agent_has_instruction(self, recruiter_agent):
        assert recruiter_agent.root_agent.instruction is not None
        assert len(recruiter_agent.root_agent.instruction) > 50


# ---------------------------------------------------------------------------
# _find_agent_by_name_or_cid helper
# ---------------------------------------------------------------------------


class TestFindAgentByNameOrCid:
    def test_exact_cid_match(self, recruiter_agent):
        recruited = {
            "cid_abc123": {"name": "Agent A", "description": "Test agent"},
        }
        cid, record = recruiter_agent._find_agent_by_name_or_cid(
            "cid_abc123", recruited
        )
        assert cid == "cid_abc123"
        assert record["name"] == "Agent A"

    def test_exact_name_match_case_insensitive(self, recruiter_agent):
        recruited = {
            "cid_abc123": {"name": "Shipping Agent", "description": "Ships things"},
        }
        cid, record = recruiter_agent._find_agent_by_name_or_cid(
            "shipping agent", recruited
        )
        assert cid == "cid_abc123"
        assert record["name"] == "Shipping Agent"

    def test_partial_name_match(self, recruiter_agent):
        recruited = {
            "cid_abc123": {"name": "Shipping Agent", "description": "Ships things"},
        }
        cid, record = recruiter_agent._find_agent_by_name_or_cid("shipping", recruited)
        assert cid == "cid_abc123"

    def test_no_match_returns_none(self, recruiter_agent):
        recruited = {
            "cid_abc123": {"name": "Shipping Agent", "description": "Ships things"},
        }
        cid, record = recruiter_agent._find_agent_by_name_or_cid(
            "accounting", recruited
        )
        assert cid is None
        assert record is None

    def test_empty_recruited_returns_none(self, recruiter_agent):
        cid, record = recruiter_agent._find_agent_by_name_or_cid("anything", {})
        assert cid is None
        assert record is None


# ---------------------------------------------------------------------------
# select_agent tool
# ---------------------------------------------------------------------------


class TestSelectAgent:
    @pytest.mark.asyncio
    async def test_select_by_cid(self, recruiter_agent):
        tool_context = MagicMock()
        tool_context.state = {
            STATE_KEY_RECRUITED_AGENTS: {
                "cid_a": {"name": "Agent A", "description": "Test agent"},
            }
        }

        result = await recruiter_agent.select_agent(
            agent_identifier="cid_a",
            tool_context=tool_context,
        )

        assert tool_context.state[STATE_KEY_SELECTED_AGENT] == "cid_a"
        assert "Agent A" in result
        assert "✓" in result or "Selected" in result

    @pytest.mark.asyncio
    async def test_select_by_name(self, recruiter_agent):
        tool_context = MagicMock()
        tool_context.state = {
            STATE_KEY_RECRUITED_AGENTS: {
                "cid_shipping": {
                    "name": "Shipping Agent",
                    "description": "Ships things",
                },
            }
        }

        result = await recruiter_agent.select_agent(
            agent_identifier="Shipping Agent",
            tool_context=tool_context,
        )

        assert tool_context.state[STATE_KEY_SELECTED_AGENT] == "cid_shipping"
        assert "Shipping Agent" in result

    @pytest.mark.asyncio
    async def test_select_by_partial_name(self, recruiter_agent):
        tool_context = MagicMock()
        tool_context.state = {
            STATE_KEY_RECRUITED_AGENTS: {
                "cid_shipping": {
                    "name": "Shipping Agent",
                    "description": "Ships things",
                },
            }
        }

        result = await recruiter_agent.select_agent(
            agent_identifier="shipping",
            tool_context=tool_context,
        )

        assert tool_context.state[STATE_KEY_SELECTED_AGENT] == "cid_shipping"

    @pytest.mark.asyncio
    async def test_select_no_match_shows_available(self, recruiter_agent):
        tool_context = MagicMock()
        tool_context.state = {
            STATE_KEY_RECRUITED_AGENTS: {
                "cid_a": {"name": "Agent A", "description": "Test"},
            }
        }

        result = await recruiter_agent.select_agent(
            agent_identifier="nonexistent",
            tool_context=tool_context,
        )

        assert "No agent found" in result
        assert "Agent A" in result  # Should show available agents

    @pytest.mark.asyncio
    async def test_select_no_recruited_agents(self, recruiter_agent):
        tool_context = MagicMock()
        tool_context.state = {}

        result = await recruiter_agent.select_agent(
            agent_identifier="anything",
            tool_context=tool_context,
        )

        assert "No agents have been recruited" in result


# ---------------------------------------------------------------------------
# deselect_agent tool
# ---------------------------------------------------------------------------


class TestDeselectAgent:
    @pytest.mark.asyncio
    async def test_deselect_when_agent_selected(self, recruiter_agent):
        tool_context = MagicMock()
        tool_context.state = {
            STATE_KEY_SELECTED_AGENT: "cid_a",
            STATE_KEY_RECRUITED_AGENTS: {
                "cid_a": {"name": "Agent A"},
            },
        }

        result = await recruiter_agent.deselect_agent(tool_context=tool_context)

        assert tool_context.state[STATE_KEY_SELECTED_AGENT] is None  # Cleared to None
        assert "Deselected" in result
        assert "Agent A" in result

    @pytest.mark.asyncio
    async def test_deselect_when_no_agent_selected(self, recruiter_agent):
        tool_context = MagicMock()
        tool_context.state = {}

        result = await recruiter_agent.deselect_agent(tool_context=tool_context)

        assert "No agent was selected" in result


# ---------------------------------------------------------------------------
# send_to_agent tool
# ---------------------------------------------------------------------------


class TestSendToAgent:
    @pytest.mark.asyncio
    async def test_send_when_agent_selected(self, recruiter_agent):
        tool_context = MagicMock()
        tool_context.state = {
            STATE_KEY_SELECTED_AGENT: "cid_a",
            STATE_KEY_RECRUITED_AGENTS: {
                "cid_a": {"name": "Agent A"},
            },
        }

        result = await recruiter_agent.send_to_agent(
            message="Hello agent!",
            tool_context=tool_context,
        )

        assert tool_context.state[STATE_KEY_TASK_MESSAGE] == "Hello agent!"
        assert "Agent A" in result
        assert "dynamic_workflow" in result.lower()

    @pytest.mark.asyncio
    async def test_send_when_no_agent_selected(self, recruiter_agent):
        tool_context = MagicMock()
        tool_context.state = {}

        result = await recruiter_agent.send_to_agent(
            message="Hello!",
            tool_context=tool_context,
        )

        assert "No agent is currently selected" in result
        assert STATE_KEY_TASK_MESSAGE not in tool_context.state
