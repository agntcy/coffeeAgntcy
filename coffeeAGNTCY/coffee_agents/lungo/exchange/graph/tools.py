# Copyright AGNTCY Contributors (https://github.com/agntcy)
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
from agntcy_app_sdk.protocols.a2a.protocol import A2AProtocol
from graph.shared import get_factory
from config.config import (
    DEFAULT_MESSAGE_TRANSPORT, 
    TRANSPORT_SERVER_ENDPOINT, 
    FARM_BROADCAST_TOPIC,
    IDENTITY_API_KEY,
    IDENTITY_API_SERVER_URL,
)
from farms.brazil.card import AGENT_CARD as brazil_agent_card
from farms.colombia.card import AGENT_CARD as colombia_agent_card
from farms.vietnam.card import AGENT_CARD as vietnam_agent_card
from exchange.graph.models import (
    InventoryArgs,
    CreateOrderArgs,
)
from services.identity_service import IdentityService
from services.identity_service_impl import IdentityServiceImpl

from ioa_observe.sdk.decorators import tool as ioa_tool_decorator

logger = logging.getLogger("lungo.supervisor.tools")

def tools_or_next(tools_node: str, end_node: str = "__end__"):
  """
  Returns a conditional function for LangGraph to determine the next node 
  based on whether the last message contains tool calls.

  If the message includes tool calls, the workflow proceeds to the `tools_node`.
  If the message is a ToolMessage or has no tool calls, the workflow proceeds to `end_node`.

  Args:
    tools_node (str): The name of the node to route to if tool calls are detected.
    end_node (str, optional): The fallback node if no tool calls are found. Defaults to '__end__'.

  Returns:
    Callable: A function compatible with LangGraph conditional edge handling.
  """

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
    """
    Maps a farm name string to its corresponding AgentCard.

    Args:
        farm (str): The name of the farm (e.g., "Brazil", "Colombia", "Vietnam").

    Returns:
        AgentCard | None: The matching AgentCard if found, otherwise None.
    """
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

def verify_farm_identity(identity_service: IdentityService, farm_name: str):
    """
    Verifies the identity of a farm by matching the farm name with the app name,
    retrieving the badge, and verifying it.

    Args:
        identity_service (IdentityServiceImpl): The identity service implementation.
        farm_name (str): The name of the farm to verify.

    Raises:
        ValueError: If the app is not found or verification fails.
    """
    try:
        all_apps = identity_service.get_all_apps()
        matched_app = None
        for app in all_apps.apps:
            if app.name.lower() == farm_name.lower():
                matched_app = app
                break
        if not matched_app:
            raise ValueError(f"Identity verification failed.")

        badge = identity_service.get_badge_for_app(matched_app.id)
        _ = identity_service.verify_badges(badge)
    except Exception as e:
        logger.error(f"Identity verification failed for farm '{farm_name}': {e}")
        raise ValueError(f"Identity verification failed.")

@tool(args_schema=InventoryArgs)
@ioa_tool_decorator(name="get_farm_yield_inventory")
async def get_farm_yield_inventory(prompt: str, farm: str) -> str:
    """
    Fetch yield inventory from a specific farm.

    Args:
        prompt (str): The prompt to send to the farm to retrieve their yields
        farm (str): The farm to send the request to

    Returns:
        str: current yield amount
    """
    logger.info("entering get_farm_yield_inventory tool with prompt: %s, farm: %s", prompt, farm)
    if farm == "":
        return "No farm was provided, please provide a farm to get the yield from."
    
    card = get_farm_card(farm)
    if card is None:
        return f"Farm '{farm}' not recognized. Available farms are: {brazil_agent_card.name}, {colombia_agent_card.name}, {vietnam_agent_card.name}."
    
    # Shared factory & transport
    factory = get_factory()
    transport = factory.create_transport(
        DEFAULT_MESSAGE_TRANSPORT,
        endpoint=TRANSPORT_SERVER_ENDPOINT,
    )
    
    client = await factory.create_client(
        "A2A",
        agent_topic=A2AProtocol.create_agent_topic(card),
        transport=transport,
    )

    request = SendMessageRequest(
        id=str(uuid4()),
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
@ioa_tool_decorator(name="get_all_farms_yield_inventory")
async def get_all_farms_yield_inventory(prompt: str) -> str:
    """
    Broadcasts a prompt to all farms and aggregates their inventory responses.

    Args:
        prompt (str): The prompt to broadcast to all farm agents.

    Returns:
        str: A summary string containing yield information from all farms.
    """
    logger.info("entering get_all_farms_yield_inventory tool with prompt: %s", prompt)

    # Shared factory & transport
    factory = get_factory()
    transport = factory.create_transport(
        DEFAULT_MESSAGE_TRANSPORT,
        endpoint=TRANSPORT_SERVER_ENDPOINT,
    )

    client = await factory.create_client(
        "A2A",
        agent_topic=FARM_BROADCAST_TOPIC,
        transport=transport,
    )

    request = SendMessageRequest(
        id=str(uuid4()),
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
        # we want a dict for farm name -> yield, the farm_name will be in the response metadata
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

    logger.info(f"Farm yields: {farm_yields}")
    return farm_yields.strip()


@tool(args_schema=CreateOrderArgs)
@ioa_tool_decorator(name="create_order")
async def create_order(farm: str, quantity: int, price: float) -> str:
    """
    Sends a request to create a coffee order with a specific farm.

    Args:
        farm (str): The target farm for the order.
        quantity (int): Quantity of coffee to order.
        price (float): Proposed price per unit.

    Returns:
        str: Confirmation message or error string from the farm agent.
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

    logger.info(f"Using farm card: {card.name} for order creation")
    identity_service = IdentityServiceImpl(api_key=IDENTITY_API_KEY, base_url=IDENTITY_API_SERVER_URL)
    try:
        verify_farm_identity(identity_service, card.name)
    except ValueError as e:
        return str(e)

    # Shared factory & transport
    factory = get_factory()
    transport = factory.create_transport(
        DEFAULT_MESSAGE_TRANSPORT,
        endpoint=TRANSPORT_SERVER_ENDPOINT,
    )

    client = await factory.create_client(
        "A2A",
        agent_topic=A2AProtocol.create_agent_topic(card),
        transport=transport,
    )

    request = SendMessageRequest(
        id=str(uuid4()),
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
@ioa_tool_decorator(name="get_order_details")
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
    
    # Shared factory & transport
    factory = get_factory()
    transport = factory.create_transport(
        DEFAULT_MESSAGE_TRANSPORT,
        endpoint=TRANSPORT_SERVER_ENDPOINT,
    )
    
    client = await factory.create_client(
        "A2A",
        agent_topic=FARM_BROADCAST_TOPIC,
        transport=transport,
    )

    request = SendMessageRequest(
        id=str(uuid4()),
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