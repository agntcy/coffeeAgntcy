# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""ADK tool function that communicates with the remote recruiter A2A service
and persists results in session state."""

import asyncio
import json
import logging
from uuid import NAMESPACE_DNS, UUID, uuid4, uuid5

import httpx
from pydantic import ValidationError
from a2a.client import ClientConfig, ClientFactory
from a2a.types import (
    AgentCard,
    DataPart,
    Message,
    Part,
    Role,
    Task,
    TaskState,
    TaskStatusUpdateEvent,
    TextPart,
)
from google.adk.tools.tool_context import ToolContext

from agents.supervisors.recruiter.models import (
    STATE_KEY_EVALUATION_RESULTS,
    STATE_KEY_RECRUITED_AGENTS,
    RecruitmentResponse,
)
from agents.supervisors.recruiter.recruiter_service_card import (
    RECRUITER_AGENT_CARD,
)
from common.stable_agent_id import stable_agent_id_for_name
from common.workflow_context_prop import read_workflow_context
from common.workflow_utils.builders import build_event, make_node
from common.workflow_utils.event_sink import WorkflowAPIEventSink
from common.workflow_utils.inflight import read_trace_context
from common.workflow_utils.workflow_catalog import lookup_workflow
from config.config import EMIT_WORKFLOW_EVENTS
from schema.types import (
    EdgeId,
    InstanceId,
    NodeId,
    Operation,
    PartialEdge,
    PartialTopology,
)

logger = logging.getLogger("lungo.recruiter.supervisor.recruiter_client")

# Discovered agents are merged into the live workflow instance topology so the
# frontend renders and disposes of them through the normal topology channel.
# The anchor node shares the seeded recruiter node's label (and carries no
# stable_agent_id) so the frontend collapses it onto "Agentic Recruiter" and
# re-points the discovered-agent edges there.
_RECRUITER_ANCHOR_LABEL = "Agentic Recruiter"
_DISCOVERY_NS = uuid5(NAMESPACE_DNS, "recruiter.discovery.lungo")
_discovery_event_sink = WorkflowAPIEventSink() if EMIT_WORKFLOW_EVENTS else None


def _is_valid_instance_id(value: str) -> bool:
    """True when value is a canonical ``instance://<uuid>`` id (schema-validated)."""
    try:
        InstanceId(root=value)
    except ValidationError:
        return False
    return True

# ---------------------------------------------------------------------------
# Side-channel queue for streaming A2A events to main.py
# ---------------------------------------------------------------------------
# The ADK runner blocks while a tool executes, so it cannot forward
# intermediate A2A events.  We use a module-level asyncio.Queue as a
# side-channel: recruit_agents pushes status dicts onto it and
# main.py's stream_generator drains it in parallel.
# ---------------------------------------------------------------------------

_a2a_event_queue: asyncio.Queue[dict | None] = asyncio.Queue()


def get_a2a_event_queue() -> asyncio.Queue[dict | None]:
    """Return the module-level queue that carries A2A streaming events."""
    return _a2a_event_queue


def _parse_dict_values(data: dict) -> dict[str, dict]:
    """Ensure all values are dicts, parsing JSON strings if needed.

    The recruiter service may return record values as JSON-encoded strings
    rather than parsed dicts.
    """
    result: dict[str, dict] = {}
    for key, value in data.items():
        if isinstance(value, dict):
            result[key] = value
        elif isinstance(value, str):
            try:
                parsed = json.loads(value)
                if isinstance(parsed, dict):
                    result[key] = parsed
                else:
                    logger.warning("Value for key %s parsed to %s, not dict; skipping", key, type(parsed).__name__)
            except (json.JSONDecodeError, TypeError):
                logger.warning("Value for key %s is not valid JSON; skipping", key)
        else:
            logger.warning("Unexpected value type %s for key %s; skipping", type(value).__name__, key)
    return result


def _extract_parts(parts: list[Part]) -> RecruitmentResponse:
    """Extract text, agent records, and evaluation results from A2A message parts."""
    text = None
    agent_records: dict[str, dict] = {}
    evaluation_results: dict[str, dict] = {}
    for part in parts:
        root = part.root
        if isinstance(root, TextPart):
            text = root.text
        elif isinstance(root, DataPart):
            meta_type = root.metadata.get("type") if root.metadata else None
            if meta_type == "found_agent_records":
                agent_records = _parse_dict_values(root.data)
            elif meta_type == "evaluation_results":
                evaluation_results = _parse_dict_values(root.data)
    return RecruitmentResponse(
        text=text,
        agent_records=agent_records,
        evaluation_results=evaluation_results,
    )


