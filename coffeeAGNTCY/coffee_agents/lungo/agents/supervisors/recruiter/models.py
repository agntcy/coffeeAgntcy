# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""Shared state keys and data models for the Recruiter Supervisor."""

from enum import Enum
from typing import Any, Optional

from a2a.compat.v0_3 import conversions as v03_conversions
from a2a.compat.v0_3 import types as v03_types
from a2a.types import AgentCapabilities, AgentCard, AgentInterface
from agntcy_app_sdk.directory.oasf_converter import oasf_to_agent_card
from google.protobuf.json_format import ParseDict
from pydantic import BaseModel, ConfigDict, PrivateAttr


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


def _is_legacy_card_dict(data: dict[str, Any]) -> bool:
    """True for a pre-1.x (A2A v0.3) card dict: ``url`` / ``preferredTransport``."""
    if "supportedInterfaces" in data or "supported_interfaces" in data:
        return False
    return any(
        key in data for key in ("url", "preferredTransport", "additionalInterfaces")
    )


def card_from_dict(data: dict[str, Any]) -> AgentCard:
    """Build an ``AgentCard`` from a flat card dict, v1 JSON or legacy v0.3.

    Legacy records (the Directory still stores v0.3 cards) go through the
    a2a-sdk v0.3 compat conversion, which folds ``url`` / ``preferredTransport``
    / ``additionalInterfaces`` into ``supported_interfaces``. This mirrors how
    ``oasf_to_agent_card`` reads the card nested in an OASF record.
    """
    if _is_legacy_card_dict(data):
        legacy = v03_types.AgentCard.model_validate(data)
        return v03_conversions.to_core_agent_card(legacy)
    return ParseDict(data, AgentCard(), ignore_unknown_fields=True)


def _card_has_transport_endpoint(card: AgentCard) -> bool:
    """True when the card advertises at least one non-empty transport URL."""
    return any(
        (interface.url or "").strip() for interface in card.supported_interfaces
    )


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

    # AgentCard is a protobuf message; pydantic stores it without a schema.
    model_config = ConfigDict(arbitrary_types_allowed=True)

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
        instance = cls(cid=cid, card=card_from_dict(data), protocol=protocol)
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
            url = record.get("url", "") or ""
            # A flat record is a v0.3 card: its url is the primary interface,
            # spoken as A2A v0.3 (same as the compat conversion).
            interfaces = (
                [
                    AgentInterface(
                        url=url,
                        protocol_binding=str(preferred) if preferred else "JSONRPC",
                        protocol_version="0.3",
                    )
                ]
                if url.strip()
                else []
            )
            card = AgentCard(
                name=record.get("name", ""),
                description=record.get("description", ""),
                version=record.get("version", "1.0.0"),
                capabilities=AgentCapabilities(streaming=False),
                skills=[],
                default_input_modes=["text"],
                default_output_modes=["text"],
                supported_interfaces=interfaces,
            )

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
        survive. Fall back to a copy of the stored card for flat AgentCard records.
        """
        card = oasf_to_agent_card(self._raw)
        if card is not None:
            return card
        copy = AgentCard()
        copy.CopyFrom(self.card)
        return copy

    @property
    def name(self) -> str:
        return self.card.name


class RecruitmentResponse(BaseModel):
    """Parsed response from the recruiter A2A service."""

    text: Optional[str] = None
    agent_records: dict[str, dict] = {}
    evaluation_results: dict[str, dict] = {}
