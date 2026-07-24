# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""Centralized client for calling MCP tools over the agntcy message bus."""

from common.mcp_client.client import (
	call_mcp_tool,
	mcp_endpoint,
	mcp_transport,
)

__all__ = [
	"call_mcp_tool",
	"mcp_endpoint",
	"mcp_transport",
]