def _discovery_node_id(cid: str) -> str:
    """Deterministic runtime node id for a discovered agent CID."""
    return f"node://{uuid5(_DISCOVERY_NS, f'agent::{cid}')}"


def _discovery_edge_id(source_nid: str, target_nid: str) -> str:
    """Deterministic edge id for an anchor -> discovered-agent connection."""
    return f"edge://{uuid5(_DISCOVERY_NS, f'{source_nid}->{target_nid}')}"


async def _emit_discovery_topology(agent_records: dict[str, dict]) -> None:
    """Merge discovered agents into the live workflow instance topology.

    Emits a STATE_PROGRESS_UPDATE that creates one node per discovered agent
    (carrying its full OASF record inline) plus an anchor node sharing the
    seeded recruiter's label so the frontend collapses it onto "Agentic
    Recruiter" and re-points the new edges there. Nodes therefore arrive,
    render, and dispose through the normal topology channel.
    """
    if _discovery_event_sink is None or not agent_records:
        return

    wf_ctx = read_workflow_context()
    workflow_name = wf_ctx.workflow_name
    instance_id = wf_ctx.instance_id
    if not workflow_name or lookup_workflow(workflow_name) is None:
        logger.debug(
            "recruit discovery: no/unknown workflow_name=%r; skipping topology emit",
            workflow_name,
        )
        return
    if not instance_id or not _is_valid_instance_id(instance_id):
        logger.debug(
            "recruit discovery: missing/invalid instance_id=%r; skipping topology emit",
            instance_id,
        )
        return

    trace_ctx = read_trace_context()
    anchor_id = f"node://{uuid5(_DISCOVERY_NS, 'recruiter-anchor')}"
    nodes: list = [
        make_node(
            anchor_id,
            operation=Operation.CREATE,
            node_type="customNode",
            label=_RECRUITER_ANCHOR_LABEL,
            layer_index=0,
        )
    ]
    edges: list = []
    for cid, record in agent_records.items():
        name = str(record.get("name") or "").strip() or cid
        node_id = _discovery_node_id(cid)
        nodes.append(
            make_node(
                node_id,
                operation=Operation.CREATE,
                node_type="customNode",
                label=name,
                layer_index=1,
                stable_agent_id=stable_agent_id_for_name(name),
                extras={"oasf_record": record, "agent_cid": cid},
            )
        )
        edges.append(
            PartialEdge(
                id=EdgeId(_discovery_edge_id(anchor_id, node_id)),
                operation=Operation.CREATE,
                type="custom",
                source=NodeId(anchor_id),
                target=NodeId(node_id),
                bidirectional=False,
                weight=1.0,
            )
        )

    topology = PartialTopology(nodes=nodes, edges=edges)
    correlation_id = (
        f"correlation://{UUID(int=trace_ctx.trace_id)}"
        if trace_ctx.trace_id is not None
        else f"correlation://{uuid4()}"
    )
    try:
        event = build_event(
            source="recruiter_supervisor",
            workflow_name=workflow_name,
            instance_id=instance_id,
            topology=topology,
            correlation_id=correlation_id,
            correlation_message=f"discovered {len(agent_records)} agent(s)",
            trace_id=trace_ctx.trace_id,
            span_id=trace_ctx.span_id,
        )
    except RuntimeError:
        logger.warning(
            "recruit discovery: build_event failed for workflow=%r", workflow_name
        )
        return

    await _discovery_event_sink.emit(event)
    logger.info(
        "recruit discovery: emitted %d discovered node(s) to instance %s",
        len(agent_records),
        instance_id,
    )


async def _forward_status_update(
    update: TaskStatusUpdateEvent, tool_name: str
) -> None:
    """Forward one intermediate A2A status update onto the side-channel queue.

    Shared by recruit_agents and evaluate_agent: each non-final text status part
    is republished as a ``status_update`` event for main.py's stream_generator
    to drain in parallel.
    """
    if update.final or not update.status or not update.status.message:
        return
    message = update.status.message
    for part in message.parts or []:
        root = part.root
        if not isinstance(root, TextPart) or not root.text:
            continue
        status_text = root.text
        author = None
        event_type = "a2a_status"
        if message.metadata:
            author = message.metadata.get("author") or message.metadata.get(
                "from_agent"
            )
            event_type = message.metadata.get("event_type", "a2a_status")
        logger.info(
            "[tool:%s] A2A status: %s (state=%s, final=%s)",
            tool_name,
            status_text[:120],
            update.status.state if update.status else "?",
            update.final,
        )
        await _a2a_event_queue.put(
            {
                "event_type": "status_update",
                "message": status_text,
                "state": "working",
                "author": author or "recruiter_service",
                "a2a_event_type": event_type,
            }
        )


