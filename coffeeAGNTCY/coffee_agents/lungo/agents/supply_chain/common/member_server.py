# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""Server plumbing shared by the supplier and logistics agents.

Each agent's own ``server.py`` keeps the module-level ``factory``,
``serve_all_a2a_interfaces`` and ``AGENT_CARD`` that the placeholder-secret
tests patch, and delegates to the functions here.
"""

from __future__ import annotations

import asyncio
import logging
from os import getenv

from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import AgentCard
from agntcy_app_sdk import A2AServerConfig
from agntcy_app_sdk.semantic.a2a import ClientConfig, SlimTransportConfig
from agntcy_app_sdk.semantic.a2a.client.factory import A2AClientFactory
from starlette.applications import Starlette
from starlette.middleware.cors import CORSMiddleware
from starlette.responses import JSONResponse
from starlette.routing import Route
from uvicorn import Config, Server

from agents.supply_chain.common.member import MemberAgent
from agents.supply_chain.common.member_executor import MemberAgentExecutor
from common.cors import get_cors_allowed_origins
from common.slim_placeholder_secret import (
    apply_placeholder_secret_policy,
    start_builder,
)
from config.config import SLIM_SERVER

logger = logging.getLogger("lungo.supply_chain.member_server")


def build_request_handler(agent: MemberAgent, card: AgentCard) -> DefaultRequestHandler:
    return DefaultRequestHandler(
        agent_executor=MemberAgentExecutor(agent, card),
        task_store=InMemoryTaskStore(),
        agent_card=card,
    )


def make_liveness_probe(client_name: str, peer_card: AgentCard):
    """Build a ``/v1/health`` handler that verifies SLIM connectivity.

    It creates an A2A client for ``peer_card``; success within the timeout
    means the SLIM server is reachable.
    """

    async def liveness_probe(request) -> JSONResponse:
        config = ClientConfig(
            slim_config=SlimTransportConfig(
                endpoint=f"http://{SLIM_SERVER}",
                name=client_name,
                shared_secret_identity=getenv("SLIM_SHARED_SECRET") or None,
            ),
        )
        try:
            await asyncio.wait_for(
                A2AClientFactory(config).create(peer_card), timeout=30
            )
            logger.info("Liveness probe succeeded: SLIM connectivity verified.")
            return JSONResponse({"status": "alive"})
        except asyncio.TimeoutError:
            return JSONResponse(
                {"error": "Timeout occurred while creating client."}, status_code=500
            )
        except Exception as e:
            return JSONResponse({"error": f"Error occurred: {e!s}"}, status_code=500)

    return liveness_probe


def build_http_app(a2a_app: A2AServerConfig, liveness_probe) -> Starlette:
    cors_origins = get_cors_allowed_origins()
    logger.info("CORS allow_origins: %s", cors_origins)
    app_ = a2a_app.build_app()
    app_.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app_.router.routes.append(Route("/v1/health", liveness_probe, methods=["GET"]))
    return app_


async def run_http_server(server: A2AServerConfig, liveness_probe, port: int) -> None:
    app_ = build_http_app(server, liveness_probe)
    try:
        userver = Server(Config(app=app_, host="0.0.0.0", port=port, loop="asyncio"))
        await userver.serve()
    except Exception as e:
        logger.error("HTTP server encountered an error: %s", e)


async def serve_a2a(factory, request_handler, agent_card: AgentCard) -> None:
    """Serve ``agent_card``'s SLIM interface without keep-alive."""
    session = factory.create_app_session()
    builder = apply_placeholder_secret_policy(
        session.add_a2a_card(agent_card, request_handler)
    )
    await start_builder(builder, keep_alive=False)
    logger.info("Agent ready")


async def run_agent(
    serve_all_a2a_interfaces,
    agent: MemberAgent,
    card: AgentCard,
    liveness_probe,
    port: int,
) -> None:
    request_handler = build_request_handler(agent, card)
    server = A2AServerConfig(agent_card=card, request_handler=request_handler)
    await asyncio.gather(
        serve_all_a2a_interfaces(request_handler, card),
        run_http_server(server, liveness_probe, port),
    )
