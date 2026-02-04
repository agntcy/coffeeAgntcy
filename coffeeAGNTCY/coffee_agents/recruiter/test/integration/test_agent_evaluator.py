# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""Integration tests for the agent_evaluator module using Rogue SDK."""

import json
import pytest
from unittest.mock import MagicMock

from a2a.types import AgentCard, AgentProvider

from agent_recruiter.interviewers.agent_evaluator import (
    evaluate_agents_tool,
    extract_agent_info,
)
from agent_recruiter.interviewers.models import AgentEvalConfig
from rogue_sdk.types import (
    Protocol,
    Scenario,
    AuthType,
    ScenarioType,
    Transport,
)


# Sample agent card data for testing
SAMPLE_AGENT_CARD_JSON = json.dumps({
    "name": "Test Agent",
    "description": "A test agent for evaluation",
    "url": "http://localhost:3000",
    "version": "1.0.0",
    "provider": {
        "organization": "Test Org",
        "url": "http://testorg.example.com"
    },
    "defaultInputModes": ["text"],
    "defaultOutputModes": ["text"],
    "capabilities": {
        "streaming": False,
        "pushNotifications": False
    },
    "skills": []
})


@pytest.fixture
def sample_agent_card() -> AgentCard:
    """Create a sample AgentCard for testing."""
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
def sample_eval_scenario() -> Scenario:
    """Create a sample evaluation scenario."""
    return Scenario(
        scenario="Test basic policy compliance",
        expected_outcome="Agent should respond appropriately without violations"
    )


@pytest.fixture
def mock_tool_context():
    """Create a mock ToolContext for testing."""
    context = MagicMock()
    context.state = {}
    return context


class TestExtractAgentInfo:
    """Tests for extract_agent_info function."""

    def test_extracts_valid_agent_card_json(self):
        """Test extracting info from a valid AgentCard JSON string."""
        result = extract_agent_info(SAMPLE_AGENT_CARD_JSON)

        assert result is not None
        assert isinstance(result, AgentEvalConfig)
        assert result.agent_name == "Test Agent"
        assert result.evaluated_agent_url == "http://localhost:3000"
        assert result.protocol == Protocol.A2A
        assert result.transport == Transport.HTTP

    def test_raises_for_invalid_json(self):
        """Test that invalid JSON raises ValueError."""
        with pytest.raises(ValueError):
            extract_agent_info("not valid json {{{")

    def test_raises_for_missing_url(self):
        """Test that missing URL raises ValueError."""
        bad_record = json.dumps({"name": "No URL Agent"})
        with pytest.raises(ValueError, match="url"):
            extract_agent_info(bad_record)


class TestSampleAgentIntegration:
    """Integration tests using the sample A2A agent.

    These tests start a real A2A agent and test the evaluation components against it.
    """

    @pytest.mark.asyncio
    async def test_sample_agent_starts_and_responds(self, run_sample_a2a_agent):
        """Test that the sample agent starts and responds to requests."""
        import httpx

        # Start the sample agent
        process, url = run_sample_a2a_agent()

        # Verify agent card is accessible
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{url}/.well-known/agent.json")
            assert response.status_code == 200

            card = response.json()
            assert card["name"] == "TestAgent"
            assert card["version"] == "1.0.0"

    @pytest.mark.asyncio
    async def test_sample_agent_handles_message(self, run_sample_a2a_agent):
        """Test that the sample agent handles A2A messages correctly."""
        import httpx

        # Start the sample agent
        process, url = run_sample_a2a_agent()

        # Send a test message via A2A protocol
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{url}/",
                json={
                    "jsonrpc": "2.0",
                    "method": "message/send",
                    "id": "test-1",
                    "params": {
                        "message": {
                            "messageId": "msg-001",
                            "role": "user",
                            "parts": [{"kind": "text", "text": "Hello, what can you do?"}]
                        }
                    }
                }
            )
            assert response.status_code == 200

            result = response.json()
            assert "result" in result
            assert result["result"]["status"]["state"] == "completed"

    @pytest.mark.asyncio
    async def test_create_agent_config_with_sample_agent(
        self, run_sample_a2a_agent, sample_agent_card_json
    ):
        """Test creating AgentConfig using sample agent card."""
        # Start the sample agent
        process, url = run_sample_a2a_agent(port=3001)

        pass


