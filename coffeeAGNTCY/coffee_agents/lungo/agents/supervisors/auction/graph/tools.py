# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

import logging
import json
import uuid
from datetime import datetime
from typing import Any, Union, Literal, NoReturn, Annotated
from uuid import uuid4
from pydantic import BaseModel
from langchain_core.messages import AIMessage
from langgraph.prebuilt import InjectedState
import redis

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
from agntcy_app_sdk.semantic.a2a.protocol import A2AProtocol
from ioa_observe.sdk.decorators import tool as ioa_tool_decorator


from agents.farms.brazil.card import AGENT_CARD as brazil_agent_card
from agents.farms.colombia.card import AGENT_CARD as colombia_agent_card
from agents.farms.vietnam.card import AGENT_CARD as vietnam_agent_card
from agents.supervisors.auction.graph.models import (
    InventoryArgs,
    CreateOrderArgs,
)
from agents.supervisors.auction.graph.shared import get_factory
from config.config import (
    DEFAULT_MESSAGE_TRANSPORT, 
    TRANSPORT_SERVER_ENDPOINT, 
    FARM_BROADCAST_TOPIC,
    IDENTITY_API_KEY,
    IDENTITY_API_SERVER_URL,
    REDIS_URL,
    REDIS_TTL,
)
from services.identity_service import IdentityService
from services.identity_service_impl import IdentityServiceImpl


logger = logging.getLogger("lungo.supervisor.tools")

# Simple Redis client for tracking
redis_client = redis.from_url(REDIS_URL, decode_responses=True)

def start_step(prompt_id: str, agent_name: str) -> str:
    """Start a new step and return step_id"""
    logger.info(f"DEBUG: start_step called with prompt_id={prompt_id}, agent_name={agent_name}")
    
    if not prompt_id:
        logger.warning("DEBUG: start_step returning None - no prompt_id")
        return None
        
    if not redis_client:
        logger.warning("DEBUG: start_step returning None - no redis_client")
        return None
        
    try:
        # Get existing prompt data
        key = f"prompt:{prompt_id}"
        logger.info(f"DEBUG: Getting existing data from Redis key: {key}")
        existing_data = redis_client.get(key)
        
        if existing_data:
            data = json.loads(existing_data)
            logger.info(f"DEBUG: Found existing data with {len(data.get('route', []))} routes")
        else:
            data = {"prompt_id": prompt_id, "prompt": "", "route": []}
            logger.warning("DEBUG: No existing data found, creating new tracking record")
        
        # Create new step
        step_id = str(uuid.uuid4())
        step = {
            "step_id": step_id,
            "agent_name": agent_name,
            "start_time": datetime.utcnow().isoformat(),
            "end_time": None,
            "success": None
        }
        
        # Add step to route
        data["route"].append(step)
        logger.info(f"DEBUG: Added step to route. New route count: {len(data['route'])}")
        
        # Save back to Redis
        logger.info(f"DEBUG: Saving updated data to Redis with key: {key}")
        redis_client.setex(key, REDIS_TTL, json.dumps(data))
        logger.info(f"DEBUG: Successfully saved to Redis")
        return step_id
        
    except Exception as e:
        logger.error(f"DEBUG: Redis start_step failed with exception: {e}")
        return None

def end_step(prompt_id: str, step_id: str, success: bool):
    """End a step with success status"""
    if not prompt_id or not step_id:
        return
        
    try:
        # Get existing prompt data
        key = f"prompt:{prompt_id}"
        existing_data = redis_client.get(key)
        
        if not existing_data:
            return
            
        data = json.loads(existing_data)
        
        # Find and update the step
        for step in data["route"]:
            if step["step_id"] == step_id:
                step["end_time"] = datetime.utcnow().isoformat()
                step["success"] = success
                break
        
        # Save back to Redis
        redis_client.setex(key, REDIS_TTL, json.dumps(data))
        
    except Exception as e:
        logger.warning(f"Redis end_step failed: {e}")

