# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""
Evaluator Agent Factory.

Creates the appropriate evaluator agent based on protocol.
Policy evaluation uses these agents, while red team evaluation
is handled by the server's red_teaming.orchestrator module.
"""

from typing import Callable, Optional
from rogue_sdk.types import Protocol, Scenarios, Transport

from agent_recruiter.interviewers.a2a.a2a_evaluator_agent import A2AEvaluatorAgent
from agent_recruiter.interviewers.base_evaluator_agent import BaseEvaluatorAgent

_PROTOCOL_TO_AGENT_CLASS = {
    Protocol.A2A: A2AEvaluatorAgent,
    #Protocol.MCP: MCPEvaluatorAgent,
}

def get_evaluator_agent(
    protocol: Protocol,
    transport: Optional[Transport],
    evaluated_agent_address: Optional[str] = None,
    scenarios: Optional[Scenarios] = None,
    business_context: Optional[str] = None,
    headers: Optional[dict[str, str]] = None,
    debug: bool = False,
    deep_test_mode: bool = False,
    chat_update_callback: Optional[Callable[[dict], None]] = None,
    **kwargs,
) -> BaseEvaluatorAgent:
    """
    Get an evaluator agent based on protocol.

    This factory creates agents for policy-based scenario evaluation.
    Red team (vulnerability-centric) evaluation is handled separately
    by the server's red_teaming.orchestrator module.

    Args:
        protocol: Communication protocol (A2A, MCP, or PYTHON)
        transport: Transport mechanism (not used for PYTHON protocol)
        evaluated_agent_address: URL of the agent to evaluate (for A2A/MCP)
        scenarios: Scenarios to test
        business_context: Business context for the target agent
        headers: HTTP headers for agent connection
        debug: Enable debug logging
        deep_test_mode: Enable deep testing mode
        chat_update_callback: Callback for chat updates
        **kwargs: Additional keyword arguments

    Returns:
        BaseEvaluatorAgent instance
    """
    agent_class = _PROTOCOL_TO_AGENT_CLASS.get(protocol, None)
    if not agent_class:
        raise ValueError(f"Invalid protocol: {protocol}")

    # Handle A2A and MCP protocols
    if not evaluated_agent_address:
        raise ValueError(
            f"evaluated_agent_address is required for {protocol.value} protocol",
        )

    return agent_class(
        transport=transport,
        evaluated_agent_address=evaluated_agent_address,
        scenarios=scenarios or Scenarios(),
        business_context=business_context,
        headers=headers,
        debug=debug,
        deep_test_mode=deep_test_mode,
        chat_update_callback=chat_update_callback,
        **kwargs,
    )