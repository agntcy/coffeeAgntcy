# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

import asyncio
import logging
import os
import re
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional, Sequence
from uuid import uuid4

from a2a.helpers import get_message_text
from a2a.types import (
    Message,
    Part,
    Role,
    SendMessageRequest,
)
from agents.logistics.accountant.card import AGENT_CARD as ACCOUNTANT_CARD
from agents.logistics.farm.card import AGENT_CARD as TATOOINE_CARD
from agents.logistics.helpdesk.card import AGENT_CARD as HELPDESK_CARD
from agents.logistics.shipper.card import AGENT_CARD as SHIPPER_CARD
from agents.supervisors.logistics.card import LOGISTICS_SUPERVISOR_CARD
from agents.supervisors.logistics.graph.shared import a2a_client_factory
from agntcy_app_sdk import get_agent_identifier
from common.a2a_event_middleware import EventEmittingInterceptor
from common.a2a_helpers import message_metadata, response_message, response_text
from common.logistics_states import LogisticsStatus
from fastapi import HTTPException

logger = logging.getLogger("lungo.logistics.supervisor.tools")


# A2A middleware singleton that captures outbound and inbound calls.
_event_interceptor = EventEmittingInterceptor(caller_card=LOGISTICS_SUPERVISOR_CARD)


def _order_request(text: str) -> SendMessageRequest:
    """Build the group chat's initial user message."""
    return SendMessageRequest(
        message=Message(
            message_id=str(uuid4()),
            role=Role.ROLE_USER,
            parts=[Part(text=text)],
        )
    )


def _reply_name_and_text(response: Any) -> tuple[str, str] | None:
    """``(metadata.name, text)`` of a group chat reply, or None without a message."""
    msg = response_message(response)
    if msg is None:
        return None
    name = message_metadata(msg).get("name") or "Unknown"
    return str(name), get_message_text(msg).strip()


async def create_order(farm: str, quantity: int, price: float) -> str:
    """
    Broadcast a coffee order request to shipper, farm, and accountant agents via SLIM.

    Args:
        farm: Target farm name (currently informational; broadcast goes to fixed set).
        quantity: Units requested (must be > 0).
        price: Proposed unit price (must be > 0).

    Returns:
        Aggregated status summary string.
    """

    farm = farm.strip().lower()
    logger.info(
        "Creating order | farm=%s quantity=%s price=%s",
        farm or "<none>",
        quantity,
        price,
    )

    if price <= 0 or quantity <= 0:
        return "Price and quantity must both be greater than zero."
    if not farm:
        return "No farm provided. Please specify a farm."

    try:
        client = await a2a_client_factory.create(
            SHIPPER_CARD,
            interceptors=[_event_interceptor],
        )

        # Note the status must be included to trigger the logistic flow
        request = _order_request(
            f"{LogisticsStatus.RECEIVED_ORDER.value} | Supervisor -> Tatooine Farm: Create an order {uuid.uuid4().hex} with price {price} and quantity {quantity}."
        )
    except Exception as e:
        logger.error("Failed to create A2A client or message request: %s", e)
        raise HTTPException(
            status_code=500,
            detail="Internal server error: failed to create A2A client or message request",
        )

    # Experimental: includes the HelpDesk in the broadcast (enabled by default for broader testing and demos).
    # Known issue: concurrent delete_session executions may cause the agents to lose connectivity from SLIM.
    # (see https://github.com/agntcy/slim/issues/780; tentative fix targeted for versions 0.6.0 or 0.7.0).
    # Note: Helpdesk agent is an additional agent that will listen to the peer group messages.
    helpdesk_enabled = os.getenv("EXPERIMENTAL_FEATURE", "false").lower() == "true"
    logger.info("Helpdesk enabled: %s", helpdesk_enabled)
    base_cards = (SHIPPER_CARD, TATOOINE_CARD, ACCOUNTANT_CARD)
    cards = base_cards + (HELPDESK_CARD,) if helpdesk_enabled else base_cards

    recipients = [get_agent_identifier(card) for card in cards]
    logger.info(
        "Broadcasting order to recipients (helpdesk_enabled=%s): %s",
        helpdesk_enabled,
        recipients,
    )

    # Retry configuration
    max_retries = 3
    base_delay = 2.0  # seconds

    for attempt in range(max_retries):
        try:
            responses = await client.start_groupchat(
                init_message=request,
                group_channel=f"{uuid4()}",
                participants=recipients,
                end_message="DELIVERED",
                timeout=60,
            )
            # If we get here, the call succeeded
            break

        except Exception as e:
            if attempt < max_retries - 1:  # Not the last attempt
                delay = base_delay * (
                    2**attempt
                )  # Exponential backoff: 2, 4, 8 seconds
                logger.warning(
                    "Broadcast attempt %d failed: %s. Retrying in %.1f seconds...",
                    attempt + 1,
                    str(e),
                    delay,
                )
                await asyncio.sleep(delay)
            else:  # Last attempt failed
                logger.error(
                    "Failed to broadcast message after %d attempts: %s", max_retries, e
                )
                raise HTTPException(
                    status_code=500,
                    detail="Internal server error: failed to process order after retries",
                )

    logger.debug("Raw peer group responses: %s", responses)
    formatted = _summarize_a2a_responses(responses)
    return formatted