def create_prompt_tracking(prompt_id: str, prompt: str):
    """Create initial prompt tracking record"""
    try:
        data = {
            "prompt_id": prompt_id,
            "prompt": prompt,
            "route": []
        }
        key = f"prompt:{prompt_id}"
        redis_client.setex(key, REDIS_TTL, json.dumps(data))
    except Exception as e:
        logger.warning(f"Redis create_prompt_tracking failed: {e}")

# Global factory and transport instances
factory = get_factory()
transport = factory.create_transport(
    DEFAULT_MESSAGE_TRANSPORT,
    endpoint=TRANSPORT_SERVER_ENDPOINT,
    name="default/default/exchange_graph"
)


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

# node utility for streaming
async def get_farm_yield_inventory(prompt: str, farm: str, prompt_id: str = None) -> str:
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
    logger.info("TRACKING: Point-to-point inventory request initiated to farm: %s", farm)
    
    logger.info(f"DEBUG: Single farm tool called with prompt_id={prompt_id}")
    
    # Start exchange step (supervisor)
    exchange_step_id = start_step(prompt_id, "exchange") if prompt_id else None
    
    if not farm:
        if prompt_id and exchange_step_id:
            end_step(prompt_id, exchange_step_id, False)
        raise ValueError("No farm was provided. Please provide a farm to get the yield from.")
    
    card = get_farm_card(farm)
    if card is None:
        raise A2AAgentError(f"Farm '{farm}' not recognized. Available farms "
                             f"are: {brazil_agent_card.name}, {colombia_agent_card.name}, {vietnam_agent_card.name}.")
    
    try:
        logger.info("TRACKING: Creating A2A client for farm: %s", farm)
        
        # Start farm step
        farm_step_id = start_step(prompt_id, farm) if prompt_id else None
        
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

        logger.info("TRACKING: Sending inventory request to farm: %s", farm)
        response = await client.send_message(request)
        logger.info(f"Response received from A2A agent: {response}")
        
        if response.root.result and response.root.result.parts:
            part = response.root.result.parts[0].root
            if hasattr(part, "text"):
                logger.info("TRACKING: Successfully received inventory response from farm: %s", farm)
                if prompt_id and farm_step_id:
                    end_step(prompt_id, farm_step_id, True)
                if prompt_id and exchange_step_id:
                    end_step(prompt_id, exchange_step_id, True)
                return part.text.strip()
            else:
                logger.error("TRACKING: Farm %s returned result without text content", farm)
                if prompt_id and farm_step_id:
                    end_step(prompt_id, farm_step_id, False)
                if prompt_id and exchange_step_id:
                    end_step(prompt_id, exchange_step_id, False)
                raise A2AAgentError(f"Farm '{farm}' returned a result without text content.")
        elif response.root.error:
                logger.error(f"A2A error from farm '{farm}': {response.root.error.message}")
                logger.error("TRACKING: Inventory request failed for farm: %s", farm)
                if prompt_id and farm_step_id:
                    end_step(prompt_id, farm_step_id, False)
                if prompt_id and exchange_step_id:
                    end_step(prompt_id, exchange_step_id, False)
                raise A2AAgentError(f"Error from farm '{farm}': {response.root.error.message}")
        else:
            logger.error(f"Unknown response type from farm '{farm}'.")
            logger.error("TRACKING: Unknown response type from farm: %s", farm)
            if prompt_id and farm_step_id:
                end_step(prompt_id, farm_step_id, False)
            if prompt_id and exchange_step_id:
                end_step(prompt_id, exchange_step_id, False)
            raise A2AAgentError(f"Unknown response type from farm '{farm}'.")
    except Exception as e: # Catch any underlying communication or client creation errors
        logger.error(f"Failed to communicate with farm '{farm}': {e}")
        logger.error("TRACKING: Communication failed with farm: %s", farm)
        if prompt_id and exchange_step_id:
            end_step(prompt_id, exchange_step_id, False)
        raise A2AAgentError(f"Failed to communicate with farm '{farm}'. Details: {e}")

