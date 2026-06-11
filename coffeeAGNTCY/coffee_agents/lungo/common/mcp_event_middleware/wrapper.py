# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""Client-side MCP middleware for emitting workflow topology events.

Wraps an MCP client so each ``call_tool`` invocation emits a transient
topology node: CREATE when the call starts and DELETE when it ends (success
or error, including streamed responses). Pure event builders live in
``common.workflow_utils.mcp``; this module owns the orchestration (identity
resolution, timing, sink lifecycle).

Workflow identity for the farm-to-MCP hop is resolved once, at wrap time,
in this order:

1. OTel baggage (present and non-empty) — the identity the farm executor
   re-establishes around ``agent.ainvoke`` from the supervisor metadata.
2. Explicit ``workflow_name``/``instance_id`` passed by the call site.
3. None — the original MCP client is returned unwrapped and no events are
   emitted, preserving the pre-instrumentation behavior.
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
	"""Workflow identity resolved for a wrapped MCP client."""

	workflow_name: str
	instance_id: str
	trace_id: int | None
	span_id: int | None


def _identity_from(
	workflow_name: str | None,
	instance_id: str | None,
	*,
	trace_id: int | None,
	span_id: int | None,
) -> _ResolvedIdentity | None:
	"""Validate one ``(workflow_name, instance_id)`` candidate into an identity.

	Returns None when the workflow_name is not in the catalog or the
	instance_id is missing/malformed, so the caller can try the next source.
	"""
	metadata = lookup_workflow(workflow_name)
	if metadata is None:
		return None
	if not instance_id or not _is_valid_instance_id(instance_id):
		return None
	return _ResolvedIdentity(
		workflow_name=metadata.workflow_name,
		instance_id=instance_id,
		trace_id=trace_id,
		span_id=span_id,
	)


def _resolve_identity(
	*,
	source: str,
	explicit_workflow_name: str | None,
	explicit_instance_id: str | None,
) -> _ResolvedIdentity | None:
	"""Resolve workflow identity for the farm-to-MCP hop.

	Tries OTel baggage first (the identity the farm executor re-establishes
	around ``agent.ainvoke``), then the explicit values passed by the call
	site, then gives up (None) so the client is left unwrapped.
	"""
	trace_ctx = read_trace_context()

	baggage_name = trace_ctx.workflow.workflow_name
	baggage_instance = trace_ctx.workflow.instance_id
	if baggage_name or baggage_instance:
		identity = _identity_from(
			baggage_name,
			baggage_instance,
			trace_id=trace_ctx.trace_id,
			span_id=trace_ctx.span_id,
		)
		if identity is not None:
			return identity

	if explicit_workflow_name or explicit_instance_id:
		identity = _identity_from(
			explicit_workflow_name,
			explicit_instance_id,
			trace_id=trace_ctx.trace_id,
			span_id=trace_ctx.span_id,
		)
		if identity is not None:
			return identity

	logger.debug(
		"wrap_mcp_client [%s]: no resolvable workflow identity (baggage "
		"name=%r instance=%r; explicit name=%r instance=%r); leaving MCP "
		"client unwrapped.",
		source,
		baggage_name,
		baggage_instance,
		explicit_workflow_name,
		explicit_instance_id,
	)
	return None


