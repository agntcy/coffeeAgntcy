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
    STATE_KEY_SELECTED_AGENT_CIDS,
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
    async def test_no_selected_cids_yields_warning(self):
        """When no CIDs are selected, the agent should yield a warning event."""
        agent = DynamicWorkflowAgent(name="dw_test", description="test")
        ctx = _make_ctx(state={})

        events = []
        async for event in agent._run_async_impl(ctx):
            events.append(event)

        assert len(events) == 1
        assert "No agents were selected" in events[0].content.parts[0].text

    @pytest.mark.asyncio
    async def test_selected_cids_not_in_recruited_yields_error(self):
        """When selected CIDs don't match recruited agents."""
        agent = DynamicWorkflowAgent(name="dw_test", description="test")
        ctx = _make_ctx(
            state={
                STATE_KEY_SELECTED_AGENT_CIDS: ["nonexistent_cid"],
                STATE_KEY_RECRUITED_AGENTS: {},
            }
        )

        events = []
        async for event in agent._run_async_impl(ctx):
            events.append(event)

        assert len(events) == 1
        assert "None of the selected" in events[0].content.parts[0].text

    @pytest.mark.asyncio
    async def test_single_agent_creates_remote_a2a(self):
        """With one selected CID, a single RemoteA2aAgent should be created and run."""
        agent = DynamicWorkflowAgent(name="dw_test", description="test")

        state = {
            STATE_KEY_SELECTED_AGENT_CIDS: ["cid1"],
            STATE_KEY_RECRUITED_AGENTS: {
                "cid1": {
                    "name": "Test Agent",
                    "description": "A test agent",
                    "url": "http://localhost:9000",
                }
            },
            STATE_KEY_TASK_MESSAGE: "Do the task",
        }
        ctx = _make_ctx(state=state)

        # Mock RemoteA2aAgent so we don't make real HTTP calls
        mock_event = MagicMock()
        mock_event.author = "test_agent"

        async def fake_run_async(context):
            yield mock_event

        with patch(
            "agents.supervisors.recruiter.dynamic_workflow_agent.RemoteA2aAgent"
        ) as MockRemote:
            mock_instance = MagicMock()
            mock_instance.run_async = fake_run_async
            mock_instance.name = "test_agent_abcd1234"
            mock_instance._client = None
            MockRemote.return_value = mock_instance

            events = []
            async for event in agent._run_async_impl(ctx):
                events.append(event)

        assert len(events) == 1
        assert events[0] == mock_event

        # Verify selection state was cleared
        assert STATE_KEY_SELECTED_AGENT_CIDS not in ctx.session.state
        assert STATE_KEY_TASK_MESSAGE not in ctx.session.state

    @pytest.mark.asyncio
    async def test_multiple_agents_creates_parallel_agent(self):
        """With multiple CIDs, agents should be wrapped in a ParallelAgent."""
        agent = DynamicWorkflowAgent(name="dw_test", description="test")

        state = {
            STATE_KEY_SELECTED_AGENT_CIDS: ["cid1", "cid2"],
            STATE_KEY_RECRUITED_AGENTS: {
                "cid1": {
                    "name": "Agent A",
                    "description": "Agent A desc",
                    "url": "http://localhost:9000",
                },
                "cid2": {
                    "name": "Agent B",
                    "description": "Agent B desc",
                    "url": "http://localhost:9001",
                },
            },
            STATE_KEY_TASK_MESSAGE: "Do both tasks",
        }
        ctx = _make_ctx(state=state)

        mock_event = MagicMock()

        async def fake_run_async(context):
            yield mock_event

        with patch(
            "agents.supervisors.recruiter.dynamic_workflow_agent.RemoteA2aAgent"
        ) as MockRemote, patch(
            "agents.supervisors.recruiter.dynamic_workflow_agent.ParallelAgent"
        ) as MockParallel:
            mock_remote = MagicMock()
            mock_remote._client = None
            MockRemote.return_value = mock_remote

            mock_parallel = MagicMock()
            mock_parallel.run_async = fake_run_async
            MockParallel.return_value = mock_parallel

            events = []
            async for event in agent._run_async_impl(ctx):
                events.append(event)

        # ParallelAgent should have been constructed
        MockParallel.assert_called_once()
        call_kwargs = MockParallel.call_args
        assert len(call_kwargs.kwargs["sub_agents"]) == 2

    @pytest.mark.asyncio
    async def test_invalid_record_skipped(self):
        """Agent records that fail to parse should be skipped gracefully."""
        agent = DynamicWorkflowAgent(name="dw_test", description="test")

        state = {
            STATE_KEY_SELECTED_AGENT_CIDS: ["bad_cid"],
            STATE_KEY_RECRUITED_AGENTS: {
                # Missing required 'url' field
                "bad_cid": {"name": "Bad Agent"},
            },
            STATE_KEY_TASK_MESSAGE: "Try this",
        }
        ctx = _make_ctx(state=state)

        events = []
        async for event in agent._run_async_impl(ctx):
            events.append(event)

        # Should get the "None of the selected" fallback
        assert len(events) == 1
        assert "None of the selected" in events[0].content.parts[0].text

    @pytest.mark.asyncio
    async def test_task_message_injected_into_events(self):
        """The task message should be appended to session events."""
        agent = DynamicWorkflowAgent(name="dw_test", description="test")

        state = {
            STATE_KEY_SELECTED_AGENT_CIDS: ["cid1"],
            STATE_KEY_RECRUITED_AGENTS: {
                "cid1": {
                    "name": "Agent A",
                    "description": "desc",
                    "url": "http://localhost:9000",
                }
            },
            STATE_KEY_TASK_MESSAGE: "Execute the accounting report",
        }
        ctx = _make_ctx(state=state)

        async def fake_run_async(context):
            return
            yield  # make it an async generator

        with patch(
            "agents.supervisors.recruiter.dynamic_workflow_agent.RemoteA2aAgent"
        ) as MockRemote:
            mock_instance = MagicMock()
            mock_instance.run_async = fake_run_async
            mock_instance.name = "agent_a_abcd1234"
            mock_instance._client = None
            MockRemote.return_value = mock_instance

            events = []
            async for event in agent._run_async_impl(ctx):
                events.append(event)

        # The task message should have been injected into ctx.session.events
        injected = [
            e
            for e in ctx.session.events
            if hasattr(e, "content")
            and e.content
            and e.content.parts
            and any(
                hasattr(p, "text") and p.text == "Execute the accounting report"
                for p in e.content.parts
            )
        ]
        assert len(injected) == 1
