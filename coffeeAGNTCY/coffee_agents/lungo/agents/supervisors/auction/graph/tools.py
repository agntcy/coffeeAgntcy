# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

import logging
from typing import Any, Literal, Union
from uuid import uuid4

from a2a.client import ClientCallContext
from a2a.helpers import get_message_text
from a2a.types import (
    AgentCard,
    Message,
    Part,
    Role,
    SendMessageRequest,
    SendMessageResponse,
)
from agents.supervisors.auction.card import AUCTION_SUPERVISOR_CARD
from agents.supervisors.auction.graph.a2a_retry import (
    RemoteAgentNoResponseError,
    TransportTimeoutError,
    send_a2a_with_retry,
)
from agents.supervisors.auction.graph.models import (
    CreateOrderArgs,
)
from agents.supervisors.auction.graph.shared import a2a_client_factory, farm_registry
from agntcy_app_sdk import InterfaceTransport, get_agent_identifier
from agntcy_app_sdk.semantic.a2a import A2ABroadcastError
from common.a2a_event_middleware import EventEmittingInterceptor
from common.a2a_helpers import (
    message_metadata,
    prefer_transport,
    response_message,
    response_text,
)
from common.workflow_context_prop import read_workflow_context
from config.config import (
    DEFAULT_MESSAGE_TRANSPORT,
    IDENTITY_API_KEY,
    IDENTITY_API_SERVER_URL,
)
from ioa_observe.sdk.decorators import tool as ioa_tool_decorator
from langchain_core.messages import AnyMessage, ToolMessage
from langchain_core.tools import ToolException, tool
from pydantic import BaseModel
from services.identity_service import IdentityService
from services.identity_service_impl import IdentityServiceImpl

logger = logging.getLogger("lungo.supervisor.tools")


def _workflow_message_metadata() -> dict[str, str] | None:
    """Workflow identity for outbound farm messages.

    Farms emit MCP tool-call events correlated to the supervisor's workflow
    instance; that identity is propagated in the A2A message metadata.
    """
    workflow = read_workflow_context()
    metadata: dict[str, str] = {}
    if workflow.workflow_name:
        metadata["workflow_name"] = workflow.workflow_name
    if workflow.instance_id:
        metadata["workflow_instance_id"] = workflow.instance_id
    return metadata or None


def _transport_should_close_after_tool(transport: object) -> bool:
    """True only for transports that are safe to close after each tool call.

    SLIM/SlimRPC are backed by the process-scoped ``A2AClientFactory`` in
    ``shared.py``; closing them after every call breaks later discovery/broadcast
    (integration conftest keeps that module loaded to avoid duplicate SLIM
    connections). NATS pattern clients are typically per-use and should be
    released.
    """
    cls = type(transport)
    label = f"{getattr(cls, '__module__', '')}.{getattr(cls, '__name__', '')}".lower()
    if "slim" in label:
        return False
    if "nats" in label:
        return True
    return False


async def _dispose_a2a_client(client: object) -> None:
    """Best-effort close for transports that own their connection (e.g. NATS)."""
    transport = getattr(client, "transport", None)
    if transport is None:
        return
    if not _transport_should_close_after_tool(transport):
        return
    closer = getattr(transport, "close", None)
    if closer is None:
        return
    try:
        await closer()
    except Exception:
        logger.debug("A2A client transport close failed", exc_info=True)


# A2A middleware singleton that captures outbound and inbound calls.
_event_interceptor = EventEmittingInterceptor(caller_card=AUCTION_SUPERVISOR_CARD)


class A2AAgentError(ToolException):
    """Custom exception for errors related to A2A agent communication or status."""

    pass


def _extract_text_from_events(events: list) -> str | None:
    """Extract the last text content from a list of A2A ``StreamResponse`` events.

    Reads the message, task status message, or artifact text of each event.
    Returns the last non-empty text found, or None.
    """
    result_text = None
    for response in events:
        text = response_text(response).strip()
        if text:
            result_text = text
    return result_text


