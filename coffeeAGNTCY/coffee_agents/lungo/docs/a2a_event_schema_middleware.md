# A2A and MCP Event Schema Middleware Flow

This document explains how Lungo emits workflow topology events for A2A calls
and MCP tool calls.

## Package Layout

Shared, transport-agnostic pieces live in `common/workflow_utils/`:

- `common/workflow_utils/builders.py` — `event_v1` metadata, nodes, edges, and full `Event` assembly.
- `common/workflow_utils/mcp.py` — transient MCP tool-call topology builders + `emit_mcp_tool_call_event`.
- `common/workflow_utils/event_sink.py` — `EventSink` and `WorkflowAPIEventSink` (HTTP POST to workflow API).
- `common/workflow_utils/inflight.py` — trace-scoped in-flight state, runtime ID allocator, span-end cleanup.
- `common/workflow_utils/workflow_catalog.py` — workflow name → pattern/use-case metadata (`lookup_workflow`).
- `common/workflow_utils/__init__.py` — public exports for emitters (A2A, MCP, etc.).

A2A-specific orchestration remains in `common/a2a_event_middleware/`:

- `common/a2a_event_middleware/middleware.py` — `EventEmittingInterceptor`, `make_event_emitting_consumer`, A2A topology builders.
- `common/a2a_event_middleware/__init__.py` — minimal public API: interceptor, consumer factory, cleanup registration.
- `common/a2a_event_middleware/{event_sink,inflight,workflow_catalog}.py` — compatibility shims re-exporting from `workflow_utils`.

MCP-specific orchestration lives in `common/mcp_event_middleware/`:

- `common/mcp_event_middleware/wrapper.py` — `EventEmittingMCPClient` and `wrap_mcp_client` (client-side `call_tool` instrumentation).
- `common/mcp_event_middleware/__init__.py` — public API: wrapper class + factory.

## Purpose

The middleware reports topology updates to the workflow API at two points:

1. **Outbound request (interceptor)** emits `Operation.CREATE` fragments.
2. **Inbound response (consumer)** emits `Operation.UPDATE` fragments.

Both events are correlated by OTel `trace_id` and a shared in-flight state map.

## Main Components

- **`EventEmittingInterceptor`**
  - Runs before outbound A2A calls.
  - Resolves workflow identity from OTel baggage (`common.workflow_context_prop`).
  - Computes correlation and instance IDs.
  - Builds outbound topology and emits an event.
  - Stores trace-scoped state for the consumer.

- **`make_event_emitting_consumer(...)`**
  - Returns a consumer callback for inbound events.
  - Looks up previously stored trace-scoped state.
  - Builds inbound topology and emits an event.
  - Drops the event with a warning when no in-flight state exists.

- **`InFlightCleanupSpanProcessor`**
  - Removes trace-scoped state when the owning span ends.
  - Prevents long-lived in-memory buildup.

- **`WorkflowAPIEventSink`**
  - Sends events asynchronously to the workflow API endpoint.
  - Uses fire-and-forget background tasks with best-effort logging.

## Outbound Flow

1. Interceptor receives `method_name`, `agent_card`, and optional `context`.
2. Workflow identity is read from propagated OTel baggage (`workflow_name`, `workflow_instance_id`) and validated against the catalog.
3. Trace context (`trace_id`, `span_id`, `owner_span_id`) is read from OTel.
4. Correlation ID is resolved from context, trace, or a new UUID.
5. Remote targets are collected from broadcast cards (or single target card).
6. In-flight state is upserted by `trace_id` (`upsert_in_flight_state`).
7. Topology is generated using `Operation.CREATE`.
8. Event is built (`workflow_utils.builders.build_event`) and emitted to the sink.

## Inbound Flow

1. Consumer receives response event + `agent_card`.
2. Trace context is read from OTel.
3. Remote agent ID is extracted from response metadata (fallback to card name).
4. Correlation/workflow/allocator are resolved from in-flight state (`resolve_consumer_state`).
   - If missing, event is dropped with warning.
5. Topology is generated using `Operation.UPDATE`.
6. Event is built and emitted to the sink.

## State and ID Rules

- `trace_id` links outbound and inbound updates.
- `correlation_id` precedence:
  1. `context.state["correlation_id"]`
  2. `correlation://<trace-based UUID>`
  3. random UUID
