# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

from typing import Optional
import httpx
from agntcy_app_sdk.factory import AgntcyFactory
from config.config import OTEL_SDK_DISABLED, A2A_CLIENT_TIMEOUT_SECONDS
from agntcy_app_sdk.semantic.a2a.client.factory import A2AClientFactory
from common.a2a_transport_config import build_a2a_client_config

_factory: Optional[AgntcyFactory] = None

def set_factory(factory: AgntcyFactory):
    global _factory
    _factory = factory

def get_factory() -> AgntcyFactory:
    if _factory is None:
        return AgntcyFactory("lungo.recruiter_supervisor", enable_tracing=not OTEL_SDK_DISABLED)
    return _factory

config = build_a2a_client_config(
    namespace="lungo",
    group="agents",
    agent_name="recruiter_supervisor",
    include_nats=True,
)

# Discovered agents are reached over JSONRPC (their OASF records advertise it),
# and httpx defaults to a 5s read timeout — too short for LLM-backed agents.
# Only the JSONRPC transport consumes httpx_client; SLIM/NATS ignore it.
config.httpx_client = httpx.AsyncClient(
    timeout=httpx.Timeout(A2A_CLIENT_TIMEOUT_SECONDS, connect=10.0)
)

# -- A2A client factory --
# Holds all transports; callers set preferred_transport on the card
# before calling create(). Factory negotiates based on card interfaces.
a2a_client_factory = A2AClientFactory(config)
