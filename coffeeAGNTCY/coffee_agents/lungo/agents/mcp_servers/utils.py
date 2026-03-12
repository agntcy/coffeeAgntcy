# Copyright 2025 AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

from typing import Literal
from agntcy_app_sdk.factory import AgntcyFactory
from agents.exceptions import AuthError
from common.agentic_patterns import PATTERNS, TransportType
from config.config import SLIM_SERVER, NATS_SERVER, OTEL_SDK_DISABLED
import os

# Resolve the enabled MCP transport variant (slim or nats) from the pattern registry.
# To switch transports, toggle the 'enabled' flag in config/agentic_patterns.yaml
# (e.g. disable slim-mcp-client-server, enable nats-mcp-client-server).
_mcp_pattern = PATTERNS.resolve("mcp-client-server")
_mcp_transport = _mcp_pattern.transport.value.upper()  # "slim" -> "SLIM", "nats" -> "NATS"

# Derive the endpoint from the resolved transport type and existing server configs.
_MCP_ENDPOINT_MAP = {
    TransportType.SLIM: f"http://{SLIM_SERVER}",
    TransportType.NATS: f"nats://{NATS_SERVER}",
}
_mcp_endpoint = _MCP_ENDPOINT_MAP[_mcp_pattern.transport]

async def invoke_payment_mcp_tool(tool_name: Literal["create_payment", "list_transactions"]) -> dict:
  # don't invoke if identity auth is not enabled
  if os.getenv("IDENTITY_AUTH_ENABLED", "").lower() not in ["true", "enabled"]:
    return {}

  factory = AgntcyFactory("lungo.payment_mcp_client", enable_tracing=not OTEL_SDK_DISABLED)

  transport_instance = factory.create_transport(
    transport=_mcp_transport,
    endpoint=_mcp_endpoint,
    name="default/default/fast_mcp_client",
  )

  client = await factory.mcp().create_client(
    "FastMCP",
    agent_topic="lungo_payment_service",
    transport=transport_instance,
    url=os.getenv("MCP_PAYMENT_SERVICE_URL", "http://localhost:8081/mcp"),
  )

  try:
    async with client as c:
      result = await c.call_tool(tool_name, {})
      return result
  except Exception as e:
    error_message = str(e).lower()
    if any(keyword in error_message for keyword in ["authentication failed", "unauthorized"]):
      tool_action = "creating a payment" if tool_name == "create_payment" else "listing transactions"
      raise AuthError(
        f"Authentication failed or unauthorized access detected while {tool_action}. "
      ) from e
    raise
