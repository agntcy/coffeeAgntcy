# Reference: OpenAPI → FastAPI mapping for lungo

Concrete templates and mapping rules used by `SKILL.md`. All Python paths below are relative to `coffeeAGNTCY/coffee_agents/lungo/`.

## SPDX header

Every generated `.py` file starts with:

```python
# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0
```

## Naming derivations

| OpenAPI | Python |
|---------|--------|
| Tag `agentic-workflows` | Package `api/agentic_workflows/`, function `create_agentic_workflows_router` |
| `operationId: listPatterns` | Handler `list_patterns` |
| `operationId: getWorkflowInstanceState` | Handler `get_workflow_instance_state` |
| Schema name `WorkflowSummaryMapResponse` | Class `WorkflowSummaryMapResponse` (kept verbatim) |

Convert `operationId` from camelCase to snake_case for the handler name; keep schema names exactly as the OpenAPI uses them.

## DTO mapping

### Reuse types from `schema.types`

If a `components/schemas` entry resolves (after `$ref` chasing) to a type already exported from `schema.types`, import it instead of redefining. Known reusable types include `InstanceId`, `WorkflowInstance`, `Workflow`, `Topology`, `PartialTopology`, `Event`. Check `schema/types/__init__.py` for the current `__all__`.

### Object with `additionalProperties: false`

```yaml
Pattern:
  type: object
  required: [name]
  additionalProperties: false
  properties:
    name:
      type: string
      minLength: 1
```

```python
class Pattern(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: Annotated[str, Field(min_length=1)]
```

### Object acting as a map (`additionalProperties: <schema>`)

```yaml
WorkflowSummaryMapResponse:
  type: object
  additionalProperties:
    $ref: "#/components/schemas/WorkflowSummary"
```

```python
class WorkflowSummaryMapResponse(RootModel[dict[str, WorkflowSummary]]):
    """Map keyed by workflow name."""
```

