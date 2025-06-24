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

from gateway_sdk.factory import GatewayFactory

from a2a.server.apps import A2AStarletteApplication
from a2a.server.tasks import InMemoryTaskStore
from a2a.server.request_handlers import DefaultRequestHandler

from agent_executor import FarmAgentExecutor
from config.config import (
    DEFAULT_MESSAGE_TRANSPORT, 
    TRANSPORT_SERVER_ENDPOINT,
    FARM_BROADCAST_TOPIC,
)
from card import AGENT_CARD

# Initialize a multi-protocol, multi-transport gateway factory.
factory = GatewayFactory()

async def main():
    """Run the A2A server with the Farm Agent."""

    request_handler = DefaultRequestHandler(
        agent_executor=FarmAgentExecutor(),
        task_store=InMemoryTaskStore(),
    )

    server = A2AStarletteApplication(
        agent_card=AGENT_CARD, http_handler=request_handler
    )

    transport = factory.create_transport(
        DEFAULT_MESSAGE_TRANSPORT,
        endpoint=TRANSPORT_SERVER_ENDPOINT,
    )

    # explicitly create a broadcast bridge to the farm yield topic
    broadcast_bridge = factory.create_bridge(
        server, transport=transport, topic=FARM_BROADCAST_TOPIC
    )

    # create the default bridge to the server with a topic generated from the agent card
    bridge = factory.create_bridge(server, transport=transport) 

    await broadcast_bridge.start(blocking=False)
    await bridge.start(blocking=True)

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nShutting down gracefully on keyboard interrupt.")
    except Exception as e:
        print(f"Error occurred: {e}")