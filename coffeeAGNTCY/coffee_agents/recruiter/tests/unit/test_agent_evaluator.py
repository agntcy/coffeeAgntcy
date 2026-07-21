# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""Unit tests for agent_evaluator helpers and error paths (no Docker, no LLM)."""

import json
from unittest.mock import MagicMock

import pytest
from a2a.types import AgentCard, AgentProvider

from agent_recruiter.interviewers.agent_evaluator import (
    evaluate_agents_tool,
    extract_agent_info,
)
from agent_recruiter.interviewers.models import AgentEvalConfig
from rogue_sdk.types import Protocol, Transport


SAMPLE_AGENT_CARD_JSON = json.dumps({
    "name": "Test Agent",
    "description": "A test agent for evaluation",
    "url": "http://localhost:3000",
    "version": "1.0.0",
    "provider": {
        "organization": "Test Org",
        "url": "http://testorg.example.com",
    },
    "defaultInputModes": ["text"],
    "defaultOutputModes": ["text"],
    "capabilities": {
        "streaming": False,
        "pushNotifications": False,
    },
    "skills": [],
})


@pytest.fixture
def sample_agent_card() -> AgentCard:
    return AgentCard(
        name="Test Agent",
        description="A test agent for evaluation",
        url="http://localhost:3000",
        version="1.0.0",
        provider=AgentProvider(organization="Test Org", url="http://testorg.example.com"),
        defaultInputModes=["text"],
        defaultOutputModes=["text"],
        capabilities={"streaming": False, "pushNotifications": False},
        skills=[],
    )


@pytest.fixture
def mock_tool_context():
    context = MagicMock()
    context.state = {}
    return context


@pytest.fixture
def sample_agent_card_json():
    def _create(port: int = 3210):
        return json.dumps({
            "name": "TestAgent",
            "description": "A simple test agent for integration testing with basic tools.",
            "url": f"http://localhost:{port}",
            "version": "1.0.0",
            "provider": {
                "organization": "Test Org",
                "url": "http://testorg.example.com",
            },
            "defaultInputModes": ["text/plain"],
            "defaultOutputModes": ["text/plain"],
            "capabilities": {
                "streaming": True,
                "pushNotifications": False,
            },
            "skills": [],
        })

    return _create


class TestExtractAgentInfo:
    def test_extracts_valid_agent_card_json(self):
        result = extract_agent_info(SAMPLE_AGENT_CARD_JSON)

        assert result is not None
        assert isinstance(result, AgentEvalConfig)
        assert result.agent_name == "Test Agent"
        assert result.evaluated_agent_url == "http://localhost:3000"
        assert result.protocol == Protocol.A2A
        assert result.transport == Transport.HTTP

    def test_raises_for_invalid_json(self):
        with pytest.raises(ValueError):
            extract_agent_info("not valid json {{{")

    def test_raises_for_missing_url(self):
        bad_record = json.dumps({"name": "No URL Agent"})
        with pytest.raises(ValueError, match="url"):
            extract_agent_info(bad_record)


class TestEvaluateAgentsToolErrorHandling:
    @pytest.mark.asyncio
    async def test_error_handling_no_agent_records(self, mock_tool_context):
        mock_tool_context.state = {
            "found_agent_records": {},
            "evaluation_criteria": [
                {"scenario": "test", "expected_outcome": "pass"},
            ],
        }

        result = await evaluate_agents_tool(mock_tool_context)

        assert result["status"] == "error"
        assert "No agent records found" in result["message"]
        assert result["results"] == []

    @pytest.mark.asyncio
    async def test_error_handling_no_criteria(self, mock_tool_context, sample_agent_card_json):
        mock_tool_context.state = {
            "found_agent_records": {
                "agent1": sample_agent_card_json(),
            },
            "evaluation_criteria": [],
        }

        result = await evaluate_agents_tool(mock_tool_context)

        assert result["status"] == "error"
        assert "No evaluation criteria provided" in result["message"]
        assert result["results"] == []

    @pytest.mark.asyncio
    async def test_error_handling_invalid_agent_url(self, mock_tool_context):
        bad_agent_record = json.dumps({
            "name": "Bad Agent",
            "description": "Agent with no URL",
        })

        mock_tool_context.state = {
            "found_agent_records": {
                "bad-agent": bad_agent_record,
            },
            "evaluation_criteria": [
                {"scenario": "test", "expected_outcome": "pass"},
            ],
        }

        result = await evaluate_agents_tool(mock_tool_context)

        assert len(result["results"]) == 1
        assert result["results"][0]["status"] == "error"
        assert "url" in result["results"][0]["error"].lower()