class EventEmittingMCPClient:
	"""Wrap an MCP client and emit topology events around ``call_tool``.

	Constructed only with an already-resolved identity (see
	``wrap_mcp_client``), so emission is unconditional once wrapped.
	"""

	def __init__(
		self,
		client: Any,
		*,
		agent_id: str,
		mcp_server: str,
		source: str,
		identity: _ResolvedIdentity,
		layer_index: int = 0,
	) -> None:
		# ``_cm`` is the async context manager handed to us; ``_session`` is the
		# object that exposes call_tool/list_tools. They are the same until
		# __aenter__ yields a distinct session (as the real SDK client does):
		# __aexit__ must always close ``_cm`` so its teardown runs, while method
		# delegation must target ``_session``.
		self._cm = client
		self._session = client
		self._agent_id = agent_id
		self._mcp_server = mcp_server
		self._source = source
		self._identity = identity
		self._layer_index = layer_index
		self._allocator = RuntimeIdAllocator()
		# Active call_tool count: the invoking-agent node is created on the
		# first in-flight call and deleted when the last one ends.
		self._inflight = 0
		self._event_sink = WorkflowAPIEventSink()

	async def __aenter__(self) -> "EventEmittingMCPClient":
		entered = await self._cm.__aenter__()
		# Some clients (e.g. the agntcy SDK MCP client) return a distinct
		# session object from __aenter__; route method calls to it.
		self._session = entered if entered is not None else self._cm
		return self

	async def __aexit__(self, *exc_info: Any) -> Any:
		# Exit the original context manager, never the yielded session: the
		# SDK client's teardown (cancelling anyio task groups, closing
		# streams) lives in the context manager's finally block.
		return await self._cm.__aexit__(*exc_info)

	def __getattr__(self, item: str) -> Any:
		# Only reached for attributes not defined on the wrapper itself, so
		# methods like list_tools transparently hit the underlying session.
		session = self.__dict__.get("_session")
		if session is None:
			raise AttributeError(item)
		return getattr(session, item)

	@staticmethod
	def _extract_tool_name(args: tuple[Any, ...], kwargs: dict[str, Any]) -> str:
		if "name" in kwargs:
			return str(kwargs["name"])
		if args:
			return str(args[0])
		return "unknown"

	async def _emit(
		self,
		*,
		operation: Operation,
		tool_name: str,
		call_key: str,
		correlation_id: str,
		duration_ms: float | None = None,
		error: str | None = None,
		delete_agent_node: bool = False,
	) -> None:
		"""Best-effort emission; never propagates failures to the tool call."""
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
				workflow_name=self._identity.workflow_name,
				instance_id=self._identity.instance_id,
				trace_id=self._identity.trace_id,
				span_id=self._identity.span_id,
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
			duration_ms=(monotonic() - start) * 1000.0,
			error=error,
			delete_agent_node=self._inflight <= 0,
		)

	async def call_tool(self, *args: Any, **kwargs: Any) -> Any:
		"""Invoke the underlying tool, emitting CREATE/DELETE topology events."""
		tool_name = self._extract_tool_name(args, kwargs)
		correlation_id = resolve_correlation_id(
			ctx_state={}, trace_id=self._identity.trace_id,
		)
		call_key = f"mcp-tool-{self._agent_id}-{tool_name}-{uuid4()}"

		self._inflight += 1
		await self._emit(
			operation=Operation.CREATE,
			tool_name=tool_name,
			call_key=call_key,
			correlation_id=correlation_id,
		)

		start = monotonic()
		try:
			result = await self._session.call_tool(*args, **kwargs)
		except Exception as exc:
			await self._emit_end(
				tool_name=tool_name,
				call_key=call_key,
				correlation_id=correlation_id,
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
				start=start,
			)

		await self._emit_end(
			tool_name=tool_name,
			call_key=call_key,
			correlation_id=correlation_id,
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
				start=start,
				error=error,
			)


def wrap_mcp_client(
	client: Any,
	*,
	agent_id: str,
	mcp_server: str,
	source: str,
	workflow_name: str | None = None,
	instance_id: str | None = None,
	layer_index: int = 0,
) -> Any:
	"""Wrap an MCP client for event emission, or return it unwrapped.

	Emission is enabled only when ``EMIT_WORKFLOW_EVENTS`` is set and a
	workflow identity resolves (baggage first, then the explicit
	``workflow_name``/``instance_id``). Otherwise the original client is
	returned untouched so the tool call behaves exactly as before.
	"""
	if not EMIT_WORKFLOW_EVENTS:
		logger.warning(
			"wrap_mcp_client [%s]: EMIT_WORKFLOW_EVENTS is false; leaving MCP "
			"client unwrapped.",
			source,
		)
		return client

	identity = _resolve_identity(
		source=source,
		explicit_workflow_name=workflow_name,
		explicit_instance_id=instance_id,
	)
	if identity is None:
		return client

	return EventEmittingMCPClient(
		client,
		agent_id=agent_id,
		mcp_server=mcp_server,
		source=source,
		identity=identity,
		layer_index=layer_index,
	)