async def recruit_agents(query: str, tool_context: ToolContext) -> str:
    """Search the AGNTCY directory for agents matching a task description.

    Sends a streaming recruitment request to the remote recruiter A2A service
    and stores the discovered agent records in session state for later use by
    the DynamicWorkflowAgent.

    Args:
        query: Natural-language description of the task or capabilities needed.
        tool_context: Automatically injected by ADK; provides session state access.

    Returns:
        Human-readable summary of the recruitment results.
    """
    logger.info("[tool:recruit_agents] Called with query=%r", query)

    async with httpx.AsyncClient(timeout=httpx.Timeout(120.0)) as httpx_client:
        config = ClientConfig(httpx_client=httpx_client, streaming=True)
        factory = ClientFactory(config)
        # No A2A topology middleware here: the internal hop to the recruiter
        # service is an implementation detail. Discovery results are surfaced
        # via _emit_discovery_topology so only the seeded recruiter node and
        # the discovered agents appear on the graph.
        client = factory.create(RECRUITER_AGENT_CARD)

        message = Message(
            role=Role.user,
            message_id=str(uuid4()),
            parts=[Part(root=TextPart(text=query))],
        )

        response_data = RecruitmentResponse()

        async for event in client.send_message(message):
            # Streaming mode yields (Task, UpdateEvent) tuples
            if isinstance(event, tuple) and len(event) == 2:
                task, update = event

                # Forward intermediate status updates via the side-channel queue
                if isinstance(update, TaskStatusUpdateEvent):
                    await _forward_status_update(update, "recruit_agents")

                # Extract final result from completed task
                if (
                    isinstance(task, Task)
                    and task.status
                    and task.status.state == TaskState.completed
                    and task.status.message
                ):
                    response_data = _extract_parts(task.status.message.parts)
            elif isinstance(event, Message):
                response_data = _extract_parts(event.parts)

        # Signal that A2A streaming is done for this tool invocation
        await _a2a_event_queue.put(None)

    # Merge into session state (preserve previously recruited agents)
    existing_agents = tool_context.state.get(STATE_KEY_RECRUITED_AGENTS, {})
    existing_agents.update(response_data.agent_records)
    tool_context.state[STATE_KEY_RECRUITED_AGENTS] = existing_agents

    existing_evals = tool_context.state.get(STATE_KEY_EVALUATION_RESULTS, {})
    existing_evals.update(response_data.evaluation_results)
    tool_context.state[STATE_KEY_EVALUATION_RESULTS] = existing_evals

    # Merge discovered agents into the live instance topology so the frontend
    # renders/disposes them like any other instance node.
    await _emit_discovery_topology(response_data.agent_records)

    logger.info(
        "[tool:recruit_agents] Found %d agent(s), %d evaluation(s)",
        len(response_data.agent_records),
        len(response_data.evaluation_results),
    )

    # Build a human-readable summary
    if not response_data.agent_records:
        summary = response_data.text or "No agents found matching the query."
        logger.info("[tool:recruit_agents] Result: %s", summary)
        return summary

    summary_lines = [response_data.text or "Recruitment results:"]
    for cid, record in response_data.agent_records.items():
        name = record.get("name", "Unknown")
        desc = record.get("description", "")
        summary_lines.append(f"  - CID: {cid} | Name: {name} | {desc}")

    result = "\n".join(summary_lines)
    logger.info("[tool:recruit_agents] Result: %s", result)
    return result

