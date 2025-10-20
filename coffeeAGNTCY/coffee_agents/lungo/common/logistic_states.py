# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

from enum import Enum
import re
import uuid

from typing import Optional

class LogisticStatus(Enum):
  RECEIVED_ORDER = "RECEIVED_ORDER"
  HANDOVER_TO_SHIPPER = "HANDOVER_TO_SHIPPER"
  CUSTOMS_CLEARANCE = "CUSTOMS_CLEARANCE"
  PAYMENT_COMPLETE = "PAYMENT_COMPLETE"
  DELIVERED = "DELIVERED"
  STATUS_UNKNOWN = "STATUS_UNKNOWN"

# Lowercase lookup map -> canonical enum
STATUS_LOOKUP = {s.value: s for s in LogisticStatus}

def extract_status(message: str) -> LogisticStatus | None:
  """
  Extracts the logistic status from a given message string.
  Returns the corresponding LogisticStatus enum member if found, else None.
  """
  print(f"Extracting status from message: {message}")
  for key, status in STATUS_LOOKUP.items():
    if key in message:
      return status
  return LogisticStatus.STATUS_UNKNOWN


# --- Message Formatting Helpers ---

def _base_transition_narrative(
        order_id: str,
        from_state: Optional[str],
        to_state: str,
        sender: str,
        receiver: str,
        details: Optional[str],
) -> str:
  """
  Generic narrative used when no specialized template exists.
  Keeps the `to_state` token first for downstream parsers.
  """
  parts = [
    f"{to_state}",
    f"| {sender} -> {receiver}:",
    f"Order {order_id} advanced",
  ]
  if from_state and from_state != to_state:
    parts.append(f"from {from_state} to {to_state}.")
  else:
    parts.append(f"to {to_state}.")
  if details:
    parts.append(details.rstrip(".") + ".")
  return " ".join(parts)


def _specialized_narrative(
        order_id: str,
        to_state: str,
        sender: str,
        receiver: str,
) -> Optional[str]:
  """
  Return a specialized narrative for well-known states, else None.
  """
  try:
    enum_state = LogisticStatus(to_state)
  except Exception:
    return None

  if enum_state is LogisticStatus.CUSTOMS_CLEARANCE:
    return (
      f"{to_state} | {sender} -> {receiver}: "
      f"Customs cleared for order {order_id}; documents forwarded for payment processing."
    )
  if enum_state is LogisticStatus.PAYMENT_COMPLETE:
    return (
      f"{to_state} | {sender} -> {receiver}: "
      f"Payment confirmed on order {order_id}; preparing final delivery."
    )
  if enum_state is LogisticStatus.DELIVERED:
    return (
      f"{to_state} | {sender} -> {receiver}: "
      f"Order {order_id} delivered successfully; closing shipment cycle."
    )
  if enum_state is LogisticStatus.HANDOVER_TO_SHIPPER:
    return (
      f"{to_state} | {sender} -> {receiver}: "
      f"Order {order_id} handed off for international transit."
    )
  if enum_state is LogisticStatus.RECEIVED_ORDER:
    return (
      f"{to_state} | {sender} -> {receiver}: "
      f"Order {order_id} intake acknowledged; initiating processing workflow."
    )

  return None


def build_transition_message(
        order_id: str,
        sender: str,
        receiver: str,
        to_state: str,
        details: Optional[str] = None,
) -> str:
  """
  Construct a lively, parsable transition message.
  """
  specialized = _specialized_narrative(order_id, to_state, sender, receiver)
  if specialized:
    if details:
      base = specialized.rstrip(".!? ")
      detail_text = details.strip().rstrip(".!? ")
      return f"{base}. {detail_text}."
    return specialized


ORDER_ID_RE = re.compile(r"Order\s+([A-Za-z0-9\-]+)", re.IGNORECASE)
def extract_order_id(message: str) -> str | None:
  """
  Return the first order id found (token after 'Order') or None.
  """
  m = ORDER_ID_RE.search(message)
  return m.group(1) if m else None

def ensure_order_id(message: str, fallback: str | None = None) -> str:
  """
  Return existing order id from message or provided fallback or generate one.
  """
  return extract_order_id(message) or fallback or uuid.uuid4().hex[:12]
