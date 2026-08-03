---
name: agentic-workflows-api-documentation-lungo
description: >-
  Authors and maintains the human-facing Agentic Workflows API documentation for the lungo subproject at coffeeAGNTCY/coffee_agents/lungo/docs/workflow-instance_api.md.
  OpenAPI under coffeeAGNTCY/coffee_agents/lungo/schema/openapi/ is the HTTP contract source of truth (paths, shapes, response statuses): updated manually or via LLM, never generated from code.
  Covers the catalog API, workflow-instance lifecycle/state, internal event ingress, SSE and NDJSON streaming, event_v1, and topology/use-case shapes.
  Use when documenting or updating the lungo workflow API; when schema/openapi/, schema/jsonschemas/, or api/agentic_workflows/ changes; or when a prompt references a ticket/issue, pull request, or file/folder that changes lungo API contracts.
  DO NOT TRIGGER AUTOMATICALLY. ASK THE USER IF THE SKILL SHOULD BE USED.
---

# Agentic Workflows API documentation (lungo)

Produces and maintains a single human-facing reference document for the lungo **Agentic Workflows API** from the machine-readable contracts already in the repo. The document is a guide; **`schema/openapi/` is the source of truth** for the published HTTP contract. Derive prose from the specs; never invent shapes or status codes.

