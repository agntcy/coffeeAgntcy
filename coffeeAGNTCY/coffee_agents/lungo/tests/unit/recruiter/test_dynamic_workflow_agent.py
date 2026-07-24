# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""Unit tests for agents.supervisors.recruiter.dynamic_workflow_agent."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from agents.supervisors.recruiter import dynamic_workflow_agent as dwa
from agents.supervisors.recruiter.dynamic_workflow_agent import (
    DynamicWorkflowAgent,
    _reachable_url,
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


class TestReachableUrl:
    @pytest.mark.parametrize(
        "case, url, host, expected",
        [
            (
                "rewrites 0.0.0.0 keeping port",
                "http://0.0.0.0:9999",
                "host.docker.internal",
                "http://host.docker.internal:9999",
            ),
            (
                "rewrites 0.0.0.0 to localhost for host run",
                "http://0.0.0.0:9998",
                "localhost",
                "http://localhost:9998",
            ),
            (
                "rewrites 127.0.0.1",
                "http://127.0.0.1:9997/a2a",
                "host.docker.internal",
                "http://host.docker.internal:9997/a2a",
            ),
            (
                "rewrites localhost",
                "http://localhost:9999",
                "host.docker.internal",
                "http://host.docker.internal:9999",
            ),
            (
                "leaves routable host untouched",
                "http://brazil-farm-server:9999",
                "host.docker.internal",
                "http://brazil-farm-server:9999",
            ),
            (
                "leaves non-http transport untouched",
                "slim://0.0.0.0:46357",
                "host.docker.internal",
                "slim://0.0.0.0:46357",
            ),
            (
                "handles missing port",
                "http://0.0.0.0",
                "host.docker.internal",
                "http://host.docker.internal",
            ),
            (
                "returns empty unchanged",
                "",
                "host.docker.internal",
                "",
            ),
        ],
    )
    def test_reachable_url(self, case, url, host, expected):
        with patch.object(dwa, "DISCOVERED_AGENT_HOST", host):
            assert _reachable_url(url) == expected, case


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

    @pytest.mark.asyncio
    async def test_delegation_transport_error_yields_error(self):
        """Transport/client setup failures should yield a delegation error event."""
        agent = DynamicWorkflowAgent(name="dw_test", description="test")
        record = {
            "name": "Farm Agent",
            "url": "http://farm:9999",
            "preferredTransport": "jsonrpc",
            "description": "desc",
            "version": "1.0.0",
            "capabilities": {"streaming": False},
            "defaultInputModes": ["text"],
            "defaultOutputModes": ["text"],
            "skills": [],
        }
        state = {
            STATE_KEY_SELECTED_AGENT: "farm_cid",
            STATE_KEY_RECRUITED_AGENTS: {"farm_cid": record},
            STATE_KEY_TASK_MESSAGE: "Try this",
        }
        ctx = _make_ctx(state=state)

        mock_factory = MagicMock()
        mock_factory.create = AsyncMock(
            side_effect=ValueError("no compatible transports found.")
        )

        events = []
        with patch.object(dwa, "a2a_client_factory", mock_factory):
            async for event in agent._run_async_impl(ctx):
                events.append(event)

        assert len(events) == 1
        assert "Failed to delegate" in events[0].content.parts[0].text
        assert "no compatible transports found" in events[0].content.parts[0].text