The key type is always `str`, regardless of any `propertyNames` schema. See [§ Map responses with constrained keys](#map-responses-with-constrained-keys) below for why and for the current handling.

### Map responses with constrained keys

When the OpenAPI map declares `propertyNames` (a pattern, format, `$ref`, etc.), the generated DTO ignores that constraint and uses a plain `dict[str, <value_t>]`:

```yaml
WorkflowInstanceMapResponse:
  type: object
  propertyNames:
    $ref: "#/components/schemas/InstanceId"   # itself: type: string, pattern: ^instance://...
  additionalProperties:
    $ref: "#/components/schemas/WorkflowInstance"
```

```python
class WorkflowInstanceMapResponse(RootModel[dict[str, WorkflowInstance]]):
    """Workflow instances keyed by InstanceId URI."""
```

> **Known exception — flag in output.** `propertyNames` is **not enforced at the DTO layer**. Re-implementing the constraint here (for instance copying the `InstanceId` regex from `schema/types/event.py` into a `field_validator`) would duplicate logic that already lives in `schema/types/` and silently drift the next time the canonical type changes. The skill deliberately relies on the value type's own validation: a `WorkflowInstance` already validates its `id: InstanceId` field, so any caller that constructs a value with a mismatched key gets a runtime check on the nested id (and the cross-check that key equals nested id is, today, the responsibility of the value type itself — see `Workflow.instances` in `schema/types/event.py`). When generating or validating a DTO with a constrained `propertyNames`, mention this exception in the output and recommend revisiting it once `schema/types/` exposes its key patterns as importable constants (which would let the skill enforce the constraint without duplication).

Why never `dict[InstanceId, V]` (or any other Pydantic `RootModel` subclass as the key):

- `RootModel` instances are unhashable by default (`__hash__ = None`); `model_validate(...)` on the map raises `TypeError: unhashable type` before it can populate anything.
- Setting `model_config = ConfigDict(frozen=True)` on the key model fixes hashability but `model_dump_json` then serializes keys as the model's Python repr (e.g. `"root='instance://...'"`), which violates the OpenAPI contract that JSON object keys are bare strings.
- Membership tests with bare strings (`"instance://..." in m.root`) silently return `False`.

### Optional vs required fields

Fields not listed in `required` get a `None` default:

```python
class Foo(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: Annotated[str, Field(min_length=1)]
    note: str | None = None
```

### Constraints

| OpenAPI | Pydantic `Field` |
|---------|------------------|
| `minLength` / `maxLength` | `min_length=`, `max_length=` |
| `pattern` | `pattern=` |
| `minimum` / `maximum` | `ge=`, `le=` |
| `exclusiveMinimum` / `exclusiveMaximum` | `gt=`, `lt=` |
| `format: uuid` | `uuid.UUID` (Python type) |
| `format: date-time` | `datetime.datetime` |
| `enum: [...]` | `Literal[...]` or a `StrEnum` subclass |

### Imports

Top of `dtos.py`:

```python
from __future__ import annotations

from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, RootModel
```

Add `from schema.types import <names>` only for types actually reused.

## Router templates

### Skeleton

```python
from __future__ import annotations

from typing import Annotated

from api.<tag_snake>.dtos import (...)
from fastapi import APIRouter, HTTPException, Path, Query, Request

_TAG = "<tag-kebab>"


def create_<tag_snake>_router() -> APIRouter:
    router = APIRouter(tags=[_TAG])

    # ... handlers ...

    return router
```

### Preserving existing `APIRouter(...)` arguments

`tags=[...]` is the only constructor argument the skill derives from the OpenAPI document. Everything else passed to `APIRouter(...)` in existing code is **user-owned router behavior** and must be carried over verbatim on regeneration — the spec cannot tell you it is there, so dropping it silently changes runtime behavior.

The most important case is router-level `dependencies=`, commonly an authentication/authorization gate:

```python
from api.<tag_snake>.auth import require_workflow_api_key  # whatever the existing import is — keep it
from fastapi import APIRouter, Depends


def create_<tag_snake>_router() -> APIRouter:
    router = APIRouter(
        tags=[_TAG],
        dependencies=[Depends(require_workflow_api_key)],  # example dependency; preserve ANY dependencies found
    )

    # ... handlers ...

    return router
```

Rules:

- If the on-disk `APIRouter(...)` has a `dependencies=[...]` list, keep the entire list (and the imports it needs) exactly. Do not assume the dependency is `require_workflow_api_key`; that is only the example here. Apply the same rule to any callable(s) the user passed.
- Preserve other constructor keywords too (`prefix=`, `responses=`, `default_response_class=`, `deprecated=`, etc.).
- The skill only reconciles `tags`: add it if missing, otherwise leave the construction's other arguments untouched.
- When validating (not regenerating), report a router that has lost a previously-present `dependencies=` (or other constructor argument) as a behavior regression, not a cosmetic diff.

### GET with query params and JSON response

```yaml
/patterns/:
  get:
    operationId: listPatterns
    summary: List patterns
    responses:
      "200":
        description: ...
        content:
          application/json:
            schema:
              $ref: "#/components/schemas/PatternListResponse"
```

```python
@router.get(
    "/patterns/",
    response_model=PatternListResponse,
    summary="List patterns",
)
async def list_patterns() -> PatternListResponse:
    """GET /patterns/."""
    raise HTTPException(status_code=501, detail="Not implemented")
```

### Path params with constraints

```python
@router.get(
    "/agentic-workflows/{workflow_name}/",
    response_model=Workflow,
    summary="Get workflow details",
)
async def get_agentic_workflow(
    workflow_name: Annotated[str, Path(min_length=1)],
    topology_only: Annotated[bool, Query()] = False,
) -> Workflow:
    """GET /agentic-workflows/{workflow_name}/."""
    raise HTTPException(status_code=501, detail="Not implemented")
```

### UUID path params (e.g. `WorkflowInstancePathId` → `format: uuid`)

```python
from uuid import UUID

@router.get(
    "/.../instances/{workflow_instance_id}/",
    response_model=WorkflowInstance,
    summary="...",
)
async def get_workflow_instance_state(
    workflow_instance_id: Annotated[UUID, Path(description="...")],
) -> WorkflowInstance:
    raise HTTPException(status_code=501, detail="Not implemented")
```

### Request body

```python
@router.post(
    "/.../events/",
    status_code=204,
    summary="Post event",
)
async def post_event(event: Event) -> None:
    raise HTTPException(status_code=501, detail="Not implemented")
```

### Non-JSON responses

| OpenAPI media type | FastAPI response class | Return annotation |
|--------------------|------------------------|-------------------|
| `text/event-stream` | `StreamingResponse` | `StreamingResponse` |
| Redirect (3xx with `Location`) | `RedirectResponse` | `RedirectResponse` |

For these, omit `response_model` and set `response_class=` and `status_code=` instead.

### Repeated query params (arrays)

OpenAPI `style: form, explode: true` over an array → typed as `Annotated[list[str] | None, Query()] = None`.

## Test templates

### Spec validation

```python
# tests/unit/openapi/test_<tag_snake>_openapi_spec.py
from __future__ import annotations

import warnings
from pathlib import Path

import pytest
from openapi_spec_validator import validate
from prance import ResolvingParser

_LUNGO_ROOT = Path(__file__).resolve().parents[3]
_OPENAPI_ROOT = _LUNGO_ROOT / "schema" / "openapi" / "openapi.yaml"


@pytest.mark.filterwarnings("ignore::UserWarning:requests")
def test_<tag_snake>_openapi_spec_validates() -> None:
    assert _OPENAPI_ROOT.is_file(), f"missing OpenAPI entry {_OPENAPI_ROOT}"
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", category=UserWarning)
        parser = ResolvingParser(str(_OPENAPI_ROOT.resolve()), lazy=True)
        parser.parse()
    validate(parser.specification)
    assert "paths" in parser.specification
    assert len(parser.specification["paths"]) >= 1
```

### Routes-match-app

```python
# tests/unit/openapi/test_<tag_snake>_openapi_routes_match_app.py
from __future__ import annotations

import warnings
from pathlib import Path

import pytest
from api.<tag_snake>.router import create_<tag_snake>_router
from fastapi import FastAPI
from prance import ResolvingParser

_LUNGO_ROOT = Path(__file__).resolve().parents[3]
_OPENAPI_ROOT = _LUNGO_ROOT / "schema" / "openapi" / "openapi.yaml"

_HTTP_METHODS = frozenset(
    {"get", "post", "put", "patch", "delete", "head", "options", "trace"},
)


def _operations_from_paths(paths: object) -> set[tuple[str, str]]:
    out: set[tuple[str, str]] = set()
    if not isinstance(paths, dict):
        return out
    for path, item in paths.items():
        if not isinstance(item, dict):
            continue
        for key, val in item.items():
            k = key.lower()
            if k in _HTTP_METHODS and isinstance(val, dict):
                out.add((str(path), k.upper()))
    return out


def _minimal_app() -> FastAPI:
    app = FastAPI(openapi_url=None, docs_url=None, redoc_url=None)
    app.include_router(create_<tag_snake>_router())
    return app


@pytest.mark.filterwarnings("ignore::UserWarning:requests")
def test_<tag_snake>_spec_paths_match_fastapi_router() -> None:
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", category=UserWarning)
        parser = ResolvingParser(str(_OPENAPI_ROOT.resolve()), lazy=True)
        parser.parse()
    spec_ops = _operations_from_paths(parser.specification.get("paths"))

    app = _minimal_app()
    app_ops = _operations_from_paths(app.openapi().get("paths"))

    assert spec_ops == app_ops, (
        f"spec vs app path/method mismatch.\n"
        f"Only in spec: {sorted(spec_ops - app_ops)}\n"
        f"Only in app: {sorted(app_ops - spec_ops)}"
    )
```

## Common pitfalls

- `prance` may import `requests` and emit a `UserWarning`. Suppress it exactly as shown in the templates; the project's pytest config promotes warnings to errors.
- Do not strip a trailing slash from a path. `/patterns/` and `/patterns` are different operations to FastAPI.
- `additionalProperties: false` must always become `ConfigDict(extra="forbid")`; omitting it lets clients smuggle fields through and silently break the spec contract.
- For map-style responses, use `RootModel[dict[K, V]]`, not a wrapper class with a single `root: dict[...]` field — the JSON shape differs.
- When the user added per-tag helpers (constants, helper functions) outside the `create_<tag_snake>_router` function, leave them alone and preserve their imports.
- Never strip arguments off an existing `APIRouter(...)`. The skill only owns `tags=[...]`; `dependencies=[...]` (auth/authz gates and the like), `prefix=`, `responses=`, etc. are user-owned and must be preserved verbatim, including their imports. See [§ Preserving existing `APIRouter(...)` arguments](#preserving-existing-apirouter-arguments).