# node utility for streaming
async def get_all_farms_yield_inventory(prompt: str, state: Annotated[dict, InjectedState]) -> str:
    """
    Broadcasts a prompt to all farms and aggregates their inventory responses.

    Args:
        prompt (str): The prompt to broadcast to all farm agents.

    Returns:
        str: A summary string containing yield information from all farms.
    """
    logger.info("entering get_all_farms_yield_inventory tool with prompt: %s", prompt)
    logger.info("TRACKING: Broadcast inventory request initiated to ALL farms")
    
    # Extract prompt_id from state
    prompt_id = state.get("prompt_id") if state else None
    logger.info(f"DEBUG: Broadcast tool called with prompt_id={prompt_id}, state={state}")
    
    # Start exchange step (supervisor)
    exchange_step_id = start_step(prompt_id, "exchange") if prompt_id else None
    logger.info(f"DEBUG: Started exchange step with step_id={exchange_step_id}")

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

    if DEFAULT_MESSAGE_TRANSPORT == "SLIM":
        client_handshake_topic = A2AProtocol.create_agent_topic(get_farm_card("brazil"))
    else:
        # using NATS 
        client_handshake_topic = FARM_BROADCAST_TOPIC

    try:
        logger.info("TRACKING: Creating broadcast client for all farms")
        # create an A2A client, retrieving an A2A card from agent_topic
        client = await factory.create_client(
            "A2A",
            agent_topic=client_handshake_topic,
            transport=transport,
        )

        # create a list of recipients to include in the broadcast
        recipients = [A2AProtocol.create_agent_topic(get_farm_card(farm)) for farm in ['brazil', 'colombia', 'vietnam']]
        
        logger.info("TRACKING: Sending broadcast to farms: %s", ', '.join(['brazil', 'colombia', 'vietnam']))
        # create a broadcast message and collect responses
        responses = await client.broadcast_message(request, broadcast_topic=FARM_BROADCAST_TOPIC, recipients=recipients)

        logger.info(f"got {len(responses)} responses back from farms")
        logger.info("TRACKING: Received %d responses from broadcast", len(responses))

        farm_yields = ""
        farm_step_ids = {}
        for response in responses:
            # we want a dict for farm name -> yield, the farm_name will be in the response metadata
            if response.root.result and response.root.result.parts:
                part = response.root.result.parts[0].root
                if hasattr(response.root.result, "metadata"):
                    farm_name = response.root.result.metadata.get("name", "Unknown Farm")
                else:
                    farm_name = "Unknown Farm"

                # Extract canonical farm name from metadata
                canonical_farm_name = "unknown"
                
                # Map display names to canonical names
                if "brazil" in farm_name.lower():
                    canonical_farm_name = "brazil"
                elif "vietnam" in farm_name.lower():
                    canonical_farm_name = "vietnam"
                elif "colombia" in farm_name.lower():
                    canonical_farm_name = "colombia"

                # Start farm step
                farm_step_id = start_step(prompt_id, canonical_farm_name) if prompt_id else None
                farm_step_ids[farm_name] = farm_step_id

                logger.info("TRACKING: Successfully received inventory response from farm: %s (canonical: %s)", farm_name, canonical_farm_name)
                farm_yields += f"{farm_name} : {part.text.strip()}\n"
                
                # End farm step
                if prompt_id and farm_step_id:
                    end_step(prompt_id, farm_step_id, True)
            elif response.root.error:
                err_msg = f"A2A error from farm: {response.root.error.message}"
                logger.error(err_msg)
                logger.error("TRACKING: Broadcast inventory request failed for a farm")
                # End all farm steps and exchange step on error
                for farm_name, step_id in farm_step_ids.items():
                    if prompt_id and step_id:
                        end_step(prompt_id, step_id, False)
                if prompt_id and exchange_step_id:
                    end_step(prompt_id, exchange_step_id, False)
                raise A2AAgentError(err_msg)
            else:
                err_msg = f"Unknown response type from farm"
                logger.error(err_msg)
                logger.error("TRACKING: Unknown response type from farm during broadcast")
                # End all farm steps and exchange step on error
                for farm_name, step_id in farm_step_ids.items():
                    if prompt_id and step_id:
                        end_step(prompt_id, step_id, False)
                if prompt_id and exchange_step_id:
                    end_step(prompt_id, exchange_step_id, False)
                raise A2AAgentError(err_msg)

        logger.info(f"Farm yields: {farm_yields}")
        logger.info("TRACKING: Successfully completed broadcast inventory request")
        if prompt_id and exchange_step_id:
            end_step(prompt_id, exchange_step_id, True)
        return farm_yields.strip()
    except Exception as e: # Catch any underlying communication or client creation errors
        logger.error(f"Failed to communicate with all farms during broadcast: {e}")
        logger.error("TRACKING: Broadcast inventory request failed")
        if prompt_id and exchange_step_id:
            end_step(prompt_id, exchange_step_id, False)
        raise A2AAgentError(f"Failed to communicate with all farms. Details: {e}")

