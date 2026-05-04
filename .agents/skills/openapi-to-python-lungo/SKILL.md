---
name: openapi-to-python-lungo
description: >-
  Generates and validates Python FastAPI routers and DTOs from the OpenAPI schemas in coffeeAGNTCY/coffee_agents/lungo/schema/openapi for the lungo subproject. Use when adding, removing, renaming, or modifying endpoints in any lungo OpenAPI document; when generating or regenerating files under coffeeAGNTCY/coffee_agents/lungo/api/<tag>/ (router.py, dtos.py); when validating that hand-edited handlers or DTOs still match the OpenAPI spec; or when scaffolding the OpenAPI unit tests for a router.
---

# OpenAPI → FastAPI Generator and Validator (lungo)

This skill turns the OpenAPI documents under `coffeeAGNTCY/coffee_agents/lungo/schema/openapi/` into Python FastAPI routers and Pydantic DTOs, and validates that hand-edited code still matches the spec. All paths in this document are relative to the repository root.

The lungo project root is `coffeeAGNTCY/coffee_agents/lungo/`. All other paths below (`api/...`, `schema/...`, `tests/...`) are relative to that project root.

## Conventions

The skill follows one consistent layout per OpenAPI **tag**. The tag is the discriminator that maps an OpenAPI operation to a Python package; everything else is derived deterministically from it.

| OpenAPI concept | Python artifact |
|-----------------|-----------------|
| Tag (kebab-case), e.g. `agentic-workflows` | Snake-case package: `api/agentic_workflows/` |
| All operations sharing that tag | Single `api/<tag_snake>/router.py` |
| All `components/schemas` referenced by those operations | Single `api/<tag_snake>/dtos.py` |
| Per-tag router function | `create_<tag_snake>_router() -> APIRouter` |
| OpenAPI entry point | `schema/openapi/openapi.yaml` (may `$ref` `paths/<tag>.yaml` and `components/schemas.yaml`) |

The skill must remain **general** across tags: never hard-code endpoint names, schemas, or counts. Only the layout and naming rules above are fixed.

## File ownership

- `dtos.py` is **owned by this skill**. It is regenerated from scratch on every run; never preserve hand edits inside it. If a user needs to edit a DTO, they must edit the OpenAPI schema instead.
- `router.py` is **co-owned**. The skill owns:
  - the module-level imports it adds for DTOs,
  - the `create_<tag_snake>_router()` function signature and the `APIRouter(tags=[...])` construction,
  - the route decorators (path, method, `response_model`, `status_code`, `summary`, etc.) and handler **signatures** (parameters, type annotations, return type).

  The user owns:
  - the **bodies** of existing handlers,
  - any module-level helpers (constants, helper functions, classes) added around the router function,
  - additional imports the user added for those helpers.

  When regenerating an existing handler, preserve its body verbatim. When decorator metadata or the signature must change to match the spec, rewrite the decorator and signature, but keep the body.
- The OpenAPI tests under `tests/unit/openapi/` are **owned by this skill**. Regenerate them when missing or stale; do not preserve hand edits inside them.

## Workflow selector

Pick the workflow that matches the user's intent, then jump to that section:

| Trigger | Workflow |
|---------|----------|
| OpenAPI changed (added/removed/renamed paths or schemas), or `router.py` / `dtos.py` is missing | **Generate / regenerate** |
| User edited a handler signature, decorator, or DTO and wants to confirm it is still valid | **Validate** |
| Just want to confirm everything is consistent end-to-end | **Validate**, then run tests |

## Generate / regenerate workflow

Track progress with this checklist:

```
- [ ] 1. Identify affected tags
- [ ] 2. Resolve the OpenAPI spec
- [ ] 3. Regenerate dtos.py from scratch
- [ ] 4. Reconcile router.py (preserve handler bodies)
- [ ] 5. Generate or refresh tests under tests/unit/openapi/
- [ ] 6. Run the tests and the linter
```

### Step 1 — Identify affected tags

Read `schema/openapi/openapi.yaml` and any files it `$ref`s under `schema/openapi/paths/` and `schema/openapi/components/`. List every tag that appears on at least one operation. For each tag, the target package is `api/<tag_snake>/` where `tag_snake` is the kebab-case tag with `-` replaced by `_`.

