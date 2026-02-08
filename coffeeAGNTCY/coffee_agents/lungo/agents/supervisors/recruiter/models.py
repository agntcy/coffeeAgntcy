# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""Shared state keys and data models for the Recruiter Supervisor."""

import re
from typing import Optional

from a2a.types import AgentCard, AgentCapabilities
from pydantic import BaseModel

# ---------------------------------------------------------------------------
# Session state keys
# ---------------------------------------------------------------------------

STATE_KEY_RECRUITED_AGENTS = "recruited_agents"  # dict[str, dict] keyed by CID
STATE_KEY_EVALUATION_RESULTS = "evaluation_results"  # dict[str, dict] keyed by agent_id
STATE_KEY_SELECTED_AGENT_CIDS = "selected_agent_cids"  # list[str] set by supervisor (legacy)
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

    def to_agent_card(self) -> AgentCard:
        """Convert to an A2A AgentCard for use with RemoteA2aAgent."""
        return AgentCard(
            name=self.name,
            url=self.url,
            description=self.description,
            version=self.version,
            capabilities=AgentCapabilities(streaming=False),
            skills=[],
            defaultInputModes=["text"],
            defaultOutputModes=["text"],
            supportsAuthenticatedExtendedCard=False,
        )

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
