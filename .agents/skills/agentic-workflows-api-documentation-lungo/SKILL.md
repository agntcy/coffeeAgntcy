---
name: agentic-workflows-api-documentation-lungo
description: >-
  Authors and maintains the human-facing Agentic Workflows API documentation for the lungo subproject at coffeeAGNTCY/coffee_agents/lungo/docs/workflow-instance_api.md.
  OpenAPI under coffeeAGNTCY/coffee_agents/lungo/schema/openapi/ is the HTTP contract source of truth (paths, shapes, response statuses): updated manually or via LLM, never generated from code.
  Covers the catalog API, workflow-instance lifecycle/state, internal event ingress, SSE and NDJSON streaming, event_v1, and topology/use-case shapes.
  Use when documenting or updating the lungo workflow API; when schema/openapi/ or schema/jsonschemas/ changes; or when a prompt references a ticket/issue, pull request, or file/folder that changes lungo API contracts.
  DO NOT TRIGGER AUTOMATICALLY. ASK THE USER IF THE SKILL SHOULD BE USED.
---

# Agentic Workflows API documentation (lungo)

Produces and maintains a single human-facing reference document for the lungo **Agentic Workflows API** from the machine-readable contracts already in the repo. The document is a guide, not the contract.

**Source of truth:** `schema/openapi/` (HTTP paths, shapes, response statuses) and `schema/jsonschemas/` (instance/event payloads). Read those folders fresh on every run; resolve `$ref`s from the OpenAPI entry point. Do not trust the existing human doc or this skill to list every file inside those trees - layout may change.

The lungo project root is `coffeeAGNTCY/coffee_agents/lungo/`. The output document lives at `docs/workflow-instance_api.md` and links to in-repo specs with paths relative to `docs/` (e.g. `../schema/...`).

**Scope:** This skill updates OpenAPI under `schema/openapi/` and `workflow-instance_api.md` only. Python routers/DTOs: [openapi-to-python-lungo](../openapi-to-python-lungo/SKILL.md). Pydantic types from JSON Schema: [jsonschema-to-pydantic-lungo](../jsonschema-to-pydantic-lungo/SKILL.md). For trigger-condition prose or streaming behavior OpenAPI omits, read implementation only as needed via openapi-to-python-lungo's scope - do not treat Python files as contract sources.

## Output

- Human guide: `docs/workflow-instance_api.md`
- OpenAPI (when paths, shapes, or response statuses change): files under `schema/openapi/` - discover path items, shared schemas, and reusable error responses by reading the tree

