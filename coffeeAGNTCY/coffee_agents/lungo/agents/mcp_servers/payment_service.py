# Copyright 2025 AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

import logging
import asyncio
from mcp.server.fastmcp import FastMCP
from agntcy_app_sdk.factory import AgntcyFactory
from config.config import DEFAULT_MESSAGE_TRANSPORT, TRANSPORT_SERVER_ENDPOINT

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("payment_service")

mcp = FastMCP()
factory = AgntcyFactory("lungo_payment_mcp_server", enable_tracing=True)

@mcp.tool()
def authenticate_user() -> dict:
  """Stub: always returns authenticated with a fixed fake token."""
  return {
    "ok": True,
    "status": "user authenticated",
    "authenticated": True,
    "session_token": "stub_session_token"  # fake token
  }

@mcp.tool()
def get_balance(account_id: str = "demo") -> dict:
  """Stub: returns a fixed balance for the given account_id."""
  return {
    "ok": True,
    "status": "balance retrieved",
    "account_id": account_id,
    "balance": 125.75,
    "currency": "USD"
  }

async def main():
  transport = factory.create_transport(
    DEFAULT_MESSAGE_TRANSPORT,
    endpoint=TRANSPORT_SERVER_ENDPOINT,
    name="default/default/lungo_payment_service",
  )
  bridge = factory.create_bridge(mcp, transport=transport, topic="lungo_payment_service")
  await bridge.start(blocking=True)

if __name__ == "__main__":
  asyncio.run(main())