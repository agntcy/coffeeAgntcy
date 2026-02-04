# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

from typing import Optional
from pydantic import BaseModel
from rogue_sdk.types import AuthType, Protocol, Transport


class PolicyEvaluationResult(BaseModel):
    passed: bool
    reason: str
    policy: str


class AgentEvalConfig(BaseModel):
    """Configuration extracted from an agent record for evaluation.

    This is the standardized format returned by protocol-specific record parsers.
    It contains all the information needed to connect to and evaluate an agent.
    """

    protocol: Protocol
    """The communication protocol (A2A, MCP, etc.)"""

    transport: Transport
    """The transport mechanism (HTTP, STDIO, etc.)"""

    evaluated_agent_url: str
    """The URL/address of the agent to evaluate"""

    auth_type: AuthType = AuthType.NO_AUTH
    """The authentication type required"""

    auth_credentials: Optional[str] = None
    """Authentication credentials if required"""

    agent_name: Optional[str] = None
    """Human-readable name of the agent"""

    agent_description: Optional[str] = None
    """Description of the agent's capabilities"""

    class Config:
        use_enum_values = False  # Keep enum objects, not just values