Keep the human guide aligned with the resolved OpenAPI document. Reconcile using [Document structure](#document-structure) whenever the API surface changes. When HTTP statuses change, follow [OpenAPI status codes](#openapi-status-codes) before updating prose.

## Where to look

| Role | Path (relative to lungo root) |
|------|-------------------------------|
| HTTP contract | `schema/openapi/` |
| Event / instance JSON Schema | `schema/jsonschemas/` |
| Human guide (output) | `docs/workflow-instance_api.md` |

Enumerate endpoints, fields, and status codes from the specs - do not hard-code counts or names from memory. For worked examples in prose (patterns, use-cases, sample topology), pull real values from catalog data under `api/agentic_workflows/` when present.

Sibling skills run after contract edits (as the user directs):

- [openapi-to-python-lungo](../openapi-to-python-lungo/SKILL.md) - align FastAPI routers/DTOs and read handler behavior
- [jsonschema-to-pydantic-lungo](../jsonschema-to-pydantic-lungo/SKILL.md) - regenerate Pydantic mirrors

## Document structure

Keep the document organized in this order (headings are stable). Re-derive content from `schema/openapi/` and `schema/jsonschemas/`:

1. **Title + intro** - one-paragraph scope covering catalog, instance lifecycle, streaming, and event schema
2. **Authoritative sources** - table linking in-repo specs and example payloads; note any temporary DTO/catalog gaps pending schema consolidation
3. **Conventions** - identifier URI schemes; path-UUID vs payload-URI rule; authentication; storage model; default port
4. **Endpoint summary** - one table row per operation from OpenAPI (purpose, method and path, response type)
5. **Catalog API** - list/catalog/documentation/chat endpoints declared in OpenAPI
6. **Workflow details and topology response shapes** - workflow GET, `topology_only`, node/edge field breakdown, example topology from catalog data when available
7. **Workflow-instance lifecycle and state** - instantiate, list, get state, delete, each with status codes from OpenAPI
8. **Internal event ingress** - events POST (internal), validation, status codes
9. **Streaming formats** - SSE instance stream and NDJSON pattern chat (implementation notes where OpenAPI only declares success)
10. **Workflow-instance state JSON Schema** - link to published schema; full snapshot vs delta; top-level shape; `$defs` table; event types; worked examples
11. **Frontend integration checklist** - end-to-end flow (selectors, list, graph, instantiate, SSE, reconcile, delete)

## Workflow

```
- [ ] 1. Read schema/openapi/ and schema/jsonschemas/ (resolve OpenAPI from its entry point)
- [ ] 2. Enumerate endpoints and response statuses from the resolved spec (do not hard-code)
- [ ] 3. If a new status is needed, update OpenAPI first (see OpenAPI status codes)
- [ ] 4. Write/refresh each section per Document structure from the specs
- [ ] 5. For trigger conditions or streaming details OpenAPI omits, read handler code only as needed; surface drift to the user
- [ ] 6. Use real catalog example values where helpful; link full example payloads rather than inlining
- [ ] 7. Apply the writing conventions
- [ ] 8. Verify links, lint, and OpenAPI unit tests (see Verification)
- [ ] 9. If handlers must align with new statuses or shapes, tell the user to run openapi-to-python-lungo (not this skill)
- [ ] 10. If new contract folders or doc sections appear, update Document structure here; keep AGENTS.md in sync if skill scope changes
```

### Source-of-truth rules

- **OpenAPI first.** Paths, request/response shapes, and declared HTTP status codes live in `schema/openapi/`. Change the spec first, then the human doc and generated types (frontend `npm run generate:api-types`; Python via openapi-to-python-lungo).
- **Derive, never invent.** Every endpoint, field, and status code in the human doc must trace to OpenAPI (plus global `401` from `security`) or JSON Schema under `schema/jsonschemas/`.
- **Surface drift.** If implementation returns a status OpenAPI does not declare, add it to OpenAPI via this skill and ask the user to align handlers via openapi-to-python-lungo. Do not document undeclared codes only in markdown.
- **Enumerate, don't count.** Build tables and lists by reading the specs, not from cached skill text.
- **Generic skill, specific repo.** This skill names folders, not every file inside them; discover current layout when you run.

### Writing conventions

- Markdown prose is **not** hard-wrapped for length: one paragraph or list item per line. Keep tables, fenced code blocks, and JSON/SSE/NDJSON examples structured as-is.
- Link to source files with paths relative to `docs/`. Link full example payloads rather than pasting them; excerpt only small fragments.
- Use fenced code blocks with a language tag for samples; these are illustrative, not citations of repo lines.
- Keep terminology consistent: "endpoint", "workflow instance", "topology", "event".
- Present per-endpoint status codes as a markdown bullet list after a `Status codes:` (or similar) lead-in, one code per item: `` - `<code>` - <condition>. `` Derive codes from OpenAPI `responses` plus global `401` where auth applies.

### OpenAPI status codes

When an operation needs a new or changed HTTP status:

1. **Update OpenAPI** - under `schema/openapi/`, add or adjust `responses` on the operation (discover path items and shared `components/responses` by reading the tree):
   - **`401`** - rely on global `security` on the OpenAPI root document; do not repeat on every operation unless the spec already does
   - **`422`** - on operations with path/query/body validation, reference the shared unprocessable-entity response component
   - **Other errors** - prefer `$ref` to shared error response components; keep operation-specific `description` when generic text is too vague
2. **Update the human doc** - status bullets and conditions aligned with the spec
3. **Align implementation** - ask the user to run openapi-to-python-lungo so handlers use only declared statuses
4. **Regenerate consumers** - `npm run generate:api-types` in the lungo frontend when applicable; Python via openapi-to-python-lungo when shapes changed
5. **Same change set** - OpenAPI and markdown together in one PR; handler alignment via openapi-to-python-lungo when the user requests it

Do **not** add error `responses=` on FastAPI decorators unless the user explicitly asks; YAML under `schema/openapi/` remains the published contract.

### Verification

Run from the repo root:

```bash
cd coffeeAGNTCY/coffee_agents/lungo/docs
for p in $(grep -oE '\]\(\.\.?/[^)]+\)' workflow-instance_api.md | sed -E 's/^\]\(//; s/\)$//'); do
  [ -e "$p" ] && echo "OK   $p" || echo "MISS $p"
done
```

Fix any `MISS` link before finishing.

From `coffeeAGNTCY/coffee_agents/lungo/`:

```bash
uv run pytest tests/unit/openapi/ -q
```

Fix OpenAPI validation or spec drift when you changed `schema/openapi/`. Report handler drift to the user; do not fix handlers from this skill.

## Keeping this skill current

When a prompt references a new ticket, pull request, or contract folder:

1. **Contract edits first** - update `schema/openapi/` and/or `schema/jsonschemas/`; invoke sibling codegen skills as the user directs
2. **Update OpenAPI before prose** - follow [OpenAPI status codes](#openapi-status-codes); do not document new errors only in markdown
3. **Refresh the human doc** - re-run the [Workflow](#workflow)
4. **Adjust this skill sparingly** - prefer updating [Document structure](#document-structure) over growing file inventories; keep [`AGENTS.md`](../../../AGENTS.md) in sync if name or scope changes

Surface spec vs implementation inconsistency to the user; do not paper over drift in prose.
