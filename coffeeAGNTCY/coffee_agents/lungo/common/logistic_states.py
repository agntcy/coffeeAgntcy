from enum import Enum

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
