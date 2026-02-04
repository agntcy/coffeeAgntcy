# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""
MCP protocol record parser.

Parses MCP agent records into AgentEvalConfig for evaluation.
"""

from typing import Union

from agent_recruiter.interviewers.models import AgentEvalConfig


def parse_mcp_agent_record(raw_json: Union[str, dict]) -> AgentEvalConfig:
    """Parse an MCP agent record into AgentEvalConfig.

    Args:
        raw_json: Either a JSON string or dict containing MCP agent data

    Returns:
        AgentEvalConfig with extracted agent information

    Raises:
        NotImplementedError: MCP record parsing is not yet implemented
    """
    raise NotImplementedError(
        "MCP agent record parsing is not yet implemented. "
        "Please use A2A protocol or contribute an MCP parser implementation."
    )
