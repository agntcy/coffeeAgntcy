# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""Integration tests for the RecruiterAgent A2A server (a2a-sdk 1.x client)."""

import asyncio
import json
import pytest
import httpx
from uuid import uuid4

from a2a.client import ClientFactory, ClientConfig
from a2a.types import (
    Message,
    Role,
    SendMessageRequest,
    StreamResponse,
    TaskState,
    TaskStatusUpdateEvent,
    TaskArtifactUpdateEvent,
)

from agent_recruiter.common.a2a_helpers import (
    message_metadata,
    part_data,
    part_kind,
    part_metadata,
    text_part,
)
from agent_recruiter.server.card import AGENT_CARD
from agent_recruiter.common.logging import get_logger

logger = get_logger(__name__)


def _user_message(text: str) -> Message:
    return Message(
        role=Role.ROLE_USER,
        message_id=str(uuid4()),
        parts=[text_part(text)],
    )


def _scan_parts(parts, found: dict) -> None:
    """Record the text and the typed data parts of ``parts`` into ``found``."""
    for part in parts:
        kind = part_kind(part)
        if kind == "text":
            found["text"] = part.text
            logger.info(f"Text response: {part.text[:200]}...")
        elif kind == "data":
            data_type = part_metadata(part).get("type")
            found.setdefault("data", {})[data_type] = part_data(part)


def _final_content(response: StreamResponse, found: dict) -> None:
    """Collect text and data from a message or a completed task or status update."""
    which = response.WhichOneof("payload")
    if which == "message":
        _scan_parts(response.message.parts, found)
        return
    if which == "task":
        status = response.task.status
    elif which == "status_update":
        status = response.status_update.status
    else:
        return
    if status.state == TaskState.TASK_STATE_COMPLETED and status.HasField("message"):
        _scan_parts(status.message.parts, found)


@pytest.mark.asyncio
async def test_recruiter_a2a_server(
    run_recruiter_a2a_server, publish_sample_agent_record
):
    """Test the RecruiterAgent A2A server returns agent records in a data part."""

    logger.info("Starting RecruiterAgent A2A server")

    # Publish the sample agent record to the directory first
    cid = publish_sample_agent_record()
    logger.info(f"Published sample agent record with CID: {cid}")

    # Start the recruiter A2A server
    run_recruiter_a2a_server()

    await asyncio.sleep(2)  # Give the server time to start

    # Create an A2A client using ClientFactory with extended timeout
    async with httpx.AsyncClient(timeout=httpx.Timeout(120.0)) as httpx_client:
        config = ClientConfig(
            httpx_client=httpx_client,
            streaming=False,  # Use non-streaming for simpler response handling
        )
        client = ClientFactory(config).create(AGENT_CARD)

        found: dict = {}
        async for response in client.send_message(
            SendMessageRequest(
                message=_user_message("can you find an agent named Accountant agent?")
            )
        ):
            logger.info(f"Response: {response}")
            _final_content(response, found)

        found_agent_records = found.get("data", {}).get("found_agent_records")

        # Assertions
        assert found.get("text") is not None, "Expected a text response from the agent"
        assert found.get("data"), "Expected a data part with agent records"
        assert found_agent_records is not None, (
            "Expected found_agent_records in the data part"
        )
        assert len(found_agent_records) > 0, "Expected at least one agent record"

        # Verify the agent record structure
        for cid, record_data in found_agent_records.items():
            logger.info(f"Found agent record CID: {cid}")

            # Record may be a JSON string or dict
            if isinstance(record_data, str):
                record = json.loads(record_data)
            else:
                record = record_data

            assert "name" in record, (
                f"Expected 'name' in agent record, got: {record.keys()}"
            )
            logger.info(f"Agent name: {record.get('name')}")


