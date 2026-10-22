# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""Unit tests for agents.supervisors.recruiter.recruiter_client."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from a2a.helpers import new_data_part
from a2a.types import (
    Message,
    Part,
    Role,
    SendMessageRequest,
    StreamResponse,
    Task,
    TaskState,
    TaskStatus,
    TaskStatusUpdateEvent,
)
from agents.supervisors.recruiter.models import (
    STATE_KEY_EVALUATION_RESULTS,
    STATE_KEY_RECRUITED_AGENTS,
)
from common.stable_agent_id import stable_agent_id_for_name
from common.workflow_context_prop import WorkflowContext
from common.workflow_utils.inflight import TraceContext


def _data_part(data, part_type: str | None = None) -> Part:
    part = new_data_part(data)
    if part_type is not None:
        part.metadata.update({"type": part_type})
    return part


def _agent_message(*parts: Part, message_id: str = "msg-1") -> Message:
    return Message(role=Role.ROLE_AGENT, message_id=message_id, parts=list(parts))


def _drain_queue(recruiter_client_mod) -> list:
    queue = recruiter_client_mod.get_a2a_event_queue()
    items = []
    while not queue.empty():
        items.append(queue.get_nowait())
    return items


def _patched_client(recruiter_client_mod, events, sent: list | None = None):
    """Patch httpx + ClientFactory so ``send_message`` yields ``events``."""
    mock_client = AsyncMock()

    async def fake_send_message(request, context=None):
        if sent is not None:
            sent.append(request)
        for event in events:
            yield event

    mock_client.send_message = fake_send_message
    mock_factory = MagicMock()
    mock_factory.create.return_value = mock_client
    return (
        patch("agents.supervisors.recruiter.recruiter_client.httpx.AsyncClient"),
        patch(
            "agents.supervisors.recruiter.recruiter_client.ClientFactory",
            return_value=mock_factory,
        ),
    )


# ---------------------------------------------------------------------------
# _parse_dict_values
# ---------------------------------------------------------------------------


class TestParseDictValues:
    def test_already_dict_values(self, recruiter_client_mod):
        data = {"cid1": {"name": "Agent A"}}
        result = recruiter_client_mod._parse_dict_values(data)
        assert result == {"cid1": {"name": "Agent A"}}

    def test_json_string_values(self, recruiter_client_mod):
        """Recruiter service may return JSON strings instead of dicts."""
        import json

        data = {
            "cid1": json.dumps({"name": "Agent A", "url": "http://a:9000"}),
            "cid2": json.dumps({"name": "Agent B", "url": "http://b:9000"}),
        }
        result = recruiter_client_mod._parse_dict_values(data)
        assert result["cid1"]["name"] == "Agent A"
        assert result["cid2"]["name"] == "Agent B"

    def test_mixed_dict_and_string_values(self, recruiter_client_mod):
        import json

        data = {
            "cid1": {"name": "Agent A"},
            "cid2": json.dumps({"name": "Agent B"}),
        }
        result = recruiter_client_mod._parse_dict_values(data)
        assert result["cid1"]["name"] == "Agent A"
        assert result["cid2"]["name"] == "Agent B"

    def test_invalid_json_string_skipped(self, recruiter_client_mod):
        data = {"cid1": "not valid json {{{"}
        result = recruiter_client_mod._parse_dict_values(data)
        assert "cid1" not in result

    def test_non_dict_json_skipped(self, recruiter_client_mod):
        import json

        data = {"cid1": json.dumps(["a", "list"])}
        result = recruiter_client_mod._parse_dict_values(data)
        assert "cid1" not in result


# ---------------------------------------------------------------------------
# _extract_parts
# ---------------------------------------------------------------------------


