# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

from typing import Optional

from agntcy_app_sdk.factory import AgntcyFactory
from agntcy_app_sdk.semantic.a2a.client.factory import A2AClientFactory
from common.a2a_transport_config import build_a2a_client_config
from config.config import OTEL_SDK_DISABLED

_factory: Optional[AgntcyFactory] = None


def set_factory(factory: AgntcyFactory):
    global _factory
    _factory = factory


def get_factory() -> AgntcyFactory:
    if _factory is None:
        return AgntcyFactory(
            "lungo.supply_chain_buyer", enable_tracing=not OTEL_SDK_DISABLED
        )
    return _factory


# Transport configs are data only; no connection is made at import time. The
# member cards list SLIM only, so SLIM is the transport that is negotiated.
config = build_a2a_client_config(
    namespace="lungo",
    group="agents",
    agent_name="supply_chain_buyer",
    include_nats=False,
)

a2a_client_factory = A2AClientFactory(config)
