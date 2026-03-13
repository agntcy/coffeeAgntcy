# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

from typing import Optional
import os
from agntcy_app_sdk.factory import AgntcyFactory
from config.config import (
    SLIM_SERVER,
    NATS_SERVER,
)
from agntcy_app_sdk.factory import AgntcyFactory
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
        return AgntcyFactory("lungo.recruiter_supervisor", enable_tracing=True)
    return _factory

slim_shared_secret = os.getenv("SLIM_SHARED_SECRET")

if not slim_shared_secret:
    raise ValueError("SLIM_SHARED_SECRET environment variable must be set")

config = ClientConfig(
    slimrpc_config=SlimRpcConfig(
        namespace="lungo",
        group="agents",
        name="recruiter_supervisor",
        slim_url=f"http://{SLIM_SERVER}",
        secret=slim_shared_secret,
    ),
    slim_config=SlimTransportConfig(
        endpoint=f"http://{SLIM_SERVER}",
        name="lungo/agents/recruiter_supervisor",
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
