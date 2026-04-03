# Copyright 2025 AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

import config.logging_config  # noqa: F401 - runs setup on import; must be first

import logging
import asyncio
import os
from mcp.server.fastmcp import FastMCP
from mcp.server.transport_security import TransportSecuritySettings
from agntcy_app_sdk.app_sessions import AppContainer
from agntcy_app_sdk.factory import AgntcyFactory
from agents.mcp_servers.utils import _mcp_transport, _mcp_endpoint
from config.config import OTEL_SDK_DISABLED

logger = logging.getLogger("payment_service")

mcp = FastMCP(
  transport_security=TransportSecuritySettings(
    enable_dns_rebinding_protection=False, # Disabling this as we are managing security at a different layer of our infrastructure
  )
)

factory = AgntcyFactory("lungo.payment_mcp_server", enable_tracing=not OTEL_SDK_DISABLED)

@mcp.tool()
def create_payment() -> dict:
  """
  Creating a payment.
  Note: This is a sensitive operation that should enforce access control in a real-world payment system.
  """
  return {
    "ok": True,
    "status": "payment created",
    "payment_id": "stub_payment_id",  # fake payment ID
    "amount": 100.00,
    "currency": "USD"
  }

@mcp.tool()
def list_transactions() -> dict:
  """
  Listing transactions.
  Note: This is a sensitive operation that should enforce access control in a real-world payment system.
  """
  return {
    "ok": True,
    "status": "transactions retrieved",
    "transactions": [
      {"transaction_id": "txn_001", "amount": 50.00, "currency": "USD"},
      {"transaction_id": "txn_002", "amount": 75.00, "currency": "USD"}
    ]
  }


async def main():
  transport = factory.create_transport(
    _mcp_transport,
    endpoint=_mcp_endpoint,
    shared_secret_identity=os.getenv("SLIM_SHARED_SECRET"),
    name="default/default/lungo_payment_service",
  )

  app_session = factory.create_app_session()
  app_session \
    .add(mcp._mcp_server) \
    .with_transport(transport) \
    .with_topic("lungo_payment_service") \
    .with_session_id("default_session").build()
  
  await app_session.start_all_sessions(keep_alive=False)
  logger.info("Agent ready")
  await app_session.start_all_sessions(keep_alive=True)

if __name__ == "__main__":
  asyncio.run(main())