- `workflow_instance_id` comes from OTel baggage; emission is skipped if missing or malformed.
- Runtime topology IDs (`node://...`, `edge://...`) are allocated per interaction and reused within a trace.

## Failure/Degradation Behavior

- If `EMIT_WORKFLOW_EVENTS` is false: sink is disabled, no emission occurs.
- If OTel context is missing: middleware still emits outbound, but inbound correlation may be lost.
- If sink POST fails: error is logged, exception is not raised to caller.

## MCP Tool-Call Events

MCP tool calls are modeled as **transient** topology nodes rather than the
persistent caller/transport/remote nodes used for A2A.

- **`EventEmittingMCPClient` / `wrap_mcp_client(...)`**
  - `wrap_mcp_client(...)` resolves identity once (see below) and returns either an `EventEmittingMCPClient` or, when no identity resolves (or `EMIT_WORKFLOW_EVENTS` is false), the **original client unwrapped** so the tool call behaves exactly as before.
  - The wrapper keeps the original async context manager (`_cm`) and the object it yields (`_session`) separate: `__aexit__` always closes `_cm` so the SDK client's teardown (cancelling its anyio task group, closing streams) runs, while `call_tool`/`list_tools` and other attributes delegate to `_session`. Exiting the yielded session instead leaks those streams and hangs the event loop.
  - Intercepts `call_tool` (positional `name` or `name=` keyword), emitting one event when the call starts and one when it ends.
  - Best-effort: emission failures are logged, never raised to the tool caller.

### Lifecycle

1. **Start** → `Operation.CREATE`: emits the invoking-agent node (carrying `stable_agent_id` so it merges with the A2A agent node), a transient `mcp_tool_call` node (extras `tool_name`, `mcp_server`), and the connecting edge.
2. **End** → `Operation.DELETE`: removes the `mcp_tool_call` node and edge, attaching `duration_ms` and (on failure) `error`. The wrapper refcounts in-flight calls and, when the last one ends, the DELETE also removes the invoking-agent node so it does not linger in the instance snapshot (the frontend still renders the agent via the A2A node, which shares the same `stable_agent_id`).
   - For non-streaming results, DELETE is emitted as soon as `call_tool` returns.
   - For streamed (async-iterable) results, the wrapper returns a proxy iterator and emits DELETE only when iteration completes or raises.

The CREATE and DELETE of one call share a `node://`/`edge://` id (same per-instance `RuntimeIdAllocator` + per-call `call_key`), so the frontend can add and later remove the same transient node.

### Workflow Identity Propagation (supervisor → farm)

MCP events are emitted from the farm process but must correlate to the
supervisor's workflow instance:

1. The supervisor stamps `workflow_name` + `workflow_instance_id` (read from OTel baggage) into the outbound A2A message `metadata` (`agents/supervisors/auction/graph/tools.py`).
2. The farm executor (`agents/farms/colombia/agent_executor.py`) reads that metadata, wraps `agent.ainvoke(...)` in `workflow_context_scope` (re-establishing baggage for the graph run), and also threads the same identity explicitly through graph state.
3. `wrap_mcp_client(...)` resolves identity once, in this order:
   1. **OTel baggage** if present and non-empty (the primary channel established in step 2).
   2. otherwise the **explicit** `workflow_name`/`instance_id` passed by the call site (threaded through graph state as an in-process fallback).
   3. otherwise **None** — the client is returned unwrapped and no events are emitted (the tool call still runs).
   In all cases the candidate must validate (workflow_name in the catalog, `instance_id` matching `instance://<uuid>`); an invalid candidate falls through to the next source.
4. `register_cleanup_span_processor()` is registered on the farm (`farm_server.py`) for parity with the supervisor.

## Design Notes

- Keep transformation logic in small focused helpers (`resolve_correlation_id`, `_collect_remote_agent_ids`, `resolve_consumer_state`).
- Keep side effects localized (`upsert_in_flight_state`, `WorkflowAPIEventSink.emit`).
- Keep A2A orchestration in `middleware.py` and MCP orchestration in `mcp_event_middleware/wrapper.py`; shared builders/sink/inflight/catalog in `workflow_utils`.
