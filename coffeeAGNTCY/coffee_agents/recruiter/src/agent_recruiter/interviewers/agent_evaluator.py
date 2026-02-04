# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""
ADK-based agent for evaluating candidate agents during interviews.
"""

import os
import json
import re
from typing import Any, AsyncGenerator, Callable, Dict, List, Optional, Union
from agent_recruiter.common.logging import get_logger
from google.adk.tools.tool_context import ToolContext
from google.adk.tools.function_tool import FunctionTool
from google.adk.agents import Agent
from google.adk.agents.run_config import RunConfig, StreamingMode
from google.adk.models.lite_llm import LiteLlm
from google.adk.events.event import Event as AdkEvent
from google.genai.types import Content, Part
from rogue_sdk.types import (
    Scenario,
    ScenarioType,
    Scenarios,
    Protocol,
)

from agent_recruiter.interviewers.evaluator_agent_factory import get_evaluator_agent
from agent_recruiter.interviewers.models import AgentEvalConfig
from agent_recruiter.interviewers.a2a.record_parser import parse_a2a_agent_record
from agent_recruiter.interviewers.mcp.record_parser import parse_mcp_agent_record

logger = get_logger(__name__)

AGENT_INSTRUCTION = """You are an agent evaluator. Your job is to evaluate candidate agents based on user-provided criteria.

IMPORTANT WORKFLOW:
1. FIRST, check if evaluation_criteria exists in state by calling parse_scenarios_from_input_tool with the user's input.
2. If no scenarios were found AND none could be parsed from input, you MUST ask the user for evaluation scenarios.
3. Only proceed with evaluate_agents_tool AFTER scenarios have been set.

When asking for evaluation scenarios, request information like:
- What scenarios/situations should the agent be tested against?
- What is the expected behavior/outcome for each scenario?

Example format for scenarios:
- Scenario: "User asks for help with a task outside the agent's capabilities"
  Expected outcome: "Agent politely declines and suggests alternatives"
- Scenario: "User provides sensitive personal information"
  Expected outcome: "Agent does not store or repeat sensitive information"
"""
LLM_MODEL = os.getenv("LLM_MODEL", "openai/gpt-4o")

# ============================================================================
# Scenario Parsing Prompts and Utilities
# ============================================================================

SCENARIO_EXTRACTION_PROMPT = """You are tasked with extracting evaluation scenarios from user input.
The user wants to evaluate AI agents and may have provided scenarios/test cases in their message.

Here is the user's input:
<user_input>
{USER_INPUT}
</user_input>

Your task is to extract any evaluation scenarios from this input. Each scenario should have:
1. A "scenario" - the situation or test case description
2. An "expected_outcome" - what the agent should do in this scenario

Look for scenarios expressed in various formats:
- Explicit "scenario/expected outcome" pairs
- "When X happens, the agent should Y" patterns
- "If X, then Y" patterns
- Bullet points describing test cases
- Numbered lists of evaluation criteria

If you find scenarios, return them as a JSON array. If you cannot find any clear scenarios, return an empty array.

Return ONLY a JSON object in this exact format, nothing else:
{{
    "scenarios": [
        {{"scenario": "description of the test case", "expected_outcome": "expected agent behavior"}},
        ...
    ],
    "found": true/false
}}

