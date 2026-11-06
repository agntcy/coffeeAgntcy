# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

import asyncio
import logging
from os import getenv

import config.logging_config  # noqa: F401 - runs setup on import; must be first
from a2a.types import AgentCard
from agntcy_app_sdk import A2AServerConfig
from agntcy_app_sdk.factory import AgntcyFactory
from dotenv import load_dotenv
from starlette.applications import Starlette

from agents.supply_chain.common import member_server
from agents.supply_chain.common.member import MemberAgent
from agents.supply_chain.logistics.card import AGENT_CARD as LOGISTICS_AGENT_CARD
from agents.supply_chain.supplier.card import (
    AGENT_CARD,
    DEFAULT_PORTS,
    supplier_id_from_env,
)
from config.config import OTEL_SDK_DISABLED

load_dotenv()

SUPPLIER_ID = supplier_id_from_env()
PORT = getenv("AGENT_PORT", DEFAULT_PORTS[SUPPLIER_ID])

factory = AgntcyFactory(
    f"lungo.supply_chain_{SUPPLIER_ID}", enable_tracing=not OTEL_SDK_DISABLED
)

logger = logging.getLogger("lungo.supply_chain.supplier.server")

agent = MemberAgent(SUPPLIER_ID)
liveness_probe = member_server.make_liveness_probe(
    f"lungo/agents/supply_chain/{SUPPLIER_ID}", LOGISTICS_AGENT_CARD
)


def create_app() -> Starlette:
    request_handler = member_server.build_request_handler(agent, AGENT_CARD)
    server = A2AServerConfig(agent_card=AGENT_CARD, request_handler=request_handler)
    return member_server.build_http_app(server, liveness_probe)


async def serve_all_a2a_interfaces(request_handler, agent_card: AgentCard):
    """Serve this supplier over the SLIM interface declared in its AgentCard."""
    await member_server.serve_a2a(factory, request_handler, agent_card)


async def main():
    await member_server.run_agent(
        serve_all_a2a_interfaces, agent, AGENT_CARD, liveness_probe, int(PORT)
    )


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Shutting down gracefully on keyboard interrupt.")
    except Exception as e:
        logger.error("Error occurred: %s", e)
        raise SystemExit(1) from e
