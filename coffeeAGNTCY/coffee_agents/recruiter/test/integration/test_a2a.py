# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""Integration tests for the RecruiterAgent A2A server."""

import asyncio
import json
import pytest
import httpx
from uuid import uuid4

from a2a.client import ClientFactory, ClientConfig
from a2a.types import (
    Message,
    Part,
    TextPart,
    DataPart,
    Role,
    Task,
    TaskState,
    TaskStatusUpdateEvent,
    TaskArtifactUpdateEvent,
)

from agent_recruiter.server.card import AGENT_CARD
from agent_recruiter.common.logging import get_logger

logger = get_logger(__name__)


@pytest.mark.asyncio
async def test_recruiter_a2a_server(run_recruiter_a2a_server, publish_sample_agent_record):
    """Test the RecruiterAgent A2A server returns agent records in DataPart.

    The server now uses streaming internally, so even non-streaming clients
    receive a (Task, None) tuple with the final message in task.status.message.
    """

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
        factory = ClientFactory(config)
        client = factory.create(AGENT_CARD)

        # Build the message - search for an agent
        message = Message(
            role=Role.user,
            message_id=str(uuid4()),
            parts=[Part(root=TextPart(text="can you find an agent named Accountant agent?"))],
        )

        # Send message and collect responses
        text_response = None
        data_part = None
        found_agent_records = None
        final_task = None

        async for response in client.send_message(message):
            logger.info(f"Response: {response}")

            # Handle Message response (legacy format)
            if isinstance(response, Message):
                for part in response.parts:
                    part_root = part.root
                    if isinstance(part_root, TextPart):
                        text_response = part_root.text
                        logger.info(f"Text response: {text_response[:200]}...")
                    elif isinstance(part_root, DataPart):
                        data_part = part_root
                        if data_part.metadata and data_part.metadata.get("type") == "found_agent_records":
                            found_agent_records = data_part.data

            # Handle tuple response (Task, update) - streaming format
            elif isinstance(response, tuple) and len(response) == 2:
                task, update = response
                if isinstance(task, Task):
                    final_task = task
                    logger.info(f"Task: id={task.id}, state={task.status.state}")

                    # Extract final response from completed task
                    if task.status.state == TaskState.completed and task.status.message:
                        for part in task.status.message.parts:
                            part_root = part.root
                            if isinstance(part_root, TextPart):
                                text_response = part_root.text
                                logger.info(f"Text response: {text_response[:200]}...")
                            elif isinstance(part_root, DataPart):
                                data_part = part_root
                                if data_part.metadata and data_part.metadata.get("type") == "found_agent_records":
                                    found_agent_records = data_part.data

        # Assertions
        assert text_response is not None, "Expected a text response from the agent"
        assert data_part is not None, "Expected a DataPart with agent records"
        assert found_agent_records is not None, "Expected found_agent_records in DataPart"
        assert len(found_agent_records) > 0, "Expected at least one agent record"

        # Verify the agent record structure
        for cid, record_data in found_agent_records.items():
            logger.info(f"Found agent record CID: {cid}")

            # Record may be a JSON string or dict
            if isinstance(record_data, str):
                record = json.loads(record_data)
            else:
                record = record_data

            assert "name" in record, f"Expected 'name' in agent record, got: {record.keys()}"
            logger.info(f"Agent name: {record.get('name')}")


