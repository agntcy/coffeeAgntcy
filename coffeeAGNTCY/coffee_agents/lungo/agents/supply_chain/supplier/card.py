# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

import os

from a2a.types import AgentCapabilities, AgentCard, AgentInterface, AgentSkill
from agntcy_app_sdk.semantic.a2a.transport_types import InterfaceTransport

from agents.supply_chain.common.fixtures import SUPPLIERS, SupplierId
from config.config import SLIM_SERVER

DEFAULT_PORTS: dict[SupplierId, str] = {
    "supplier_a": "9096",
    "supplier_b": "9097",
    "supplier_c": "9098",
}


def supplier_id_from_env() -> SupplierId:
    """Map ``SUPPLIER_ID`` (a, b or c) to the party id."""
    raw = os.getenv("SUPPLIER_ID", "a").strip().lower()
    party = f"supplier_{raw}"
    if party not in SUPPLIERS:
        raise ValueError(f"SUPPLIER_ID must be a, b or c, got {raw!r}")
    return party


def agent_id(supplier_id: SupplierId) -> str:
    return "supply-chain-" + supplier_id.replace("_", "-")


def build_agent_card(supplier_id: SupplierId) -> AgentCard:
    letter = supplier_id.removeprefix("supplier_").upper()
    skill = AgentSkill(
        id="offer_supply",
        name="Offer Supply",
        description=(
            "Offers a lot of green coffee from this supplier's own inventory "
            "and states when it is ready for pickup at origin."
        ),
        tags=["coffee", "supply", "negotiation"],
        examples=[
            "How many tonnes can you supply and when is the lot ready?",
            "Do you confirm this plan?",
        ],
    )
    return AgentCard(
        name=f"Supplier {letter} agent",
        description=(
            f"A green coffee supplier (Supplier {letter}) that negotiates a "
            "supply commitment with a buyer and a logistics provider."
        ),
        version="1.0.0",
        default_input_modes=["text"],
        default_output_modes=["text"],
        capabilities=AgentCapabilities(streaming=True),
        skills=[skill],
        supported_interfaces=[
            AgentInterface(
                protocol_binding=InterfaceTransport.SLIM_PATTERNS,
                url=f"slim://{SLIM_SERVER}/lungo/agents/{agent_id(supplier_id)}",
            ),
        ],
    )


AGENT_CARDS: dict[SupplierId, AgentCard] = {s: build_agent_card(s) for s in SUPPLIERS}
AGENT_CARD = AGENT_CARDS[supplier_id_from_env()]
