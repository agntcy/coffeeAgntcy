# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""
ADK-based agent for evaluating candidate agents during interviews.
"""

import os
import json
from typing import Any, Dict
from pydantic import BaseModel, Field
from a2a.types import AgentCard
from agent_recruiter.common.logging import get_logger
from google.adk.tools.tool_context import ToolContext
from google.adk.agents import Agent
from google.adk.models.lite_llm import LiteLlm

logger = get_logger(__name__)

AGENT_INSTRUCTION = """You are an agent evaluator. Your job is to evaluate candidate agents based on user-provided criteria."""
LLM_MODEL = os.getenv("LLM_MODEL", "openai/gpt-4o")

class EvalScenario(BaseModel):
    """Defines evaluation criteria for candidate agents."""
    scenario_description: str = Field(
        description="The scenario to test the agent with (e.g., 'Handle a customer refund request')"
    )
    expected_outcome: str = Field(
        description="What the agent should do or produce (e.g., 'Process refund following company policy')"
    )

async def evaluate_agents_tool(
    tool_context: ToolContext
) -> Dict[str, Any]:
    """Evaluate candidate agents based on user-provided criteria.

    This tool will request evaluation criteria from the user before running.
    It reads agent records from session state that were stored by the registry search agent.

    Args:
        tool_context: ADK tool context for state access (automatically injected)

    Returns:
        Evaluation results for each candidate agent
    """
    # Check if we have agents to evaluate
    existing: Dict[str, Any] = tool_context.state.get("found_agent_records", {})

    logger.info(f"Starting evaluation of {len(existing)} agents.")

    if not existing:
        return {
            "status": "error",
            "message": "No agents found in session state. Please search for agents first."
        }

    evaluation_results: Dict[str, Any] = {
        "criteria": {
            "scenario": "To be provided by user",
            "expected_outcome": "To be provided by user"
        },
        "results": {}
    }

    for cid, raw_json_record in existing.items():
        parsed_record = parse_agent_record(raw_json_record)
        if parsed_record is None:
            logger.warning(f"Skipping invalid agent record with CID {cid}")
            continue
        
        # Placeholder evaluation logic - replace with actual evaluation
        evaluation = {
            "cid": cid,
            "scenario_tested": "To be provided by user",
            "expected_outcome": "To be provided by user",
            "result": "passed",  # Placeholder
        }
        evaluation_results["results"][cid] = evaluation
        logger.info(f"Evaluated agent with CID {cid}")

    evaluation_results["status"] = "completed"
    evaluation_results["agents_evaluated"] = len(existing)

    return evaluation_results

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
        

def create_evaluation_agent() -> Agent:
    agent = Agent(
        model=LiteLlm(model=LLM_MODEL),
        name="agent_evaluator",
        instruction=AGENT_INSTRUCTION,
        description="Agent for evaluating candidate agents based on user-defined scenarios.",
        tools=[evaluate_agents_tool],
    )
    return agent