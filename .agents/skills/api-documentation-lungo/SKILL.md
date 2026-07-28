---
name: api-documentation-lungo
description: >-
  Authors and maintains the human-facing Agentic Workflows API documentation for the lungo subproject at coffeeAGNTCY/coffee_agents/lungo/docs/workflow-instance_api.md, and keeps hand-maintained OpenAPI response/status coverage in coffeeAGNTCY/coffee_agents/lungo/schema/openapi aligned with router behavior. Covers the catalog API, workflow-instance lifecycle/state, internal event ingress, SSE and NDJSON streaming, event_v1, and topology/use-case shapes. Use when documenting or updating the lungo workflow API; when OpenAPI under coffeeAGNTCY/coffee_agents/lungo/schema/openapi, JSON Schema under coffeeAGNTCY/coffee_agents/lungo/schema/jsonschemas, or api/agentic_workflows changes; or when a pull request changes lungo API contracts. DO NOT TRIGGER AUTOMATICALLY. ASK THE USER IF THE SKILL SHOULD BE USED.
---

# Agentic Workflows API documentation (lungo)

Produces and maintains a single human-facing reference document for the lungo **Agentic Workflows API** from the machine-readable contracts already in the repo. The document is a guide; the specs are the source of truth, so the skill **derives** prose from the specs and never invents shapes.