class TestExtractParts:
    def test_text_only(self, recruiter_client_mod):
        parts = [Part(text="Hello world")]
        result = recruiter_client_mod._extract_parts(parts)
        assert result.text == "Hello world"
        assert result.agent_records == {}
        assert result.evaluation_results == {}

    def test_agent_records(self, recruiter_client_mod):
        parts = [_data_part({"cid1": {"name": "Agent A"}}, "found_agent_records")]
        result = recruiter_client_mod._extract_parts(parts)
        assert result.text is None
        assert "cid1" in result.agent_records

    def test_evaluation_results(self, recruiter_client_mod):
        parts = [_data_part({"cid1": {"score": 0.95}}, "evaluation_results")]
        result = recruiter_client_mod._extract_parts(parts)
        assert result.evaluation_results == {"cid1": {"score": 0.95}}

    def test_all_parts_combined(self, recruiter_client_mod):
        parts = [
            Part(text="Found 1 agent"),
            _data_part({"cid1": {"name": "Agent A"}}, "found_agent_records"),
            _data_part({"cid1": {"score": 0.9}}, "evaluation_results"),
        ]
        result = recruiter_client_mod._extract_parts(parts)
        assert result.text == "Found 1 agent"
        assert "cid1" in result.agent_records
        assert "cid1" in result.evaluation_results

    def test_data_part_without_metadata(self, recruiter_client_mod):
        parts = [_data_part({"key": "val"})]
        result = recruiter_client_mod._extract_parts(parts)
        assert result.text is None
        assert result.agent_records == {}
        assert result.evaluation_results == {}

    def test_non_dict_data_part_is_skipped(self, recruiter_client_mod):
        parts = [_data_part(["a", "list"], "found_agent_records")]
        result = recruiter_client_mod._extract_parts(parts)
        assert result.agent_records == {}

    def test_integral_numbers_survive_the_struct_round_trip(
        self, recruiter_client_mod
    ):
        """Struct stores numbers as doubles; OASF ids must come back as ints."""
        record = {"name": "Agent A", "skills": [{"id": 10201}], "score": 0.5}
        parts = [_data_part({"cid1": record}, "found_agent_records")]
        result = recruiter_client_mod._extract_parts(parts)
        restored = result.agent_records["cid1"]
        assert restored == record
        assert isinstance(restored["skills"][0]["id"], int)

    def test_integral_floats_outside_id_stay_floats(self, recruiter_client_mod):
        """A score of 1.0 is a genuine float and must not become the int 1."""
        results = {"cid1": {"score": 1.0, "details": [{"weight": 2.0, "id": 7}]}}
        parts = [_data_part(results, "evaluation_results")]
        restored = recruiter_client_mod._extract_parts(parts).evaluation_results
        assert restored == results
        assert isinstance(restored["cid1"]["score"], float)
        assert isinstance(restored["cid1"]["details"][0]["weight"], float)
        assert isinstance(restored["cid1"]["details"][0]["id"], int)

    def test_empty_parts(self, recruiter_client_mod):
        result = recruiter_client_mod._extract_parts([])
        assert result.text is None
        assert result.agent_records == {}


# ---------------------------------------------------------------------------
# recruit_agents tool
# ---------------------------------------------------------------------------


class TestRecruitAgents:
    @pytest.mark.asyncio
    async def test_recruit_agents_stores_in_state(self, recruiter_client_mod):
        """recruit_agents should merge results into tool_context.state."""
        agent_records = {"cid_abc": {"name": "Agent A", "url": "http://a:9000"}}
        event = StreamResponse(
            message=_agent_message(
                Part(text="Found 1 agent"),
                _data_part(agent_records, "found_agent_records"),
            )
        )
        sent: list = []
        tool_context = MagicMock()
        tool_context.state = {}

        httpx_patch, factory_patch = _patched_client(
            recruiter_client_mod, [event], sent
        )
        with httpx_patch, factory_patch:
            result = await recruiter_client_mod.recruit_agents(
                "find accounting agents", tool_context
            )

        assert tool_context.state[STATE_KEY_RECRUITED_AGENTS] == agent_records
        assert "Found 1 agent" in result
        [request] = sent
        assert isinstance(request, SendMessageRequest)
        assert request.message.role == Role.ROLE_USER
        assert request.message.parts[0].text == "find accounting agents"
        assert _drain_queue(recruiter_client_mod) == [None]

    @pytest.mark.asyncio
    async def test_recruit_agents_merges_with_existing(self, recruiter_client_mod):
        """recruit_agents should merge new results with pre-existing state."""
        new_records = {"cid_new": {"name": "New Agent", "url": "http://new:9000"}}
        event = StreamResponse(
            message=_agent_message(
                Part(text="Found another"),
                _data_part(new_records, "found_agent_records"),
                message_id="msg-2",
            )
        )
        tool_context = MagicMock()
        tool_context.state = {
            STATE_KEY_RECRUITED_AGENTS: {"cid_old": {"name": "Old Agent"}},
            STATE_KEY_EVALUATION_RESULTS: {},
        }

        httpx_patch, factory_patch = _patched_client(recruiter_client_mod, [event])
        with httpx_patch, factory_patch:
            await recruiter_client_mod.recruit_agents("find more", tool_context)

        state_agents = tool_context.state[STATE_KEY_RECRUITED_AGENTS]
        assert "cid_old" in state_agents
        assert "cid_new" in state_agents
        _drain_queue(recruiter_client_mod)

    @pytest.mark.asyncio
    async def test_recruit_agents_no_results(self, recruiter_client_mod):
        """recruit_agents should return a message when no agents are found."""
        event = StreamResponse(
            message=_agent_message(
                Part(text="No matching agents found."), message_id="msg-3"
            )
        )
        tool_context = MagicMock()
        tool_context.state = {}

        httpx_patch, factory_patch = _patched_client(recruiter_client_mod, [event])
        with httpx_patch, factory_patch:
            result = await recruiter_client_mod.recruit_agents("find xyz", tool_context)

        assert "No matching agents found" in result
        _drain_queue(recruiter_client_mod)

    @pytest.mark.asyncio
    async def test_recruit_agents_streams_status_then_completed_task(
        self,
        recruiter_client_mod,
    ):
        """Working updates go to the side-channel; the completed task is the result."""
        agent_records = {"cid_task": {"name": "Task Agent", "url": "http://t:9000"}}
        working = StreamResponse(
            status_update=TaskStatusUpdateEvent(
                task_id="task-1",
                context_id="ctx-1",
                status=TaskStatus(
                    state=TaskState.TASK_STATE_WORKING,
                    message=Message(
                        role=Role.ROLE_AGENT,
                        message_id="s1",
                        parts=[Part(text="Searching directory")],
                        metadata={"author": "recruiter", "event_type": "search"},
                    ),
                ),
            )
        )
        completed = StreamResponse(
            task=Task(
                id="task-1",
                context_id="ctx-1",
                status=TaskStatus(
                    state=TaskState.TASK_STATE_COMPLETED,
                    message=_agent_message(
                        Part(text="Task completed"),
                        _data_part(agent_records, "found_agent_records"),
                        message_id="msg-4",
                    ),
                ),
            )
        )
        tool_context = MagicMock()
        tool_context.state = {}

        httpx_patch, factory_patch = _patched_client(
            recruiter_client_mod, [working, completed]
        )
        with httpx_patch, factory_patch:
            result = await recruiter_client_mod.recruit_agents(
                "find task agents", tool_context
            )

        assert "cid_task" in tool_context.state[STATE_KEY_RECRUITED_AGENTS]
        assert "Task completed" in result
        assert _drain_queue(recruiter_client_mod) == [
            {
                "event_type": "status_update",
                "message": "Searching directory",
                "state": "working",
                "author": "recruiter",
                "a2a_event_type": "search",
            },
            None,
        ]


