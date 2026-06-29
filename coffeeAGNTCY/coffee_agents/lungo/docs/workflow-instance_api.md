# Agentic Workflow Instance API

Interface documentation for the Lungo **Agentic Workflows API**: the catalog (patterns, use-cases, workflows), workflow-instance lifecycle and state, the internal event ingress, and the Server-Sent Events (SSE) stream. It also documents the wire formats — the canonical `event_v1` JSON Schema, SSE framing, and the NDJSON pattern-chat stream — and the response shapes a frontend needs to render the use-case list and workflow topology without guessing.

This document satisfies the interface-definition tickets [#447 — API endpoints](https://github.com/agntcy/coffeeAgntcy/issues/447) and [#446 — workflow-instance state JSON schema](https://github.com/agntcy/coffeeAgntcy/issues/446).

## Authoritative sources

The contracts described here are **published in-repo**. This document is a guide; the machine-readable specs are the source of truth.

| Contract | File |
| --- | --- |
| OpenAPI 3.1 spec (root) | [`../schema/openapi/openapi.yaml`](../schema/openapi/openapi.yaml) |
| OpenAPI path items | [`../schema/openapi/paths/agentic-workflows.yaml`](../schema/openapi/paths/agentic-workflows.yaml) |
| OpenAPI shared schemas | [`../schema/openapi/components/schemas.yaml`](../schema/openapi/components/schemas.yaml) |
| **Workflow-instance state JSON Schema** (`event_v1`) | [`../schema/jsonschemas/event_v1.json`](../schema/jsonschemas/event_v1.json) |
| Event-type enum JSON Schema | [`../schema/jsonschemas/event_type_v1.json`](../schema/jsonschemas/event_type_v1.json) |
| Pydantic mirror of the schema | [`../schema/types/event.py`](../schema/types/event.py) |
| FastAPI router (implementation) | [`../api/agentic_workflows/router.py`](../api/agentic_workflows/router.py) |

Examples of complete and partial messages live alongside the schema:

- Full snapshot: [`../schema/jsonschemas/examples/event_v1_full.json`](../schema/jsonschemas/examples/event_v1_full.json)
- Partial delta: [`../schema/jsonschemas/examples/event_v1_partial.json`](../schema/jsonschemas/examples/event_v1_partial.json)
- Empty workflows: [`../schema/jsonschemas/examples/event_v1_empty_workflows.json`](../schema/jsonschemas/examples/event_v1_empty_workflows.json)

> **Status.** The catalog list DTOs (patterns, use-cases, workflow summaries) are temporary API-layer types defined in [`../api/agentic_workflows/dtos.py`](../api/agentic_workflows/dtos.py). They are being folded into the canonical JSON Schema (tracked in [#468](https://github.com/agntcy/coffeeAgntcy/issues/468)) so OpenAPI, JSON Schema, and Pydantic remain a single source of truth. The instance/state and event shapes (`Workflow`, `WorkflowInstance`, `Topology`, `Event`) are already canonical in `event_v1.json`.

## Conventions

### Identifiers

All identifiers are opaque URI strings with a scheme prefix wrapping a UUID. The canonical patterns are defined in `event_v1.json#/$defs`:

| Kind | Scheme | Example |
| --- | --- | --- |
| Event | `event://` | `event://6ba7b811-9dad-11d1-80b4-00c04fd430c8` |
| Correlation | `correlation://` | `correlation://6ba7b810-9dad-11d1-80b4-00c04fd430c8` |
| Workflow instance | `instance://` | `instance://6ba7b817-9dad-11d1-80b4-00c04fd430c8` |
| Graph node | `node://` | `node://6ba7b812-9dad-11d1-80b4-00c04fd430c8` |
| Graph edge | `edge://` | `edge://6ba7b815-9dad-11d1-80b4-00c04fd430c8` |
| Stable agent id | `agent://` | `agent://470de4a0-a6bc-5e1b-82dd-e41de2af3f85` |
| Chat session | `session://` | `session://550e8400-e29b-41d4-a716-446655440000` |

**Path vs. payload identifiers.** Instance-scoped routes take a **bare UUID** in the URL path (`WorkflowInstancePathId`, e.g. `/agentic-workflows/Publish%20Subscribe/instances/6ba7b817-9dad-11d1-80b4-00c04fd430c8/`). JSON payloads and response fields always use the full `instance://<uuid>` URI (`InstanceId`). The server converts between the two.

### Authentication

Every endpoint (except `GET /health`) requires a bearer token:

```http
Authorization: Bearer <WORKFLOW_API_KEY>
```

A missing or mismatched token yields `401 Unauthorized` ([`../api/agentic_workflows/auth.py`](../api/agentic_workflows/auth.py)). The server refuses to start unless `WORKFLOW_API_KEY` is configured.

### Storage model

State is held **in-memory**, keyed by `workflow_instance_id`, with **no persistence** (per #447). The state API and SSE endpoint read from the store; the internal `POST .../events/` ingress (the A2A / MCP middleware path) writes to the store and notifies SSE subscribers. The store surface is defined in [`../common/workflow_instance_store/interfaces.py`](../common/workflow_instance_store/interfaces.py).

### Default port

The standalone service listens on `:9105` ([`../api/agentic_workflows/server.py`](../api/agentic_workflows/server.py)).

## Endpoint summary

| Purpose | Method & path | Response |
| --- | --- | --- |
| Redirect root to catalog | `GET /` | `307` → `/patterns/` |
| List patterns | `GET /patterns/` | `PatternListResponse` |
| Chat with a pattern's docs | `POST /patterns/{name}/chat` | NDJSON stream |
| List use-cases | `GET /use-cases/` | `UseCaseListResponse` |
| List workflows (filterable) | `GET /agentic-workflows/` | `WorkflowSummaryMapResponse` |
| Workflow details / starting topology | `GET /agentic-workflows/{workflow_name}/` | `Workflow` |
| Workflow documentation (markdown) | `GET /agentic-workflows/{workflow_name}/documentation/` | `WorkflowDocumentationResponse` |
| Instantiate a workflow | `POST /agentic-workflows/{workflow_name}/` | `InstantiateWorkflowResponse` |
| List workflow instances | `GET /agentic-workflows/{workflow_name}/instances/` | `WorkflowInstanceMapResponse` |
| Get instance state (full / topology only) | `GET /agentic-workflows/{workflow_name}/instances/{workflow_instance_id}/` | `WorkflowInstance` |
| Delete instance | `DELETE /agentic-workflows/{workflow_name}/instances/{workflow_instance_id}/` | `202` / `204` |
| **(internal)** Post state update event | `POST /agentic-workflows/{workflow_name}/instances/{workflow_instance_id}/events/` | `204` |
| SSE stream of instance events | `GET /agentic-workflows/{workflow_name}/instances/{workflow_instance_id}/events/stream` | `text/event-stream` |

The endpoint set mirrors the table in [#447](https://github.com/agntcy/coffeeAgntcy/issues/447); `documentation/` and `patterns/{name}/chat` are additional surfaces present in the implementation.

---

## Catalog API

The catalog lets a frontend discover what can be run and how to filter it. All catalog data is currently static ([`patterns.py`](../api/agentic_workflows/patterns.py), [`use_cases.py`](../api/agentic_workflows/use_cases.py), [`starting_workflows.json`](../api/agentic_workflows/starting_workflows.json)).

### `GET /patterns/` — list patterns

Returns the architectural patterns available in the catalog.

```json
{
  "items": [
    { "name": "Supervisor" },
    { "name": "Peer Group" },
    { "name": "Recruiter" }
  ]
}
```

### `GET /use-cases/` — list use-cases

Returns the business use-cases available in the catalog. This is the shape a frontend should bind a use-case selector to.

```json
{
  "items": [
    { "name": "Coffee Agntcy" }
  ]
}
```

`UseCaseListResponse` is an object with a required `items` array; each item is an object with a required, non-empty `name` string and no additional properties (`UseCase` / `UseCaseListResponse` in [`components/schemas.yaml`](../schema/openapi/components/schemas.yaml)). The list-of-objects shape (rather than a bare array of strings) is intentional so each use-case can grow extra fields later without breaking clients.

### `GET /agentic-workflows/` — list workflows

Returns the workflows in the catalog as a **map keyed by workflow name**. Optional repeated query parameters filter the result:

- `patterns` — `[]string` (repeat the param: `?patterns=Supervisor&patterns=Recruiter`)
- `use_cases` — `[]string` (`?use_cases=Coffee%20Agntcy`)

Both filters are independent; when both are supplied a workflow must match a pattern **and** a use-case to be included.

```http
GET /agentic-workflows/?patterns=Supervisor&use_cases=Coffee%20Agntcy
```

```json
{
  "Publish Subscribe": {
    "name": "Publish Subscribe",
    "pattern": "Supervisor",
    "use_case": "Coffee Agntcy",
    "scenario": "Purchasing"
  },
  "Publish Subscribe Streaming": {
    "name": "Publish Subscribe Streaming",
    "pattern": "Supervisor",
    "use_case": "Coffee Agntcy",
    "scenario": "Purchasing"
  }
}
```

Each value is a `WorkflowSummary`: `name`, `pattern`, `use_case`, and `scenario` (a brief extra qualifier for the use-case). The map key always equals `WorkflowSummary.name`.

### `GET /agentic-workflows/{workflow_name}/documentation/` — workflow docs

Returns the reference markdown for a catalog workflow, both as a single blob and split into sections at `##` headings (for TOC / anchored rendering). Backed by files under [`../api/agentic_workflows/docs/workflows/`](../api/agentic_workflows/docs/workflows).

```json
{
  "slug": "publish_subscribe",
  "workflow_name": "Publish Subscribe",
  "title": "Publish Subscribe",
  "sections": [
    {
      "anchor": "overview",
      "heading": "Overview",
      "body_markdown": "..."
    }
  ],
  "full_markdown": "# Publish Subscribe\n\n## Overview\n..."
}
```

Returns `404` for an unknown workflow name or when no markdown file maps to it.

### `POST /patterns/{name}/chat` — chat with a pattern's docs (NDJSON)

A retrieval-grounded chat over a pattern's reference markdown. See [NDJSON pattern-chat stream](#ndjson-pattern-chat-stream) for the wire format.

---

## Workflow details & topology response shapes

### `GET /agentic-workflows/{workflow_name}/` — workflow details

Returns the full `Workflow` object (`event_v1.json#/$defs/workflow`): catalog metadata, the predefined **`starting_topology`**, and the `instances` map. This is the shape a frontend renders to draw the **starting graph** before any instance is created.

Query parameter:

- `topology_only` (boolean, default `false`) — when `true`, the server returns a topology-focused projection (the `instances` map is emptied), so the client gets just the starting graph.

`Workflow` (required fields): `name`, `pattern`, `use_case`, `scenario`, `starting_topology`, `instances`. `additionalProperties` is allowed.

#### Topology shape

A **topology** (`event_v1.json#/$defs/topology`) is an object with `nodes` and `edges` arrays. The *full* form (used for `starting_topology` and instance init) requires both arrays; the *partial* form (`#/$defs/partial_topology`, used for deltas) allows them to be omitted.

**Node** (`#/$defs/regular_node`, required for a full node): `id` (`node://…`), `operation` (`create` | `read` | `update` | `delete`), `type` (e.g. `customNode`, `transportNode`, `group`), `label`, `size` (`{ width, height }`, relative layout sizing), and `layer_index`. `additionalProperties` is allowed (the starting catalog, for example, carries an extra `position: { x, y }`).

An **agent node** (`#/$defs/agent_node`) additionally carries `agent_record_uri` (required) and `stable_agent_id` (`agent://…`). Nodes without agent extension fields are plain regular nodes; the schema keeps the two mutually exclusive via `anyOf`/`not`.

**Edge** (`#/$defs/edge`, required for a full edge): `id` (`edge://…`), `operation`, `type`, `source` (`node://…`), `target` (`node://…`), `bidirectional` (boolean), and `weight` (number). `additionalProperties` is allowed.

Example topology projection (`?topology_only=true`):

```json
{
  "name": "A2A HTTP",
  "pattern": "Recruiter",
  "use_case": "Coffee Agntcy",
  "scenario": "Capability Discovery",
  "starting_topology": {
    "nodes": [
      {
        "id": "node://4a000001-0001-4000-a001-000000000001",
        "operation": "read",
        "type": "customNode",
        "label": "Agentic Recruiter",
        "size": { "width": 1.0, "height": 1.0 },
        "layer_index": 0,
        "position": { "x": 400, "y": 300 },
        "agent_record_uri": "../../agents/supervisors/recruiter/oasf/agents/recruiter.json"
      },
      {
        "id": "node://4a000001-0001-4000-a001-000000000002",
        "operation": "read",
        "type": "customNode",
        "label": "AGNTCY Agent Directory",
        "size": { "width": 1.0, "height": 1.0 },
        "layer_index": 1,
        "position": { "x": 800, "y": 100 }
      }
    ],
    "edges": [
      {
        "id": "edge://4a000001-0001-4000-a001-e00000000001",
        "operation": "read",
        "type": "custom",
        "source": "node://4a000001-0001-4000-a001-000000000002",
        "target": "node://4a000001-0001-4000-a001-000000000001",
        "bidirectional": false,
        "weight": 1.0
      }
    ]
  },
  "instances": {}
}
```

Returns `404` when `workflow_name` is not in the catalog.

> **Note on node ids.** At startup the catalog loader assigns fresh runtime `node://`/`edge://` ids and derives `stable_agent_id` (a UUID5 of the agent record `name`) for agent nodes. Treat ids returned by the API as the live values; do not assume they match the static JSON file verbatim.

---

## Workflow-instance lifecycle & state

### `POST /agentic-workflows/{workflow_name}/` — instantiate

Creates a new instance of the workflow and seeds its starting topology into the store. Responds with the instance id to track (as an `instance://…` URI).

```json
{ "workflow_instance_id": "instance://6ba7b817-9dad-11d1-80b4-00c04fd430c8" }
```

Behavior and status codes:

- `200` — instance created; body is `InstantiateWorkflowResponse`.
- `404` — unknown `workflow_name`.
- `400` — the seed event failed schema validation.
- `503` — store not configured / closed.
- `504` — the event was accepted and queued but the in-memory merge did not finish in time. **Each `POST` creates a new instance**, so do not blindly retry; poll the instances list or `GET` the instance state first.

### `GET /agentic-workflows/{workflow_name}/instances/` — list instances

Returns the instances of a workflow as a **map keyed by `instance://…` id**; each value is a `WorkflowInstance`.

```json
{
  "instance://6ba7b817-9dad-11d1-80b4-00c04fd430c8": {
    "id": "instance://6ba7b817-9dad-11d1-80b4-00c04fd430c8",
    "topology": { "nodes": [ /* … */ ], "edges": [ /* … */ ] }
  }
}
```

Returns `404` when `workflow_name` is not in the catalog.

### `GET /agentic-workflows/{workflow_name}/instances/{workflow_instance_id}/` — instance state

Returns a single `WorkflowInstance` (`event_v1.json#/$defs/workflow_instance`): the current dynamic state of that instance. `WorkflowInstance` requires `id` (`instance://…`, identical to its key in the parent map) and `topology` (a `partial_topology` reflecting the live graph). `additionalProperties` is allowed for extra runtime state.

Query parameter:

- `topology_only` (boolean, default `false`) — when `true`, returns a topology-only projection of the instance.

`{workflow_instance_id}` is the **bare UUID** path segment; the response `id` field is the full `instance://<uuid>` URI.

Status codes: `200` on success; `404` when the workflow or the instance is unknown.

### `DELETE /agentic-workflows/{workflow_name}/instances/{workflow_instance_id}/` — delete instance

Schedules removal from the in-memory store. **Idempotent**:

- `202` — instance existed; deletion accepted (runs in the background).
- `204` — nothing to delete (already removed or never existed).
- `404` — unknown `workflow_name`.

---

## Internal event ingress

### `POST /agentic-workflows/{workflow_name}/instances/{workflow_instance_id}/events/`

> **Internal only.** This is the write path used by the A2A / MCP state middleware, not by untrusted public clients (marked `x-internal: true` in OpenAPI). See [`a2a_event_schema_middleware.md`](a2a_event_schema_middleware.md) for the emitter side.

Applies a workflow-instance **state update event** to the store. The request body is a full `Event` document validated against [`event_v1.json`](../schema/jsonschemas/event_v1.json). The server checks that:

1. The event's `data.workflows` contains the path `workflow_name`.
2. That workflow's `instances` map targets the path `workflow_instance_id` (canonicalized to `instance://<uuid>`).
3. The workflow exists in the catalog and the instance exists in the store.

On success the event is enqueued, merged into the accumulated state, and fanned out to SSE subscribers of that instance.

Status codes:

- `204` — event accepted.
- `400` — payload does not match the path target, or failed schema validation.
- `404` — unknown workflow or instance.
- `503` — store closed.

---

## Streaming formats

### SSE workflow-instance event stream

#### `GET /agentic-workflows/{workflow_name}/instances/{workflow_instance_id}/events/stream`

Opens a `text/event-stream` (SSE) connection that emits every event applied to the given instance. Response headers set `Cache-Control: no-store`, `Connection: keep-alive`, and `X-Accel-Buffering: no` so proxies don't buffer.

**Framing.** Each event is one SSE message: a single `data:` line containing the **compact `event_v1` JSON** (no `event:`/`id:` lines), terminated by a blank line. `None`-valued fields are omitted (`exclude_none`). On connect, the server first sends an SSE comment frame (`:\n\n`) to flush response headers before it blocks waiting for events.

```text
:

data: {"metadata":{"timestamp":"2026-03-17T12:00:01Z","schema_version":"1.0.0","correlation":{"id":"correlation://550e8400-e29b-41d4-a716-446655440001"},"id":"event://550e8400-e29b-41d4-a716-446655440002","type":"RecruiterNodeSearch","source":"auction_supervisor"},"data":{"workflows":{"recruiter":{"name":"Recruiter","pattern":"recruiter_pattern","use_case":"hiring","scenario":"agent recruitment","starting_topology":{ /* … */ },"instances":{"instance://550e8400-e29b-41d4-a716-446655440003":{"id":"instance://550e8400-e29b-41d4-a716-446655440003","topology":{"nodes":[{"id":"node://550e8400-e29b-41d4-a716-446655440010","operation":"update","type":"customNode","label":"Auction Agent (search)","agent_record_uri":"../../agents/supervisors/auction/oasf/agents/auction-supervisor-agent.json"}],"edges":[]}}}}}}}

```

Each `data:` payload validates against `event_v1.json`. The stream only carries events whose `data.workflows[workflow_name].instances` includes the subscribed instance id; events for other instances are filtered out server-side.

**Backpressure.** The per-subscriber queue is bounded (100 frames). When it fills past the high-water mark, the oldest frames are dropped first — clients should treat the stream as a best-effort change feed and reconcile against `GET …/instances/{id}/` if they detect a gap.

A frontend typically: `POST` to instantiate → render the `starting_topology` from `GET …/{workflow_name}/` → open the SSE stream → apply each event's `topology` delta (using `operation` per node/edge) to the rendered graph.

### NDJSON pattern-chat stream

#### `POST /patterns/{name}/chat`

A newline-delimited JSON (`application/x-ndjson`) stream for chatting with a pattern's reference docs. Request body (`PatternChatRequest`):

```json
{
  "session_id": "session://550e8400-e29b-41d4-a716-446655440000",
  "message": "How does the supervisor pattern route requests?"
}
```

- `session_id` — client-minted UUIDv4 wrapped as a `session://<uuid>` URI; the server holds conversation state in memory keyed by `(pattern_name, session_id)`.
- `message` — the latest user turn (1–32768 chars).

**Framing.** One JSON object per line:

- `{"response": "<chunk>"}` — a chunk of the answer (zero or more).
- `{"done": true}` — terminates a successful stream.
- `{"error": "<message>"}` — emitted instead if the stream fails mid-flight, then the connection closes.

```text
{"response": "The supervisor pattern "}
{"response": "routes requests by ..."}
{"done": true}
```

Returns `404` (before opening the stream) when the pattern has no reference markdown, and `422` when the request body fails validation.

---

## Workflow-instance state JSON Schema (`event_v1`)

The single, validatable contract shared by senders (agents, LangGraph adapters), the A2A state middleware, the internal event ingress, and the SSE stream is published at [`../schema/jsonschemas/event_v1.json`](../schema/jsonschemas/event_v1.json) (JSON Schema draft 2020-12, `$id` `https://github.com/agntcy/coffeeAgntcy/schema/jsonschemas/event_v1.json`). This is the schema requested in [#446](https://github.com/agntcy/coffeeAgntcy/issues/446); it is referenced by OpenAPI (`components/schemas.yaml` maps `Event`, `Workflow`, `WorkflowInstance`, `Topology`, `PartialTopology`, `InstanceId` to it) and mirrored in Pydantic ([`../schema/types/event.py`](../schema/types/event.py)). Validation helpers live in [`../schema/validate.py`](../schema/validate.py).

### Why one schema

A single schema represents **both** a full state snapshot (init / reset, when fully filled) **and** an event/delta (partial topology). Full variants (`node`, `edge`, `topology`, `regular_node`) require all fields; partial variants (`partial_node`, `partial_edge`, `partial_topology`, `partial_regular_node`) require only `id` + `operation` and allow the rest to be omitted. The `operation` field (`create` / `read` / `update` / `delete`) tells a consumer how to apply each node/edge against the current graph.

### Top-level shape

An `Event` is `{ metadata, data }` (both required, `additionalProperties: false` at the root):

```jsonc
{
  "metadata": {                       // syntactic + semantic metadata (all required)
    "timestamp": "RFC3339 date-time",
    "schema_version": "1.0.0",        // semantic version of this contract
    "correlation": {                  // ties events from one user action / request
      "id": "correlation://<uuid>",   // required
      "message": "optional string"    // additionalProperties allowed
    },
    "id": "event://<uuid>",           // unique event id
    "type": "StateProgressUpdate",    // see event_type_v1.json (extendable enum)
    "source": "auction_supervisor"    // producer identifier
    // additionalProperties allowed
  },
  "data": {                           // business data (partial_state)
    "workflows": {                    // required; map workflow_name -> workflow
      "<workflow_name>": {
        "name": "…", "pattern": "…",  // all four catalog fields required + unique
        "use_case": "…", "scenario": "…",
        "starting_topology": { /* full topology */ },   // required
        "instances": {                // required; map instance_id -> instance
          "instance://<uuid>": {
            "id": "instance://<uuid>", // required; must equal the map key
            "topology": { /* partial_topology */ }
            // additionalProperties allowed
          }
        }
        // additionalProperties allowed
      }
    }
    // additionalProperties allowed (e.g. app_state)
  }
}
```

Key invariant: each property name under `workflow.instances` **must equal** the nested object's `id` (the same `instance://<uuid>` string).

### `$defs` reference

| `$def` | Meaning |
| --- | --- |
| `event_id`, `correlation_id`, `instance_id`, `node_id`, `edge_id`, `stable_agent_id` | URI-pattern id strings (see [Identifiers](#identifiers)). |
| `operation` | Entity op: `create` \| `read` \| `update` \| `delete`. |
| `size` | Relative layout size `{ width, height }` (defaults `1.0`). |
| `metadata` | Required event metadata block. |
| `correlation` | `{ id (required), message? }`, `additionalProperties: true`. |
| `partial_regular_node` / `regular_node` | Sparse vs. full non-agent node. |
| `partial_agent_node` / `agent_node` | Node + agent extension (`agent_record_uri`, `stable_agent_id`). |
| `partial_node` / `node` | A regular node **or** an agent node (mutually exclusive). |
| `partial_edge` / `edge` | Sparse vs. full edge. |
| `partial_topology` / `topology` | `{ nodes, edges }`; partial allows omission, full requires both. |
| `workflow_instance` | `{ id (required), topology }`, `additionalProperties: true`. |
| `workflow` | Catalog metadata + `starting_topology` + `instances`. |
| `data` | `{ workflows (required) }`, `additionalProperties: true`. |

### Event types

`metadata.type` is constrained by [`event_type_v1.json#/$defs/event_type`](../schema/jsonschemas/event_type_v1.json): a string enum that is **extendable at the emitter**. Current values (`RecruiterNodeSearch`, `StateProgressUpdate`) are placeholders to be finalized as emitters are implemented.

### Worked examples

- **Full snapshot (init / reset)** — every node/edge fully populated: [`examples/event_v1_full.json`](../schema/jsonschemas/examples/event_v1_full.json).
- **Partial delta (update)** — one node carrying `operation: "update"` and only the changed fields, empty `edges`: [`examples/event_v1_partial.json`](../schema/jsonschemas/examples/event_v1_partial.json).
- **Empty workflows + extra `app_state`** — demonstrates root-level `additionalProperties`: [`examples/event_v1_empty_workflows.json`](../schema/jsonschemas/examples/event_v1_empty_workflows.json).

---
