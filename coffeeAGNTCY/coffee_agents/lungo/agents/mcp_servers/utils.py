# Copyright 2025 AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

import os
from typing import Literal

from agents.exceptions import AuthError
from common.mcp_client import call_mcp_tool


async def invoke_payment_mcp_tool(
  tool_name: Literal["create_payment", "list_transactions"],
  *,
  agent_id: str,
  source: str,
  workflow_name: str | None = None,
  instance_id: str | None = None,
) -> dict:
  # don't invoke if identity auth is not enabled
  if os.getenv("IDENTITY_AUTH_ENABLED", "").lower() not in ["true", "enabled"]:
    return {}

  try:
    return await call_mcp_tool(
      topic="lungo_payment_service",
      tool_name=tool_name,
      agent_id=agent_id,
      source=source,
      workflow_name=workflow_name,
      instance_id=instance_id,
      use_shared_secret=False,
      transport_name="default/default/fast_mcp_client",
    )
  except Exception as e:
    error_message = str(e).lower()
    if any(keyword in error_message for keyword in ["authentication failed", "unauthorized"]):
      tool_action = "creating a payment" if tool_name == "create_payment" else "listing transactions"
      raise AuthError(
        f"Authentication failed or unauthorized access detected while {tool_action}. "
      ) from e
    raise
