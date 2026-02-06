# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""Unit tests for agents.supervisors.recruiter.recruiter_client."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from a2a.types import (
    DataPart,
    Message,
    Part,
    Role,
    Task,
    TaskState,
    TaskStatus,
    TextPart,
)

from agents.supervisors.recruiter.models import (
    STATE_KEY_EVALUATION_RESULTS,
    STATE_KEY_RECRUITED_AGENTS,
    RecruitmentResponse,
)
from agents.supervisors.recruiter.recruiter_client import (
    _extract_parts,
    recruit_agents,
)


# ---------------------------------------------------------------------------
# _extract_parts
# ---------------------------------------------------------------------------


class TestExtractParts:
    def test_text_only(self):
        parts = [Part(root=TextPart(text="Hello world"))]
        result = _extract_parts(parts)
        assert result.text == "Hello world"
        assert result.agent_records == {}
        assert result.evaluation_results == {}

    def test_agent_records(self):
        parts = [
            Part(
                root=DataPart(
                    data={"cid1": {"name": "Agent A"}},
                    metadata={"type": "found_agent_records"},
                )
            ),
        ]
        result = _extract_parts(parts)
        assert result.text is None
        assert "cid1" in result.agent_records

    def test_evaluation_results(self):
        parts = [
            Part(
                root=DataPart(
                    data={"cid1": {"score": 0.95}},
                    metadata={"type": "evaluation_results"},
                )
            ),
        ]
        result = _extract_parts(parts)
        assert "cid1" in result.evaluation_results

    def test_all_parts_combined(self):
        parts = [
            Part(root=TextPart(text="Found 1 agent")),
            Part(
                root=DataPart(
                    data={"cid1": {"name": "Agent A"}},
                    metadata={"type": "found_agent_records"},
                )
            ),
            Part(
                root=DataPart(
                    data={"cid1": {"score": 0.9}},
                    metadata={"type": "evaluation_results"},
                )
            ),
        ]
        result = _extract_parts(parts)
        assert result.text == "Found 1 agent"
        assert "cid1" in result.agent_records
        assert "cid1" in result.evaluation_results

    def test_data_part_without_metadata(self):
        parts = [Part(root=DataPart(data={"key": "val"}, metadata=None))]
        result = _extract_parts(parts)
        assert result.text is None
        assert result.agent_records == {}
        assert result.evaluation_results == {}

    def test_empty_parts(self):
        result = _extract_parts([])
        assert result.text is None
        assert result.agent_records == {}


# ---------------------------------------------------------------------------
# recruit_agents tool
# ---------------------------------------------------------------------------