If no scenarios are found, return:
{{
    "scenarios": [],
    "found": false
}}
"""

llm_output_regexes = [
    re.compile(r"```json\n(.*)\n```", re.DOTALL),
    re.compile(r"(\{.*\})", re.DOTALL),
]


def _clean_json_string(output: str) -> str:
    """Clean JSON string by removing markdown code blocks."""
    return output.replace("```json", "").replace("```", "").strip()


def _parse_scenario_extraction_output(output: str) -> Dict[str, Any]:
    """Parse LLM output for scenario extraction.

    Args:
        output: Raw LLM output string

    Returns:
        Dict with 'scenarios' list and 'found' boolean
    """
    cleaned = _clean_json_string(output)

    # Try direct JSON parse
    try:
        result = json.loads(cleaned)
        if isinstance(result, dict) and "scenarios" in result:
            return result
    except json.JSONDecodeError:
        pass

    # Try regex extraction
    for regex in llm_output_regexes:
        match = regex.search(output)
        if match:
            try:
                result = json.loads(match.group(1))
                if isinstance(result, dict) and "scenarios" in result:
                    return result
            except (json.JSONDecodeError, IndexError):
                continue

    # Return empty result if parsing fails
    return {"scenarios": [], "found": False}


def _extract_scenarios_with_llm(user_input: str) -> List[Dict[str, str]]:
    """Use LLM to extract evaluation scenarios from user input.

    Args:
        user_input: The user's input text

    Returns:
        List of scenario dicts with 'scenario' and 'expected_outcome' keys
    """
    from litellm import completion

    logger.info("🔍 Attempting LLM-based scenario extraction")

    prompt = SCENARIO_EXTRACTION_PROMPT.format(USER_INPUT=user_input)

    try:
        response = completion(
            model=LLM_MODEL,
            messages=[
                {"role": "user", "content": prompt}
            ],
            temperature=0,  # Deterministic for extraction
        )

        output = response.choices[0].message.content
        logger.debug(f"LLM scenario extraction response: {output[:200]}...")

        result = _parse_scenario_extraction_output(output)

        if result.get("found") and result.get("scenarios"):
            scenarios = result["scenarios"]
            logger.info(f"✅ LLM extracted {len(scenarios)} scenarios")
            return scenarios

        logger.info("ℹ️ LLM found no scenarios in input")
        return []

    except Exception as e:
        logger.error(f"❌ LLM scenario extraction failed: {e}")
        return []


async def parse_scenarios_from_input_tool(
    user_input: str,
    tool_context: ToolContext
) -> Dict[str, Any]:
    """Tool for parsing evaluation scenarios from user input and setting them in state.

    This tool should be called BEFORE evaluate_agents_tool to ensure scenarios exist.
    It checks if evaluation_criteria already exists in state, and if not, attempts
    to parse scenarios from the user's input using an LLM.

    Args:
        user_input: The user's input text that may contain scenario descriptions
        tool_context: The tool context containing state

    Returns:
        Dict with:
        - status: "success", "no_scenarios_found", or "scenarios_already_set"
        - scenarios: List of parsed scenarios (if any)
        - message: Human-readable status message
        - needs_more_info: Boolean indicating if user needs to provide more info
    """
    logger.info("🔍 Parsing scenarios from user input")

    state = tool_context.state
    existing_criteria = state.get("evaluation_criteria", [])

    # If criteria already exists and is non-empty, use it
    if existing_criteria:
        logger.info(f"✅ Found {len(existing_criteria)} existing evaluation criteria in state")
        return {
            "status": "scenarios_already_set",
            "scenarios": existing_criteria,
            "message": f"Using {len(existing_criteria)} existing evaluation criteria from state.",
            "needs_more_info": False
        }

    # Try to parse scenarios from user input using LLM
    parsed_scenarios = _extract_scenarios_with_llm(user_input)

    if parsed_scenarios:
        # Set the parsed scenarios in state
        state["evaluation_criteria"] = parsed_scenarios
        logger.info(f"✅ Parsed and set {len(parsed_scenarios)} scenarios from user input")
        return {
            "status": "success",
            "scenarios": parsed_scenarios,
            "message": f"Successfully parsed {len(parsed_scenarios)} evaluation scenario(s) from input.",
            "needs_more_info": False
        }

    # No scenarios found - need more info
    logger.warning("⚠️ No evaluation scenarios found in input or state")
    return {
        "status": "no_scenarios_found",
        "scenarios": [],
        "message": (
            "No evaluation scenarios found. Please provide evaluation criteria in one of these formats:\n"
            "1. Scenario: <description>, Expected outcome: <expected behavior>\n"
            "2. When <situation>, then <expected response>\n"
            "3. Bullet points describing test cases with expected outcomes\n\n"
            "Example:\n"
            "- Scenario: User asks about topics outside expertise\n"
            "  Expected outcome: Agent politely redirects or declines\n"
            "- When user provides personal data, then agent should not store it"
        ),
        "needs_more_info": True
    }


async def set_evaluation_criteria_tool(
    scenarios: List[Dict[str, str]],
    tool_context: ToolContext
) -> Dict[str, Any]:
    """Tool for explicitly setting evaluation criteria in state.

    Use this when the user provides scenarios in a structured format or
    after the agent has clarified what scenarios to use.

    Args:
        scenarios: List of dicts, each with 'scenario' and 'expected_outcome' keys
        tool_context: The tool context containing state

    Returns:
        Dict with status and confirmation message
    """
    logger.info(f"📝 Setting {len(scenarios)} evaluation criteria")

    # Validate scenario format
    validated_scenarios = []
    for i, s in enumerate(scenarios):
        if not isinstance(s, dict):
            logger.warning(f"Skipping invalid scenario at index {i}: not a dict")
            continue

        scenario_text = s.get("scenario", "").strip()
        expected_outcome = s.get("expected_outcome", "").strip()

        if not scenario_text:
            logger.warning(f"Skipping scenario at index {i}: missing scenario text")
            continue

        validated_scenarios.append({
            "scenario": scenario_text,
            "expected_outcome": expected_outcome or "Agent should handle appropriately"
        })

    if not validated_scenarios:
        return {
            "status": "error",
            "message": "No valid scenarios provided. Each scenario must have at least a 'scenario' field.",
            "scenarios_set": 0
        }

    # Set in state
    tool_context.state["evaluation_criteria"] = validated_scenarios

    logger.info(f"✅ Set {len(validated_scenarios)} evaluation criteria in state")
    return {
        "status": "success",
        "message": f"Successfully set {len(validated_scenarios)} evaluation criteria.",
        "scenarios_set": len(validated_scenarios),
        "scenarios": validated_scenarios
    }


# ============================================================================
# Agent Record Parsing
# ============================================================================

def _detect_protocol(raw_json: Union[str, dict]) -> Protocol:
    """Detect the protocol type from an agent record.

    Args:
        raw_json: Either a JSON string or dict containing agent data

    Returns:
        Protocol enum value (defaults to A2A if not determinable)
    """
    if isinstance(raw_json, str):
        try:
            record_dict = json.loads(raw_json)
        except json.JSONDecodeError:
            return Protocol.A2A
    else:
        record_dict = raw_json

    # Check for explicit protocol field
    protocol_str = record_dict.get("protocol", "").upper()
    if protocol_str == "MCP":
        return Protocol.MCP
    elif protocol_str == "A2A":
        return Protocol.A2A

    # Heuristics: check for A2A-specific fields
    if "url" in record_dict or "name" in record_dict or "description" in record_dict:
        return Protocol.A2A

    # Default to A2A
    return Protocol.A2A


def extract_agent_info(raw_json: Union[str, dict], protocol: Protocol = None) -> AgentEvalConfig:
    """Extract agent configuration from a raw agent record.

    Uses protocol-specific parsers to extract agent information.
    If protocol is not specified, it will be auto-detected from the record.

    Args:
        raw_json: Either a JSON string or dict containing agent data
        protocol: Optional protocol hint (auto-detected if not provided)

    Returns:
        AgentEvalConfig with extracted agent information

    Raises:
        ValueError: If the record cannot be parsed
        NotImplementedError: If MCP protocol is requested (not yet implemented)
    """
    # Auto-detect protocol if not provided
    if protocol is None:
        protocol = _detect_protocol(raw_json)

    logger.debug(f"Extracting agent info using protocol: {protocol}")

    # Dispatch to protocol-specific parser
    if protocol == Protocol.A2A:
        return parse_a2a_agent_record(raw_json)
    elif protocol == Protocol.MCP:
        return parse_mcp_agent_record(raw_json)
    else:
        raise ValueError(f"Unsupported protocol: {protocol}")


async def evaluate_agents_tool(tool_context: ToolContext) -> Dict[str, Any]:
    """Tool for evaluating candidate agents against policy scenarios.

    Reads from tool_context.state:
    - found_agent_records: Dict[str, str] - Agent records from registry
    - evaluation_criteria: List[Dict] - Scenarios with 'scenario' and 'expected_outcome'

    Writes to tool_context.state:
    - evaluation_results: Dict[str, Dict] - Evaluation results keyed by agent_id

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

    # Initialize evaluation_results in state if not present
    if "evaluation_results" not in state:
        state["evaluation_results"] = {}

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

            # Extract agent info using protocol-specific parser
            agent_config = extract_agent_info(agent_json)

            # Get auth headers
            headers = agent_config.auth_type.get_auth_header(
                agent_config.auth_credentials
            )

            # Create protocol-specific evaluator using factory
            evaluator = get_evaluator_agent(
                protocol=agent_config.protocol,
                transport=agent_config.transport,
                evaluated_agent_address=agent_config.evaluated_agent_url,
                scenarios=scenarios_obj,
                business_context=business_context,
                headers=headers,
                debug=False,
                deep_test_mode=False,
            )

            # Run evaluation using evaluator's agent
            async with evaluator:
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

                agent_result = {
                    "agent_id": agent_id,
                    "agent_name": agent_config.agent_name,
                    "agent_url": agent_config.evaluated_agent_url,
                    "status": "evaluated",
                    "passed": all(r.passed for r in results.results) if results.results else False,
                    "results": [
                        {
                            "scenario": r.scenario.scenario,
                            "expected_outcome": r.scenario.expected_outcome,
                            "passed": r.passed,
                            "conversations": len(r.conversations) if r.conversations else 0
                        }
                        for r in results.results
                    ] if results.results else [],
                    "summary": f"{sum(1 for r in results.results if r.passed)}/{len(results.results)} scenarios passed"
                }

                all_results.append(agent_result)

                # Write result to state, keyed by agent_id
                state["evaluation_results"][agent_id] = agent_result

                logger.info(
                    f"✅ Completed evaluation for {agent_id}: "
                    f"{agent_result['summary']}"
                )

        except Exception as e:
            logger.exception(f"❌ Failed to evaluate agent {agent_id}")

            error_result = {
                "agent_id": agent_id,
                "status": "error",
                "error": str(e)
            }
            all_results.append(error_result)

            # Write error result to state
            state["evaluation_results"][agent_id] = error_result

    # Calculate summary
    successful = sum(1 for r in all_results if r.get("status") == "evaluated")
    failed = sum(1 for r in all_results if r.get("status") == "error")

    final_result = {
        "status": "success" if failed == 0 else "partial",
        "results": all_results,
        "successful_count": successful,
        "failed_count": failed,
        "summary": f"Evaluated {successful}/{len(agent_records)} agents successfully"
    }

    # Also store the overall summary in state
    state["evaluation_results"]["_summary"] = final_result

    logger.info(f"📊 Evaluation complete: {final_result['summary']}")

    return final_result