# ---------------------------------------------------------------------------
# _handle_stream_event / _forward_status_update
# ---------------------------------------------------------------------------


def _status_update(state, text: str | None = "progress") -> StreamResponse:
    status = TaskStatus(state=state)
    if text is not None:
        status.message.CopyFrom(
            Message(role=Role.ROLE_AGENT, message_id="s", parts=[Part(text=text)])
        )
    return StreamResponse(
        status_update=TaskStatusUpdateEvent(
            task_id="t", context_id="c", status=status
        )
    )


class TestHandleStreamEvent:
    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "state",
        [
            TaskState.TASK_STATE_COMPLETED,
            TaskState.TASK_STATE_FAILED,
            TaskState.TASK_STATE_CANCELED,
            TaskState.TASK_STATE_REJECTED,
        ],
    )
    async def test_terminal_status_update_is_not_forwarded(
        self, recruiter_client_mod, state
    ):
        _drain_queue(recruiter_client_mod)
        await recruiter_client_mod._handle_stream_event(_status_update(state), "t")
        assert _drain_queue(recruiter_client_mod) == []

    @pytest.mark.asyncio
    async def test_status_update_without_message_is_not_forwarded(
        self, recruiter_client_mod
    ):
        _drain_queue(recruiter_client_mod)
        event = _status_update(TaskState.TASK_STATE_WORKING, text=None)
        assert await recruiter_client_mod._handle_stream_event(event, "t") is None
        assert _drain_queue(recruiter_client_mod) == []

    @pytest.mark.asyncio
    async def test_completed_status_update_carries_the_result(
        self, recruiter_client_mod
    ):
        _drain_queue(recruiter_client_mod)
        event = _status_update(TaskState.TASK_STATE_COMPLETED, text="done")
        result = await recruiter_client_mod._handle_stream_event(event, "t")
        assert result is not None and result.text == "done"

    @pytest.mark.asyncio
    async def test_working_task_snapshot_is_not_a_result(self, recruiter_client_mod):
        event = StreamResponse(
            task=Task(
                id="t",
                context_id="c",
                status=TaskStatus(state=TaskState.TASK_STATE_WORKING),
            )
        )
        assert await recruiter_client_mod._handle_stream_event(event, "t") is None


# ---------------------------------------------------------------------------
# _emit_discovery_topology
# ---------------------------------------------------------------------------


_VALID_INSTANCE = "instance://11111111-1111-4111-8111-111111111111"
_NO_TRACE = TraceContext(trace_id=None, span_id=None, owner_span_id=None)


