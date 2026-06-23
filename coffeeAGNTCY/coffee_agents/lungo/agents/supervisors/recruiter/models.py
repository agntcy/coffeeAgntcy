# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""Shared state keys and data models for the Recruiter Supervisor."""

from enum import Enum
from typing import Optional

from a2a.types import AgentCard
from pydantic import BaseModel


class AgentProtocol(str, Enum):
    """Communication protocol supported by a recruited agent."""

    A2A = "a2a"
    MCP = "mcp"

# ---------------------------------------------------------------------------
# Session state keys
# ---------------------------------------------------------------------------

STATE_KEY_RECRUITED_AGENTS = "recruited_agents"  # dict[str, dict] keyed by CID
STATE_KEY_EVALUATION_RESULTS = "evaluation_results"  # dict[str, dict] keyed by agent_id
STATE_KEY_TASK_MESSAGE = "task_message"  # str: message to forward to selected agents
STATE_KEY_SELECTED_AGENT = "selected_agent"  # str: CID of the currently selected agent

# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------


class AgentRecord(BaseModel):
    """A recruited agent: its CID plus the full A2A AgentCard from the recruiter.

    The card is preserved verbatim (transport, interfaces, capabilities) so the
    A2A client factory can negotiate the agent's preferred transport.
    """

    cid: str
    card: AgentCard
    protocol: AgentProtocol = AgentProtocol.A2A

    @classmethod
    def from_record_data(cls, cid: str, data: dict) -> "AgentRecord":
        """Build from a stored record dict (a full A2A AgentCard)."""
        raw_protocol = data.get("protocol")
        protocol = (
            AgentProtocol(raw_protocol.lower())
            if isinstance(raw_protocol, str)
            else AgentProtocol.A2A
        )
        return cls(cid=cid, card=AgentCard.model_validate(data), protocol=protocol)

    @property
    def name(self) -> str:
        return self.card.name


class RecruitmentResponse(BaseModel):
    """Parsed response from the recruiter A2A service."""

    text: Optional[str] = None
    agent_records: dict[str, dict] = {}
    evaluation_results: dict[str, dict] = {}