async def evaluate_agent(
    agent_identifier: str, query: str, tool_context: ToolContext
) -> str:
    """Evaluate a single recruited agent against user-defined scenarios.

    Looks up the agent by name or CID from session state, then sends its
    record together with the user's evaluation criteria to the remote
    recruiter A2A service.  The service delegates to its ``agent_evaluator``
    sub-agent, which parses scenarios from the query, runs them against the
    agent, and returns pass/fail results.

    Args:
        agent_identifier: The agent's name (partial match, case-insensitive)
                          or CID (exact match).
        query: Natural-language description of the evaluation criteria /
               scenarios.  The recruiter service uses an LLM to extract
               structured scenarios from this text.
        tool_context: Automatically injected by ADK; provides session state access.

    Returns:
        Human-readable summary of the evaluation results.
    """
    logger.info(
        "[tool:evaluate_agent] Called with agent_identifier=%r, query=%r",
        agent_identifier,
        query,
    )

    # --- 1. Resolve the single agent from session state --------------------
    recruited: dict[str, dict] = tool_context.state.get(
        STATE_KEY_RECRUITED_AGENTS, {}
    )
    if not recruited:
        return (
            "No agents have been recruited yet. "
            "Please use recruit_agents to search for agents first, "
            "then call evaluate_agent to evaluate a specific agent."
        )

    # Reuse the same lookup helper used by select_agent in agent.py
    from agents.supervisors.recruiter.agent import _find_agent_by_name_or_cid

    cid, record = _find_agent_by_name_or_cid(agent_identifier, recruited)
    if not cid or not record:
        available = [
            f"  - {r.get('name', 'Unknown')} (CID: {c[:20]}...)"
            for c, r in recruited.items()
        ]
        available_list = "\n".join(available) if available else "  (none)"
        return (
            f"No agent found matching '{agent_identifier}'.\n\n"
            f"Available agents:\n{available_list}\n\n"
            "Please provide the exact name or CID of an agent from the list above."
        )

    agent_name = record.get("name", "Unknown")
    logger.info(
        "[tool:evaluate_agent] Resolved agent: name=%s, cid=%s",
        agent_name,
        cid[:20],
    )

    # --- 2. Build A2A message with evaluation request ----------------------
    # Send only the single agent's record so the recruiter service evaluates
    # just this agent.  The evaluation-focused text triggers delegation to
    # the agent_evaluator sub-agent on the remote side.
    single_agent_records = {cid: record}

    parts: list[Part] = [
        Part(
            root=TextPart(
                text=(
                    f"Evaluate the agent '{agent_name}' using these criteria:\n\n"
                    f"{query}"
                )
            )
        ),
        Part(
            root=DataPart(
                data=single_agent_records,
                metadata={"type": "found_agent_records"},
            )
        ),
    ]

    message = Message(
        role=Role.user,
        message_id=str(uuid4()),
        parts=parts,
    )

    # --- 3. Stream the A2A request -----------------------------------------
    response_data = RecruitmentResponse()

    async with httpx.AsyncClient(timeout=httpx.Timeout(300.0)) as httpx_client:
        config = ClientConfig(httpx_client=httpx_client, streaming=True)
        factory = ClientFactory(config)
        # See recruit_agents: no A2A topology middleware on the internal hop.
        client = factory.create(RECRUITER_AGENT_CARD)

        async for event in client.send_message(message):
            if isinstance(event, tuple) and len(event) == 2:
                task, update = event

                # Forward intermediate status updates via the side-channel queue
                if isinstance(update, TaskStatusUpdateEvent):
                    await _forward_status_update(update, "evaluate_agent")

                # Extract final result from completed task
                if (
                    isinstance(task, Task)
                    and task.status
                    and task.status.state == TaskState.completed
                    and task.status.message
                ):
                    response_data = _extract_parts(task.status.message.parts)
            elif isinstance(event, Message):
                response_data = _extract_parts(event.parts)

        # Signal that A2A streaming is done for this tool invocation
        await _a2a_event_queue.put(None)

    # --- 4. Persist evaluation results in session state --------------------
    existing_evals = tool_context.state.get(STATE_KEY_EVALUATION_RESULTS, {})
    existing_evals.update(response_data.evaluation_results)
    tool_context.state[STATE_KEY_EVALUATION_RESULTS] = existing_evals

    logger.info(
        "[tool:evaluate_agent] Received %d evaluation result(s) for '%s'",
        len(response_data.evaluation_results),
        agent_name,
    )

    # --- 5. Build a human-readable summary ---------------------------------
    if not response_data.evaluation_results:
        summary = (
            response_data.text
            or f"Evaluation of '{agent_name}' completed but no results were returned."
        )
        logger.info("[tool:evaluate_agent] Result: %s", summary)
        return summary

    summary_lines = [
        response_data.text or f"Evaluation results for **{agent_name}**:"
    ]
    for agent_id, result in response_data.evaluation_results.items():
        if agent_id.startswith("_"):  # skip meta-keys like _summary
            continue
        status = result.get("status", "unknown")
        passed = result.get("passed", None)
        result_summary = result.get("summary", "")

        if status == "evaluated":
            icon = "✅" if passed else "❌"
            summary_lines.append(f"  {icon} {result_summary}")

            # Include per-scenario breakdown if available
            for scenario_result in result.get("results", []):
                s_icon = "✅" if scenario_result.get("passed") else "❌"
                scenario_text = scenario_result.get("scenario", "")
                summary_lines.append(f"    {s_icon} {scenario_text}")
        elif status == "error":
            error_msg = result.get("error", "Unknown error")
            summary_lines.append(f"  ⚠️ Error — {error_msg}")
        else:
            summary_lines.append(f"  - {status}")

    result_text = "\n".join(summary_lines)
    logger.info("[tool:evaluate_agent] Result: %s", result_text)
    return result_text
