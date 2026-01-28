# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""Integration tests for the RecruiterAgent A2A server."""

import asyncio
import json
import pytest
import httpx
from uuid import uuid4

from a2a.client import ClientFactory, ClientConfig
from a2a.types import Message, Part, TextPart, DataPart, Role

from agent_recruiter.server.card import AGENT_CARD
from agent_recruiter.common.logging import get_logger

logger = get_logger(__name__)


@pytest.mark.asyncio
async def test_recruiter_a2a_server(run_recruiter_a2a_server):
    """Test the RecruiterAgent A2A server returns agent records in DataPart."""

    logger.info("Starting RecruiterAgent A2A server")

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

        async for response in client.send_message(message):
            logger.info(f"Response: {response}")

            if isinstance(response, Message):
                # Parse message parts
                for part in response.parts:
                    part_root = part.root
                    if isinstance(part_root, TextPart):
                        text_response = part_root.text
                        logger.info(f"Text response: {text_response[:200]}...")
                    elif isinstance(part_root, DataPart):
                        data_part = part_root
                        logger.info(f"Data part metadata: {data_part.metadata}")
                        logger.info(f"Data part data: {data_part.data}")

                        # Check if this is the found_agent_records data part
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