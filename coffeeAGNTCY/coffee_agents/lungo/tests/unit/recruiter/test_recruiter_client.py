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
from agents.supervisors.recruiter import recruiter_client
from agents.supervisors.recruiter.recruiter_client import (
    _emit_discovery_topology,
    _extract_parts,
    _parse_dict_values,
    recruit_agents,
)
from common.stable_agent_id import stable_agent_id_for_name
from common.workflow_context_prop import WorkflowContext
from common.workflow_utils.inflight import TraceContext


# ---------------------------------------------------------------------------
# _parse_dict_values
# ---------------------------------------------------------------------------


class TestParseDictValues:
    def test_already_dict_values(self):
        data = {"cid1": {"name": "Agent A"}}
        result = _parse_dict_values(data)
        assert result == {"cid1": {"name": "Agent A"}}

    def test_json_string_values(self):
        """Recruiter service may return JSON strings instead of dicts."""
        import json
        data = {
            "cid1": json.dumps({"name": "Agent A", "url": "http://a:9000"}),
            "cid2": json.dumps({"name": "Agent B", "url": "http://b:9000"}),
        }
        result = _parse_dict_values(data)
        assert result["cid1"]["name"] == "Agent A"
        assert result["cid2"]["name"] == "Agent B"

    def test_mixed_dict_and_string_values(self):
        import json
        data = {
            "cid1": {"name": "Agent A"},
            "cid2": json.dumps({"name": "Agent B"}),
        }
        result = _parse_dict_values(data)
        assert result["cid1"]["name"] == "Agent A"
        assert result["cid2"]["name"] == "Agent B"

    def test_invalid_json_string_skipped(self):
        data = {"cid1": "not valid json {{{"}
        result = _parse_dict_values(data)
        assert "cid1" not in result

    def test_non_dict_json_skipped(self):
        import json
        data = {"cid1": json.dumps(["a", "list"])}
        result = _parse_dict_values(data)
        assert "cid1" not in result


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

        async def fake_send_message(msg, context=None):
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

        async def fake_send_message(msg, context=None):
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

        async def fake_send_message(msg, context=None):
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

        async def fake_send_message(msg, context=None):
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


# ---------------------------------------------------------------------------
# _emit_discovery_topology
# ---------------------------------------------------------------------------


_VALID_INSTANCE = "instance://11111111-1111-4111-8111-111111111111"
_NO_TRACE = TraceContext(trace_id=None, span_id=None, owner_span_id=None)


def _patch_discovery_context(
    *,
    instance_id: str | None,
    workflow_name: str | None,
    workflow_known: bool = True,
):
    """Build the patch stack shared by discovery-emit tests."""
    return [
        patch.object(
            recruiter_client,
            "read_workflow_context",
            return_value=WorkflowContext(
                instance_id=instance_id, workflow_name=workflow_name
            ),
        ),
        patch.object(recruiter_client, "read_trace_context", return_value=_NO_TRACE),
        patch.object(
            recruiter_client,
            "lookup_workflow",
            return_value=object() if workflow_known else None,
        ),
    ]


