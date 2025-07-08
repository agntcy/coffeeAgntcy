# Copyright 2025 Cisco Systems, Inc. and its affiliates
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# SPDX-License-Identifier: Apache-2.0

import asyncio
from uvicorn import Config, Server

from a2a.server.apps import A2AStarletteApplication
from a2a.server.tasks import InMemoryTaskStore
from a2a.server.request_handlers import DefaultRequestHandler
from gateway_sdk.factory import GatewayFactory

from agent_executor import FarmAgentExecutor
from card import AGENT_CARD
from config.config import FARM_AGENT_HOST, FARM_AGENT_PORT
from config.config import DEFAULT_MESSAGE_TRANSPORT, TRANSPORT_SERVER_ENDPOINT

# Initialize a multi-protocol, multi-transport gateway factory.
factory = GatewayFactory()

async def main():
    """
    Starts the farm agent server using the specified transport mechanism.

    This function initializes a FarmAgentExecutor wrapped with a DefaultRequestHandler,
    and serves it using an A2AStarletteApplication. The agent is exposed via either:

    1. An HTTP server using native A2A (Agent-to-Agent) protocol via Starlette, or
    2. A bridge-based transport using the app-sdk factory (e.g., SLIM or other supported transports).

    The transport method is determined by the `DEFAULT_MESSAGE_TRANSPORT` environment variable.

    - If set to `"A2A"`, the agent is served via a local FastAPI/Starlette HTTP server.
    - Otherwise, it uses a pluggable transport layer (like SLIM) via the app-sdk factory, connecting to
    the server or gateway defined by `TRANSPORT_SERVER_ENDPOINT`.

    This design enables interchangeable transport layers for agent communication while keeping the
    agent logic transport-agnostic.

    Dependencies:
    - AGNTCY App SDK: https://github.com/agntcy/app-sdk

    Environment Variables:
    - DEFAULT_MESSAGE_TRANSPORT: Transport protocol name ("A2A", "slim", etc.)
    - TRANSPORT_SERVER_ENDPOINT: Endpoint for the external transport (if used)
    - FARM_AGENT_HOST / FARM_AGENT_PORT: Host and port for local HTTP server (if "A2A" is selected)
    """
    request_handler = DefaultRequestHandler(
        agent_executor=FarmAgentExecutor(),
        task_store=InMemoryTaskStore(),
    )

    server = A2AStarletteApplication(
        agent_card=AGENT_CARD, http_handler=request_handler
    )

    if DEFAULT_MESSAGE_TRANSPORT == "A2A":
        config = Config(app=server.build(), host=FARM_AGENT_HOST, port=FARM_AGENT_PORT, loop="asyncio")
        userver = Server(config)
        await userver.serve()
    else:
        transport = factory.create_transport(
            DEFAULT_MESSAGE_TRANSPORT,
            endpoint=TRANSPORT_SERVER_ENDPOINT,
        )
        bridge = factory.create_bridge(server, transport=transport)
        await bridge.start(blocking=True)

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nShutting down gracefully on keyboard interrupt.")
    except Exception as e:
        print(f"Error occurred: {e}")
