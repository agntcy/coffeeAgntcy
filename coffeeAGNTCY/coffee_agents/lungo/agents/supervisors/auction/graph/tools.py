# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

import copy
import logging
from typing import Any, Union, Literal, NoReturn
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
from langchain_core.tools import tool, ToolException
from langchain_core.messages import AnyMessage, ToolMessage
from agntcy_app_sdk import InterfaceTransport, get_agent_identifier
from ioa_observe.sdk.decorators import tool as ioa_tool_decorator


from agents.supervisors.auction.graph.models import (
    InventoryArgs,
    CreateOrderArgs,
)
from agents.supervisors.auction.graph.shared import a2a_client_factory, farm_registry
from common.agentic_patterns import PATTERNS, TransportType
from config.config import (
    IDENTITY_API_KEY,
    IDENTITY_API_SERVER_URL,
)
from services.identity_service import IdentityService
from services.identity_service_impl import IdentityServiceImpl


logger = logging.getLogger("lungo.supervisor.tools")

# Resolve the enabled publish-subscribe pattern for broadcast operations.
# To switch transports, toggle the 'enabled' flag in config/agentic_patterns.yaml
# (e.g. disable slim-publish-subscribe, enable nats-publish-subscribe).
_pubsub_pattern = PATTERNS.resolve("publish-subscribe")
_broadcast_transport = _pubsub_pattern.transport
logger.info(f"Resolved broadcast transport: {_broadcast_transport} from enabled publish-subscribe pattern: {_pubsub_pattern.name}")