If the spec references types from `schema/jsonschemas/` (and therefore from `schema/types/` Pydantic mirrors), prefer importing those Pydantic types into `dtos.py` rather than redeclaring them. See [reference.md](reference.md) for the mapping rules.

### Step 2 — Resolve the OpenAPI spec

Use `prance.ResolvingParser` to dereference `$ref`s before mapping. The resolved `paths` and `components.schemas` must drive generation; do not read the raw YAML directly to extract operations or schemas.

```python
from prance import ResolvingParser
parser = ResolvingParser("schema/openapi/openapi.yaml", lazy=True)
parser.parse()
spec = parser.specification  # dict with resolved $refs
```

### Step 3 — Regenerate `dtos.py`

Overwrite `api/<tag_snake>/dtos.py` from scratch using the rules in [reference.md § DTO mapping](reference.md). In summary:

- One Pydantic class per `components/schemas.<Name>` referenced by an operation under this tag.
- Object schema with `additionalProperties: false` → `class X(BaseModel): model_config = ConfigDict(extra="forbid")`.
- Object schema acting as a map (`additionalProperties: <schema>`) → `class X(RootModel[dict[str, <value_t>]])`. The key type is **always** `str` (or whatever underlying JSON primitive is — usually `str`), even when `propertyNames` references a typed schema. JSON object keys are strings on the wire, and using a Pydantic `RootModel` subclass as a dict key is broken in practice (the default class is unhashable; `frozen=True` makes it hashable but `model_dump_json` then writes the model's Python repr as the JSON key, which violates the contract).
- **Known exception — `propertyNames` is currently not enforced in `dtos.py`.** When `propertyNames` adds a constraint (pattern, format, `$ref`, etc.), the skill deliberately **does not** generate a `field_validator` that re-implements that constraint. The reason: doing so would duplicate logic that already lives in `schema/types/` (e.g. the `InstanceId` regex would have to be copied into every DTO map that keys on it, drifting on every change). Generated DTOs use a plain `dict[str, <value_t>]` and rely on the value type's own validation (the value typically references the typed key via a nested field, e.g. `WorkflowInstance.id: InstanceId`). This means `propertyNames` constraints are **not currently enforced at the DTO layer**; flag this in any output that mentions a `propertyNames` constraint and treat it as a known limitation to revisit (a single-source-of-truth helper, e.g. exposing pattern constants from `schema.types`, would let the skill enforce this without duplication). See [reference.md § Map responses with constrained keys](reference.md).
- Schemas that resolve to types already exported from `schema.types` (for example `InstanceId`, `WorkflowInstance`, `Event`, `Workflow`, `Topology`) must be **imported** from `schema.types`, not redefined.
- Required fields are non-default annotations; optional fields default to `None`.
- Use `Annotated[T, Field(min_length=..., pattern=..., ge=..., ...)]` for string/numeric constraints.
- Always include the standard SPDX header at the top of the file.

### Step 4 — Reconcile `router.py`

For each operation under this tag:

1. Compute the expected handler from the OpenAPI operation:
   - Function name: `operationId` converted to `snake_case`. If `operationId` is missing, derive a stable name from `<method>_<path>` and warn the user that adding `operationId` is preferred.
   - Decorator: `@router.<method>(<path>, response_model=<dto_or_type>, status_code=<status>, summary="<summary>")`. Omit `response_model` / `status_code` only when the operation declares no non-default 2xx response or no schema.
   - Parameters:
     - Path params: `Annotated[<py_type>, Path(<constraints>)]`.
     - Query params: `Annotated[<py_type>, Query(<constraints>)]` with the OpenAPI default if present.
     - Request body: typed parameter using the body schema's DTO.
   - Return type annotation: the response DTO (or `RedirectResponse`, `StreamingResponse`, etc. for non-JSON responses).
2. If the function does **not** exist, create it with the signature above and a stub body:

   ```python
   raise HTTPException(status_code=501, detail="Not implemented")
   ```

   Add a one-line docstring summarizing the method and path.
3. If the function **exists**:
   - Update its decorator and signature in place to match the spec.
   - Preserve the handler **body** verbatim.
   - Preserve any decorator-unrelated import the user added.
4. After processing all spec operations, look for handler functions inside `create_<tag_snake>_router()` that no longer correspond to any operation. Do not delete them silently — emit a warning of the form:

   ```
   Stale handler: <function_name> is no longer in the OpenAPI spec for tag '<tag>'. Remove it manually if intentional.
   ```

5. Make sure the `APIRouter` is constructed with `tags=["<tag>"]` and that `create_<tag_snake>_router()` returns it.

See [reference.md § Router templates](reference.md) for concrete snippets.

### Step 5 — Generate tests

Ensure the directory `tests/unit/openapi/` exists. For each tag, generate (or refresh) two files. File names are not load-bearing; the convention below uses `<tag_snake>` and is recommended:

- `tests/unit/openapi/test_<tag_snake>_openapi_spec.py` — validates the resolved OpenAPI document with `openapi_spec_validator`.
- `tests/unit/openapi/test_<tag_snake>_openapi_routes_match_app.py` — builds a minimal FastAPI app via `create_<tag_snake>_router()` and asserts that the `(path, METHOD)` set from `app.openapi()` equals the set extracted from the resolved OpenAPI spec.

Both tests resolve `schema/openapi/openapi.yaml` via `prance` and use the same `_HTTP_METHODS` filter shown in [reference.md § Test templates](reference.md). They must not assume any specific endpoint names — they compare full sets.

### Step 6 — Run tests and linter

Run from `coffeeAGNTCY/coffee_agents/lungo/`:

```bash
uv run pytest tests/unit/openapi/ tests/unit/api/ -q
```

If integration tests reference the affected tag (for example `tests/integration/...` files matching the tag), run them too. Then run the project's standard linter / formatter (`ruff`, `make lint`, etc., as configured for the project) on all touched files. Fix any errors before finishing.

## Validate workflow

Use this when the user has hand-edited `router.py` or `dtos.py` and wants confirmation that the spec, code, and tests are still consistent.

```
- [ ] 1. Resolve the OpenAPI spec (prance) and confirm it validates
- [ ] 2. Diff (path, METHOD) sets: spec vs FastAPI app
- [ ] 3. For each spec operation, confirm the handler signature matches
- [ ] 4. Confirm dtos.py would be regenerated identically
- [ ] 5. Run the OpenAPI and router tests
```

### Step 1 — Resolve and validate the spec

Use `prance.ResolvingParser` plus `openapi_spec_validator.validate(...)`. A failure here means the spec itself is broken; report it and stop.

### Step 2 — Path/method diff

Build the minimal FastAPI app exactly as in the generated `test_<tag_snake>_openapi_routes_match_app.py`, then compute the symmetric difference between the spec and app `(path, METHOD)` sets. Report:

- `Only in spec: ...` — handlers missing from `router.py`.
- `Only in app: ...` — extra handlers not in the spec (likely stale).

### Step 3 — Per-operation signature check

For every spec operation, confirm:

- the handler exists,
- its decorator matches (`response_model`, `status_code`, `summary`, `path`, `method`),
- the parameter list (path, query, body) and types match the spec.

Report mismatches with the operation id and a one-line diff.

### Step 4 — DTO drift check

Run the regeneration logic from step 3 of the generate workflow against an in-memory buffer and diff it against the on-disk `dtos.py`. If they differ, the user has either edited `dtos.py` by hand or the spec changed without regeneration. Recommend re-running the generate workflow.

### Step 5 — Run the tests

Run the same tests as in the generate workflow. They are the authoritative validation.

## When to ask the user

Stop and ask the user before doing any of:

- deleting or renaming a public symbol from `dtos.py` that is imported elsewhere in the project,
- removing a stale handler from `router.py` (always recommend, never auto-delete),
- changing an existing handler **body** to satisfy a signature change (only the signature is yours; body changes belong to the user).

## Additional resources

- [reference.md](reference.md) — OpenAPI → Pydantic mapping rules, router templates, and test templates with concrete snippets.
