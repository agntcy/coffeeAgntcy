# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""Starlette app that serves the recruiter agent card and A2A JSON-RPC endpoint."""

from a2a.server.agent_execution import AgentExecutor
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.routes import create_agent_card_routes, create_jsonrpc_routes
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import AgentCard
from starlette.applications import Starlette

# a2a-sdk 0.3 served the card at both paths and callers (the compose health
# check, docs, tests) still use the older one, so both are mounted.
LEGACY_AGENT_CARD_PATH = "/.well-known/agent.json"


def build_app(agent_card: AgentCard, agent_executor: AgentExecutor) -> Starlette:
    """Build the ASGI app for ``agent_executor``.

    The JSON-RPC endpoint at ``/`` speaks A2A v1.0 only: v0.3 compat is off, and
    the card (see ``server/card.py``) lists a single ``1.0`` JSON-RPC interface.
    The card is served at both ``/.well-known/agent-card.json`` and
    ``/.well-known/agent.json``.
    """
    request_handler = DefaultRequestHandler(
        agent_executor=agent_executor,
        task_store=InMemoryTaskStore(),
        agent_card=agent_card,
    )
    routes = [
        *create_agent_card_routes(agent_card),
        *create_agent_card_routes(agent_card, card_url=LEGACY_AGENT_CARD_PATH),
        *create_jsonrpc_routes(request_handler, rpc_url="/"),
    ]
    return Starlette(routes=routes)