class A2AAgentError(ToolException):
    """Custom exception for errors related to A2A agent communication or status."""
    pass


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
    Look up a farm's AgentCard by its canonical slug.

    Args:
        farm (str): The canonical slug of the farm (e.g., "brazil", "colombia", "vietnam").

    Returns:
        AgentCard | None: The matching AgentCard if found, otherwise None.
    """
    card = farm_registry.get(farm)
    if card is None:
        logger.error(
            "Unknown farm slug: '%s'. Registered farms: %s",
            farm, farm_registry.slugs(),
        )
    return card

def verify_farm_identity(identity_service: IdentityService, farm_name: str):
    """
    Verifies the identity of a farm by matching the farm name with the app name,
    retrieving the badge, and verifying it.

    Args:
        identity_service (IdentityServiceImpl): The identity service implementation.
        farm_name (str): The name of the farm to verify.

    Raises:
        A2AAgentError: If the app is not found or verification fails.
    """
    try:
        all_apps = identity_service.get_all_apps()
        matched_app = next((app for app in all_apps.apps if app.name.lower() == farm_name.lower()), None)

        if not matched_app:
            err_msg = f"No matching identity app service found, this farm does not have identity service enabled."
            logger.error(err_msg)
            raise A2AAgentError(err_msg)


        badge = identity_service.get_badge_for_app(matched_app.id)
        success = identity_service.verify_badges(badge)

        if success.get("status") is not True:
            raise A2AAgentError(f"Failed to verify badge.")

        logger.info(f"Verification successful for farm '{farm_name}'.")
    except Exception as e:
        raise A2AAgentError(e) # Re-raise as our custom exception

async def get_farm_yield_inventory(prompt: str, farm: str) -> str:
    """
    Fetch yield inventory from a specific farm.

    Args:
        prompt (str): The prompt to send to the farm to retrieve their yields
        farm (str): The farm to send the request to

    Returns:
        str: current yield amount

    Raises:
        A2AAgentError: If there's an issue with farm identification, communication, or the farm agent returns an error.
        ValueError: For invalid input arguments.
    """
    logger.info("entering get_farm_yield_inventory tool with prompt: %s, farm: %s", prompt, farm)
    if not farm:
        raise ValueError("No farm was provided. Please provide a farm to get the yield from.")
    
    card = get_farm_card(farm)
    if card is None:
        raise A2AAgentError(f"Farm '{farm}' not recognized. Available farms "
                             f"are: {', '.join(farm_registry.slugs())}.")
    
    try:
        card = copy.deepcopy(card)
        # Disable streaming: send_message returns an async generator,
        # so we iterate with `async for` instead of `await`.
        if card.capabilities is None:
            from a2a.types import AgentCapabilities
            card.capabilities = AgentCapabilities(streaming=False)
        else:
            card.capabilities.streaming = False

        client = await a2a_client_factory.create(card)

        message = Message(
            messageId=str(uuid4()),
            role=Role.user,
            parts=[Part(TextPart(text=prompt))],
        )

        result_text = None
        async for response in client.send_message(message):
            logger.info(f"Response received from A2A agent: {response}")

            if isinstance(response, Message):
                for part in response.parts:
                    part_root = part.root
                    if hasattr(part_root, "text"):
                        result_text = part_root.text.strip()
            elif isinstance(response, tuple):
                task_update, event = response
                if hasattr(task_update, "status") and task_update.status and task_update.status.message:
                    for part in task_update.status.message.parts:
                        part_root = part.root
                        if hasattr(part_root, "text"):
                            result_text = part_root.text.strip()

        if result_text:
            return result_text
        else:
            raise A2AAgentError(f"Farm '{farm}' returned no text content.")
    except Exception as e: # Catch any underlying communication or client creation errors
        logger.error(f"Failed to communicate with farm '{farm}': {e}")
        raise A2AAgentError(f"Failed to communicate with farm '{farm}'. Details: {e}")

# node utility for streaming
async def get_all_farms_yield_inventory(prompt: str) -> str:
    """
    Broadcasts a prompt to all farms and aggregates their inventory responses.

    Args:
        prompt (str): The prompt to broadcast to all farm agents.

    Returns:
        str: A summary string containing yield information from all farms.
    """
    logger.info("entering get_all_farms_yield_inventory tool with prompt: %s", prompt)

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
    
    # create a list of recipients to include in the broadcast
    recipients = [
        get_agent_identifier(get_farm_card(farm), interface_type=InterfaceTransport.SLIM_RPC) for farm in farm_registry
    ]

    try:
        # pick any card to initialize the client, will use the recipient list to route to the correct farms
        card = copy.deepcopy(farm_registry.cards()[0]) # avoid mutating the singleton card

        # use the resolved broadcast transport from the pattern registry
        card.preferred_transport = _broadcast_transport
        client = await a2a_client_factory.create(card)

        # create a broadcast message and collect responses
        responses = await client.broadcast_message(request, recipients=recipients)

        logger.info(f"got {len(responses)} responses back from farms")

        farm_yields = ""
        for response in responses:
            err = getattr(response.root, "error", None)
            result = getattr(response.root, "result", None)
            if err:
                err_msg = f"A2A error from farm: {err.message}"
                logger.error(err_msg)
                raise A2AAgentError(err_msg)
            if result and result.parts:
                part = result.parts[0].root
                farm_name = "Unknown Farm"
                if hasattr(result, "metadata") and result.metadata:
                    farm_name = result.metadata.get("name", "Unknown Farm")
                farm_yields += f"{farm_name} : {part.text.strip()}\n"
            else:
                err_msg = "Unknown response type from farm"
                logger.error(err_msg)
                raise A2AAgentError(err_msg)

        logger.info(f"Farm yields: {farm_yields}")
        return farm_yields.strip()
    except Exception as e: # Catch any underlying communication or client creation errors
        logger.error(f"Failed to communicate with all farms during broadcast: {e}")
        raise A2AAgentError(f"Failed to communicate with all farms. Details: {e}")

# node utility for streaming
async def get_all_farms_yield_inventory_streaming(prompt: str):
    """
    Broadcasts a prompt to all farms and streams their inventory responses as they arrive.

    Args:
        prompt (str): The prompt to broadcast to all farm agents.

    Yields:
        str: Yield information from each farm as it becomes available.
    """
    logger.info("entering get_all_farms_yield_inventory_streaming tool with prompt: %s", prompt)

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
    
    # create a list of recipients to include in the broadcast
    recipients = [
        get_agent_identifier(get_farm_card(farm), interface_type=InterfaceTransport.SLIM_RPC) for farm in farm_registry
    ]

    try:
        logger.info(f"Broadcasting to {len(recipients)} farms: {', '.join(recipients)}")

        card = copy.deepcopy(farm_registry.cards()[0]) # avoid mutating the singleton card

        # use the resolved broadcast transport from the pattern registry
        card.preferred_transport = _broadcast_transport
        client = await a2a_client_factory.create(card)

        # Get the async generator for streaming responses
        response_stream = client.broadcast_message_streaming(
            request,
            recipients=recipients
        )

        # Track which farms responded
        responded_farms = set()
        errors = []
        
        # Process responses as they arrive
        async for response in response_stream:
            try:
                err = getattr(response.root, "error", None)
                result = getattr(response.root, "result", None)
                if err:
                    err_msg = f"A2A error from farm: {err.message}"
                    logger.error(err_msg)
                    yield f"Error from farm: {err.message}\n"
                elif result and result.parts:
                    part = result.parts[0].root
                    farm_name = "Unknown Farm"
                    if hasattr(result, "metadata"):
                        farm_name = result.metadata.get("name", "Unknown Farm")

                    if farm_name == "None":
                        errors.append(part.text.strip())
                    else:
                        responded_farms.add(farm_name)
                        logger.info(f"Received response from {farm_name} ({len(responded_farms)}/{len(recipients)})")
                        yield f"{farm_name} : {part.text.strip()}\n"
                else:
                    err_msg = "Unknown response type from farm"
                    logger.error(err_msg)
                    yield f"Error: Unknown response format from farm\n"
            except Exception as e:
                logger.error(f"Error processing farm response: {e}")
                yield f"Error processing farm response: {str(e)}\n"
        
        # Check for missing responses and report them
        if len(responded_farms) < len(recipients):
            # Determine which farms didn't respond by checking farm names
            expected_farms = farm_registry.display_names()
            missing_farms = expected_farms - responded_farms
            
            if missing_farms:
                missing_list = ", ".join(sorted(missing_farms))
                logger.warning(f"Broadcast completed with partial responses: {len(responded_farms)}/{len(recipients)} farms responded. Missing: {missing_list}")

                response = f"No response from {missing_list}. These farms may be unavailable or slow to respond."
                if len(errors) != 0:
                    readable_errors = "\n".join(errors)
                    response += f" Errors encountered from farms:\n{readable_errors}\n"

                yield response


    except Exception as e:
        error_msg = f"Failed to communicate with farms during broadcast: {e}"
        logger.error(error_msg)
        # Check if it's a timeout-related error
        if "timeout" in str(e).lower():
            yield f"Error: Broadcast timed out. Some farms may be slow to respond or unavailable. {str(e)}\n"
        else:
            yield f"Error: {error_msg}\n"

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

    Raises:
        A2AAgentError: If there's an issue with farm identification, identity verification, communication, or the farm agent returns an error.
        ValueError: For invalid input arguments.
    """

    farm = farm.strip().lower()

    logger.info(f"Creating order with price: {price}, quantity: {quantity}")
    if price <= 0 or quantity <= 0:
        raise ValueError("Price and quantity must be greater than zero.")
    
    if not farm:
        raise ValueError("No farm was provided, please provide a farm to create an order.")
    
    card = get_farm_card(farm)
    if card is None:
        raise ValueError(f"Farm '{farm}' not recognized. Available farms are: {', '.join(farm_registry.slugs())}.")

    logger.info(f"Using farm card: {card.name} for order creation")
    identity_service = IdentityServiceImpl(api_key=IDENTITY_API_KEY, base_url=IDENTITY_API_SERVER_URL)
    try:
        verify_farm_identity(identity_service, card.name)
    except Exception as e:
        # log the error and re-raise the exception
        raise A2AAgentError(f"Identity verification failed for farm '{farm}'. Details: {e}")

    try:
        card = copy.deepcopy(card)  # avoid mutating the singleton card
        #card.preferred_transport = "slimrpc" # override preferred transport to ensure direct communication for order creation
        # Disable streaming: the SRPCTransport.send_message_streaming wrapper
        # returns a coroutine instead of an async generator, which breaks
        # BaseClient's streaming path.  Force the non-streaming (simple
        # await) code path instead.
        if card.capabilities is None:
            from a2a.types import AgentCapabilities
            card.capabilities = AgentCapabilities(streaming=False)
        else:
            card.capabilities.streaming = False

        client = await a2a_client_factory.create(card)

        message = Message(
            messageId=str(uuid4()),
            role=Role.user,
            parts=[Part(TextPart(text=f"Create an order with price {price} and quantity {quantity}"))],
        )

        result_text = None
        async for response in client.send_message(message):
            logger.info(f"Response received from A2A agent: {response}")

            if isinstance(response, Message):
                for part in response.parts:
                    part_root = part.root
                    if hasattr(part_root, "text"):
                        result_text = part_root.text.strip()
            elif isinstance(response, tuple):
                task_update, event = response
                if hasattr(task_update, "status") and task_update.status and task_update.status.message:
                    for part in task_update.status.message.parts:
                        part_root = part.root
                        if hasattr(part_root, "text"):
                            result_text = part_root.text.strip()

        if result_text:
            return result_text
        else:
            raise A2AAgentError(f"Farm '{farm}' returned no text content for order creation.")
    except Exception as e: # Catch any underlying communication or client creation errors
        logger.error(f"Failed to communicate with order agent for farm '{farm}': {e}")
        raise A2AAgentError(f"Failed to communicate with order agent for farm '{farm}'. Details: {e}")

