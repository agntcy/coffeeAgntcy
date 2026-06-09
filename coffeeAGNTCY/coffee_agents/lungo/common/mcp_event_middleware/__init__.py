# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""Client-side MCP middleware for workflow topology event emission."""

from common.mcp_event_middleware.wrapper import (
	EventEmittingMCPClient,
	wrap_mcp_client,
)

__all__ = [
	"EventEmittingMCPClient",
	"wrap_mcp_client",
]
