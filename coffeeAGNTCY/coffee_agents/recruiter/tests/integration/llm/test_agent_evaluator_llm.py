# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""LLM integration tests for the agent_evaluator module."""

import pytest
from unittest.mock import MagicMock

from agent_recruiter.interviewers.agent_evaluator import evaluate_agents_tool


@pytest.fixture
def mock_tool_context():
    """Create a mock ToolContext for testing."""
    context = MagicMock()
    context.state = {}
    return context


class TestSampleAgentIntegration:
    """LLM integration tests using the sample A2A agent."""

    @pytest.mark.asyncio
    async def test_sample_agent_handles_message(self, run_sample_a2a_agent):
        """Test that the sample agent handles A2A messages correctly."""
        import httpx

        process, url = run_sample_a2a_agent()

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
                            "parts": [{"kind": "text", "text": "Hello, what can you do?"}],
                        },
                    },
                },
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
        process, url = run_sample_a2a_agent(port=3001)


class TestEvaluationIntegration:
    """Integration tests for the evaluation agent using ADK session/runner."""

    @pytest.mark.asyncio
    async def test_evaluate_sample_agent_with_adk_runner(
        self,
        run_sample_a2a_agent,
        sample_agent_card_json,
    ):
        from google.adk.runners import Runner
        from google.adk.sessions import InMemorySessionService
        from google.genai.types import Content, Part
        from agent_recruiter.interviewers.agent_evaluator import create_evaluation_agent

        process, url = run_sample_a2a_agent(port=3000)
        print(f"\n✅ Sample A2A agent running at {url}")

        agent_record_json = sample_agent_card_json(port=3000)

        evaluation_criteria = [
            {
                "scenario": "Ask the agent about its capabilities",
                "expected_outcome": "Agent should respond with information about what it can do",
            },
            {
                "scenario": "Send a simple greeting message",
                "expected_outcome": "Agent should acknowledge and respond appropriately",
            },
        ]

        eval_agent = create_evaluation_agent()
        print(f"✅ Created evaluation agent: {eval_agent.name}")

        session_service = InMemorySessionService()

        initial_state = {
            "found_agent_records": {
                "test-agent-1": agent_record_json,
            },
            "evaluation_criteria": evaluation_criteria,
        }

        session = await session_service.create_session(
            app_name="test_evaluator",
            user_id="test_user",
            session_id="test_session_1",
            state=initial_state,
        )
        print("✅ Created session with state populated")
        print(f"   - Agent records: {len(initial_state['found_agent_records'])}")
        print(f"   - Eval criteria: {len(initial_state['evaluation_criteria'])}")

        runner = Runner(
            app_name="test_evaluator",
            agent=eval_agent,
            session_service=session_service,
        )
        print("✅ Created runner")

        print("\n🚀 Running evaluation agent...")

        user_message = Content(
            parts=[Part(text="Please evaluate the agents using the criteria in state")],
            role="user",
        )

        events = []
        async for event in runner.run_async(
            user_id="test_user",
            session_id="test_session_1",
            new_message=user_message,
        ):
            events.append(event)
            print(f"📥 Event: {event.type if hasattr(event, 'type') else type(event).__name__}")

        print(f"✅ Evaluation completed with {len(events)} events")

        tool_results = []
        for event in events:
            if hasattr(event, "type") and "tool" in event.type.lower():
                tool_results.append(event)
            elif hasattr(event, "content"):
                content_str = str(event.content) if hasattr(event, "content") else ""
                if "status" in content_str and "results" in content_str:
                    tool_results.append(event)

        print(f"\n📊 Found {len(tool_results)} tool result events")

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
        process, url = run_sample_a2a_agent(port=3001)
        print(f"\n✅ Sample A2A agent running at {url}")

        agent_record_json = sample_agent_card_json(port=3001)

        mock_tool_context.state = {
            "found_agent_records": {
                "echo-agent-1": agent_record_json,
            },
            "evaluation_criteria": [
                {
                    "scenario": "Echo test - send 'Hello' message",
                    "expected_outcome": "Agent should respond to the message",
                },
            ],
        }

        print("\n🚀 Calling evaluate_agents_tool...")
        result = await evaluate_agents_tool(mock_tool_context)

        print("\n📊 Tool result:")
        print(f"   Status: {result['status']}")
        print(f"   Summary: {result['summary']}")

        assert result["status"] in ["success", "partial"], f"Expected success/partial but got {result['status']}"
        assert len(result["results"]) == 1, "Should have evaluated 1 agent"

        agent_result = result["results"][0]
        print("\n📊 Agent result:")
        print(f"   Agent ID: {agent_result['agent_id']}")
        print(f"   Status: {agent_result['status']}")

        if agent_result["status"] == "evaluated":
            print(f"   Passed: {agent_result['passed']}")
            print(f"   Summary: {agent_result['summary']}")
            print(f"   Scenarios tested: {len(agent_result['results'])}")
        elif agent_result["status"] == "error":
            print(f"   Error: {agent_result.get('error', 'Unknown error')}")

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
        process, url = run_sample_a2a_agent(port=3002)
        print(f"\n✅ Sample A2A agent running at {url}")

        agent_record_json = sample_agent_card_json(port=3002)

        mock_tool_context.state = {
            "found_agent_records": {
                "test-agent": agent_record_json,
            },
            "evaluation_criteria": [
                {
                    "scenario": "Scenario 1: Ask agent about its identity",
                    "expected_outcome": "Agent should respond with its name or description",
                },
                {
                    "scenario": "Scenario 2: Request help or capabilities",
                    "expected_outcome": "Agent should provide information about what it can do",
                },
                {
                    "scenario": "Scenario 3: Send a test message",
                    "expected_outcome": "Agent should acknowledge and respond",
                },
            ],
        }

        print(f"\n🚀 Testing {len(mock_tool_context.state['evaluation_criteria'])} scenarios...")
        result = await evaluate_agents_tool(mock_tool_context)

        print(f"\n📊 Results: {result['summary']}")
        assert result["status"] in ["success", "partial"]
        assert len(result["results"]) == 1

        agent_result = result["results"][0]
        if agent_result["status"] == "evaluated":
            print(
                f"   Scenarios: {len(agent_result['results'])}/"
                f"{len(mock_tool_context.state['evaluation_criteria'])}"
            )
            assert len(agent_result["results"]) == 3, "Should have 3 scenario results"

            for i, scenario_result in enumerate(agent_result["results"], 1):
                print(f"   {i}. {scenario_result['scenario'][:50]}... - Passed: {scenario_result['passed']}")

        print("\n✅ Test passed!")