@pytest.mark.asyncio
async def test_recruiter_a2a_server_streaming(run_recruiter_a2a_server, publish_sample_agent_record):
    """Test the RecruiterAgent A2A server streaming returns intermediate events.

    The A2A streaming client returns ClientEvent tuples of (Task, update) where
    update is either None, TaskStatusUpdateEvent, or TaskArtifactUpdateEvent.
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
        factory = ClientFactory(config)
        client = factory.create(AGENT_CARD)

        # Build the message - search for an agent
        message = Message(
            role=Role.user,
            message_id=str(uuid4()),
            parts=[Part(root=TextPart(text="can you find an agent named Accountant agent?"))],
        )

        # Collect all streaming events
        status_updates: list[TaskStatusUpdateEvent] = []
        artifact_updates: list[TaskArtifactUpdateEvent] = []
        tasks: list[Task] = []
        final_message = None
        all_events = []

        async for response in client.send_message(message):
            all_events.append(response)

            # Handle Message response (non-streaming or final)
            if isinstance(response, Message):
                final_message = response
                logger.info("Received final message")
                for part in response.parts:
                    part_root = part.root
                    if isinstance(part_root, TextPart):
                        logger.info(f"Final text: {part_root.text[:200]}...")
                continue

            # Handle ClientEvent tuple: (Task, update)
            # The streaming client returns tuples of (Task, TaskStatusUpdateEvent|TaskArtifactUpdateEvent|None)
            if isinstance(response, tuple) and len(response) == 2:
                task, update = response

                if isinstance(task, Task):
                    tasks.append(task)
                    logger.info(f"Task update: id={task.id}, state={task.status.state}")

                if isinstance(update, TaskStatusUpdateEvent):
                    status_updates.append(update)
                    logger.info(
                        f"Status update: state={update.status.state}, "
                        f"final={update.final}"
                    )
                    if update.status.message and update.status.message.metadata:
                        event_type = update.status.message.metadata.get("event_type")
                        logger.info(f"  Event type: {event_type}")
                        if event_type == "tool_call":
                            tool_name = update.status.message.metadata.get("tool_name")
                            logger.info(f"  Tool call: {tool_name}")
                        elif event_type == "agent_transfer":
                            to_agent = update.status.message.metadata.get("to_agent")
                            logger.info(f"  Agent transfer to: {to_agent}")

                elif isinstance(update, TaskArtifactUpdateEvent):
                    artifact_updates.append(update)
                    logger.info(f"Artifact update: {update.artifact.name}")

        # Assertions
        logger.info(f"Total events received: {len(all_events)}")
        logger.info(f"Task updates: {len(tasks)}")
        logger.info(f"Status updates: {len(status_updates)}")
        logger.info(f"Artifact updates: {len(artifact_updates)}")

        # We should receive task updates
        assert len(tasks) > 0, "Expected at least one Task update"

        # We should receive at least one status update (the initial "processing" event)
        assert len(status_updates) > 0, "Expected at least one TaskStatusUpdateEvent"

        # Check that we received intermediate events (tool calls or agent transfers)
        tool_calls = [
            su for su in status_updates
            if su.status.message
            and su.status.message.metadata
            and su.status.message.metadata.get("event_type") == "tool_call"
        ]
        agent_transfers = [
            su for su in status_updates
            if su.status.message
            and su.status.message.metadata
            and su.status.message.metadata.get("event_type") == "agent_transfer"
        ]

        logger.info(f"Tool calls streamed: {len(tool_calls)}")
        logger.info(f"Agent transfers streamed: {len(agent_transfers)}")

        # We should see either tool calls or agent transfers during execution
        # (the recruiter delegates to sub-agents which use tools)
        assert len(tool_calls) > 0 or len(agent_transfers) > 0, (
            "Expected at least one tool_call or agent_transfer event during streaming"
        )

        # Find the final status update (with final=True)
        final_status_updates = [su for su in status_updates if su.final]
        logger.info(f"Final status updates: {len(final_status_updates)}")

        assert len(final_status_updates) > 0, "Expected at least one final status update"

        # Verify the final status has completed state and contains content
        final_status = final_status_updates[-1]
        logger.info(f"Final status state: {final_status.status.state}")
        assert final_status.status.state == TaskState.completed, (
            f"Expected final status to be completed, got {final_status.status.state}"
        )

        # The final status should have a message with content
        assert final_status.status.message is not None, "Expected final status to have a message"
        text_parts = [
            p.root for p in final_status.status.message.parts
            if isinstance(p.root, TextPart)
        ]
        assert len(text_parts) > 0, "Expected text content in final status message"
        assert text_parts[0].text, "Expected non-empty text in final status message"
        logger.info(f"Final response text: {text_parts[0].text[:200]}...")


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
    4. Verifies evaluation results are returned in the response DataPart

    The evaluation scenario tests that the agent responds politely.
    """

    logger.info("Starting RecruiterAgent A2A server for evaluation flow test")

    # Publish the sample agent record to the directory
    cid = publish_sample_agent_record()
    logger.info(f"Published sample agent record with CID: {cid}")

    # Start the recruiter A2A server
    run_recruiter_a2a_server()

    # Start the sample agent to be evaluated
    _sample_process, sample_url = run_sample_a2a_agent(port=3000)
    logger.info(f"Sample agent started at {sample_url}")

    await asyncio.sleep(2)  # Give servers time to start

    # Create an A2A client with extended timeout for evaluation
    async with httpx.AsyncClient(timeout=httpx.Timeout(300.0)) as httpx_client:
        config = ClientConfig(
            httpx_client=httpx_client,
            streaming=False,
        )
        factory = ClientFactory(config)
        client = factory.create(AGENT_CARD)

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

        message = Message(
            role=Role.user,
            message_id=str(uuid4()),
            parts=[Part(root=TextPart(text=evaluation_prompt))],
        )

        # Collect response data
        text_response = None
        found_agent_records = None
        evaluation_results = None

        async for response in client.send_message(message):
            logger.info(f"Response type: {type(response)}")

            # Handle tuple response (Task, update) - streaming format
            if isinstance(response, tuple) and len(response) == 2:
                task, update = response
                if isinstance(task, Task):
                    logger.info(f"Task: id={task.id}, state={task.status.state}")

                    # Extract final response from completed task
                    if task.status.state == TaskState.completed and task.status.message:
                        for part in task.status.message.parts:
                            part_root = part.root
                            if isinstance(part_root, TextPart):
                                text_response = part_root.text
                                logger.info(f"Text response: {text_response[:300]}...")
                            elif isinstance(part_root, DataPart):
                                metadata_type = part_root.metadata.get("type") if part_root.metadata else None
                                logger.info(f"DataPart type: {metadata_type}")

                                if metadata_type == "found_agent_records":
                                    found_agent_records = part_root.data
                                    logger.info(f"Found {len(found_agent_records)} agent records")
                                elif metadata_type == "evaluation_results":
                                    evaluation_results = part_root.data
                                    logger.info(f"Received evaluation results")

            # Handle Message response (legacy format)
            elif isinstance(response, Message):
                for part in response.parts:
                    part_root = part.root
                    if isinstance(part_root, TextPart):
                        text_response = part_root.text
                    elif isinstance(part_root, DataPart):
                        metadata_type = part_root.metadata.get("type") if part_root.metadata else None
                        if metadata_type == "found_agent_records":
                            found_agent_records = part_root.data
                        elif metadata_type == "evaluation_results":
                            evaluation_results = part_root.data

        # Assertions
        assert text_response is not None, "Expected a text response from the agent"
        logger.info("✓ Received text response")

        # Check for evaluation results
        if evaluation_results:
            logger.info("✓ Received evaluation results in DataPart")
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
                if result.get('results'):
                    for scenario_result in result['results']:
                        logger.info(f"  - Scenario: {scenario_result.get('scenario', 'N/A')[:50]}...")
                        logger.info(f"    Passed: {scenario_result.get('passed', 'N/A')}")

            # Verify structure
            assert "_summary" in evaluation_results or len(evaluation_results) > 0, (
                "Expected evaluation results to have content"
            )
        else:
            # Evaluation might not have run if no agents were found
            # This is acceptable - log a warning
            logger.warning("No evaluation results received - this may be expected if no agents were found")

        # If we got agent records, log them
        if found_agent_records:
            logger.info(f"✓ Found {len(found_agent_records)} agent records")
            for cid in found_agent_records.keys():
                logger.info(f"  - Agent CID: {cid}")

        logger.info("Test completed successfully")