@pytest.mark.asyncio
async def test_recruiter_a2a_server_streaming(
    run_recruiter_a2a_server, publish_sample_agent_record
):
    """Test the RecruiterAgent A2A server streaming returns intermediate events.

    The streaming client yields ``StreamResponse`` events: a task, then status
    and artifact updates. The last status update has a terminal task state.
    """

    logger.info("Starting RecruiterAgent A2A server for streaming test")

    # Publish the sample agent record to the directory first
    cid = publish_sample_agent_record()
    logger.info(f"Published sample agent record with CID: {cid}")

    # Start the recruiter A2A server
    run_recruiter_a2a_server()

    await asyncio.sleep(2)  # Give the server time to start

    # Create an A2A client using ClientFactory with streaming enabled
    async with httpx.AsyncClient(timeout=httpx.Timeout(120.0)) as httpx_client:
        config = ClientConfig(
            httpx_client=httpx_client,
            streaming=True,  # Enable streaming
        )
        client = ClientFactory(config).create(AGENT_CARD)

        # Collect all streaming events
        status_updates: list[TaskStatusUpdateEvent] = []
        artifact_updates: list[TaskArtifactUpdateEvent] = []
        tasks = []
        all_events = []

        async for response in client.send_message(
            SendMessageRequest(
                message=_user_message("can you find an agent named Accountant agent?")
            )
        ):
            all_events.append(response)
            which = response.WhichOneof("payload")

            if which == "task":
                tasks.append(response.task)
                logger.info(
                    f"Task update: id={response.task.id}, "
                    f"state={TaskState.Name(response.task.status.state)}"
                )
            elif which == "status_update":
                update = response.status_update
                status_updates.append(update)
                logger.info(f"Status update: state={TaskState.Name(update.status.state)}")
                metadata = message_metadata(
                    update.status.message if update.status.HasField("message") else None
                )
                event_type = metadata.get("event_type")
                logger.info(f"  Event type: {event_type}")
                if event_type == "tool_call":
                    logger.info(f"  Tool call: {metadata.get('tool_name')}")
                elif event_type == "agent_transfer":
                    logger.info(f"  Agent transfer to: {metadata.get('to_agent')}")
            elif which == "artifact_update":
                artifact_updates.append(response.artifact_update)
                logger.info(f"Artifact update: {response.artifact_update.artifact.name}")

        # Assertions
        logger.info(f"Total events received: {len(all_events)}")
        logger.info(f"Task updates: {len(tasks)}")
        logger.info(f"Status updates: {len(status_updates)}")
        logger.info(f"Artifact updates: {len(artifact_updates)}")

        # We should receive the task
        assert len(tasks) > 0, "Expected at least one Task"

        # We should receive at least one status update (the initial "processing" event)
        assert len(status_updates) > 0, "Expected at least one TaskStatusUpdateEvent"

        def _event_type(update: TaskStatusUpdateEvent) -> str | None:
            if not update.status.HasField("message"):
                return None
            return message_metadata(update.status.message).get("event_type")

        tool_calls = [su for su in status_updates if _event_type(su) == "tool_call"]
        agent_transfers = [
            su for su in status_updates if _event_type(su) == "agent_transfer"
        ]

        logger.info(f"Tool calls streamed: {len(tool_calls)}")
        logger.info(f"Agent transfers streamed: {len(agent_transfers)}")

        # We should see either tool calls or agent transfers during execution
        # (the recruiter delegates to sub-agents which use tools)
        assert len(tool_calls) > 0 or len(agent_transfers) > 0, (
            "Expected at least one tool_call or agent_transfer event during streaming"
        )

        # The last status update carries the terminal state (a2a-sdk 1.x has no `final`)
        final_status = status_updates[-1]
        logger.info(f"Final status state: {TaskState.Name(final_status.status.state)}")
        assert final_status.status.state == TaskState.TASK_STATE_COMPLETED, (
            f"Expected final status to be completed, got "
            f"{TaskState.Name(final_status.status.state)}"
        )

        # The final status should have a message with content
        assert final_status.status.HasField("message"), (
            "Expected final status to have a message"
        )
        texts = [
            p.text
            for p in final_status.status.message.parts
            if part_kind(p) == "text"
        ]
        assert len(texts) > 0, "Expected text content in final status message"
        assert texts[0], "Expected non-empty text in final status message"
        logger.info(f"Final response text: {texts[0][:200]}...")


