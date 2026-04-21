# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

from typing import Optional
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
        return AgntcyFactory("lungo.logistics_supervisor", enable_tracing=not OTEL_SDK_DISABLED)
    return _factory


# All supported transport configs are declared here as data (endpoints, names).
# No connections are established at import time — transport construction is
# deferred until A2AClientFactory.create(card) is called.  At that point
# the factory negotiates which transport to use based on the card's
# preferred_transport (set by the caller from a pattern lookup) and the
# interfaces the remote agent advertises.

config = build_a2a_client_config(
    namespace="lungo",
    group="agents",
    agent_name="logistics_supervisor",
    include_nats=False,
)

# -- A2A client factory --
# Holds all transports; callers set preferred_transport on the card
# before calling create(). Factory negotiates based on card interfaces.
a2a_client_factory = A2AClientFactory(config)
