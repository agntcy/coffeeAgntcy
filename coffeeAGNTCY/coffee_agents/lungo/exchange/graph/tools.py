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
from typing import Any
from uuid import uuid4
from pydantic import PrivateAttr

from a2a.types import (
    AgentCard, 
    SendMessageRequest, 
    MessageSendParams, 
    Message, 
    Part, 
    TextPart, 
    Role,
)

from langchain_core.tools import StructuredTool
from pydantic import BaseModel

from langchain_core.tools import BaseTool
from langchain_core.callbacks import (
    CallbackManagerForToolRun,
)
from graph.models import FetchHarvestInput, FetchHarvestOutput

from gateway_sdk.protocols.a2a.gateway import A2AProtocol
from gateway_sdk.factory import GatewayFactory

from config.config import DEFAULT_MESSAGE_TRANSPORT, TRANSPORT_SERVER_ENDPOINT

logger = logging.getLogger("corto.supervisor.tools")

# Initialize a multi-protocol, multi-transport gateway factory.
# All tools will share this factory instance and the transport.
factory = GatewayFactory()
transport = factory.create_transport(
    DEFAULT_MESSAGE_TRANSPORT,
    endpoint=TRANSPORT_SERVER_ENDPOINT,
)

class NoInput(BaseModel):
    pass

class GetFarmYieldTool(BaseTool):
    """
    Tool to fetch coffee yield from a specific farm.

    No input
    
    Output:
        dict: Dictionary with country as key and yield as float value (e.g., {"brazil": 100})
    """
    name: str = "get_farm_yield"
    description: str = "Fetches the coffee yield from a specific farm."

    def _run(self, input: NoInput, **kwargs: Any) -> float:
        raise NotImplementedError("Use _arun for async execution.")

    async def _arun(self, input: NoInput, **kwargs: Any) -> dict[str, float]:
        stubbed_response = {"brazil": 100}
        logger.info(f"yield status: {stubbed_response}")
        return stubbed_response

class FetchHarvestTool(BaseTool):
    """
    Tool to fetch coffee harvest by sending a message to a remote A2A agent.

    Input:
        FetchHarvestInput: Contains a 'prompt' field (non-empty string)
    
    Output:
        FetchHarvestOutput: A model with `status = 'success'` if successful
    """
    name: str = "fetch_harvest"
    description: str = "Fetches the coffee harvest from a specific farm."

    _client = PrivateAttr()

    def __init__(self, remote_agent_card: AgentCard, **kwargs: Any):
        super().__init__(**kwargs)
        self._remote_agent_card = remote_agent_card
        self._client = None

    async def _connect(self):
        logger.info(f"Connecting to remote agent: {self._remote_agent_card.name}")
       
        a2a_topic = A2AProtocol.create_agent_topic(self._remote_agent_card)
        self._client = await factory.create_client(
            "A2A", 
            agent_topic=a2a_topic,  
            agent_url=self._remote_agent_card.url, 
            transport=transport)
        
        logger.info("Connected to remote agent")

    def _run(self, input: FetchHarvestInput) -> float:
        raise NotImplementedError("Use _arun for async execution.")

    async def _arun(self, input: FetchHarvestInput, **kwargs: Any) -> FetchHarvestOutput:
        try:
            if not input.get("prompt"):
                logger.error("Invalid input: Prompt must be a non-empty string.")
                raise ValueError("Invalid input: Prompt must be a non-empty string.")
            
            resp = await self.send_message(input.get("prompt"))
            logger.info(f"Response from agent: {resp}")
            if not resp:
                logger.error("No response received from the agent.")
                raise ValueError("No response received from the agent.")

            return FetchHarvestOutput(status="success")

        except Exception as e:
            logger.error(f"Failed to fetch harvest: {str(e)}")
            raise RuntimeError(f"Failed to fetch harvest: {str(e)}")
        
    async def send_message(self, prompt: str) -> str:
        """
        Sends a message to the Brazil farm agent via A2A, specifically invoking its `get_yield` skill.
        Args:
            prompt (str): The user input prompt to send to the agent.
        Returns:
            str: The flavor profile estimation returned by the agent.
        """

        # Ensure the client is connected, use async event loop to connect if not
        if not self._client:
            await self._connect()

        request = SendMessageRequest(
            params=MessageSendParams(
                skill_id="get_yield",
                sender_id="coffee-exchange-agent",
                receiver_id="brazil-farm-agent",
                message=Message(
                    messageId=str(uuid4()),
                    role=Role.user,
                    parts=[Part(TextPart(text=prompt))],
                )
            )
        )

        response = await self._client.send_message(request)
        logger.info(f"Response received from A2A agent: {response}")

        if response.root.result:
            if not response.root.result.parts:
                raise ValueError("No response parts found in the message.")
            part = response.root.result.parts[0].root
            if hasattr(part, "text"):
                return part.text
        elif response.root.error:
            raise Exception(f"A2A error: {response.error.message}")

        raise Exception("Unknown response type")