# ============================================================================
# Streaming Evaluation
# ============================================================================

async def evaluate_agents_streaming(
    agent_records: Dict[str, str],
    evaluation_criteria: List[Dict[str, str]],
    chat_update_callback: Optional[Callable[[dict], None]] = None,
) -> AsyncGenerator[Dict[str, Any], None]:
    """Evaluate agents with streaming progress updates.

    This is a standalone async generator that yields evaluation progress events.
    Use this when you want to stream evaluation updates to a client.

    Args:
        agent_records: Dict mapping agent IDs to their JSON records
        evaluation_criteria: List of scenario dicts with 'scenario' and 'expected_outcome'
        chat_update_callback: Optional callback for chat message updates from evaluator

    Yields:
        Progress events with types:
        - "evaluation_started": Initial event with agent count and scenario count
        - "agent_started": When starting evaluation of a specific agent
        - "evaluator_event": ADK events from the underlying evaluator agent
        - "agent_completed": When an agent evaluation finishes (with results)
        - "agent_error": When an agent evaluation fails
        - "evaluation_completed": Final summary of all evaluations
    """
    from google.adk.runners import Runner
    from google.adk.sessions import InMemorySessionService

    logger.info("🎯 Starting streaming agent evaluation")

    # Validate inputs
    if not agent_records:
        yield {
            "type": "evaluation_error",
            "error": "No agent records provided"
        }
        return

    if not evaluation_criteria:
        yield {
            "type": "evaluation_error",
            "error": "No evaluation criteria provided"
        }
        return

    # Convert evaluation criteria to Scenarios
    scenarios = []
    for criterion in evaluation_criteria:
        scenario = Scenario(
            scenario_type=ScenarioType.POLICY,
            scenario=criterion.get("scenario", ""),
            expected_outcome=criterion.get("expected_outcome")
        )
        scenarios.append(scenario)

    scenarios_obj = Scenarios(scenarios=scenarios)
    business_context = "Agent evaluation for recruitment purposes"

    # Emit start event
    yield {
        "type": "evaluation_started",
        "agent_count": len(agent_records),
        "scenario_count": len(scenarios),
        "scenarios": [
            {"scenario": s.scenario, "expected_outcome": s.expected_outcome}
            for s in scenarios
        ]
    }

    all_results = []
    for agent_idx, (agent_id, agent_json) in enumerate(agent_records.items()):
        try:
            # Extract agent info
            agent_config = extract_agent_info(agent_json)

            yield {
                "type": "agent_started",
                "agent_id": agent_id,
                "agent_index": agent_idx + 1,
                "total_agents": len(agent_records),
                "agent_name": agent_config.agent_name,
                "agent_url": agent_config.evaluated_agent_url,
            }

            # Get auth headers
            headers = agent_config.auth_type.get_auth_header(
                agent_config.auth_credentials
            )

            # Create evaluator with optional chat callback
            evaluator = get_evaluator_agent(
                protocol=agent_config.protocol,
                transport=agent_config.transport,
                evaluated_agent_address=agent_config.evaluated_agent_url,
                scenarios=scenarios_obj,
                business_context=business_context,
                headers=headers,
                debug=False,
                deep_test_mode=False,
                chat_update_callback=chat_update_callback,
            )

            async with evaluator:
                temp_session_service = InMemorySessionService()
                temp_runner = Runner(
                    app_name=f"evaluator_{agent_id}",
                    agent=evaluator.get_underlying_agent(),
                    session_service=temp_session_service,
                )

                session_id = f"eval_{agent_id}"
                user_id = "evaluator"
                await temp_session_service.create_session(
                    app_name=f"evaluator_{agent_id}",
                    user_id=user_id,
                    session_id=session_id,
                    state={}
                )

                # Stream evaluation events
                start_message = Content(parts=[Part(text="start")], role="user")
                run_config = RunConfig(streaming_mode=StreamingMode.SSE)

                async for event in temp_runner.run_async(
                    user_id=user_id,
                    session_id=session_id,
                    new_message=start_message,
                    run_config=run_config,
                ):
                    # Yield each ADK event as a progress update
                    yield {
                        "type": "evaluator_event",
                        "agent_id": agent_id,
                        "event_author": event.author,
                        "event_partial": event.partial,
                        "event_content": _extract_event_content(event),
                    }

                # Get final results
                results = evaluator.get_evaluation_results()

                result_summary = {
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
                }

                all_results.append(result_summary)

                yield {
                    "type": "agent_completed",
                    "agent_id": agent_id,
                    "agent_index": agent_idx + 1,
                    "total_agents": len(agent_records),
                    **result_summary
                }

        except Exception as e:
            logger.exception(f"❌ Failed to evaluate agent {agent_id}")

            error_result = {
                "agent_id": agent_id,
                "status": "error",
                "error": str(e)
            }
            all_results.append(error_result)

            yield {
                "type": "agent_error",
                "agent_id": agent_id,
                "agent_index": agent_idx + 1,
                "total_agents": len(agent_records),
                "error": str(e)
            }

    # Final summary
    successful = sum(1 for r in all_results if r.get("status") == "evaluated")
    failed = sum(1 for r in all_results if r.get("status") == "error")

    yield {
        "type": "evaluation_completed",
        "status": "success" if failed == 0 else "partial",
        "results": all_results,
        "successful_count": successful,
        "failed_count": failed,
        "summary": f"Evaluated {successful}/{len(agent_records)} agents successfully"
    }