# node utility for streaming
async def get_all_farms_yield_inventory_streaming(prompt: str, prompt_id: str = None):
    """
    Broadcasts a prompt to all farms and streams their inventory responses as they arrive.

    Args:
        prompt (str): The prompt to broadcast to all farm agents.

    Yields:
        str: Yield information from each farm as it becomes available.
    """
    logger.info("entering get_all_farms_yield_inventory_streaming tool with prompt: %s", prompt)
    logger.info("TRACKING STREAMING: Broadcast inventory request initiated to ALL farms")
    
    logger.info(f"DEBUG STREAMING: Broadcast tool called with prompt_id={prompt_id}")
    
    # Start exchange step (supervisor)
    exchange_step_id = start_step(prompt_id, "exchange") if prompt_id else None
    logger.info(f"DEBUG STREAMING: Started exchange step with step_id={exchange_step_id}")

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

    if DEFAULT_MESSAGE_TRANSPORT == "SLIM":
        client_handshake_topic = A2AProtocol.create_agent_topic(get_farm_card("brazil"))
    else:
        # using NATS
        client_handshake_topic = FARM_BROADCAST_TOPIC

    try:
        # create an A2A client, retrieving an A2A card from agent_topic
        client = await factory.create_client(
            "A2A",
            agent_topic=client_handshake_topic,
            transport=transport,
        )

        # create a list of recipients to include in the broadcast
        farm_names = ['brazil', 'colombia', 'vietnam']
        recipients = [A2AProtocol.create_agent_topic(get_farm_card(farm)) for farm in farm_names]
        logger.info(f"Broadcasting to {len(recipients)} farms: {', '.join(farm_names)}")

        # Get the async generator for streaming responses
        response_stream = client.broadcast_message_streaming(
            request,
            broadcast_topic=FARM_BROADCAST_TOPIC,
            recipients=recipients
        )

        # Track which farms responded
        responded_farms = set()
        errors = []
        
        # Process responses as they arrive
        async for response in response_stream:
            try:
                if response.root.result and response.root.result.parts:
                    part = response.root.result.parts[0].root
                    farm_name = "Unknown Farm"
                    if hasattr(response.root.result, "metadata"):
                        farm_name = response.root.result.metadata.get("name", "Unknown Farm")

                    if farm_name == "None":
                        # received error from farm agent
                        errors.append(part.text.strip())
                    else:
                        # Extract canonical farm name from metadata
                        canonical_farm_name = "unknown"
                        
                        # Map display names to canonical names
                        if "brazil" in farm_name.lower():
                            canonical_farm_name = "brazil"
                        elif "vietnam" in farm_name.lower():
                            canonical_farm_name = "vietnam"
                        elif "colombia" in farm_name.lower():
                            canonical_farm_name = "colombia"
                        
                        # Start farm step with canonical name
                        farm_step_id = start_step(prompt_id, canonical_farm_name) if prompt_id else None
                        logger.info(f"DEBUG STREAMING: Started farm step for {canonical_farm_name} (display: {farm_name}) with step_id={farm_step_id}")
                        
                        responded_farms.add(farm_name)
                        logger.info(f"Received response from {farm_name} ({len(responded_farms)}/{len(recipients)})")
                        
                        # Yield the response
                        yield f"{farm_name} : {part.text.strip()}\n"
                        
                        # End farm step after yielding
                        if prompt_id and farm_step_id:
                            end_step(prompt_id, farm_step_id, True)
                            logger.info(f"DEBUG STREAMING: Ended farm step for {canonical_farm_name}")
                elif response.root.error:
                    err_msg = f"A2A error from farm: {response.root.error.message}"
                    logger.error(err_msg)
                    yield f"Error from farm: {response.root.error.message}\n"
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
            expected_farms = {"Brazil Coffee Farm", "Colombia Coffee Farm", "Vietnam Coffee Farm"}
            missing_farms = expected_farms - responded_farms
            
            if missing_farms:
                missing_list = ", ".join(sorted(missing_farms))
                logger.warning(f"Broadcast completed with partial responses: {len(responded_farms)}/{len(recipients)} farms responded. Missing: {missing_list}")

                response = f"No response from {missing_list}. These farms may be unavailable or slow to respond."
                if len(errors) != 0:
                    readable_errors = "\n".join(errors)
                    response += f" Errors encountered from farms:\n{readable_errors}\n"

                yield response

        # End exchange step after all processing complete
        if prompt_id and exchange_step_id:
            end_step(prompt_id, exchange_step_id, True)
            logger.info(f"DEBUG STREAMING: Ended exchange step for broadcast")


    except Exception as e:
        error_msg = f"Failed to communicate with farms during broadcast: {e}"
        logger.error(error_msg)
        
        # End exchange step on error
        if prompt_id and exchange_step_id:
            end_step(prompt_id, exchange_step_id, False)
            logger.error(f"DEBUG STREAMING: Ended exchange step due to error: {e}")
        
        # Check if it's a timeout-related error
        if "timeout" in str(e).lower():
            yield f"Error: Broadcast timed out. Some farms may be slow to respond or unavailable. {str(e)}\n"
        else:
            yield f"Error: {error_msg}\n"

