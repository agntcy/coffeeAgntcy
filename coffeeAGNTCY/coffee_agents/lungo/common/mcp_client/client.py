# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""Single entry point for calling MCP tools over the agntcy message bus.

Every MCP tool call in Lungo flows through :func:`call_mcp_tool`, so the
agntcy-app-sdk client contract lives in exactly one place:

* ``factory.mcp().create_client(...)`` is keyword-only.
* ``call_tool`` is always invoked as ``call_tool(name=..., arguments=...)``.

Per-server differences (topic, timeout, shared-secret identity, whether to
list tools first, and the result shape) are expressed as arguments rather than
as divergent, independently maintained call sites. That is what previously let
a signature regression reach one MCP chain (payment) without touching another
(weather).
"""

from __future__ import annotations

import logging
import os
from typing import Any

from agntcy_app_sdk.factory import AgntcyFactory

from common.mcp_event_middleware import wrap_mcp_client
from config.config import (
	DEFAULT_MESSAGE_TRANSPORT,
	NATS_SERVER,
	OTEL_SDK_DISABLED,
	SLIM_SERVER,
)

logger = logging.getLogger("lungo.common.mcp_client")

_TRANSPORT_MAP: dict[str, tuple[str, str]] = {
	"SLIM": ("SLIM", f"http://{SLIM_SERVER}"),
	"NATS": ("NATS", f"nats://{NATS_SERVER}"),
}

if DEFAULT_MESSAGE_TRANSPORT not in _TRANSPORT_MAP:
	raise ValueError(
		f"Unsupported DEFAULT_MESSAGE_TRANSPORT: {DEFAULT_MESSAGE_TRANSPORT}. "
		"Must be 'SLIM' or 'NATS'."
	)

# Resolved once at import: the transport kind ("SLIM"/"NATS") and its endpoint.
mcp_transport, mcp_endpoint = _TRANSPORT_MAP[DEFAULT_MESSAGE_TRANSPORT]

_DEFAULT_FACTORY_NAME = "lungo.mcp_client"
_DEFAULT_TRANSPORT_NAME = "default/default/mcp_client"


def _build_factory() -> AgntcyFactory:
	"""Build the agntcy factory used to open MCP clients."""
	return AgntcyFactory(_DEFAULT_FACTORY_NAME, enable_tracing=not OTEL_SDK_DISABLED)


async def _extract_text_content(result: Any) -> str:
	"""Normalize an MCP tool result to text (streamed or single response).

	Must run inside the client context: a streamed result is an async
	iterator that is only valid while the session is open.
	"""
	if hasattr(result, "__aiter__"):
		text = ""
		async for chunk in result:
			delta = chunk.choices[0].delta
			text += delta.content or ""
		return text

	content = getattr(result, "content", None)
	if isinstance(content, list) and content:
		return content[0].text
	return "No content returned from tool."


async def call_mcp_tool(
	*,
	topic: str,
	tool_name: str,
	arguments: dict[str, Any] | None = None,
	agent_id: str,
	source: str,
	workflow_name: str | None = None,
	instance_id: str | None = None,
	message_timeout: int | None = None,
	use_shared_secret: bool = True,
	transport_name: str = _DEFAULT_TRANSPORT_NAME,
	list_tools_first: bool = False,
	extract_text: bool = False,
	factory: AgntcyFactory | None = None,
) -> Any:
	"""Call a single MCP tool on ``topic`` and return its result.

	This is the only place that talks to the agntcy-app-sdk MCP client, so the
	call contract is defined once and shared by every Lungo MCP chain.

	Args:
		topic: Message-bus topic the target MCP server listens on
			(e.g. ``"lungo_weather_service"``). Also used as the ``mcp_server``
			label for workflow topology events.
		tool_name: Name of the tool to invoke.
		arguments: Tool arguments; defaults to ``{}``.
		agent_id: Human-readable agent name for event emission.
		source: Stable source id for event emission / correlation.
		workflow_name: Optional workflow identity fallback for event emission.
		instance_id: Optional workflow instance id fallback for event emission.
		message_timeout: Optional per-call client timeout (seconds). When
			omitted the agntcy-app-sdk default applies.
		use_shared_secret: When True, attach ``SLIM_SHARED_SECRET`` to the
			transport identity.
		transport_name: Transport registration name on the bus.
		list_tools_first: When True, log the server's advertised tools before
			calling (diagnostic parity with the original weather path).
		extract_text: When True, return the tool result's text content
			(evaluated inside the client context so streamed results are safe);
			otherwise return the raw tool result.
		factory: Optional pre-built factory (mainly for reuse/testing); a fresh
			factory is created per call when omitted.

	Returns:
		The raw MCP tool result, or its text content when ``extract_text`` is
		set.
	"""
	factory = factory or _build_factory()

	transport_kwargs: dict[str, Any] = {
		"endpoint": mcp_endpoint,
		"name": transport_name,
	}
	if use_shared_secret:
		transport_kwargs["shared_secret_identity"] = os.getenv("SLIM_SHARED_SECRET")

	transport_instance = factory.create_transport(mcp_transport, **transport_kwargs)

	# create_client is keyword-only; message_timeout is only passed when set so
	# callers that don't need it inherit the SDK default.
	client_kwargs: dict[str, Any] = {"topic": topic, "transport": transport_instance}
	if message_timeout is not None:
		client_kwargs["message_timeout"] = message_timeout

	client = await factory.mcp().create_client(**client_kwargs)
	client = wrap_mcp_client(
		client,
		agent_id=agent_id,
		mcp_server=topic,
		source=source,
		workflow_name=workflow_name,
		instance_id=instance_id,
	)

	async with client as session:
		if list_tools_first:
			listing = await session.list_tools()
			logger.info(
				"Available MCP tools on %s: %s",
				topic,
				[tool.name for tool in listing.tools],
			)

		result = await session.call_tool(name=tool_name, arguments=arguments or {})
		if extract_text:
			return await _extract_text_content(result)
		return result