def _user_message(text: str, metadata: dict[str, str] | None = None) -> Message:
    """Build an outbound user ``Message`` with a single text part."""
    return Message(
        message_id=str(uuid4()),
        role=Role.ROLE_USER,
        parts=[Part(text=text)],
        metadata=metadata,
    )


def _farm_reply(response: Any) -> tuple[str, str] | None:
    """``(farm name, text)`` of a farm's reply message, or None if it has none."""
    message = response_message(response)
    if message is None:
        return None
    text = get_message_text(message).strip()
    if not text:
        return None
    name = message_metadata(message).get("name") or "Unknown Farm"
    return str(name), text


def _reply_sender(response: Any) -> str | None:
    """Farm display name from a reply's metadata, even when its text is empty."""
    message = response_message(response)
    if message is None:
        return None
    name = message_metadata(message).get("name")
    return str(name) if name else None


def _incomplete_broadcast_note(
    responded: set[str],
    error: A2ABroadcastError | None = None,
    unusable: frozenset[str] | set[str] = frozenset(),
) -> str | None:
    """One sentence naming every farm without a usable reply, with the reason.

    A farm that failed and a farm that never answered are reported once each.
    ``responded`` holds the display names of the farms that gave a usable reply;
    ``error`` is the SDK's ``A2ABroadcastError`` for the broadcast, if it raised
    one; ``unusable`` holds the farms that replied without usable text. Returns
    None when every registered farm answered.
    """
    farm_names = {
        identifier: card.name
        for card in farm_registry.cards()
        if (identifier := get_agent_identifier(card))
    }
    reply_wait = "in time" if error is not None and error.timed_out else "at all"
    # an error reported for the same farm overwrites this; a missing-recipient entry does not
    problems: dict[str, str] = {
        farm: "gave no usable reply" for farm in sorted(unusable - responded)
    }
    unattributed: list[str] = []

    if error is not None:
        for failure in error.failures:
            reason = f"returned an error ({failure.error})"
            farm = farm_names.get(failure.sender) if failure.sender else None
            if farm is None:
                # the SDK got no sender identity with this failure
                unattributed.append(str(failure.error))
            else:
                problems[farm] = reason
        for recipient in error.missing_recipients:
            farm = farm_names.get(recipient, recipient)
            if farm in responded:
                # never name a farm that already gave a usable reply
                continue
            problems.setdefault(farm, f"did not reply {reply_wait}")

    # Farms the SDK could not name (no sender identity): every registered farm
    # without a usable reply and without a reason above.
    for farm in sorted(farm_registry.display_names() - responded - problems.keys()):
        problems[farm] = (
            "gave no usable reply" if unattributed else f"did not reply {reply_wait}"
        )

    if not problems:
        return None
    note = (
        f"Incomplete answer: {len(problems)} of {len(farm_registry)} farms gave no "
        "usable reply: " + "; ".join(f"{farm} {why}" for farm, why in problems.items())
    )
    if unattributed:
        note += f". Errors reported: {'; '.join(unattributed)}"
    return note + "."


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
    ) -> Literal[tools_node, end_node]:  # type: ignore
        if isinstance(state, list):
            ai_message = state[-1]
        elif isinstance(state, dict) and (messages := state.get(messages_key, [])):
            ai_message = messages[-1]
        elif messages := getattr(state, messages_key, []):
            ai_message = messages[-1]
        else:
            raise ValueError(f"No messages found in input state to tool_edge: {state}")

        if isinstance(ai_message, ToolMessage):
            logger.debug(
                "Last message is a ToolMessage, returning end_node: %s", end_node
            )
            return end_node

        if hasattr(ai_message, "tool_calls") and len(ai_message.tool_calls) > 0:
            logger.debug(
                "Last message has tool calls, returning tools_node: %s", tools_node
            )
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
            farm,
            farm_registry.slugs(),
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
        matched_app = next(
            (app for app in all_apps.apps if app.name.lower() == farm_name.lower()),
            None,
        )

        if not matched_app:
            err_msg = "No matching identity app service found, this farm does not have identity service enabled."
            logger.error(err_msg)
            raise A2AAgentError(err_msg)

        badge = identity_service.get_badge_for_app(matched_app.id)
        success = identity_service.verify_badges(badge)

        if success.get("status") is not True:
            raise A2AAgentError("Failed to verify badge.")

        logger.info(f"Verification successful for farm '{farm_name}'.")
    except Exception as e:
        raise A2AAgentError(e)  # Re-raise as our custom exception


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
    logger.info(
        "entering get_farm_yield_inventory tool with prompt: %s, farm: %s", prompt, farm
    )
    if not farm:
        raise ValueError(
            "No farm was provided. Please provide a farm to get the yield from."
        )

    card = get_farm_card(farm)
    if card is None:
        raise A2AAgentError(
            f"Farm '{farm}' not recognized. Available farms "
            f"are: {', '.join(farm_registry.slugs())}."
        )

    client = None
    try:
        try:
            card = prefer_transport(card, DEFAULT_MESSAGE_TRANSPORT)

            # create a client with event middleware to capture tool calls and responses for tracing in the UI
            client = await a2a_client_factory.create(
                card,
                interceptors=[_event_interceptor],
            )

            message = _user_message(prompt, _workflow_message_metadata())

            # call context (workflow identity flows via OTel baggage)
            ctx = ClientCallContext()
            events = await send_a2a_with_retry(client, message, context=ctx)
            result_text = _extract_text_from_events(events)

            if result_text:
                return result_text
            raise A2AAgentError(f"Farm '{farm}' returned no text content.")
        except (TransportTimeoutError, RemoteAgentNoResponseError) as e:
            msg = (
                "timed out"
                if isinstance(e, TransportTimeoutError)
                else "returned no response"
            )
            logger.error(f"Failed to communicate with farm '{farm}': {msg}")
            raise A2AAgentError(
                f"Failed to communicate with farm '{farm}': {msg}."
            ) from e
        except (
            Exception
        ) as e:  # Catch any underlying communication or client creation errors
            logger.error(f"Failed to communicate with farm '{farm}': {e}")
            raise A2AAgentError(
                f"Failed to communicate with farm '{farm}'. Details: {e}"
            )
    finally:
        if client is not None:
            await _dispose_a2a_client(client)


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
        message=_user_message(prompt, _workflow_message_metadata())
    )

    # create a list of recipients to include in the broadcast
    recipients = [get_agent_identifier(get_farm_card(farm)) for farm in farm_registry]

    client = None
    try:
        try:
            # pick any card to initialize the client, will use the recipient list to route to the correct farms;
            # prefer the configured publish-subscribe transport (returns a copy, the singleton card is untouched)
            card = prefer_transport(farm_registry.cards()[0], DEFAULT_MESSAGE_TRANSPORT)

            client = await a2a_client_factory.create(
                card,
                interceptors=[_event_interceptor],
            )

            # set call context for the broadcast (workflow identity comes from baggage)
            ctx = ClientCallContext(
                state={
                    "broadcast_agent_cards": [
                        get_farm_card(farm) for farm in farm_registry
                    ],
                }
            )

            # create a broadcast message and collect responses; a partial result
            # (a farm failed or never answered) arrives as A2ABroadcastError
            broadcast_error: A2ABroadcastError | None = None
            responses: list[SendMessageResponse]
            try:
                responses = await client.broadcast_message(
                    request, recipients=recipients, context=ctx
                )
            except A2ABroadcastError as e:
                logger.warning(f"Broadcast to farms incomplete: {e}")
                broadcast_error = e
                responses = list(e.responses)

            logger.info(f"got {len(responses)} responses back from farms")

            farm_yields = ""
            responded: set[str] = set()
            unusable: set[str] = set()
            skipped_unusable = False
            for response in responses:
                reply = _farm_reply(response)
                if reply is None:
                    # keep the other farms' answers; the closing note names this farm
                    logger.warning("Farm reply without usable text, skipping it")
                    skipped_unusable = True
                    if (sender := _reply_sender(response)) is not None:
                        unusable.add(sender)
                    continue
                farm_name, text = reply
                responded.add(farm_name)
                farm_yields += f"{farm_name} : {text}\n"

            note = (
                _incomplete_broadcast_note(responded, broadcast_error, unusable)
                if broadcast_error is not None or skipped_unusable
                else None
            )
            if not responded:
                raise A2AAgentError(
                    note
                    or (str(broadcast_error) if broadcast_error is not None else None)
                    or "Unknown response type from farm"
                )
            if note:
                farm_yields += f"{note}\n"

            logger.info(f"Farm yields: {farm_yields}")
            return farm_yields.strip()
        except (
            Exception
        ) as e:  # Catch any underlying communication or client creation errors
            logger.error(f"Failed to communicate with all farms during broadcast: {e}")
            raise A2AAgentError(f"Failed to communicate with all farms. Details: {e}")
    finally:
        if client is not None:
            await _dispose_a2a_client(client)


