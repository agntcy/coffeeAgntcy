# A2A Event Schema Middleware Flow

This document explains how the `common/a2a_event_middleware/` package emits workflow topology events for A2A calls.

## Package Layout

- `common/a2a_event_middleware/middleware.py`
  - Outbound interceptor and inbound consumer orchestration.
  - Topology/event assembly logic.
- `common/a2a_event_middleware/inflight.py`
  - Trace-scoped in-flight bridge state.
  - Runtime node/edge ID allocation and span-end cleanup processor.
- `common/a2a_event_middleware/workflow_registry.py`
  - Workflow identity catalog, tool registration, and resolver logic.
- `common/a2a_event_middleware/event_sink.py`
  - Event sink abstraction and workflow API HTTP delivery.
- `common/a2a_event_middleware/__init__.py`
  - Minimal public API: interceptor, consumer factory, and cleanup registration.

## Purpose

The middleware reports topology updates to the workflow API at two points:

1. **Outbound request (interceptor)** emits `Operation.CREATE` fragments.
2. **Inbound response (consumer)** emits `Operation.UPDATE` fragments.

Both events are correlated by OTel `trace_id` and a shared in-flight state map.

## Main Components

- **`EventEmittingInterceptor`**
  - Runs before outbound A2A calls.
  - Resolves workflow identity from `ClientCallContext.state["tool"]`.
  - Computes correlation and instance IDs.
  - Builds outbound topology and emits an event.
  - Stores trace-scoped state for the consumer.

- **`make_event_emitting_consumer(...)`**
  - Returns a consumer callback for inbound events.
  - Looks up previously stored trace-scoped state.
  - Builds inbound topology and emits an event.
  - Falls back to a default workflow context when no in-flight state exists.

- **`InFlightCleanupSpanProcessor`**
  - Removes trace-scoped state when the owning span ends.
  - Prevents long-lived in-memory buildup.

- **`WorkflowAPIEventSink`**
  - Sends events asynchronously to the workflow API endpoint.
  - Uses fire-and-forget background tasks with best-effort logging.

## Outbound Flow

1. Interceptor receives `method_name`, `agent_card`, and optional `context`.
2. Workflow identity is resolved via `workflow_resolver(context.state["tool"])`.
3. Trace context (`trace_id`, `span_id`, `owner_span_id`) is read from OTel.
4. Correlation and instance IDs are resolved from context, trace, or new UUIDs.
5. Remote targets are collected from broadcast cards (or single target card).
6. In-flight state is upserted by `trace_id` (`upsert_in_flight_state`).
7. Topology is generated using `Operation.CREATE`.
8. Event is built and emitted to the sink.

## Inbound Flow

1. Consumer receives response event + `agent_card`.
2. Trace context is read from OTel.
3. Remote agent ID is extracted from response metadata (fallback to card name).
4. Correlation/workflow/allocator are resolved from in-flight state (`resolve_consumer_state`).
   - If missing, fallback uses default workflow context.
   - If no fallback is available, event is dropped with warning.
5. Topology is generated using `Operation.UPDATE`.
6. Event is built and emitted to the sink.

## State and ID Rules

- `trace_id` links outbound and inbound updates.
- `correlation_id` precedence:
  1. `context.state["correlation_id"]`
  2. `correlation://<trace-based UUID>`
  3. random UUID
- `instance_id` precedence:
  1. `context.state["instance_id"]`
  2. deterministic `uuid5(trace_id + workflow_name)`
  3. random UUID
- Runtime topology IDs (`node://...`, `edge://...`) are allocated per interaction and reused within a trace.

## Failure/Degradation Behavior

- If `EMIT_WORKFLOW_EVENTS` is false: sink is disabled, no emission occurs.
- If OTel context is missing: middleware still emits, but correlation across outbound/inbound may be lost.
- If sink POST fails: error is logged, exception is not raised to caller.

## Design Notes

- Keep transformation logic in small focused helpers (`resolve_interaction_ids`, `_collect_remote_agent_ids`, `resolve_consumer_state`).
- Keep side effects localized (`upsert_in_flight_state`, `WorkflowAPIEventSink.emit`).
- Keep middleware orchestration in `middleware.py` and isolate OTel/in-flight lifecycle in `inflight.py`.
