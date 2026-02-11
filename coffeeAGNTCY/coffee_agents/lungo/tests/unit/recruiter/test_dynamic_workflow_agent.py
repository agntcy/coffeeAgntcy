# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""Unit tests for agents.supervisors.recruiter.dynamic_workflow_agent."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from agents.supervisors.recruiter.dynamic_workflow_agent import (
    DynamicWorkflowAgent,
)
from agents.supervisors.recruiter.models import (
    STATE_KEY_RECRUITED_AGENTS,
    STATE_KEY_SELECTED_AGENT,
    STATE_KEY_TASK_MESSAGE,
)


def _make_ctx(state: dict | None = None):
    """Build a minimal mock InvocationContext."""
    ctx = MagicMock()
    ctx.session.state = state or {}
    ctx.invocation_id = "abcd1234-5678"
    ctx.session.events = []
    return ctx


class TestDynamicWorkflowAgentConstruction:
    def test_can_instantiate(self):
        agent = DynamicWorkflowAgent(
            name="test_dynamic",
            description="test",
        )
        assert agent.name == "test_dynamic"

    def test_result_state_prefix_is_class_var(self):
        assert hasattr(DynamicWorkflowAgent, "RESULT_STATE_PREFIX")
        assert isinstance(DynamicWorkflowAgent.RESULT_STATE_PREFIX, str)


class TestDynamicWorkflowAgentRun:
    @pytest.mark.asyncio
    async def test_no_selected_agent_yields_warning(self):
        """When no agent is selected, the agent should yield a warning event."""
        agent = DynamicWorkflowAgent(name="dw_test", description="test")
        ctx = _make_ctx(state={})

        events = []
        async for event in agent._run_async_impl(ctx):
            events.append(event)

        assert len(events) == 1
        assert "No agents were selected" in events[0].content.parts[0].text

    @pytest.mark.asyncio
    async def test_selected_agent_not_in_recruited_yields_error(self):
        """When selected agent doesn't match recruited agents."""
        agent = DynamicWorkflowAgent(name="dw_test", description="test")
        ctx = _make_ctx(
            state={
                STATE_KEY_SELECTED_AGENT: "nonexistent_cid",
                STATE_KEY_RECRUITED_AGENTS: {},
            }
        )

        events = []
        async for event in agent._run_async_impl(ctx):
            events.append(event)

        assert len(events) == 1
        assert "not found" in events[0].content.parts[0].text

    @pytest.mark.asyncio
    async def test_invalid_record_yields_error(self):
        """Agent records that fail to parse should yield an error event."""
        agent = DynamicWorkflowAgent(name="dw_test", description="test")

        state = {
            STATE_KEY_SELECTED_AGENT: "bad_cid",
            STATE_KEY_RECRUITED_AGENTS: {
                # Missing required 'name' field - this will fail pydantic validation
                "bad_cid": {"description": "No name field"},
            },
            STATE_KEY_TASK_MESSAGE: "Try this",
        }
        ctx = _make_ctx(state=state)

        events = []
        async for event in agent._run_async_impl(ctx):
            events.append(event)

        # Should get an error about failing to parse
        assert len(events) == 1
        assert "Failed to parse" in events[0].content.parts[0].text
