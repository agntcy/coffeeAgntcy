# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

from typing import Optional
import os
from a2a.types import AgentCard
from config.config import (
    SLIM_SERVER,
    NATS_SERVER,
)
from agntcy_app_sdk.factory import AgntcyFactory
from config.config import OTEL_SDK_DISABLED
from agntcy_app_sdk.semantic.a2a.client.factory import A2AClientFactory
from agntcy_app_sdk.semantic.a2a import (
    ClientConfig,
    NatsTransportConfig,
    SlimRpcConfig,
    SlimTransportConfig,
)

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

slim_shared_secret = os.getenv("SLIM_SHARED_SECRET")

if not slim_shared_secret:
    raise ValueError("SLIM_SHARED_SECRET environment variable must be set")

config = ClientConfig(
    slimrpc_config=SlimRpcConfig(
        namespace="lungo",
        group="agents",
        name="auction_supervisor",
        slim_url=f"http://{SLIM_SERVER}",
        secret=slim_shared_secret,
    ),
    slim_config=SlimTransportConfig(
        endpoint=f"http://{SLIM_SERVER}",
        name="lungo/agents/auction_supervisor",
        shared_secret_identity=slim_shared_secret,
    ),
    nats_config=NatsTransportConfig(
        endpoint=NATS_SERVER,
    ),
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
