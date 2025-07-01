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
from typing import Any, Union, Literal
from uuid import uuid4
from pydantic import BaseModel

from a2a.types import (
    AgentCard,
    SendMessageRequest,
    MessageSendParams,
    Message,
    Part,
    TextPart,
    Role,
)
from langchain_core.tools import tool
from langchain_core.messages import AnyMessage, ToolMessage
from gateway_sdk.protocols.a2a.gateway import A2AProtocol
from gateway_sdk.factory import GatewayFactory
from config.config import (
    DEFAULT_MESSAGE_TRANSPORT, 
    TRANSPORT_SERVER_ENDPOINT, 
    FARM_BROADCAST_TOPIC,
)
from farms.brazil.card import AGENT_CARD as brazil_agent_card
from farms.colombia.card import AGENT_CARD as colombia_agent_card
from farms.vietnam.card import AGENT_CARD as vietnam_agent_card
from exchange.graph.models import (
    InventoryArgs,
    CreateOrderArgs,
)

logger = logging.getLogger("lungo.supervisor.tools")

# Shared factory & transport
factory = GatewayFactory()
transport = factory.create_transport(
    DEFAULT_MESSAGE_TRANSPORT,
    endpoint=TRANSPORT_SERVER_ENDPOINT,
)

def tools_or_next(tools_node: str, end_node: str = "__end__"):
  """Return a function that returns the tools_node if the last message has tool calls. Otherwise return the end_node."""

  def custom_tools_condition_fn(
    state: Union[list[AnyMessage], dict[str, Any], BaseModel],
    messages_key: str = "messages",
  ) -> Literal[tools_node, end_node]: # type: ignore

    if isinstance(state, list):
      ai_message = state[-1]
    elif isinstance(state, dict) and (messages := state.get(messages_key, [])):
      ai_message = messages[-1]
    elif messages := getattr(state, messages_key, []):
      ai_message = messages[-1]
    else:
      raise ValueError(f"No messages found in input state to tool_edge: {state}")
    
    if isinstance(ai_message, ToolMessage):
        logger.debug("Last message is a ToolMessage, returning end_node: %s", end_node)
        return end_node

    if hasattr(ai_message, "tool_calls") and len(ai_message.tool_calls) > 0:
      logger.debug("Last message has tool calls, returning tools_node: %s", tools_node)
      return tools_node
    
    logger.debug("Last message has no tool calls, returning end_node: %s", end_node)
    return end_node

  return custom_tools_condition_fn

def get_farm_card(farm: str) -> AgentCard | None:
    farm = farm.strip().lower()
    if 'brazil' in farm.lower():
        return brazil_agent_card
    elif 'colombia' in farm.lower():
        return colombia_agent_card
    elif 'vietnam' in farm.lower():
        return vietnam_agent_card
    else:
        logger.error(f"Unknown farm name: {farm}. Expected one of 'brazil', 'colombia', or 'vietnam'.")
        return None