class TestRecruitAgents:
    @pytest.mark.asyncio
    async def test_recruit_agents_stores_in_state(self):
        """recruit_agents should merge results into tool_context.state."""
        agent_records = {"cid_abc": {"name": "Agent A", "url": "http://a:9000"}}

        # Build a fake A2A response (Message with text + data parts)
        response_message = Message(
            role=Role.agent,
            message_id="msg-1",
            parts=[
                Part(root=TextPart(text="Found 1 agent")),
                Part(
                    root=DataPart(
                        data=agent_records,
                        metadata={"type": "found_agent_records"},
                    )
                ),
            ],
        )

        # Mock the A2A client to yield our fake message
        mock_client = AsyncMock()

        async def fake_send_message(msg):
            yield response_message

        mock_client.send_message = fake_send_message

        mock_factory = MagicMock()
        mock_factory.create.return_value = mock_client

        # Mock ToolContext with a dict-like state
        tool_context = MagicMock()
        tool_context.state = {}

        with patch(
            "agents.supervisors.recruiter.recruiter_client.httpx.AsyncClient"
        ), patch(
            "agents.supervisors.recruiter.recruiter_client.ClientFactory",
            return_value=mock_factory,
        ):
            result = await recruit_agents("find accounting agents", tool_context)

        assert STATE_KEY_RECRUITED_AGENTS in tool_context.state
        assert "cid_abc" in tool_context.state[STATE_KEY_RECRUITED_AGENTS]
        assert "Found 1 agent" in result

    @pytest.mark.asyncio
    async def test_recruit_agents_merges_with_existing(self):
        """recruit_agents should merge new results with pre-existing state."""
        new_records = {"cid_new": {"name": "New Agent", "url": "http://new:9000"}}

        response_message = Message(
            role=Role.agent,
            message_id="msg-2",
            parts=[
                Part(root=TextPart(text="Found another")),
                Part(
                    root=DataPart(
                        data=new_records,
                        metadata={"type": "found_agent_records"},
                    )
                ),
            ],
        )

        mock_client = AsyncMock()

        async def fake_send_message(msg):
            yield response_message

        mock_client.send_message = fake_send_message

        mock_factory = MagicMock()
        mock_factory.create.return_value = mock_client

        tool_context = MagicMock()
        tool_context.state = {
            STATE_KEY_RECRUITED_AGENTS: {"cid_old": {"name": "Old Agent"}},
            STATE_KEY_EVALUATION_RESULTS: {},
        }

        with patch(
            "agents.supervisors.recruiter.recruiter_client.httpx.AsyncClient"
        ), patch(
            "agents.supervisors.recruiter.recruiter_client.ClientFactory",
            return_value=mock_factory,
        ):
            await recruit_agents("find more", tool_context)

        state_agents = tool_context.state[STATE_KEY_RECRUITED_AGENTS]
        assert "cid_old" in state_agents
        assert "cid_new" in state_agents

    @pytest.mark.asyncio
    async def test_recruit_agents_no_results(self):
        """recruit_agents should return a message when no agents are found."""
        response_message = Message(
            role=Role.agent,
            message_id="msg-3",
            parts=[Part(root=TextPart(text="No matching agents found."))],
        )

        mock_client = AsyncMock()

        async def fake_send_message(msg):
            yield response_message

        mock_client.send_message = fake_send_message

        mock_factory = MagicMock()
        mock_factory.create.return_value = mock_client

        tool_context = MagicMock()
        tool_context.state = {}

        with patch(
            "agents.supervisors.recruiter.recruiter_client.httpx.AsyncClient"
        ), patch(
            "agents.supervisors.recruiter.recruiter_client.ClientFactory",
            return_value=mock_factory,
        ):
            result = await recruit_agents("find xyz", tool_context)

        assert "No matching agents found" in result

    @pytest.mark.asyncio
    async def test_recruit_agents_handles_task_tuple_response(self):
        """recruit_agents should handle (Task, update) tuple responses from A2A."""
        agent_records = {"cid_task": {"name": "Task Agent", "url": "http://t:9000"}}

        task = Task(
            id="task-1",
            contextId="ctx-1",
            status=TaskStatus(
                state=TaskState.completed,
                message=Message(
                    role=Role.agent,
                    message_id="msg-4",
                    parts=[
                        Part(root=TextPart(text="Task completed")),
                        Part(
                            root=DataPart(
                                data=agent_records,
                                metadata={"type": "found_agent_records"},
                            )
                        ),
                    ],
                ),
            ),
        )

        mock_client = AsyncMock()

        async def fake_send_message(msg):
            yield (task, None)

        mock_client.send_message = fake_send_message

        mock_factory = MagicMock()
        mock_factory.create.return_value = mock_client

        tool_context = MagicMock()
        tool_context.state = {}

        with patch(
            "agents.supervisors.recruiter.recruiter_client.httpx.AsyncClient"
        ), patch(
            "agents.supervisors.recruiter.recruiter_client.ClientFactory",
            return_value=mock_factory,
        ):
            result = await recruit_agents("find task agents", tool_context)

        assert "cid_task" in tool_context.state[STATE_KEY_RECRUITED_AGENTS]
        assert "Task completed" in result
