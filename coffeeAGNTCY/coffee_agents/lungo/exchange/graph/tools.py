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

import logging
from typing import Any, Dict
from uuid import uuid4
from pydantic import BaseModel, PrivateAttr

from a2a.types import (
    AgentCard,
    SendMessageRequest,
    MessageSendParams,
    Message,
    Part,
    TextPart,
    Role,
)
from langchain_core.tools import BaseTool, tool
from graph.models import FetchHarvestInput, FetchHarvestOutput
from gateway_sdk.protocols.a2a.gateway import A2AProtocol
from gateway_sdk.factory import GatewayFactory
from config.config import DEFAULT_MESSAGE_TRANSPORT, TRANSPORT_SERVER_ENDPOINT
from config.config import FARM_YIELD_TOPIC

logger = logging.getLogger("corto.supervisor.tools")

# Shared factory & transport
factory = GatewayFactory()
transport = factory.create_transport(
    DEFAULT_MESSAGE_TRANSPORT,
    endpoint=TRANSPORT_SERVER_ENDPOINT,
)

class NoInput(BaseModel):
    pass

@tool
async def get_farm_yields(prompt: str) -> Dict[str, str]:
    """
    Fetch all farm yields.

    Args:
    prompt (str): The prompt to send to all farms to retrieve their yields.

    Returns:
    dict: A dictionary containing the yields from all farms.
    """
    logger.info("entering get_farm_yields tool with prompt: %s", prompt)

    client = await factory.create_client(
        "A2A",
        agent_topic=FARM_YIELD_TOPIC,
        transport=transport,
    )

    request = SendMessageRequest(
        params=MessageSendParams(
            message=Message(
                messageId=str(uuid4()),
                role=Role.user,
                parts=[Part(TextPart(text=prompt))],
            ),
        )
    )

    responses = await client.broadcast_message(request, limit=3)

    logger.info(f"got {len(responses)} responses back from farms")

    farm_yield_responds = {}
    for response in responses:
        # we want a dict for farm name -> yield, the yarm_name will be in the response metadata
        if response.root.result and response.root.result.parts:
            part = response.root.result.parts[0].root
            if hasattr(part, "text"):
                farm_name = response.root.metadata.get("name", "unknown_farm")
                farm_yield_responds[farm_name] = part.text.strip()
        elif response.root.error:
            logger.error(f"A2A error from farm: {response.root.error.message}") 
        else:
            logger.error("Unknown response type from farm")
    return farm_yield_responds

# Base A2A tool for harvest fetching
class BaseHarvestTool(BaseTool):
    _client = PrivateAttr()

    def __init__(self, remote_agent_card: AgentCard, receiver_id: str, **kwargs: Any):
        super().__init__(**kwargs)
        self._remote_agent_card = remote_agent_card
        self._receiver_id = receiver_id
        self._client = None

    def _run(self, input: FetchHarvestInput) -> float:
        raise NotImplementedError("Use _arun for async execution.")

    async def _connect(self):
        logger.info(f"Connecting to remote agent: {self._remote_agent_card.name}")
        a2a_topic = A2AProtocol.create_agent_topic(self._remote_agent_card)
        self._client = await factory.create_client(
            "A2A",
            agent_topic=a2a_topic,
            agent_url=self._remote_agent_card.url,
            transport=transport,
        )
        logger.info("Connected to remote agent")

    async def send_message(self, prompt: str) -> str:
        if not self._client:
            await self._connect()

        request = SendMessageRequest(
            params=MessageSendParams(
                skill_id="get_yield",
                sender_id="coffee-exchange-agent",
                receiver_id=self._receiver_id,
                message=Message(
                    messageId=str(uuid4()),
                    role=Role.user,
                    parts=[Part(TextPart(text=prompt))],
                ),
            )
        )

        response = await self._client.send_message(request)
        logger.info(f"Response received from A2A agent: {response}")

        if response.root.result and response.root.result.parts:
            part = response.root.result.parts[0].root
            if hasattr(part, "text"):
                return part.text
        elif response.root.error:
            raise Exception(f"A2A error: {response.error.message}")

        raise Exception("Unknown response type")

    async def _arun(self, input: FetchHarvestInput, **kwargs: Any) -> FetchHarvestOutput:
        try:
            prompt = input.get("prompt")
            if not prompt:
                raise ValueError("Invalid input: Prompt must be a non-empty string.")

            raw_text = await self.send_message(prompt)

            if not raw_text.strip():
                raise RuntimeError("Empty message received from agent.")

            return FetchHarvestOutput(status="success", yield_lb=raw_text.strip())

        except Exception as e:
            logger.error(f"Failed to fetch harvest: {str(e)}")
            raise RuntimeError(f"Failed to fetch harvest: {str(e)}")


# Specific farm implementations
class FetchBrazilHarvestTool(BaseHarvestTool):
    """
    Fetches the coffee harvest from the Brazil farm agent.
    """
    name: str = "fetch_brazil_harvest"
    description: str = "Fetches the coffee harvest from the Brazil farm."

    def __init__(self, remote_agent_card: AgentCard, **kwargs: Any):
        super().__init__(remote_agent_card, receiver_id="brazil-farm-agent", **kwargs)

class FetchColombiaHarvestTool(BaseHarvestTool):
    """
    Fetches the coffee harvest from the Colombia farm agent.
    """
    name: str = "fetch_colombia_harvest"
    description: str = "Fetches the coffee harvest from the colombia farm."

    def __init__(self, remote_agent_card: AgentCard, **kwargs: Any):
        super().__init__(remote_agent_card, receiver_id="colombia-farm-agent", **kwargs)

class FetchVietnamHarvestTool(BaseHarvestTool):
    """
    Fetches the coffee harvest from the Vietnam farm agent.
    """
    name: str = "fetch_vietnam_harvest"
    description: str = "Fetches the coffee harvest from the Vietnam farm."

    def __init__(self, remote_agent_card: AgentCard, **kwargs: Any):
        super().__init__(remote_agent_card, receiver_id="vietnam-farm-agent", **kwargs)