@tool(args_schema=InventoryArgs)
async def get_farm_yield_inventory(prompt: str, farm: str) -> str:
    """
    Fetch yield inventory from a specific farm.

    Args:
    prompt (str): The prompt to send to the farm to retrieve their yields
    farm (srr): The farm to send the request to

    Returns:
    str: current yield amount
    """
    logger.info("entering get_farm_yield_inventory tool with prompt: %s, farm: %s", prompt, farm)
    if farm == "":
        return "No farm was provided, please provide a farm to get the yield from."
    
    card = get_farm_card(farm)
    if card is None:
        return f"Farm '{farm}' not recognized. Available farms are: {brazil_agent_card.name}, {colombia_agent_card.name}, {vietnam_agent_card.name}."
    
    client = await factory.create_client(
        "A2A",
        agent_topic=A2AProtocol.create_agent_topic(card),
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

    response = await client.send_message(request)
    logger.info(f"Response received from A2A agent: {response}")
    if response.root.result and response.root.result.parts:
        part = response.root.result.parts[0].root
        if hasattr(part, "text"):
            return part.text.strip()
    elif response.root.error:
        logger.error(f"A2A error: {response.root.error.message}")
        return f"Error from farm: {response.root.error.message}"
    else:
        logger.error("Unknown response type")
        return "Unknown response type from farm"

@tool
async def get_all_farms_yield_inventory(prompt: str) -> str:
    """
    Fetch all farm yield inventories.

    Args:
    prompt (str): The prompt to send to all farms to retrieve their yields.

    Returns:
    dict: A dictionary containing the yields from all farms.
    """
    logger.info("entering get_all_farms_yield_inventory tool with prompt: %s", prompt)

    client = await factory.create_client(
        "A2A",
        agent_topic=FARM_BROADCAST_TOPIC,
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

    responses = await client.broadcast_message(request, expected_responses=3)

    logger.info(f"got {len(responses)} responses back from farms")

    farm_yields = ""
    for response in responses:
        # we want a dict for farm name -> yield, the yarm_name will be in the response metadata
        if response.root.result and response.root.result.parts:
            part = response.root.result.parts[0].root
            if hasattr(response.root.result, "metadata"):
                farm_name = response.root.result.metadata.get("name", "Unknown Farm")
            else:
                farm_name = "Unknown Farm"

            farm_yields += f"{farm_name} : {part.text.strip()}\n"
        elif response.root.error:
            logger.error(f"A2A error from farm: {response.root.error.message}") 
        else:
            logger.error("Unknown response type from farm")

    print(f"Farm yields: {farm_yields}")
    return farm_yields.strip()

@tool(args_schema=CreateOrderArgs)
async def create_order(farm: str, quantity: int, price: float) -> str:
    """
    Create an order for coffee beans.

    Args:
    price (float): The price of the coffee beans.
    quantity (int): The quantity of the coffee beans.

    Returns:
    str: Confirmation message of the order creation.
    """

    farm = farm.strip().lower()

    logger.info(f"Creating order with price: {price}, quantity: {quantity}")
    if price <= 0 or quantity <= 0:
        return "Price and quantity must be greater than zero."
    
    if farm == "":
        return "No farm was provided, please provide a farm to create an order."
    
    card = get_farm_card(farm)
    if card is None:
        return f"Farm '{farm}' not recognized. Available farms are: {brazil_agent_card.name}, {colombia_agent_card.name}, {vietnam_agent_card.name}."
    
    client = await factory.create_client(
        "A2A",
        agent_topic=A2AProtocol.create_agent_topic(card),
        transport=transport,
    )

    request = SendMessageRequest(
        params=MessageSendParams(
            message=Message(
                messageId=str(uuid4()),
                role=Role.user,
                parts=[Part(TextPart(text=f"Create an order with price {price} and quantity {quantity}"))],
            ),
        )
    )

    response = await client.send_message(request)
    logger.info(f"Response received from A2A agent: {response}")
    if response.root.result and response.root.result.parts:
        part = response.root.result.parts[0].root
        if hasattr(part, "text"):
            return part.text.strip()
    elif response.root.error:
        logger.error(f"A2A error: {response.root.error.message}")
        return f"Error from order agent: {response.root.error.message}"
    else:
        logger.error("Unknown response type")
        return "Unknown response type from order agent"
    
@tool
async def get_order_details(order_id: str) -> str:
    """
    Get details of an order.

    Args:
    order_id (str): The ID of the order.

    Returns:
    str: Details of the order.
    """
    logger.info(f"Getting details for order ID: {order_id}")
    if not order_id:
        return "Order ID must be provided."
    
    client = await factory.create_client(
        "A2A",
        agent_topic=FARM_BROADCAST_TOPIC,
        transport=transport,
    )

    request = SendMessageRequest(
        params=MessageSendParams(
            message=Message(
                messageId=str(uuid4()),
                role=Role.user,
                parts=[Part(TextPart(text=f"Get details for order ID {order_id}"))],
            ),
        )
    )

    response = await client.send_message(request)
    logger.info(f"Response received from A2A agent: {response}")
    if response.root.result and response.root.result.parts:
        part = response.root.result.parts[0].root
        if hasattr(part, "text"):
            return part.text.strip()
    elif response.root.error:
        logger.error(f"A2A error: {response.root.error.message}")
        return f"Error from order agent: {response.root.error.message}"
    else:
        logger.error("Unknown response type")
        return "Unknown response type from order agent"