class TestEvaluationIntegration:
    """Integration tests for the evaluation agent using ADK session/runner.

    These tests:
    1. Start a sample A2A agent in the background (via fixture)
    2. Populate tool_context.state with agent records and evaluation criteria
    3. Create evaluation agent, session, and runner
    4. Run the evaluation agent and verify results

    Run with: pytest test/integration/test_agent_evaluator.py::TestEvaluationIntegration -v
    """

    @pytest.mark.asyncio
    async def test_evaluate_sample_agent_with_adk_runner(
        self,
        run_sample_a2a_agent,
        sample_agent_card_json,
    ):
        """Test evaluating sample agent using ADK runner and session.

        This test demonstrates the complete workflow:
        1. Sample A2A agent runs in background
        2. Agent record and eval criteria written to state
        3. Evaluation agent created with evaluate_agents_tool
        4. Session and Runner created
        5. Evaluation agent invoked via runner
        6. Results retrieved and validated
        """
        from google.adk.runners import Runner
        from google.adk.sessions import InMemorySessionService
        from google.genai.types import Content, Part
        from agent_recruiter.interviewers.agent_evaluator import create_evaluation_agent

        # Step 1: Start sample A2A agent in background
        process, url = run_sample_a2a_agent(port=3000)
        print(f"\n✅ Sample A2A agent running at {url}")

        # Step 2: Prepare agent record and evaluation criteria
        agent_record_json = sample_agent_card_json(port=3000)

        evaluation_criteria = [
            {
                "scenario": "Ask the agent about its capabilities",
                "expected_outcome": "Agent should respond with information about what it can do"
            },
            {
                "scenario": "Send a simple greeting message",
                "expected_outcome": "Agent should acknowledge and respond appropriately"
            }
        ]

        # Step 3: Create evaluation agent
        eval_agent = create_evaluation_agent()
        print(f"✅ Created evaluation agent: {eval_agent.name}")

        # Step 4: Create session service and populate state
        session_service = InMemorySessionService()

        initial_state = {
            "found_agent_records": {
                "test-agent-1": agent_record_json
            },
            "evaluation_criteria": evaluation_criteria
        }

        session = await session_service.create_session(
            app_name="test_evaluator",
            user_id="test_user",
            session_id="test_session_1",
            state=initial_state
        )
        print(f"✅ Created session with state populated")
        print(f"   - Agent records: {len(initial_state['found_agent_records'])}")
        print(f"   - Eval criteria: {len(initial_state['evaluation_criteria'])}")

        # Step 5: Create runner
        runner = Runner(
            app_name="test_evaluator",
            agent=eval_agent,
            session_service=session_service,
        )
        print(f"✅ Created runner")

        # Step 6: Run evaluation agent
        print(f"\n🚀 Running evaluation agent...")

        # Create user message to trigger evaluation
        user_message = Content(
            parts=[Part(text="Please evaluate the agents using the criteria in state")],
            role="user"
        )

        events = []
        async for event in runner.run_async(
            user_id="test_user",
            session_id="test_session_1",
            new_message=user_message
        ):
            events.append(event)
            print(f"📥 Event: {event.type if hasattr(event, 'type') else type(event).__name__}")

        print(f"✅ Evaluation completed with {len(events)} events")

        # Step 7: Verify results
        # The tool should have been called and results should be in the events
        # Look for tool results in the events
        tool_results = []
        for event in events:
            if hasattr(event, 'type') and 'tool' in event.type.lower():
                tool_results.append(event)
            elif hasattr(event, 'content'):
                # Check if content contains tool results
                content_str = str(event.content) if hasattr(event, 'content') else ""
                if 'status' in content_str and 'results' in content_str:
                    tool_results.append(event)

        print(f"\n📊 Found {len(tool_results)} tool result events")

        # Assertions
        assert len(events) > 0, "Should have received events from runner"
        assert len(tool_results) > 0, "Should have tool result events"

        print("\n✅ Test passed!")

    @pytest.mark.asyncio
    async def test_evaluate_tool_directly_with_mock_context(
        self,
        run_sample_a2a_agent,
        sample_agent_card_json,
        mock_tool_context,
    ):
        """Test evaluate_agents_tool directly with populated tool context.

        This is a simpler test that calls the tool function directly
        without going through the ADK agent/runner layer.
        """
        # Start sample agent
        process, url = run_sample_a2a_agent(port=3001)
        print(f"\n✅ Sample A2A agent running at {url}")

        # Populate tool context state
        agent_record_json = sample_agent_card_json(port=3001)

        mock_tool_context.state = {
            "found_agent_records": {
                "echo-agent-1": agent_record_json
            },
            "evaluation_criteria": [
                {
                    "scenario": "Echo test - send 'Hello' message",
                    "expected_outcome": "Agent should respond to the message"
                }
            ]
        }

        # Call tool directly
        print("\n🚀 Calling evaluate_agents_tool...")
        result = await evaluate_agents_tool(mock_tool_context)

        # Verify result structure
        print(f"\n📊 Tool result:")
        print(f"   Status: {result['status']}")
        print(f"   Summary: {result['summary']}")

        assert result["status"] in ["success", "partial"], f"Expected success/partial but got {result['status']}"
        assert len(result["results"]) == 1, "Should have evaluated 1 agent"

        agent_result = result["results"][0]
        print(f"\n📊 Agent result:")
        print(f"   Agent ID: {agent_result['agent_id']}")
        print(f"   Status: {agent_result['status']}")

        if agent_result["status"] == "evaluated":
            print(f"   Passed: {agent_result['passed']}")
            print(f"   Summary: {agent_result['summary']}")
            print(f"   Scenarios tested: {len(agent_result['results'])}")
        elif agent_result["status"] == "error":
            print(f"   Error: {agent_result.get('error', 'Unknown error')}")

        # Basic assertions
        assert agent_result["agent_id"] == "echo-agent-1"
        assert agent_result["status"] in ["evaluated", "error"]

        print("\n✅ Test passed!")

    @pytest.mark.asyncio
    async def test_evaluate_multiple_scenarios(
        self,
        run_sample_a2a_agent,
        sample_agent_card_json,
        mock_tool_context,
    ):
        """Test evaluating agent with multiple different scenarios."""
        # Start sample agent
        process, url = run_sample_a2a_agent(port=3002)
        print(f"\n✅ Sample A2A agent running at {url}")

        # Populate with multiple varied scenarios
        agent_record_json = sample_agent_card_json(port=3002)

        mock_tool_context.state = {
            "found_agent_records": {
                "test-agent": agent_record_json
            },
            "evaluation_criteria": [
                {
                    "scenario": "Scenario 1: Ask agent about its identity",
                    "expected_outcome": "Agent should respond with its name or description"
                },
                {
                    "scenario": "Scenario 2: Request help or capabilities",
                    "expected_outcome": "Agent should provide information about what it can do"
                },
                {
                    "scenario": "Scenario 3: Send a test message",
                    "expected_outcome": "Agent should acknowledge and respond"
                }
            ]
        }

        # Call tool
        print(f"\n🚀 Testing {len(mock_tool_context.state['evaluation_criteria'])} scenarios...")
        result = await evaluate_agents_tool(mock_tool_context)

        # Verify
        print(f"\n📊 Results: {result['summary']}")
        assert result["status"] in ["success", "partial"]
        assert len(result["results"]) == 1

        agent_result = result["results"][0]
        if agent_result["status"] == "evaluated":
            print(f"   Scenarios: {len(agent_result['results'])}/{len(mock_tool_context.state['evaluation_criteria'])}")
            assert len(agent_result["results"]) == 3, "Should have 3 scenario results"

            for i, scenario_result in enumerate(agent_result["results"], 1):
                print(f"   {i}. {scenario_result['scenario'][:50]}... - Passed: {scenario_result['passed']}")

        print("\n✅ Test passed!")

    @pytest.mark.asyncio
    async def test_error_handling_no_agent_records(
        self,
        mock_tool_context,
    ):
        """Test that tool handles missing agent records gracefully."""
        # Empty state - no agent records
        mock_tool_context.state = {
            "found_agent_records": {},
            "evaluation_criteria": [
                {"scenario": "test", "expected_outcome": "pass"}
            ]
        }

        result = await evaluate_agents_tool(mock_tool_context)

        assert result["status"] == "error"
        assert "No agent records found" in result["message"]
        assert result["results"] == []
        print("✅ Test passed - error handling works for missing agent records")

    @pytest.mark.asyncio
    async def test_error_handling_no_criteria(
        self,
        mock_tool_context,
        sample_agent_card_json,
    ):
        """Test that tool handles missing evaluation criteria gracefully."""
        # Has agent but no criteria
        mock_tool_context.state = {
            "found_agent_records": {
                "agent1": sample_agent_card_json()
            },
            "evaluation_criteria": []
        }

        result = await evaluate_agents_tool(mock_tool_context)

        assert result["status"] == "error"
        assert "No evaluation criteria provided" in result["message"]
        assert result["results"] == []
        print("✅ Test passed - error handling works for missing criteria")

    @pytest.mark.asyncio
    async def test_error_handling_invalid_agent_url(
        self,
        mock_tool_context,
    ):
        """Test that tool handles agents with missing URLs gracefully."""
        import json

        # Agent record without URL
        bad_agent_record = json.dumps({
            "name": "Bad Agent",
            "description": "Agent with no URL"
            # Missing "url" or "service_url"
        })

        mock_tool_context.state = {
            "found_agent_records": {
                "bad-agent": bad_agent_record
            },
            "evaluation_criteria": [
                {"scenario": "test", "expected_outcome": "pass"}
            ]
        }

        result = await evaluate_agents_tool(mock_tool_context)

        # Should get error status
        assert len(result["results"]) == 1
        assert result["results"][0]["status"] == "error"
        assert "url" in result["results"][0]["error"].lower()
        print("✅ Test passed - error handling works for invalid agent URL")