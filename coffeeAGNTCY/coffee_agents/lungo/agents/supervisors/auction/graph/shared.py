# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

from typing import Optional
from a2a.types import AgentCard
from agntcy_app_sdk.factory import AgntcyFactory
from config.config import OTEL_SDK_DISABLED
from agntcy_app_sdk.semantic.a2a.client.factory import A2AClientFactory
from common.a2a_transport_config import build_a2a_client_config

_factory: Optional[AgntcyFactory] = None

def set_factory(factory: AgntcyFactory):
    global _factory
    _factory = factory

def get_factory() -> AgntcyFactory:
    if _factory is None:
        return AgntcyFactory("lungo.auction_supervisor", enable_tracing=not OTEL_SDK_DISABLED)
    return _factory


# All supported transport configs are declared here as data (endpoints, names).
# No connections are established at import time — transport construction is
# deferred until A2AClientFactory.create(card) is called.  At that point
# the factory negotiates which transport to use based on the card's
# preferred_transport.

config = build_a2a_client_config(
    namespace="lungo",
    group="agents",
    agent_name="auction_supervisor",
    include_nats=True,
)

# -- A2A client factory --
# Holds all transports; callers set preferred_transport on the card
# before calling create(). Factory negotiates based on card interfaces.
a2a_client_factory = A2AClientFactory(config)


# -- Farm registry --
# Central registry mapping canonical farm slugs to their AgentCards.
# All farm lookups in the auction supervisor go through this registry.
# To add or remove a farm, modify the register() calls below — no other
# files in the auction supervisor need to change.

class FarmRegistry:
    """
    Central registry mapping canonical farm slugs to their AgentCards.
    All farm lookups in the auction supervisor go through this registry.
    """

    def __init__(self):
        self._farms: dict[str, AgentCard] = {}

    def register(self, slug: str, card: AgentCard) -> None:
        """Register a farm card under a canonical slug (lowercase, stripped)."""
        self._farms[slug.strip().lower()] = card

    def get(self, slug: str) -> AgentCard | None:
        """Exact lookup by canonical slug. Returns None if not found."""
        return self._farms.get(slug.strip().lower())

    def slugs(self) -> list[str]:
        """Return all registered farm slugs."""
        return list(self._farms.keys())

    def cards(self) -> list[AgentCard]:
        """Return all registered AgentCards."""
        return list(self._farms.values())

    def display_names(self) -> set[str]:
        """Return the set of AgentCard.name values (display names)."""
        return {card.name for card in self._farms.values()}

    def __iter__(self):
        return iter(self._farms)

    def __len__(self):
        return len(self._farms)


from agents.farms.brazil.card import AGENT_CARD as brazil_agent_card
from agents.farms.colombia.card import AGENT_CARD as colombia_agent_card
from agents.farms.vietnam.card import AGENT_CARD as vietnam_agent_card

farm_registry = FarmRegistry()
farm_registry.register("brazil", brazil_agent_card)
farm_registry.register("colombia", colombia_agent_card)
farm_registry.register("vietnam", vietnam_agent_card)
