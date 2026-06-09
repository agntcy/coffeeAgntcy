# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""Client-side MCP middleware for emitting workflow topology events.

Wraps an MCP client so each ``call_tool`` invocation emits a transient
topology node: CREATE when the call starts and DELETE when it ends (success
or error, including streamed responses). Pure event builders live in
``common.workflow_utils.mcp``; this module owns the orchestration (identity
resolution, timing, sink lifecycle).
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from time import monotonic
from typing import Any, AsyncIterator
from uuid import uuid4

from pydantic import ValidationError

from common.workflow_utils.event_sink import WorkflowAPIEventSink
from common.workflow_utils.inflight import (
	RuntimeIdAllocator,
	read_trace_context,
	resolve_correlation_id,
)
from common.workflow_utils.mcp import emit_mcp_tool_call_event
from common.workflow_utils.workflow_catalog import lookup_workflow
from config.config import EMIT_WORKFLOW_EVENTS
from schema.types import InstanceId, Operation

logger = logging.getLogger("lungo.common.event_middleware")


def _is_valid_instance_id(instance_id: str) -> bool:
	"""True when *instance_id* matches the schema's ``instance://<uuid>`` form."""
	try:
		InstanceId(root=instance_id)
	except ValidationError:
		return False
	return True


@dataclass(frozen=True)
class _ResolvedIdentity:
	"""Workflow identity resolved for a single tool call."""

	workflow_name: str
	instance_id: str
	trace_id: int | None
	span_id: int | None