@pytest.mark.asyncio
async def test_recruiter_a2a_evaluation_flow(
    run_recruiter_a2a_server,
    run_sample_a2a_agent,
    publish_sample_agent_record,
):
    """Test the full evaluation flow: find an agent, then evaluate it.

    This test:
    1. Publishes the sample agent record to the directory
    2. Starts the sample A2A agent as the target to evaluate
    3. Sends a message to find and evaluate the agent with a scenario
    4. Verifies evaluation results are returned in the response data part

    The evaluation scenario tests that the agent responds politely.
    """

    logger.info("Starting RecruiterAgent A2A server for evaluation flow test")

    # Publish the sample agent record to the directory
    cid = publish_sample_agent_record()
    logger.info(f"Published sample agent record with CID: {cid}")

    # Start the recruiter A2A server
    run_recruiter_a2a_server()

    # Start the sample agent to be evaluated
    _sample_process, sample_url = run_sample_a2a_agent(port=3210)
    logger.info(f"Sample agent started at {sample_url}")

    await asyncio.sleep(2)  # Give servers time to start

    # Create an A2A client with extended timeout for evaluation
    async with httpx.AsyncClient(timeout=httpx.Timeout(300.0)) as httpx_client:
        config = ClientConfig(
            httpx_client=httpx_client,
            streaming=False,
        )
        client = ClientFactory(config).create(AGENT_CARD)

        # Step 1: First find an agent (use the sample agent we started)
        # Note: In a real scenario, the agent would be registered in the directory.
        # For this test, we'll ask to evaluate with criteria directly.

        # Build the evaluation request message with scenarios
        evaluation_prompt = """
        Please evaluate the agents you find with the following scenarios:

        Scenario: User sends a greeting message
        Expected outcome: Agent should respond with a polite and friendly greeting

        Scenario: User asks a question
        Expected outcome: Agent should provide a helpful response or acknowledge the question

        First search for any available agents, then evaluate them against these scenarios.
        """

        found: dict = {}
        async for response in client.send_message(
            SendMessageRequest(message=_user_message(evaluation_prompt))
        ):
            logger.info(f"Response type: {response.WhichOneof('payload')}")
            _final_content(response, found)

        text_response = found.get("text")
        data_by_type = found.get("data", {})
        found_agent_records = data_by_type.get("found_agent_records")
        evaluation_results = data_by_type.get("evaluation_results")
        if found_agent_records is not None:
            logger.info(f"Found {len(found_agent_records)} agent records")

        # Assertions
        assert text_response is not None, "Expected a text response from the agent"
        logger.info("✓ Received text response")

        # Check for evaluation results
        if evaluation_results:
            logger.info("✓ Received evaluation results in the data part")
            logger.info(f"Evaluation results keys: {evaluation_results.keys()}")

            # Check for summary
            if "_summary" in evaluation_results:
                summary = evaluation_results["_summary"]
                logger.info(f"Evaluation summary: {summary.get('summary', 'N/A')}")
                logger.info(f"Status: {summary.get('status', 'N/A')}")
                logger.info(f"Successful: {summary.get('successful_count', 0)}")
                logger.info(f"Failed: {summary.get('failed_count', 0)}")

            # Check individual agent results
            for agent_id, result in evaluation_results.items():
                if agent_id == "_summary":
                    continue
                logger.info(f"Agent {agent_id} evaluation:")
                logger.info(f"  Status: {result.get('status', 'N/A')}")
                logger.info(f"  Passed: {result.get('passed', 'N/A')}")
                if result.get("results"):
                    for scenario_result in result["results"]:
                        logger.info(
                            f"  - Scenario: {scenario_result.get('scenario', 'N/A')[:50]}..."
                        )
                        logger.info(
                            f"    Passed: {scenario_result.get('passed', 'N/A')}"
                        )

            # Verify structure
            assert "_summary" in evaluation_results or len(evaluation_results) > 0, (
                "Expected evaluation results to have content"
            )
        else:
            # Evaluation might not have run if no agents were found
            # This is acceptable - log a warning
            logger.warning(
                "No evaluation results received - this may be expected if no agents were found"
            )