# node utility for streaming
async def get_all_farms_yield_inventory_streaming(prompt: str):
    """
    Broadcasts a prompt to all farms and streams their inventory responses as they arrive.

    Args:
        prompt (str): The prompt to broadcast to all farm agents.

    Yields:
        str: Yield information from each farm as it becomes available.
    """
    logger.info(
        "entering get_all_farms_yield_inventory_streaming tool with prompt: %s", prompt
    )

    request = SendMessageRequest(
        message=_user_message(prompt, _workflow_message_metadata())
    )

    # create a list of recipients to include in the broadcast
    recipients = [get_agent_identifier(get_farm_card(farm)) for farm in farm_registry]

    client = None
    try:
        try:
            logger.info(
                f"Broadcasting to {len(recipients)} farms: {', '.join(recipients)}"
            )

            # prefer the configured publish-subscribe transport for broadcasts
            # (returns a copy, the singleton card is untouched)
            card = prefer_transport(farm_registry.cards()[0], DEFAULT_MESSAGE_TRANSPORT)

            client = await a2a_client_factory.create(
                card,
                interceptors=[_event_interceptor],
            )

            ctx = ClientCallContext(
                state={
                    "broadcast_agent_cards": [
                        get_farm_card(farm) for farm in farm_registry
                    ],
                }
            )

            # Get the async generator for streaming responses. Workflow identity
            # is propagated via OTel context attached in ``graph.py``.
            response_stream = client.broadcast_message_streaming(
                request,
                recipients=recipients,
                context=ctx,
            )

            # Track which farms responded
            responded_farms: set[str] = set()
            unusable: set[str] = set()
            broadcast_error: A2ABroadcastError | None = None

            # Process responses as they arrive. Failed or missing replies are
            # reported once the stream ends, as A2ABroadcastError.
            try:
                async for response in response_stream:
                    try:
                        payload = response.WhichOneof("payload")
                        reply = (
                            _farm_reply(response)
                            if payload in ("message", "task")
                            else None
                        )
                        if reply is None and payload in (
                            "task",
                            "status_update",
                            "artifact_update",
                        ):
                            # intermediate progress event; the farm's answer is its final message
                            logger.debug("Skipping intermediate broadcast event")
                            continue
                        if reply is None:
                            # no separate error line: the closing note names this farm once
                            logger.warning(
                                "Farm reply without usable text, skipping it"
                            )
                            if payload == "message" and (
                                sender := _reply_sender(response)
                            ):
                                unusable.add(sender)
                            continue
                        farm_name, text = reply
                        responded_farms.add(farm_name)
                        logger.info(
                            f"Received response from {farm_name} ({len(responded_farms)}/{len(recipients)})",
                        )
                        yield f"{farm_name} : {text}\n"
                    except Exception as e:
                        logger.error(f"Error processing farm response: {e}")
                        yield f"Error processing farm response: {str(e)}\n"
            except A2ABroadcastError as e:
                logger.warning(f"Broadcast to farms incomplete: {e}")
                if not responded_farms and not e.failures:
                    raise
                broadcast_error = e

            # Report every farm without a usable reply once, with the reason
            note = _incomplete_broadcast_note(
                responded_farms, broadcast_error, unusable
            )
            if note:
                logger.warning(
                    f"Broadcast completed with partial responses: {len(responded_farms)}/{len(recipients)} "
                    "farms responded. " + note
                )
                yield f"{note}\n"

        except Exception as e:
            error_msg = f"Failed to communicate with farms during broadcast: {e}"
            logger.error(error_msg)
            # Check if it's a timeout-related error
            if isinstance(e, TimeoutError) or "timeout" in str(e).lower():
                yield (
                    f"Error: Broadcast timed out. Some farms may be slow to respond or unavailable. {str(e)}\n"
                )
            else:
                yield f"Error: {error_msg}\n"
    finally:
        if client is not None:
            await _dispose_a2a_client(client)


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
        raise ValueError(
            "No farm was provided, please provide a farm to create an order."
        )

    card = get_farm_card(farm)
    if card is None:
        raise ValueError(
            f"Farm '{farm}' not recognized. Available farms are: {', '.join(farm_registry.slugs())}."
        )

    logger.info(f"Using farm card: {card.name} for order creation")
    identity_service = IdentityServiceImpl(
        api_key=IDENTITY_API_KEY, base_url=IDENTITY_API_SERVER_URL
    )
    try:
        verify_farm_identity(identity_service, card.name)
    except Exception as e:
        # log the error and re-raise the exception
        raise A2AAgentError(
            f"Identity verification failed for farm '{farm}'. Details: {e}"
        )

    client = None
    try:
        try:
            # returns a copy, the singleton card is untouched
            card = prefer_transport(card, DEFAULT_MESSAGE_TRANSPORT)

            client = await a2a_client_factory.create(
                card,
                interceptors=[_event_interceptor],
            )

            message = _user_message(
                f"Create an order with price {price} and quantity {quantity}"
            )

            ctx = ClientCallContext()

            events = await send_a2a_with_retry(client, message, context=ctx)
            result_text = _extract_text_from_events(events)

            if result_text:
                return result_text
            raise A2AAgentError(
                f"Farm '{farm}' returned no text content for order creation."
            )
        except (TransportTimeoutError, RemoteAgentNoResponseError) as e:
            msg = (
                "timed out"
                if isinstance(e, TransportTimeoutError)
                else "returned no response"
            )
            logger.error(
                f"Failed to communicate with order agent for farm '{farm}': {msg}"
            )
            raise A2AAgentError(
                f"Failed to communicate with order agent for farm '{farm}': {msg}."
            ) from e
        except (
            Exception
        ) as e:  # Catch any underlying communication or client creation errors
            logger.error(
                f"Failed to communicate with order agent for farm '{farm}': {e}"
            )
            raise A2AAgentError(
                f"Failed to communicate with order agent for farm '{farm}'. Details: {e}"
            )
    finally:
        if client is not None:
            await _dispose_a2a_client(client)


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

    client = None
    try:
        try:
            # pick any card to initialize the client; prefer SLIM to ensure direct
            # communication for order details, even on a NATS run (returns a copy)
            card = prefer_transport(farm_registry.cards()[0], InterfaceTransport.SLIM)

            client = await a2a_client_factory.create(
                card,
                interceptors=[_event_interceptor],
            )

            message = _user_message(f"Get details for order ID {order_id}")

            ctx = ClientCallContext()

            events = await send_a2a_with_retry(client, message, context=ctx)
            result_text = _extract_text_from_events(events)

            if result_text:
                return result_text
            raise A2AAgentError(
                f"Order agent returned no text content for order ID '{order_id}'."
            )
        except (TransportTimeoutError, RemoteAgentNoResponseError) as e:
            msg = (
                "timed out"
                if isinstance(e, TransportTimeoutError)
                else "returned no response"
            )
            logger.error(
                f"Failed to communicate with order agent for order ID '{order_id}': {msg}"
            )
            raise A2AAgentError(
                f"Failed to communicate with order agent for order ID '{order_id}': {msg}.",
            ) from e
        except (
            Exception
        ) as e:  # Catch any underlying communication or client creation errors
            logger.error(
                f"Failed to communicate with order agent for order ID '{order_id}': {e}"
            )
            raise A2AAgentError(
                f"Failed to communicate with order agent for order ID '{order_id}'. Details: {e}",
            )
    finally:
        if client is not None:
            await _dispose_a2a_client(client)
