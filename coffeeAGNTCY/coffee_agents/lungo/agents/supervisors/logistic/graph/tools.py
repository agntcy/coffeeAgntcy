# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

import asyncio
import logging
import re
from typing import Any, Sequence
from uuid import uuid4

from a2a.types import (
  Message,
  MessageSendParams,
  Part,
  Role,
  SendMessageRequest,
  TextPart,
)
from agntcy_app_sdk.protocols.a2a.protocol import A2AProtocol
from fastapi import HTTPException
from langchain_core.messages import ToolMessage
from langchain_core.tools import tool

from agents.logistics.accountant.card import AGENT_CARD as ACCOUNTANT_CARD
from agents.logistics.farm.card import AGENT_CARD as TATOOINE_CARD
from agents.logistics.shipper.card import AGENT_CARD as SHIPPER_CARD
from agents.supervisors.logistic.graph.models import CreateOrderArgs
from agents.supervisors.logistic.graph.shared import get_factory
from config.config import (
  DEFAULT_MESSAGE_TRANSPORT,
  TRANSPORT_SERVER_ENDPOINT,
)
from common.logistic_states import LogisticStatus

logger = logging.getLogger("lungo.logistic.supervisor.tools")


def next_tools_or_end(state: dict[str, Any]) -> str:
  """
  Routing helper for LangGraph:
  - If the last AI message has tool calls -> go to tools node.
  - If the last message is a ToolMessage or has no tool calls -> end.
  Expects state['messages'] to be a non-empty list.
  """
  msg = state["messages"][-1]
  if isinstance(msg, ToolMessage):
    return "__end__"
  return "orders_tools" if getattr(msg, "tool_calls", None) else "__end__"


@tool(args_schema=CreateOrderArgs)
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
  if DEFAULT_MESSAGE_TRANSPORT != "SLIM":
    raise ValueError("Only SLIM transport is supported for logistic agents.")

  farm = farm.strip().lower()
  logger.info("Creating order | farm=%s quantity=%s price=%s", farm or "<none>", quantity, price)

  if price <= 0 or quantity <= 0:
    return "Price and quantity must both be greater than zero."
  if not farm:
    return "No farm provided. Please specify a farm."

  try:
    factory = get_factory()
    transport = factory.create_transport(
      DEFAULT_MESSAGE_TRANSPORT,
      endpoint=TRANSPORT_SERVER_ENDPOINT,
      name="default/default/logistic_graph",
    )
  except Exception as e:
    logger.error("Failed to create factory or transport: %s", e)
    raise HTTPException(status_code=500, detail="Internal server error: failed to create transport")

  try:
    client = await factory.create_client(
      "A2A",
      # Use shipper routable name to satisfy SLIM client creation requirement.
      agent_topic=A2AProtocol.create_agent_topic(SHIPPER_CARD),
      transport=transport,
    )

    request = SendMessageRequest(
      id=str(uuid4()),
      params=MessageSendParams(
        message=Message(
          messageId=str(uuid4()),
          role=Role.user,
          parts=[
            Part(
              TextPart(
                # Note the status must be included to trigger the logistic flow
                text = f"Create an order with price {price} and quantity {quantity}. Status: {LogisticStatus.RECEIVED_ORDER.value}"
              )
            )
          ],
        )
      ),
    )
  except Exception as e:
    logger.error("Failed to create A2A client or message request: %s", e)
    raise HTTPException(status_code=500, detail="Internal server error: failed to create A2A client or message request")

  recipients = [
    A2AProtocol.create_agent_topic(card)
    for card in (SHIPPER_CARD, TATOOINE_CARD, ACCOUNTANT_CARD)
  ]
  logger.info("Broadcasting order to recipients: %s", recipients)

  # Retry configuration
  max_retries = 3
  base_delay = 2.0  # seconds

  for attempt in range(max_retries):
    try:
      responses = await client.broadcast_message(
        request,
        broadcast_topic=f"{uuid4()}",
        recipients=recipients,
        end_message="DELIVERED",
        group_chat=True,
        timeout=60,
      )
      # If we get here, the call succeeded
      break

    except Exception as e:
      if attempt < max_retries - 1:  # Not the last attempt
        delay = base_delay * (2 ** attempt)  # Exponential backoff: 2, 4, 8 seconds
        logger.warning("Broadcast attempt %d failed: %s. Retrying in %.1f seconds...",
                      attempt + 1, str(e), delay)
        await asyncio.sleep(delay)
      else:  # Last attempt failed
        logger.error("Failed to broadcast message after %d attempts: %s", max_retries, e)
        raise HTTPException(status_code=500, detail="Internal server error: failed to process order after retries")

  logger.debug("Raw group chat responses: %s", responses)
  formatted = _summarize_a2a_responses(responses)
  logger.info("Summarized order status: %s", formatted)
  return formatted


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
      msg = response.root.result  # Underlying message object
      name = (msg.metadata or {}).get("name", "Unknown")
      parts = msg.parts or []
      text = next(
        (
          getattr(getattr(p, "root", p), "text", "").strip()
          for p in parts
          if getattr(getattr(p, "root", p), "text", "").strip()
        ),
        "",
      )
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