The lungo project root is `coffeeAGNTCY/coffee_agents/lungo/`. Paths in [Where to look](#where-to-look) are relative to that project root. The output document lives at `coffeeAGNTCY/coffee_agents/lungo/docs/workflow-instance_api.md` and links to sources with paths relative to its own `docs/` folder (e.g. `../schema/jsonschemas/event_v1.json`).

**Scope:** This skill updates OpenAPI YAML and `workflow-instance_api.md` only. Aligning Python routers/DTOs with the spec is owned by [openapi-to-python-lungo](../openapi-to-python-lungo/SKILL.md). Regenerating Pydantic types from JSON Schema is owned by [jsonschema-to-pydantic-lungo](../jsonschema-to-pydantic-lungo/SKILL.md).

## Output

- Document: `coffeeAGNTCY/coffee_agents/lungo/docs/workflow-instance_api.md`.
- OpenAPI (when paths, shapes, or response statuses change): `schema/openapi/paths/agentic-workflows.yaml` - per-operation `responses` and descriptions; reuse `components/responses` in `schema/openapi/components/schemas.yaml`.

The human guide and OpenAPI path items must stay aligned. Derive shapes and status codes from `schema/openapi/` and `schema/jsonschemas/`. Reconcile the human doc using [Document structure](#document-structure) whenever the API surface changes. When HTTP statuses change, follow [OpenAPI status codes](#openapi-status-codes) **before** updating the human doc.

## Where to look

Read these inputs fresh on every run; do not trust the existing document to be current. Enumerate from the specs rather than hard-coding endpoint names or counts.

### Source of truth (contracts)

| Role | Path (relative to lungo root) | What to extract |
|------|-------------------------------|-----------------|
| OpenAPI | `schema/openapi/` | Entry point (`openapi.yaml`), path items (`paths/*.yaml`), shared schemas and **`components/responses`** (`components/schemas.yaml` or split files). Every endpoint: method, path, params, query flags, **`responses`**, `x-internal`. Global `security`, title, version, tags. |
| JSON Schema | `schema/jsonschemas/` | **`event_v1.json`** - `$defs`, required fields, full-vs-partial variants, identifier patterns, invariants. **`event_type_v1.json`** - `metadata.type` enum. **`examples/*.json`** - worked payloads to link and (sparingly) excerpt. |

### Human doc output and examples

| Role | Path | What to extract |
|------|------|-----------------|
| Output document | `docs/workflow-instance_api.md` | Current prose to refresh against the contracts |
| Catalog data | `api/agentic_workflows/patterns.py`, `api/agentic_workflows/use_cases.py`, `api/agentic_workflows/starting_workflows.json` | Real example values for patterns, use-cases, workflows, topology |

### Implementation context (read-only)

Use these only for trigger-condition prose and behavior OpenAPI cannot express (SSE framing, NDJSON frames, backpressure, `topology_only` projection). **Do not treat them as the HTTP contract.** If they disagree with OpenAPI, surface the drift to the user; update OpenAPI first, then invoke [openapi-to-python-lungo](../openapi-to-python-lungo/SKILL.md) to align handlers.

| Path | What to read |
|------|--------------|
| `api/agentic_workflows/router.py` | When each declared status is returned; streaming details |
| `api/agentic_workflows/instance_lifecycle.py` | Lifecycle conditions mapped to status codes |
| `api/agentic_workflows/dtos.py` | Field constraints; temporary catalog DTO status note |
| `api/agentic_workflows/auth.py` | Bearer requirement (`401` via global OpenAPI `security`) |
| `common/workflow_instance_store/interfaces.py` | Storage model (in-memory, keyed-by-instance) |
| `api/agentic_workflows/server.py` | Default port, app wiring |

Sibling skills generate Python from the contracts above; when contracts change they are usually the upstream cause and should run **after** OpenAPI/JSON Schema updates:

- `.agents/skills/openapi-to-python-lungo/SKILL.md` - OpenAPI ⇄ FastAPI router/DTOs; handler alignment with declared statuses.
- `.agents/skills/jsonschema-to-pydantic-lungo/SKILL.md` - JSON Schema ⇄ Pydantic types.

## Document structure

Keep the document organized in this order (the headings are stable so links and anchors don't churn). Re-derive the content of each from the contracts:

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
- [ ] 1. Read OpenAPI and JSON Schema under schema/openapi/ and schema/jsonschemas/
- [ ] 2. Enumerate endpoints and response statuses from OpenAPI (do not hard-code)
- [ ] 3. If a new status is needed, update OpenAPI first (see OpenAPI status codes)
- [ ] 4. Write/refresh each document section per "Document structure", deriving shapes and status lists from OpenAPI
- [ ] 5. Use router/helpers only for trigger-condition prose and streaming behavior OpenAPI omits
- [ ] 6. Use real example values from the catalog data files; link (don't inline) full example payloads
- [ ] 7. Apply the writing conventions
- [ ] 8. Verify links, lint, and OpenAPI unit tests (see Verification)
- [ ] 9. If handlers must align with new statuses or shapes, tell the user to run openapi-to-python-lungo (not this skill)
- [ ] 10. If new issues/PRs or contract files were referenced, update this skill and the document (see "Keeping current")
```

### Source-of-truth rules

- **OpenAPI first.** Paths, request/response shapes, and declared HTTP status codes live in `schema/openapi/`. Change the spec first, then the human doc and generated types (frontend `npm run generate:api-types`; Python via openapi-to-python-lungo).
- **Derive, never invent.** Every endpoint, field, and status code in the human doc must trace to OpenAPI (plus global `401` from `security`) or `event_v1.json`.
- **Surface drift.** If handlers return a status OpenAPI does not declare, **add it to OpenAPI** (via this skill) and ask the user to align handlers via [openapi-to-python-lungo](../openapi-to-python-lungo/SKILL.md). Do not document undeclared codes only in markdown.
- **Trigger conditions from code.** For each status listed in OpenAPI, use `router.py` and helpers to describe *when* it is returned. Streaming details (SSE comment frame, NDJSON frames, backpressure) remain implementation notes where OpenAPI only declares `200`.
- **Enumerate, don't count.** Build the endpoint summary and `$defs` table by listing what's in the specs.
- **Real examples.** Pull patterns, use-cases, workflow summaries, and topology from catalog data files.

### Writing conventions

- Markdown prose is **not** hard-wrapped for length: one paragraph or list item per line. Keep tables, fenced code blocks, and JSON/SSE/NDJSON examples structured as-is (their line breaks are meaningful).
- Link to source files with paths relative to `docs/` (`../schema/...`, `../api/...`). Link full example payloads rather than pasting them; excerpt only small, illustrative fragments.
- Use fenced code blocks with a language tag (`json`, `jsonc`, `http`, `text`, `bash`) for samples; these are illustrative, not citations of repo lines.
- Keep terminology consistent: "endpoint", "workflow instance", "topology", "event".
- Present per-endpoint status codes as a markdown bullet list introduced by a `Status codes:` line (or an equivalent lead-in such as `Behavior and status codes:`), one code per item in the form `` - `<code>` - <condition>. `` - never as an inline semicolon- or comma-separated sentence. Derive the code list from OpenAPI `responses` (+ global `401` where auth applies).

### OpenAPI status codes

When an operation needs a new or changed HTTP status:

1. **Update path items** - in `schema/openapi/paths/agentic-workflows.yaml`, add or adjust the status under that operation's `responses`:
   - **`401`** - do **not** repeat on every operation; rely on global `security` in `schema/openapi/openapi.yaml` (`WorkflowApiKeyBearer`).
   - **`422`** - on every operation with path/query/body validation, `$ref: ../components/schemas.yaml#/components/responses/UnprocessableEntity` (body uses full FastAPI validation JSON via `HttpError` + `RequestValidationErrorItem`).
   - **Other errors** - prefer `$ref` to shared `components/responses` (`BadRequest`, `NotFound`, `InternalServerError`, `ServiceUnavailable`, `GatewayTimeout`). Keep endpoint-specific `description` text when the generic component text is too vague.
2. **Update the human doc** - status bullets and conditions aligned with the spec.
3. **Align implementation** - ask the user to run [openapi-to-python-lungo](../openapi-to-python-lungo/SKILL.md) so handlers raise or return only statuses declared in OpenAPI.
4. **Regenerate consumers** - frontend `npm run generate:api-types` when applicable; Python DTOs/router via openapi-to-python-lungo when shapes changed.
5. **Same change set** - OpenAPI and markdown should land together in one PR; handler alignment can follow in the same PR via openapi-to-python-lungo when the user requests it.

Do **not** add error `responses=` on FastAPI decorators unless the user explicitly asks; the OpenAPI YAML under `schema/openapi/` remains the published contract.

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

Fix any OpenAPI validation, route-parity, or implementation-status drift failures before finishing when you changed `schema/openapi/`. Report handler drift to the user; do not fix handlers from this skill.

## Keeping the sources and this skill current

This is a standing requirement, not a one-off. When a prompt or request references a **new ticket/issue, pull request, or file/folder** that changes the lungo API contracts or specifications:

1. **Run upstream skills after contract edits.** When `schema/openapi/*` or `schema/jsonschemas/*` change, invoke openapi-to-python-lungo and/or jsonschema-to-pydantic-lungo before or alongside documenting (as the user directs).
2. **Update OpenAPI first** - if behavior or status codes change, follow [OpenAPI status codes](#openapi-status-codes); do not document new errors only in markdown.
3. **Update the document** - re-run the [Workflow](#workflow) so every affected section reflects the new contract.
4. **Update this skill** - if a new contract folder or document section is needed, extend [Where to look](#where-to-look) or [Document structure](#document-structure). Keep the frontmatter `description` trigger terms in sync with newly referenced paths.
5. **Keep the index in sync** - this skill is registered in the repository [`AGENTS.md`](../../../AGENTS.md) Skills table; update that entry if the skill's name or scope changes.

Surface any contract inconsistency you find (spec vs router vs schema) to the user rather than silently papering over it in prose.