@tool(args_schema=CreateOrderArgs)
@ioa_tool_decorator(name="create_order")
async def create_order(farm: str, quantity: int, price: float, state: Annotated[dict, InjectedState]) -> str:
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
    logger.info("TRACKING: Create order request initiated for farm: %s, quantity: %d, price: %.2f", farm, quantity, price)
    
    # Extract prompt_id from state
    prompt_id = state.get("prompt_id") if state else None
    
    # Start exchange step (supervisor)
    exchange_step_id = start_step(prompt_id, "exchange") if prompt_id else None
    
    if price <= 0 or quantity <= 0:
        if prompt_id and exchange_step_id:
            end_step(prompt_id, exchange_step_id, False)
        raise ValueError("Price and quantity must be greater than zero.")
    
    if not farm:
        if prompt_id and exchange_step_id:
            end_step(prompt_id, exchange_step_id, False)
        raise ValueError("No farm was provided, please provide a farm to create an order.")
    
    card = get_farm_card(farm)
    if card is None:
        raise ValueError(f"Farm '{farm}' not recognized. Available farms are: {brazil_agent_card.name}, {colombia_agent_card.name}, {vietnam_agent_card.name}.")

    logger.info(f"Using farm card: {card.name} for order creation")
    logger.info("TRACKING: Creating A2A client for order to farm: %s", farm)
    
    identity_service = IdentityServiceImpl(api_key=IDENTITY_API_KEY, base_url=IDENTITY_API_SERVER_URL)
    try:
        verify_farm_identity(identity_service, card.name)
        logger.info("TRACKING: Identity verification successful for farm: %s", farm)
    except Exception as e:
        # log the error and re-raise the exception
        logger.error("TRACKING: Identity verification failed for farm: %s", farm)
        if prompt_id and exchange_step_id:
            end_step(prompt_id, exchange_step_id, False)
        raise A2AAgentError(f"Identity verification failed for farm '{farm}'. Details: {e}")

    try:
        client = await factory.create_client(
            "A2A",
            agent_topic=A2AProtocol.create_agent_topic(card),
            transport=transport,
        )

        # Start farm step
        farm_step_id = start_step(prompt_id, farm) if prompt_id else None

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

        logger.info("TRACKING: Sending order request to farm: %s", farm)
        response = await client.send_message(request)
        logger.info(f"Response received from A2A agent: {response}")

        if response.root.result and response.root.result.parts:
            part = response.root.result.parts[0].root
            if hasattr(part, "text"):
                logger.info("TRACKING: Successfully received order confirmation from farm: %s", farm)
                if prompt_id and farm_step_id:
                    end_step(prompt_id, farm_step_id, True)
                if prompt_id and exchange_step_id:
                    end_step(prompt_id, exchange_step_id, True)
                return part.text.strip()
            else:
                logger.error("TRACKING: Farm %s returned order result without text content", farm)
                if prompt_id and farm_step_id:
                    end_step(prompt_id, farm_step_id, False)
                if prompt_id and exchange_step_id:
                    end_step(prompt_id, exchange_step_id, False)
                raise A2AAgentError(f"Farm '{farm}' returned a result without text content for order creation.")
        elif response.root.error:
            logger.error(f"A2A error: {response.root.error.message}")
            logger.error("TRACKING: Order request failed for farm: %s", farm)
            if prompt_id and farm_step_id:
                end_step(prompt_id, farm_step_id, False)
            if prompt_id and exchange_step_id:
                end_step(prompt_id, exchange_step_id, False)
            raise A2AAgentError(f"Error from order agent for farm '{farm}': {response.root.error.message}")
        else:
            logger.error("Unknown response type")
            logger.error("TRACKING: Unknown response type from farm: %s for order", farm)
            if prompt_id and farm_step_id:
                end_step(prompt_id, farm_step_id, False)
            if prompt_id and exchange_step_id:
                end_step(prompt_id, exchange_step_id, False)
            raise A2AAgentError("Unknown response type from order agent")
    except Exception as e: # Catch any underlying communication or client creation errors
        logger.error(f"Failed to communicate with order agent for farm '{farm}': {e}")
        logger.error("TRACKING: Order communication failed with farm: %s", farm)
        if prompt_id and exchange_step_id:
            end_step(prompt_id, exchange_step_id, False)
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
            else:
                raise A2AAgentError(f"Order agent returned a result without text content for order ID '{order_id}'.")
        elif response.root.error:
            logger.error(f"A2A error from order agent for order ID '{order_id}': {response.root.error.message}")
            raise A2AAgentError(f"Error from order agent for order ID '{order_id}': {response.root.error.message}")
        else:
            logger.error(f"Unknown response type from order agent for order ID '{order_id}'.")
            raise A2AAgentError(f"Unknown response type from order agent for order ID '{order_id}'.")
    except Exception as e: # Catch any underlying communication or client creation errors
        logger.error(f"Failed to communicate with order agent for order ID '{order_id}': {e}")
        raise A2AAgentError(f"Failed to communicate with order agent for order ID '{order_id}'. Details: {e}")