The lungo project root is `coffeeAGNTCY/coffee_agents/lungo/`. Paths in the [Source registry](#source-registry) are relative to that project root. The output document itself lives at `coffeeAGNTCY/coffee_agents/lungo/docs/workflow-instance_api.md` and links to sources with paths relative to its own `docs/` folder (e.g. `../schema/jsonschemas/event_v1.json`).

## Output

- Document: `coffeeAGNTCY/coffee_agents/lungo/docs/workflow-instance_api.md`.
- OpenAPI (when status/behavior changes): `schema/openapi/paths/agentic-workflows.yaml` — per-operation `responses` and descriptions; reuse `components/responses` in `schema/openapi/components/schemas.yaml`.
- Curated drift manifest (when the reachable status set changes): `tests/unit/openapi/fixtures/agentic_workflows_expected_status_codes.yaml`.

These outputs stay coupled: the human guide, OpenAPI path items, and manifest must reflect the same contracts and router behavior. Derive everything from the [Source registry](#source-registry); do not add external tracker links to the markdown. Reconcile the human doc using [Document structure](#document-structure) whenever the API surface changes. When the set of HTTP statuses an operation can return changes, follow [OpenAPI status codes](#openapi-status-codes) in the same change set as handler updates.

## Source registry

These are the authoritative inputs. Read them fresh on every run; do not trust the existing document to be current. Enumerate from the specs rather than hard-coding endpoint names or counts - the document must scale as the contracts grow.

| Role | Path (relative to lungo root) | What to extract |
|------|-------------------------------|-----------------|
| OpenAPI entry point | `schema/openapi/openapi.yaml` | Title, version, tag, top-level structure |
| OpenAPI path items | `schema/openapi/paths/agentic-workflows.yaml` | Every endpoint: method, path, params, query flags, responses, `x-internal` |
| OpenAPI shared schemas | `schema/openapi/components/schemas.yaml` | Catalog/list DTO shapes; mapping of `Event`/`Workflow`/`WorkflowInstance`/`Topology`/`InstanceId` to `event_v1`; reusable **`components/responses`** (`Unauthorized`, `UnprocessableEntity`, `NotFound`, etc.) and **`HttpError`** / **`RequestValidationErrorItem`** |
| Status-code drift manifest | `tests/unit/openapi/fixtures/agentic_workflows_expected_status_codes.yaml` | Expected HTTP status set per `operationId` (includes `401` for documentation; OpenAPI asserts global security separately) |
| **Canonical state schema** | `schema/jsonschemas/event_v1.json` | `$defs`, required fields, full-vs-partial variants, identifier patterns, invariants |
| Event-type enum | `schema/jsonschemas/event_type_v1.json` | `metadata.type` enum values and extensibility note |
| Schema examples | `schema/jsonschemas/examples/*.json` | Worked full/partial/empty payloads to link and (sparingly) excerpt |
| Router (behavior not in spec) | `api/agentic_workflows/router.py` | Per-endpoint status codes and their trigger conditions (every `HTTPException` in the handler **and** in dependencies/helpers it calls, not just the OpenAPI-declared responses), SSE framing/comment-frame, backpressure, NDJSON framing, `topology_only` projection behavior |
| Instance lifecycle helpers | `api/agentic_workflows/instance_lifecycle.py` | Error conditions the handlers translate into status codes (e.g. `ValueError` from `build_instantiate_seed_event`/projection helpers → `500`) |
| DTOs | `api/agentic_workflows/dtos.py` | Field constraints; temporary catalog DTO status note (pending JSON Schema consolidation) |
| Auth | `api/agentic_workflows/auth.py` | Bearer requirement, `401`, startup key assertion |
| Store interface | `common/workflow_instance_store/interfaces.py` | In-memory, keyed-by-instance, read vs write/fan-out split |
| Server | `api/agentic_workflows/server.py` | Default port, app wiring |
| Catalog data | `api/agentic_workflows/patterns.py`, `api/agentic_workflows/use_cases.py`, `api/agentic_workflows/starting_workflows.json` | Real example values for patterns, use-cases, workflows, topology |
| Related doc | `docs/a2a_event_schema_middleware.md` | Cross-link for the event emitter (write) side |

Sibling skills generate the contracts this document describes; when contracts change they are usually the upstream cause and should run first:

- `.agents/skills/openapi-to-python-lungo/SKILL.md` - OpenAPI ⇄ FastAPI router/DTOs.
- `.agents/skills/jsonschema-to-pydantic-lungo/SKILL.md` - JSON Schema ⇄ Pydantic types.

## Document structure

Keep the document organized in this order (the headings are stable so links and anchors don't churn). Re-derive the content of each from the [Source registry](#source-registry):

1. **Title + intro** - one-paragraph scope covering catalog, instance lifecycle, streaming, and `event_v1`.
2. **Authoritative sources** - a table linking the in-repo specs (OpenAPI, `event_v1.json`, Pydantic mirror, router) plus the example payloads, and a status note about temporary catalog DTOs (pending JSON Schema consolidation).
3. **Conventions** - identifier URI schemes table; path-UUID vs payload-URI rule; authentication; storage model; default port.
4. **Endpoint summary** - one table row per endpoint (purpose, method & path, response type).
5. **Catalog API** - `GET /patterns/`, `GET /use-cases/`, `GET /agentic-workflows/` (filters), `…/documentation/`, and a pointer to the NDJSON chat.
6. **Workflow details & topology response shapes** - `GET …/{workflow_name}/` + `topology_only`; an explicit node/agent-node/edge field breakdown; an example topology projection from `starting_workflows.json`.
7. **Workflow-instance lifecycle & state** - instantiate, list, get state, delete, each with status codes.
8. **Internal event ingress** - `POST …/events/` (mark internal), validation checks, status codes.
9. **Streaming formats** - SSE instance-event stream (framing, comment frame, filtering, backpressure) and the NDJSON pattern-chat stream.
10. **Workflow-instance state JSON Schema (`event_v1`)** - link to the published schema; "why one schema" (full snapshot vs delta); top-level shape; `$defs` reference table; event types; worked examples.
11. **Frontend integration checklist** - numbered end-to-end flow (selectors → list → starting graph → instantiate → SSE → reconcile → delete).

## Workflow

Copy this checklist and tick items as you go:

```
- [ ] 1. Read every input in the Source registry (specs first, then router for behavior)
- [ ] 2. Enumerate endpoints from OpenAPI and $defs from event_v1.json (do not hard-code)
- [ ] 3. Reconcile spec against router.py; capture behavior the spec can't (the full reachable status-code set + trigger conditions from handlers, dependencies, and helper modules; SSE/NDJSON framing; backpressure)
- [ ] 4. Update OpenAPI responses when the reachable status set changes (see OpenAPI status codes)
- [ ] 5. Write/refresh each document section per "Document structure", deriving every shape from a source
- [ ] 6. Use real example values from the catalog data files; link (don't inline) full example payloads
- [ ] 7. Apply the writing conventions
- [ ] 8. Verify links, lint, and OpenAPI unit tests (see Verification)
- [ ] 9. If new pull requests or contract files were referenced, update the Source registry AND the document (see "Keeping current")
```

### Source-of-truth rules

- **Derive, never invent.** Every endpoint, field, status code, and constraint must trace to a source file. If the spec and the router disagree on **behavior**, treat **`router.py`** (and its dependencies/helpers) as authoritative for what the server returns; **update OpenAPI and the status manifest** so the contract catches up — do not leave OpenAPI under-documenting errors while only fixing prose.
- **Spec for shape, router for behavior.** OpenAPI/JSON Schema give request/response shapes; `router.py` is authoritative for things the spec omits — exact status codes (e.g. `504` on instantiate merge timeout, `202`/`204` idempotent delete), the SSE leading comment frame and `exclude_none` compaction, per-subscriber queue bounds/drop-oldest, and the NDJSON `{"response"}`/`{"done"}`/`{"error"}` frames.
- **Derive the full status-code set from the code, not just the OpenAPI `responses`.** For each endpoint, trace every reachable `HTTPException` — in the handler body, in shared dependencies it uses (e.g. `_workflow_instance_store` → `503` when the store is unset), and in helper modules it calls (e.g. `instance_lifecycle.py` `ValueError` → `500`). The OpenAPI spec often documents only the happy-path and a subset of errors; the document must list the codes the code can actually return. For each code, state the **condition** that triggers it (and note when it reflects a server-side fault vs. client input).
- **Enumerate, don't count.** Build the endpoint summary and `$defs` table by listing what's in the specs so the document stays correct as endpoints/types are added.
- **Real examples.** Pull patterns, use-cases, workflow summaries, and topology from `patterns.py`, `use_cases.py`, and `starting_workflows.json` so samples match what the API returns.

### Writing conventions

- Markdown prose is **not** hard-wrapped for length: one paragraph or list item per line. Keep tables, fenced code blocks, and JSON/SSE/NDJSON examples structured as-is (their line breaks are meaningful).
- Link to source files with paths relative to `docs/` (`../schema/...`, `../api/...`). Link full example payloads rather than pasting them; excerpt only small, illustrative fragments.
- Use fenced code blocks with a language tag (`json`, `jsonc`, `http`, `text`, `bash`) for samples; these are illustrative, not citations of repo lines.
- Keep terminology consistent: "endpoint", "workflow instance", "topology", "event".
- Present per-endpoint status codes as a markdown bullet list introduced by a `Status codes:` line (or an equivalent lead-in such as `Behavior and status codes:`), one code per item in the form `` - `<code>` - <condition>. `` - never as an inline semicolon- or comma-separated sentence. Keep this consistent across every endpoint that lists more than one code.

### OpenAPI status codes

When reconciliation finds a status code the backend can return but OpenAPI does not declare:

1. **Update the manifest** — add the code under the correct `operationId` in `tests/unit/openapi/fixtures/agentic_workflows_expected_status_codes.yaml` (list every reachable code including `401` for human/doc parity).
2. **Update path items** — in `schema/openapi/paths/agentic-workflows.yaml`, add the status under that operation's `responses`:
   - **`401`** — do **not** repeat on every operation; rely on global `security` in `schema/openapi/openapi.yaml` (`WorkflowApiKeyBearer`). The drift test skips per-operation `401` checks.
   - **`422`** — on every operation with path/query/body validation, `$ref: ../components/schemas.yaml#/components/responses/UnprocessableEntity` (body uses full FastAPI validation JSON via `HttpError` + `RequestValidationErrorItem`).
   - **Other errors** — prefer `$ref` to shared `components/responses` (`BadRequest`, `NotFound`, `InternalServerError`, `ServiceUnavailable`, `GatewayTimeout`). Keep endpoint-specific `description` text when the generic component text is too vague (e.g. pattern-chat `404`, documentation `404`).
3. **Update the human doc** — same status/condition bullets as today in `workflow-instance_api.md`.
4. **Same change set** — OpenAPI + manifest + markdown should land together with router/handler changes that introduce new statuses (or in the immediately following commit on the same PR).

Do **not** add error `responses=` on FastAPI decorators unless the user explicitly asks; the hand-maintained YAML is the contract for consumers and codegen documentation.

### Verification

Run from the repo root (the doc lives under the lungo project):

```bash
cd coffeeAGNTCY/coffee_agents/lungo/docs
for p in $(grep -oE '\]\(\.\.?/[^)]+\)' workflow-instance_api.md | sed -E 's/^\]\(//; s/\)$//'); do
  [ -e "$p" ] && echo "OK   $p" || echo "MISS $p"
done
```

Fix any `MISS` link before finishing, then check the document for linter/markdown warnings and resolve any introduced.

From `coffeeAGNTCY/coffee_agents/lungo/`:

```bash
uv run pytest tests/unit/openapi/ -q
```

Fix any OpenAPI validation, route-parity, or status-manifest drift failures before finishing when you changed `schema/openapi/` or the manifest.

## Keeping the sources and this skill current

This is a standing requirement, not a one-off. When a prompt or request references a **new pull request or file/folder** that changes the lungo API contracts or specifications:

1. **Run upstream skills first if the contract files changed.** A reference that adds/renames endpoints or types usually means `schema/openapi/*` or `schema/jsonschemas/*` (and their Pydantic/router mirrors) should be regenerated via the sibling skills before documenting.
2. **Update the document** — re-run the [Workflow](#workflow) so every affected section reflects the new contract.
3. **Update OpenAPI and manifest** — if behavior or status codes changed, follow [OpenAPI status codes](#openapi-status-codes); do not document new errors only in markdown.
4. **Update this skill** — if a new authoritative file/folder is now part of the contract surface, add a row to the [Source registry](#source-registry); if a new endpoint family or document section is needed, extend [Document structure](#document-structure). Keep the frontmatter `description` trigger terms in sync with any newly referenced paths so discovery stays accurate. Only add durable file/folder sources to the registry, not ephemeral tracking IDs.
5. **Keep the index in sync** — this skill is registered in the repository [`AGENTS.md`](../../../AGENTS.md) Skills table; update that entry if the skill's name or scope changes.

Surface any contract inconsistency you find (spec vs router vs schema) to the user rather than silently papering over it in prose.