class TestEmitDiscoveryTopology:
    @pytest.mark.asyncio
    async def test_emits_anchor_node_and_discovered_agents(self):
        """A valid context emits an anchor node plus one node/edge per agent."""
        records = {
            "cidB": {"name": "Brazil", "url": "http://brazil:9000"},
            "cidC": {"name": "Colombia", "url": "http://colombia:9000"},
        }
        sink = AsyncMock()
        build_event_mock = MagicMock(return_value=MagicMock())

        ctx_patches = _patch_discovery_context(
            instance_id=_VALID_INSTANCE, workflow_name="recruiter_pattern"
        )
        with ctx_patches[0], ctx_patches[1], ctx_patches[2], patch.object(
            recruiter_client, "build_event", build_event_mock
        ), patch.object(recruiter_client, "_discovery_event_sink", sink):
            await _emit_discovery_topology(records)

        sink.emit.assert_awaited_once()
        topology = build_event_mock.call_args.kwargs["topology"]
        labels = [node.label for node in topology.nodes]
        assert labels[0] == "Agentic Recruiter"
        assert "Brazil" in labels and "Colombia" in labels
        # The anchor carries the seeded recruiter's stable_agent_id so the
        # backend merge layer reconciles it onto the real recruiter node.
        assert topology.nodes[0].stable_agent_id == stable_agent_id_for_name(
            "Agentic Recruiter agent"
        )
        # One edge per discovered agent, all sourced from the anchor node.
        anchor_id = topology.nodes[0].id
        assert len(topology.edges) == 2
        assert all(edge.source == anchor_id for edge in topology.edges)
        # The full OASF record travels inline on the discovered node.
        brazil = next(node for node in topology.nodes if node.label == "Brazil")
        assert brazil.oasf_record == records["cidB"]
        assert brazil.agent_cid == "cidB"

    @pytest.mark.asyncio
    async def test_discovery_node_ids_are_deterministic(self):
        """Re-discovering the same CID yields the same node id (idempotent merge)."""
        records = {"cidB": {"name": "Brazil"}}
        first = MagicMock(return_value=MagicMock())
        second = MagicMock(return_value=MagicMock())

        for build_mock in (first, second):
            ctx_patches = _patch_discovery_context(
                instance_id=_VALID_INSTANCE, workflow_name="recruiter_pattern"
            )
            with ctx_patches[0], ctx_patches[1], ctx_patches[2], patch.object(
                recruiter_client, "build_event", build_mock
            ), patch.object(recruiter_client, "_discovery_event_sink", AsyncMock()):
                await _emit_discovery_topology(records)

        first_node = first.call_args.kwargs["topology"].nodes[1].id
        second_node = second.call_args.kwargs["topology"].nodes[1].id
        assert first_node == second_node

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "description,records,instance_id,workflow_name,workflow_known",
        [
            ("empty records", {}, _VALID_INSTANCE, "recruiter_pattern", True),
            (
                "missing instance id",
                {"cidB": {"name": "Brazil"}},
                None,
                "recruiter_pattern",
                True,
            ),
            (
                "invalid instance id",
                {"cidB": {"name": "Brazil"}},
                "not-an-instance",
                "recruiter_pattern",
                True,
            ),
            (
                "unknown workflow",
                {"cidB": {"name": "Brazil"}},
                _VALID_INSTANCE,
                "ghost_workflow",
                False,
            ),
            (
                "missing workflow name",
                {"cidB": {"name": "Brazil"}},
                _VALID_INSTANCE,
                None,
                True,
            ),
        ],
    )
    async def test_no_emit_when_context_incomplete(
        self, description, records, instance_id, workflow_name, workflow_known
    ):
        sink = AsyncMock()
        build_event_mock = MagicMock()
        ctx_patches = _patch_discovery_context(
            instance_id=instance_id,
            workflow_name=workflow_name,
            workflow_known=workflow_known,
        )
        with ctx_patches[0], ctx_patches[1], ctx_patches[2], patch.object(
            recruiter_client, "build_event", build_event_mock
        ), patch.object(recruiter_client, "_discovery_event_sink", sink):
            await _emit_discovery_topology(records)

        sink.emit.assert_not_awaited()
        build_event_mock.assert_not_called()

    @pytest.mark.asyncio
    async def test_no_emit_when_sink_disabled(self):
        """With events disabled (_discovery_event_sink is None) nothing is emitted."""
        ctx_patches = _patch_discovery_context(
            instance_id=_VALID_INSTANCE, workflow_name="recruiter_pattern"
        )
        with ctx_patches[0], ctx_patches[1], ctx_patches[2], patch.object(
            recruiter_client, "_discovery_event_sink", None
        ):
            await _emit_discovery_topology({"cidB": {"name": "Brazil"}})
        # No exception means the guard short-circuited cleanly.
