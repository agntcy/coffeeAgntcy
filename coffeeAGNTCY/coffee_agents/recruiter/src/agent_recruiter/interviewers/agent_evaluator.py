# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""
ADK-based agent for evaluating candidate agents during interviews.
"""

import os
import json
from typing import Any, Dict
from a2a.types import AgentCard
from agent_recruiter.common.logging import get_logger
from google.adk.tools.tool_context import ToolContext
from google.adk.tools.function_tool import FunctionTool
from google.adk.agents import Agent
from google.adk.models.lite_llm import LiteLlm
from google.genai.types import Content, Part
from rogue_sdk.types import (
    Scenario,
    ScenarioType,
    AuthType,
    Scenarios,
    Protocol,
    Transport
)

from agent_recruiter.interviewers.evaluator_agent_factory import get_evaluator_agent

logger = get_logger(__name__)

AGENT_INSTRUCTION = """You are an agent evaluator. Your job is to evaluate candidate agents based on user-provided criteria."""
LLM_MODEL = os.getenv("LLM_MODEL", "openai/gpt-4o")

def parse_agent_record(raw_json_str: str):
    """Parse raw JSON agent record into structured format.

    Args:
        raw_json: The raw JSON record of the agent

    Returns:
        Parsed agent record with key details
    """
    try:
        a2a_card = AgentCard.model_validate_json(raw_json_str)
        logger.info(f"Parsed AgentCard for agent: {a2a_card.name}")
        return a2a_card
    except Exception as e:
        logger.error(f"Failed to parse agent record: {e}")

    try:
        record_dict = json.loads(raw_json_str)
        return record_dict
    except json.JSONDecodeError as e:
        logger.error(f"JSON decoding error: {e}")
        return None

def extract_agent_info(raw_json_str: str) -> Dict[str, Any]:
    """Extract agent URL and protocol from raw JSON agent record.

    Uses defaults when information cannot be determined:
    - protocol: Protocol.A2A
    - transport: Transport.HTTP
    - auth_type: AuthType.NO_AUTH
    - auth_credentials: None

    Args:
        raw_json: The raw JSON record of the agent
    Returns:
        Dict containing:
        - protocol: The communication protocol
        - transport: The transport mechanism
        - evaluated_agent_url: The URL of the agent to evaluate
        - auth_type: The authentication type
        - auth_credentials: The authentication credentials
    Raises:
        ValueError: If agent URL cannot be extracted
    """
    parsed = parse_agent_record(raw_json_str)

    # Extract URL
    evaluated_agent_url = None
    if isinstance(parsed, AgentCard):
        evaluated_agent_url = parsed.url
    elif isinstance(parsed, dict):
        evaluated_agent_url = parsed.get("url") or parsed.get("service_url")

    if not evaluated_agent_url:
        raise ValueError("Cannot extract agent URL from record")

    # Determine protocol (default: A2A)
    protocol = Protocol.A2A
    if isinstance(parsed, dict):
        protocol_str = parsed.get("protocol", "a2a").upper()
        try:
            protocol = Protocol[protocol_str]
        except KeyError:
            logger.warning(f"Unknown protocol '{protocol_str}', defaulting to A2A")
            protocol = Protocol.A2A

    return {
        "protocol": protocol,
        "transport": Transport.HTTP,
        "evaluated_agent_url": evaluated_agent_url,
        "auth_type": AuthType.NO_AUTH,
        "auth_credentials": None,
    }


async def evaluate_agents_tool(tool_context: ToolContext) -> Dict[str, Any]:
    """Tool for evaluating candidate agents against policy scenarios.

    Reads from tool_context.state:
    - found_agent_records: Dict[str, str] - Agent records from registry
    - evaluation_criteria: List[Dict] - Scenarios with 'scenario' and 'expected_outcome'

    Returns:
        Dict with:
        - status: "success", "error", or "partial"
        - results: List of per-agent results
        - summary: Overall summary
    """
    logger.info("🎯 Starting agent evaluation tool")

    # Get state
    state = tool_context.state
    agent_records = state.get("found_agent_records", {})
    eval_criteria_raw = state.get("evaluation_criteria", [])

    # Validate inputs
    if not agent_records:
        return {
            "status": "error",
            "message": "No agent records found. Run registry search first.",
            "results": []
        }

    if not eval_criteria_raw:
        return {
            "status": "error",
            "message": "No evaluation criteria provided.",
            "results": []
        }

    # Convert evaluation criteria to Scenarios
    scenarios = []
    for criterion in eval_criteria_raw:
        scenario = Scenario(
            scenario_type=ScenarioType.POLICY,
            scenario=criterion.get("scenario", ""),
            expected_outcome=criterion.get("expected_outcome")
        )
        scenarios.append(scenario)

    scenarios_obj = Scenarios(scenarios=scenarios)
    business_context = "Agent evaluation for recruitment purposes"

    logger.info(
        f"📋 Evaluating {len(agent_records)} agents against {len(scenarios)} scenarios"
    )

    # Evaluate each agent
    all_results = []
    for agent_id, agent_json in agent_records.items():
        try:
            logger.info(f"🤖 Evaluating agent: {agent_id}")

            # Extract agent info with defaults
            agent_info = extract_agent_info(agent_json)

            # Get auth headers
            headers = agent_info["auth_type"].get_auth_header(
                agent_info["auth_credentials"]
            )

            # Create protocol-specific evaluator using factory
            evaluator = get_evaluator_agent(
                protocol=agent_info["protocol"],
                transport=agent_info["transport"],
                evaluated_agent_address=agent_info["evaluated_agent_url"],
                scenarios=scenarios_obj,
                business_context=business_context,
                headers=headers,
                debug=False,
                deep_test_mode=False,
            )

            # Run evaluation using evaluator's agent
            async with evaluator as eval_ctx:
                # Create temporary runner for this evaluation
                from google.adk.runners import Runner
                from google.adk.sessions import InMemorySessionService

                temp_session_service = InMemorySessionService()
                temp_runner = Runner(
                    app_name=f"evaluator_{agent_id}",
                    agent=evaluator.get_underlying_agent(),
                    session_service=temp_session_service,
                )

                # Create session
                session_id = f"eval_{agent_id}"
                user_id = "evaluator"
                _ = await temp_session_service.create_session(
                    app_name=f"evaluator_{agent_id}",
                    user_id=user_id,
                    session_id=session_id,
                    state={}
                )

                # Run the evaluator agent
                logger.info(f"🚀 Running evaluator for {agent_id}")
                start_message = Content(parts=[Part(text="start")], role="user")
                async for event in temp_runner.run_async(
                    user_id=user_id,
                    session_id=session_id,
                    new_message=start_message  # Trigger evaluation
                ):
                    # Process events (agent runs scenarios automatically)
                    pass

                # Get results
                results = evaluator.get_evaluation_results()

                all_results.append({
                    "agent_id": agent_id,
                    "status": "evaluated",
                    "passed": all(r.passed for r in results.results) if results.results else False,
                    "results": [
                        {
                            "scenario": r.scenario.scenario,
                            "passed": r.passed,
                            "conversations": len(r.conversations) if r.conversations else 0
                        }
                        for r in results.results
                    ] if results.results else [],
                    "summary": f"{sum(1 for r in results.results if r.passed)}/{len(results.results)} scenarios passed"
                })

                logger.info(
                    f"✅ Completed evaluation for {agent_id}: "
                    f"{all_results[-1]['summary']}"
                )

        except Exception as e:
            logger.exception(f"❌ Failed to evaluate agent {agent_id}")
            all_results.append({
                "agent_id": agent_id,
                "status": "error",
                "error": str(e)
            })

    # Calculate summary
    successful = sum(1 for r in all_results if r["status"] == "evaluated")
    failed = sum(1 for r in all_results if r["status"] == "error")

    return {
        "status": "success" if failed == 0 else "partial",
        "results": all_results,
        "summary": f"Evaluated {successful}/{len(agent_records)} agents successfully"
    }


def create_evaluation_agent() -> Agent:
    """Create the evaluation sub-agent with evaluation tool."""

    # Create tool
    eval_tool = FunctionTool(func=evaluate_agents_tool)

    agent = Agent(
        model=LiteLlm(model=LLM_MODEL),
        name="agent_evaluator",
        instruction=AGENT_INSTRUCTION,
        description="Agent for evaluating candidate agents based on user-defined scenarios.",
        tools=[eval_tool]
    )
    return agent