def _patch_discovery_context(
    recruiter_client_mod,
    *,
    instance_id: str | None,
    workflow_name: str | None,
    workflow_known: bool = True,
):
    """Build the patch stack shared by discovery-emit tests."""
    return [
        patch.object(
            recruiter_client_mod,
            "read_workflow_context",
            return_value=WorkflowContext(
                instance_id=instance_id, workflow_name=workflow_name
            ),
        ),
        patch.object(
            recruiter_client_mod, "read_trace_context", return_value=_NO_TRACE
        ),
        patch.object(
            recruiter_client_mod,
            "lookup_workflow",
            return_value=object() if workflow_known else None,
        ),
    ]


class TestEmitDiscoveryTopology:
    @pytest.mark.asyncio
    async def test_emits_anchor_node_and_discovered_agents(self, recruiter_client_mod):
        """A valid context emits an anchor node plus one node/edge per agent."""
        records = {
            "cidB": {"name": "Brazil", "url": "http://brazil:9000"},
            "cidC": {"name": "Colombia", "url": "http://colombia:9000"},
        }
        sink = AsyncMock()
        build_event_mock = MagicMock(return_value=MagicMock())

        ctx_patches = _patch_discovery_context(
            recruiter_client_mod,
            instance_id=_VALID_INSTANCE,
            workflow_name="recruiter_pattern",
        )
        with (
            ctx_patches[0],
            ctx_patches[1],
            ctx_patches[2],
            patch.object(recruiter_client_mod, "build_event", build_event_mock),
            patch.object(recruiter_client_mod, "_discovery_event_sink", sink),
        ):
            await recruiter_client_mod._emit_discovery_topology(records)

        sink.emit.assert_awaited_once()
        topology = build_event_mock.call_args.kwargs["topology"]
        labels = [node.label for node in topology.nodes]
        assert labels[0] == "Agentic Recruiter"
        assert "Brazil" in labels and "Colombia" in labels
        # The anchor carries the seeded recruiter's stable_agent_id so the
        # backend merge layer reconciles it onto the real recruiter node.
        assert topology.nodes[0].stable_agent_id.root == stable_agent_id_for_name(
            "Agentic Recruiter agent"
        )
        # One edge per discovered agent, all sourced from the anchor node.
        anchor_id = topology.nodes[0].id
        assert len(topology.edges) == 2
        assert all(edge.source == anchor_id for edge in topology.edges)
        # The inline agent record travels on the discovered node (``oasf_record``).
        brazil = next(node for node in topology.nodes if node.label == "Brazil")
        assert brazil.oasf_record == records["cidB"]
        assert brazil.agent_cid == "cidB"

    @pytest.mark.asyncio
    async def test_discovery_node_ids_are_deterministic(self, recruiter_client_mod):
        """Re-discovering the same CID yields the same node id (idempotent merge)."""
        records = {"cidB": {"name": "Brazil"}}
        first = MagicMock(return_value=MagicMock())
        second = MagicMock(return_value=MagicMock())

        for build_mock in (first, second):
            ctx_patches = _patch_discovery_context(
                recruiter_client_mod,
                instance_id=_VALID_INSTANCE,
                workflow_name="recruiter_pattern",
            )
            with (
                ctx_patches[0],
                ctx_patches[1],
                ctx_patches[2],
                patch.object(recruiter_client_mod, "build_event", build_mock),
                patch.object(
                    recruiter_client_mod, "_discovery_event_sink", AsyncMock()
                ),
            ):
                await recruiter_client_mod._emit_discovery_topology(records)

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
        self,
        recruiter_client_mod,
        description,
        records,
        instance_id,
        workflow_name,
        workflow_known,
    ):
        sink = AsyncMock()
        build_event_mock = MagicMock()
        ctx_patches = _patch_discovery_context(
            recruiter_client_mod,
            instance_id=instance_id,
            workflow_name=workflow_name,
            workflow_known=workflow_known,
        )
        with (
            ctx_patches[0],
            ctx_patches[1],
            ctx_patches[2],
            patch.object(recruiter_client_mod, "build_event", build_event_mock),
            patch.object(recruiter_client_mod, "_discovery_event_sink", sink),
        ):
            await recruiter_client_mod._emit_discovery_topology(records)

        sink.emit.assert_not_awaited()
        build_event_mock.assert_not_called()

    @pytest.mark.asyncio
    async def test_no_emit_when_sink_disabled(self, recruiter_client_mod):
        """With events disabled (_discovery_event_sink is None) nothing is emitted."""
        ctx_patches = _patch_discovery_context(
            recruiter_client_mod,
            instance_id=_VALID_INSTANCE,
            workflow_name="recruiter_pattern",
        )
        with (
            ctx_patches[0],
            ctx_patches[1],
            ctx_patches[2],
            patch.object(recruiter_client_mod, "_discovery_event_sink", None),
        ):
            await recruiter_client_mod._emit_discovery_topology(
                {"cidB": {"name": "Brazil"}}
            )
        # No exception means the guard short-circuited cleanly.