async def create_order_streaming(farm: str, quantity: int, price: float):
    """
    Broadcast a coffee order request to shipper, farm, and accountant agents via SLIM with streaming support.

    Args:
        farm: Target farm name (currently informational; broadcast goes to fixed set).
        quantity: Units requested (must be > 0).
        price: Proposed unit price (must be > 0).

    Yields:
        Response objects from agents as they arrive (idle messages are filtered out).
    """

    farm = farm.strip().lower()
    logger.info(
        "Creating order | farm=%s quantity=%s price=%s",
        farm or "<none>",
        quantity,
        price,
    )

    if price <= 0 or quantity <= 0:
        yield "Price and quantity must both be greater than zero."
        return
    if not farm:
        yield "No farm provided. Please specify a farm."
        return

    cards = (SHIPPER_CARD, TATOOINE_CARD, ACCOUNTANT_CARD)
    recipients = [get_agent_identifier(card) for card in cards]

    try:
        client = await a2a_client_factory.create(
            SHIPPER_CARD,
            interceptors=[_event_interceptor],
        )  # slim is the first (preferred) interface in these cards
        order_id = str(uuid4())
        logger.debug(f"Sending order {order_id} to agent: {farm}")

        # Note the status must be included to trigger the logistic flow
        request = _order_request(
            f"{LogisticsStatus.RECEIVED_ORDER.value} | Supervisor -> Tatooine Farm: Create an order {order_id} with price {price} and quantity {quantity}."
        )
    except Exception as e:
        logger.error("Failed to create A2A client or message request: %s", e)
        raise HTTPException(
            status_code=500,
            detail="Internal server error: failed to create A2A client or message request",
        )

    logger.info("Streaming order to recipients: %s", recipients)

    try:
        # Yield the initial RECEIVED_ORDER message from Supervisor
        initial_message = {
            "order_id": order_id,
            "sender": "Supervisor",
            "receiver": "Tatooine Farm",
            "message": f"Create an order {order_id} with price {price} and quantity {quantity}.",
            "state": "RECEIVED_ORDER",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        yield initial_message

        responses = client.start_streaming_groupchat(
            init_message=request,
            group_channel=f"{uuid4()}",
            participants=recipients,
            end_message="DELIVERED",
            timeout=60,
        )
        async for response in responses:
            logger.debug("Streaming response: %s", response)
            # Skip idle messages
            if "idle" not in response_text(response).lower():
                # Parse the response into structured format
                parsed_event = _parse_order_event(response)
                if parsed_event:
                    # Add delay to simulate streaming chunks
                    await asyncio.sleep(1.0)
                    yield parsed_event
    except Exception as e:
        logger.error("Failed to broadcast message: %s", e)
        raise HTTPException(
            status_code=500, detail="Internal server error: failed to process order"
        )


def _summarize_a2a_responses(responses: Sequence[Any]) -> str:
    """
    Summarize A2A SendMessageResponse objects into a single status line.

    Rules:
      - Skip messages containing 'idle' (case-insensitive).
      - Aggregate non-final statuses per agent in first-seen order.
      - Each 'delivered' (case-insensitive whole word) status becomes its own segment.
      - Preserve chronological order for first agent appearance and delivered segments.
      - Append '(final)' if any delivered status was observed.
    """
    agent_first_order: list[str] = []
    agent_statuses: dict[str, list[str]] = {}
    delivered_segments: list[str] = []
    delivered_seen = False

    for response in responses:
        try:
            reply = _reply_name_and_text(response)
            if reply is None:
                continue
            name, text = reply
            if not text or "idle" in text.lower():
                continue

            if re.search(r"\bdelivered\b", text, re.IGNORECASE):
                delivered_seen = True
                delivered_segments.append(f"{name}: {text}")
                continue

            if name not in agent_statuses:
                agent_statuses[name] = []
                agent_first_order.append(name)

            if not agent_statuses[name] or agent_statuses[name][-1] != text:
                agent_statuses[name].append(text)
        except Exception:  # noqa: BLE001
            # Skip malformed entries silently
            continue

    if not agent_first_order and not delivered_segments:
        return "No non-idle status updates received."

    segments: list[str] = [
        f"{agent}: {', '.join(agent_statuses[agent])}"
        for agent in agent_first_order
        if agent_statuses[agent]
    ]
    segments.extend(delivered_segments)

    summary = "Order status updates: " + " | ".join(segments)
    if delivered_seen:
        summary += " (final)"
    return summary


def _parse_order_event(response: Any) -> Optional[Dict[str, str]]:
    """
    Parse a group chat reply (StreamResponse or SendMessageResponse) and
    extract order event details.

    Returns:
      Dict with order_id, sender, receiver, message, state, timestamp
    """
    try:
        reply = _reply_name_and_text(response)
        if reply is None:
            return None
        sender_raw, text = reply

        # Map agent names to their role names
        # "Shipping agent" -> "Shipper", "Tatooine Farm agent" -> "Tatooine Farm", etc.
        if sender_raw == "Unknown":
            sender = "Unknown"
        elif "Shipping" in sender_raw or "Shipper" in sender_raw:
            sender = "Shipper"
        else:
            # Remove " agent" suffix for other agents
            sender = sender_raw.replace(" agent", "")

        if not text:
            return None

        # Parse the text: "STATE | Sender -> Receiver: Message"
        parts = text.split("|", 1)
        if len(parts) != 2:
            return None

        state = parts[0].strip()
        remainder = parts[1].strip()

        # Split sender -> receiver : message
        arrow_parts = remainder.split("->", 1)
        if len(arrow_parts) != 2:
            return None

        recv_and_msg = arrow_parts[1].strip()
        recv_parts = recv_and_msg.split(":", 1)
        if len(recv_parts) != 2:
            return None

        receiver = recv_parts[0].strip()
        message = recv_parts[1].strip()

        # Extract order ID from message (UUID with or without dashes)
        order_id_match = re.search(
            r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}",
            message.lower(),
        )
        if not order_id_match:
            order_id_match = re.search(r"[0-9a-f]{32}", message.lower())

        order_id = order_id_match.group(0) if order_id_match else "unknown"

        # Generate timestamp
        timestamp = datetime.now(timezone.utc).isoformat()

        return {
            "order_id": order_id,
            "sender": sender,
            "receiver": receiver,
            "message": message,
            "state": state,
            "timestamp": timestamp,
        }
    except Exception as e:
        logger.error(f"Failed to parse order event: {e}")
        return None
