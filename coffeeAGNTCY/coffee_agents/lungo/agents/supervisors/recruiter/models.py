# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""Shared state keys and data models for the Recruiter Supervisor."""

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


def _card_has_transport_endpoint(card: AgentCard) -> bool:
    """True when the card advertises at least one non-empty transport URL."""
    if (card.url or "").strip():
        return True
    if card.additional_interfaces:
        for interface in card.additional_interfaces:
            if (interface.url or "").strip():
                return True
    return False


def _require_delegation_card(card: AgentCard) -> None:
    """Reject cards that cannot be used for A2A delegation."""
    if not (card.name or "").strip():
        raise ValueError("agent record is missing a name")
    if not _card_has_transport_endpoint(card):
        raise ValueError("agent record has no transport endpoint")


class AgentRecord(BaseModel):
    """A recruited agent: its CID plus the full A2A AgentCard.

    The card is preserved verbatim so the client factory can negotiate transport.
    The original record dict is retained for OASF-aware conversion when the card
    is nested under ``modules[].data.card_data``.
    """

    cid: str
    card: AgentCard
    protocol: AgentProtocol = AgentProtocol.A2A

    _raw: dict[str, Any] = PrivateAttr(default_factory=dict)

    @classmethod
    def from_record_data(cls, cid: str, data: dict) -> "AgentRecord":
        """Build from a stored record dict (a full A2A AgentCard)."""
        raw_protocol = data.get("protocol")
        protocol = (
            AgentProtocol(raw_protocol.lower())
            if isinstance(raw_protocol, str)
            else AgentProtocol.A2A
        )
        instance = cls(cid=cid, card=AgentCard.model_validate(data), protocol=protocol)
        instance._raw = data
        return instance

    @classmethod
    def from_record(cls, cid: str, record: dict[str, Any]) -> "AgentRecord":
        """Parse a recruiter record dict, retaining the raw form for conversion."""
        card = oasf_to_agent_card(record)
        if card is None:
            preferred = record.get("preferredTransport") or record.get(
                "preferred_transport"
            )
            kwargs: dict[str, Any] = {
                "name": record.get("name", ""),
                "url": record.get("url", ""),
                "description": record.get("description", ""),
                "version": record.get("version", "1.0.0"),
                "capabilities": AgentCapabilities(streaming=False),
                "skills": [],
                "defaultInputModes": ["text"],
                "defaultOutputModes": ["text"],
                "supportsAuthenticatedExtendedCard": False,
            }
            if preferred:
                kwargs["preferred_transport"] = str(preferred)
            card = AgentCard(**kwargs)

        raw_protocol = record.get("protocol")
        protocol = (
            AgentProtocol(raw_protocol.lower())
            if isinstance(raw_protocol, str)
            else AgentProtocol.A2A
        )
        _require_delegation_card(card)
        instance = cls(cid=cid, card=card, protocol=protocol)
        instance._raw = record
        return instance

    def to_agent_card(self) -> AgentCard:
        """Convert to an A2A AgentCard for delegation.

        Recruited agents are stored as full OASF records with the card nested
        under ``modules[].data.card_data``; prefer that so url and transport
        survive. Fall back to the stored card for flat AgentCard records.
        """
        card = oasf_to_agent_card(self._raw)
        if card is not None:
            return card
        return self.card.model_copy(deep=True)

    @property
    def name(self) -> str:
        return self.card.name


class RecruitmentResponse(BaseModel):
    """Parsed response from the recruiter A2A service."""

    text: Optional[str] = None
    agent_records: dict[str, dict] = {}
    evaluation_results: dict[str, dict] = {}
