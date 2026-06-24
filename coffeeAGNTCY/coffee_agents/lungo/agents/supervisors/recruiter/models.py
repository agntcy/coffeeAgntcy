# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""Shared state keys and data models for the Recruiter Supervisor."""

import re
from enum import Enum
from typing import Any, Optional

from a2a.types import AgentCard, AgentCapabilities
from agntcy_app_sdk.directory.oasf_converter import oasf_to_agent_card
from pydantic import BaseModel, PrivateAttr


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
    """A recruited agent record returned by the recruiter service."""

    cid: str
    name: str
    description: str = ""
    url: str = ""  # Optional - may not be present in all agent records
    version: str = "1.0.0"
    skills: list[dict] = []
    protocol: AgentProtocol = AgentProtocol.A2A

    # Original record dict, retained so to_agent_card() can recover the nested
    # OASF card (url/preferredTransport/additionalInterfaces) that the flat
    # fields above don't capture. Populated by from_record().
    _raw: dict[str, Any] = PrivateAttr(default_factory=dict)

    @classmethod
    def from_record(cls, cid: str, record: dict[str, Any]) -> "AgentRecord":
        """Parse a recruiter record dict, retaining the raw form for conversion."""
        instance = cls(cid=cid, **record)
        instance._raw = record
        return instance

    def to_agent_card(self) -> AgentCard:
        """Convert to an A2A AgentCard for use with RemoteA2aAgent.

        Recruited agents are stored as full OASF records with the card nested
        under ``modules[].data.card_data``; prefer that so url and transport
        survive. Fall back to the flat fields for non-OASF records.
        """
        card = oasf_to_agent_card(self._raw)
        if card is not None:
            return card

        preferred = self._raw.get("preferredTransport") or self._raw.get("preferred_transport")
        kwargs: dict[str, Any] = {
            "name": self.name,
            "url": self.url,
            "description": self.description,
            "version": self.version,
            "capabilities": AgentCapabilities(streaming=False),
            "skills": [],
            "defaultInputModes": ["text"],
            "defaultOutputModes": ["text"],
            "supportsAuthenticatedExtendedCard": False,
        }
        if preferred:
            kwargs["preferred_transport"] = str(preferred)
        return AgentCard(**kwargs)

    def to_safe_agent_name(self) -> str:
        """Return a valid Python identifier suitable for ADK agent naming.

        BaseAgent validates that ``name.isidentifier()`` is True, so we
        sanitise the human-readable name into a safe form.
        """
        safe = re.sub(r"[^a-zA-Z0-9_]", "_", self.name).strip("_").lower()
        if not safe or not safe[0].isalpha():
            safe = "agent_" + safe
        return safe


class RecruitmentResponse(BaseModel):
    """Parsed response from the recruiter A2A service."""

    text: Optional[str] = None
    agent_records: dict[str, dict] = {}
    evaluation_results: dict[str, dict] = {}