@tool
@ioa_tool_decorator(name="get_order_details")
async def get_order_details(order_id: str) -> str:
    """
    Get details of an order.

    Args:
    order_id (str): The ID of the order.

    Returns:
    str: Details of the order.

    Raises:
    A2AAgentError: If there's an issue with communication or the order agent returns an error.
    ValueError: For invalid input arguments.
    """
    logger.info(f"Getting details for order ID: {order_id}")
    if not order_id:
        raise ValueError("Order ID must be provided.")

    try:
        # pick any card to initialize the client
        card = copy.deepcopy(farm_registry.cards()[0]) # avoid mutating the singleton card
        # override preferred transport to ensure direct communication for order creation
        card.preferred_transport = InterfaceTransport.SLIM_RPC

        # Disable streaming to use the non-streaming code path
        if card.capabilities is None:
            from a2a.types import AgentCapabilities
            card.capabilities = AgentCapabilities(streaming=False)
        else:
            card.capabilities.streaming = False

        client = await a2a_client_factory.create(card)

        message = Message(
            messageId=str(uuid4()),
            role=Role.user,
            parts=[Part(TextPart(text=f"Get details for order ID {order_id}"))],
        )

        result_text = None
        async for response in client.send_message(message):
            logger.info(f"Response received from A2A agent: {response}")

            if isinstance(response, Message):
                for part in response.parts:
                    part_root = part.root
                    if hasattr(part_root, "text"):
                        result_text = part_root.text.strip()
            elif isinstance(response, tuple):
                task_update, event = response
                if hasattr(task_update, "status") and task_update.status and task_update.status.message:
                    for part in task_update.status.message.parts:
                        part_root = part.root
                        if hasattr(part_root, "text"):
                            result_text = part_root.text.strip()

        if result_text:
            return result_text
        else:
            raise A2AAgentError(f"Order agent returned no text content for order ID '{order_id}'.")
    except Exception as e: # Catch any underlying communication or client creation errors
        logger.error(f"Failed to communicate with order agent for order ID '{order_id}': {e}")
        raise A2AAgentError(f"Failed to communicate with order agent for order ID '{order_id}'. Details: {e}")
