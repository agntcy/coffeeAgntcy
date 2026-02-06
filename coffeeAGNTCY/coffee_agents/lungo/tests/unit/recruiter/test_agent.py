# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""Unit tests for agents.supervisors.recruiter.agent (select_and_delegate tool, agent structure)."""

from unittest.mock import MagicMock

import pytest

from agents.supervisors.recruiter.agent import (
    root_agent,
    select_and_delegate,
    dynamic_workflow_agent,
    root_runner,
    session_service,
    APP_NAME,
)
from agents.supervisors.recruiter.models import (
    STATE_KEY_RECRUITED_AGENTS,
    STATE_KEY_SELECTED_AGENT_CIDS,
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
        assert "select_and_delegate" in tool_names

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
# select_and_delegate tool
# ---------------------------------------------------------------------------


class TestSelectAndDelegate:
    @pytest.mark.asyncio
    async def test_valid_cids(self):
        tool_context = MagicMock()
        tool_context.state = {
            STATE_KEY_RECRUITED_AGENTS: {
                "cid_a": {"name": "Agent A"},
                "cid_b": {"name": "Agent B"},
            }
        }

        result = await select_and_delegate(
            agent_cids=["cid_a"],
            task_message="Do accounting",
            tool_context=tool_context,
        )

        assert tool_context.state[STATE_KEY_SELECTED_AGENT_CIDS] == ["cid_a"]
        assert tool_context.state[STATE_KEY_TASK_MESSAGE] == "Do accounting"
        assert "Agent A" in result
        assert "1 agent(s)" in result

    @pytest.mark.asyncio
    async def test_multiple_valid_cids(self):
        tool_context = MagicMock()
        tool_context.state = {
            STATE_KEY_RECRUITED_AGENTS: {
                "cid_a": {"name": "Agent A"},
                "cid_b": {"name": "Agent B"},
            }
        }

        result = await select_and_delegate(
            agent_cids=["cid_a", "cid_b"],
            task_message="Do both tasks",
            tool_context=tool_context,
        )

        assert len(tool_context.state[STATE_KEY_SELECTED_AGENT_CIDS]) == 2
        assert "2 agent(s)" in result

    @pytest.mark.asyncio
    async def test_invalid_cids_rejected(self):
        tool_context = MagicMock()
        tool_context.state = {STATE_KEY_RECRUITED_AGENTS: {}}

        result = await select_and_delegate(
            agent_cids=["nonexistent"],
            task_message="Do something",
            tool_context=tool_context,
        )

        assert "None of the provided CIDs" in result
        assert STATE_KEY_SELECTED_AGENT_CIDS not in tool_context.state

    @pytest.mark.asyncio
    async def test_mixed_valid_and_invalid_cids(self):
        tool_context = MagicMock()
        tool_context.state = {
            STATE_KEY_RECRUITED_AGENTS: {
                "cid_good": {"name": "Good Agent"},
            }
        }

        result = await select_and_delegate(
            agent_cids=["cid_good", "cid_bad"],
            task_message="Do task",
            tool_context=tool_context,
        )

        # Valid CID should still be selected
        assert tool_context.state[STATE_KEY_SELECTED_AGENT_CIDS] == ["cid_good"]
        assert "1 agent(s)" in result

    @pytest.mark.asyncio
    async def test_no_recruited_agents_in_state(self):
        tool_context = MagicMock()
        tool_context.state = {}

        result = await select_and_delegate(
            agent_cids=["cid_a"],
            task_message="Do task",
            tool_context=tool_context,
        )

        assert "None of the provided CIDs" in result

    @pytest.mark.asyncio
    async def test_returns_transfer_instruction(self):
        tool_context = MagicMock()
        tool_context.state = {
            STATE_KEY_RECRUITED_AGENTS: {
                "cid_a": {"name": "Agent A"},
            }
        }

        result = await select_and_delegate(
            agent_cids=["cid_a"],
            task_message="Execute",
            tool_context=tool_context,
        )

        assert "dynamic_workflow" in result.lower()