class EventEmittingMCPClient:
	"""Wrap an MCP client and emit topology events around ``call_tool``."""

	def __init__(
		self,
		client: Any,
		*,
		agent_id: str,
		mcp_server: str,
		source: str,
		layer_index: int = 0,
	) -> None:
		self._client = client
		self._agent_id = agent_id
		self._mcp_server = mcp_server
		self._source = source
		self._layer_index = layer_index
		self._allocator = RuntimeIdAllocator()
		# Active call_tool count: the invoking-agent node is created on the
		# first in-flight call and deleted when the last one ends.
		self._inflight = 0

		if not EMIT_WORKFLOW_EVENTS:
			logger.warning(
				"EventEmittingMCPClient [%s]: EMIT_WORKFLOW_EVENTS is false, "
				"wrapper will not emit events.",
				self._source,
			)
			self._event_sink: WorkflowAPIEventSink | None = None
		else:
			self._event_sink = WorkflowAPIEventSink()

	async def __aenter__(self) -> "EventEmittingMCPClient":
		entered = await self._client.__aenter__()
		# Some clients return a distinct session object from __aenter__.
		if entered is not None and entered is not self._client:
			self._client = entered
		return self

	async def __aexit__(self, *exc_info: Any) -> Any:
		return await self._client.__aexit__(*exc_info)

	def __getattr__(self, item: str) -> Any:
		# Only reached for attributes not defined on the wrapper itself, so
		# methods like list_tools transparently hit the underlying client.
		client = self.__dict__.get("_client")
		if client is None:
			raise AttributeError(item)
		return getattr(client, item)

	@staticmethod
	def _extract_tool_name(args: tuple[Any, ...], kwargs: dict[str, Any]) -> str:
		if "name" in kwargs:
			return str(kwargs["name"])
		if args:
			return str(args[0])
		return "unknown"

	def _resolve_identity(self) -> _ResolvedIdentity | None:
		"""Resolve workflow identity from OTel context; None to skip emission.

		Identity is read from the OTel baggage the farm executor establishes via
		``workflow_context_scope`` around ``agent.ainvoke``. This works because
		LangGraph runs its nodes as asyncio tasks, which inherit the scope's
		contextvars; it would silently stop resolving if a tool call were ever
		dispatched to a thread pool (no contextvar propagation there).
		"""
		trace_ctx = read_trace_context()
		metadata = lookup_workflow(trace_ctx.workflow.workflow_name)
		if metadata is None:
			logger.debug(
				"EventEmittingMCPClient [%s]: no catalog match for propagated "
				"workflow_name=%r; skipping MCP event emission.",
				self._source,
				trace_ctx.workflow.workflow_name,
			)
			return None

		instance_id = trace_ctx.workflow.instance_id
		if not instance_id or not _is_valid_instance_id(instance_id):
			logger.debug(
				"EventEmittingMCPClient [%s]: missing or malformed propagated "
				"workflow_instance_id=%r; skipping MCP event emission.",
				self._source,
				instance_id,
			)
			return None

		return _ResolvedIdentity(
			workflow_name=metadata.workflow_name,
			instance_id=instance_id,
			trace_id=trace_ctx.trace_id,
			span_id=trace_ctx.span_id,
		)

	async def _emit(
		self,
		*,
		operation: Operation,
		tool_name: str,
		call_key: str,
		correlation_id: str,
		identity: _ResolvedIdentity,
		duration_ms: float | None = None,
		error: str | None = None,
		delete_agent_node: bool = False,
	) -> None:
		"""Best-effort emission; never propagates failures to the tool call."""
		if self._event_sink is None:
			return
		try:
			await emit_mcp_tool_call_event(
				sink=self._event_sink,
				source=self._source,
				agent_id=self._agent_id,
				tool_name=tool_name,
				mcp_server=self._mcp_server,
				operation=operation,
				allocator=self._allocator,
				call_key=call_key,
				correlation_id=correlation_id,
				workflow_name=identity.workflow_name,
				instance_id=identity.instance_id,
				trace_id=identity.trace_id,
				span_id=identity.span_id,
				layer_index=self._layer_index,
				duration_ms=duration_ms,
				error=error,
				delete_agent_node=delete_agent_node,
			)
		except Exception as exc:
			logger.warning(
				"EventEmittingMCPClient [%s]: failed to emit %s event for tool "
				"%s: %s",
				self._source,
				operation,
				tool_name,
				exc,
			)

	async def _emit_end(
		self,
		*,
		tool_name: str,
		call_key: str,
		correlation_id: str,
		identity: _ResolvedIdentity,
		start: float,
		error: str | None = None,
	) -> None:
		"""Emit the DELETE event, removing the agent node on the last call."""
		self._inflight -= 1
		await self._emit(
			operation=Operation.DELETE,
			tool_name=tool_name,
			call_key=call_key,
			correlation_id=correlation_id,
			identity=identity,
			duration_ms=(monotonic() - start) * 1000.0,
			error=error,
			delete_agent_node=self._inflight <= 0,
		)

	async def call_tool(self, *args: Any, **kwargs: Any) -> Any:
		"""Invoke the underlying tool, emitting CREATE/DELETE topology events."""
		if self._event_sink is None:
			return await self._client.call_tool(*args, **kwargs)

		identity = self._resolve_identity()
		if identity is None:
			return await self._client.call_tool(*args, **kwargs)

		tool_name = self._extract_tool_name(args, kwargs)
		correlation_id = resolve_correlation_id(ctx_state={}, trace_id=identity.trace_id)
		call_key = f"mcp-tool-{self._agent_id}-{tool_name}-{uuid4()}"

		self._inflight += 1
		await self._emit(
			operation=Operation.CREATE,
			tool_name=tool_name,
			call_key=call_key,
			correlation_id=correlation_id,
			identity=identity,
		)

		start = monotonic()
		try:
			result = await self._client.call_tool(*args, **kwargs)
		except Exception as exc:
			await self._emit_end(
				tool_name=tool_name,
				call_key=call_key,
				correlation_id=correlation_id,
				identity=identity,
				start=start,
				error=str(exc),
			)
			raise

		if hasattr(result, "__aiter__"):
			return self._instrument_stream(
				result,
				tool_name=tool_name,
				call_key=call_key,
				correlation_id=correlation_id,
				identity=identity,
				start=start,
			)

		await self._emit_end(
			tool_name=tool_name,
			call_key=call_key,
			correlation_id=correlation_id,
			identity=identity,
			start=start,
		)
		return result

	async def _instrument_stream(
		self,
		source_iter: AsyncIterator[Any],
		*,
		tool_name: str,
		call_key: str,
		correlation_id: str,
		identity: _ResolvedIdentity,
		start: float,
	) -> AsyncIterator[Any]:
		"""Forward streamed chunks, emitting DELETE on completion or error."""
		error: str | None = None
		try:
			async for chunk in source_iter:
				yield chunk
		except Exception as exc:
			error = str(exc)
			raise
		finally:
			await self._emit_end(
				tool_name=tool_name,
				call_key=call_key,
				correlation_id=correlation_id,
				identity=identity,
				start=start,
				error=error,
			)


def wrap_mcp_client(
	client: Any,
	*,
	agent_id: str,
	mcp_server: str,
	source: str,
	layer_index: int = 0,
) -> EventEmittingMCPClient:
	"""Wrap an MCP client (or its async context manager) for event emission."""
	return EventEmittingMCPClient(
		client,
		agent_id=agent_id,
		mcp_server=mcp_server,
		source=source,
		layer_index=layer_index,
	)