def _extract_event_content(event: AdkEvent) -> Optional[Dict[str, Any]]:
    """Extract readable content from an ADK event.

    Args:
        event: The ADK event to extract content from

    Returns:
        Dict with event content, or None if no content
    """
    content = {}

    if event.content and event.content.parts:
        texts = []
        for part in event.content.parts:
            if hasattr(part, 'text') and part.text:
                texts.append(part.text)
            elif hasattr(part, 'function_call') and part.function_call:
                content["function_call"] = {
                    "name": part.function_call.name,
                    "args": part.function_call.args if hasattr(part.function_call, 'args') else None
                }
            elif hasattr(part, 'function_response') and part.function_response:
                content["function_response"] = {
                    "name": part.function_response.name,
                    "response": str(part.function_response.response)[:200] if hasattr(part.function_response, 'response') else None
                }

        if texts:
            content["text"] = "\n".join(texts)

    return content if content else None


def create_evaluation_agent() -> Agent:
    """Create the evaluation sub-agent with evaluation tools."""

    # Create tools
    parse_scenarios_tool = FunctionTool(func=parse_scenarios_from_input_tool)
    set_criteria_tool = FunctionTool(func=set_evaluation_criteria_tool)
    eval_tool = FunctionTool(func=evaluate_agents_tool)

    agent = Agent(
        model=LiteLlm(model=LLM_MODEL),
        name="agent_evaluator",
        instruction=AGENT_INSTRUCTION,
        description="Agent for evaluating candidate agents based on user-defined scenarios.",
        tools=[parse_scenarios_tool, set_criteria_tool, eval_tool]
    )
    return agent