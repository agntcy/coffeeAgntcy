---
name: jsonschema-to-pydantic-lungo
description: Generates Pydantic v2 model classes from the JSON Schema documents under `coffeeAGNTCY/coffee_agents/lungo/schema/jsonschemas/` into `coffeeAGNTCY/coffee_agents/lungo/schema/types/*.py`. DO NOT TRIGGER AUTOMATICALLY. ASK THE USER IF THE SKILL SHOULD BE USED. Use when a `*_v*.json` schema under that folder is added or modified, when regenerating the lungo Pydantic types after a schema change, or when the user mentions regenerating schema types, lungo types, JSON Schema → Pydantic, or fixing drift between schema and types.
---

# JSON Schema → Pydantic v2 (lungo)

## What this skill does

Generates one Pydantic v2 module per JSON Schema in `coffeeAGNTCY/coffee_agents/lungo/schema/jsonschemas/*.json`. Output goes to `coffeeAGNTCY/coffee_agents/lungo/schema/types/<schema_name>.py`. The package `__init__.py` is updated to re-export the public symbols.

The generator is the schema. **Do not** read existing files in `schema/types/` to decide naming, layout, or behaviour — they may be missing, stale, or wrong. The only authoritative inputs are:

1. The `.json` files under `schema/jsonschemas/` (excluding `examples/`).
2. Cross-field validation logic that isn't expressible in JSON Schema, found in `coffeeAGNTCY/coffee_agents/lungo/schema/json_schema.py` (and any sibling modules under `schema/`).

## Workflow

Copy this checklist and tick items as you go:

```
- [ ] 1. Enumerate input schemas under schema/jsonschemas/*.json (skip examples/)
- [ ] 2. Read each schema fully, including $defs, $ref, allOf, anyOf, propertyNames
- [ ] 3. Read schema/json_schema.py for Python-only constraints (e.g. validate_version_specific_criteria)
- [ ] 4. Generate one schema/types/<name>.py per schema, applying the mapping rules
- [ ] 5. Update schema/types/__init__.py: re-export every public class, type alias, and `*_from_uuid` helper
- [ ] 6. Run: cd coffeeAGNTCY/coffee_agents/lungo && uv run --frozen pytest tests/unit/schemas/ -x
- [ ] 7. Run: cd coffeeAGNTCY/coffee_agents/lungo && uv run --frozen pytest tests/unit/ -x
```

If step 6 or 7 fails, identify which mapping rule(s) you applied incorrectly and **re-emit** the affected file(s) end-to-end — do not patch the failing portion in isolation. Do not edit tests or non-generated consumer code unless the user explicitly asks. If a rule itself seems wrong or insufficient to make the tests pass, surface that to the user instead of working around it.

## Naming

| Source artefact | Target Python identifier |
|---|---|
| `event_v1.json` | `event.py` (strip the `_v<N>` version suffix) |
| `$defs.foo_bar` | `class FooBar` (snake_case → PascalCase, **no semantic renames**) |
| Top-level object schema with `title: "Event (v1)"` | `class Event` (title without parenthesised version) |
| Top-level schema with no root `type` (enum-only / `$defs`-only file, e.g. `event_type_v1.json`) | no root class — the module just contains the `$defs` outputs |
| `$defs.<x>_id` referencing `<prefix>://<UUID>` strings | `class <X>Id(RootModel[str])` + helper `<x>_id_from_uuid` |
| Cross-schema `$ref` (e.g. `event_type_v1.json#/$defs/event_type`) | `from schema.types.<other_module> import <Class>` |
| Enum member name | SCREAMING_SNAKE_CASE of the value, even when the value itself is PascalCase. Example: `RECRUITER_NODE_SEARCH = "RecruiterNodeSearch"`. |

The class name is derived **mechanically** from the `$defs` key. Do not shorten, expand, or reinterpret the name. You should, however, translate it from snake_case to PascalCase. For example, `stable_agent_id` becomes `StableAgentId`, never `AgentId`. If a consumer breaks because of a rename, that's the consumer's bug to fix, not the skill's.

### Naming for *merged* classes (anyOf branches that compose ≥2 `$defs`)

Whenever an `anyOf` branch is an `allOf` that references **two or more** `$defs`, that branch produces a *merged* leaf class with no `$def` name of its own. The rule applies regardless of where the branch sits in the `anyOf` (schemas are human-written; ordering is not a contract) and regardless of how many `$defs` are composed.

For each unique composition, pick a name that:

- Reads naturally as *base concept* "with" *extension(s)*, drawing the tokens from the composed `$def` keys.
- PascalCase-joins the components, deduplicating any common prefix/suffix shared between the keys so the result does not stutter (prefer `PartialNodeWithAgentExtension` over `PartialNodeWithPartialNodeAgentExtension`).
- Treats one of the composed `$defs` as the *base* and the rest as *extensions*. The base is most easily identified as the `$def` that another branch in the same `anyOf` references alone (or with fewer extensions). Falling back: pick the `$def` with the largest field set, or the one whose name does not look extension-shaped (e.g. lacks an `_extension` / `_ext` suffix).
- For ≥2 extensions, chain them: `<Base>With<Ext1>And<Ext2>...`. If the chain becomes unreadable, pick a domain-meaningful umbrella token instead — record the choice in the class docstring.

The merged class name must be a function of the *set* of composed `$defs`, not of the branch position. Two branches that compose the same set must resolve to the same class.

A `$def` that is **only** ever referenced inside an `allOf` composing a merged class is **not** emitted as a standalone class: its fields appear directly on the merged class instead. If the same `$def` is also referenced standalone elsewhere in the schema, emit it standalone too.

This rule applies whenever the composition is anonymous. If the schema gives the composition its own `$def` name (as `partial_agent_node` / `agent_node` do in `event_v1.json`), follow the standard naming rule and emit classes named after that key — see [`mapping-rules.md`](mapping-rules.md) §D for how the named-composition case interacts with sibling-key discrimination.

## File header

Every generated file starts with:

```python
# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""Generated from ``schema/jsonschemas/<source_file>.json``.

Do not edit by hand: regenerate with the ``jsonschema-to-pydantic-lungo`` skill.

<short paraphrase of the schema's `title` and `description`>
"""
```

Use `from __future__ import annotations` and group imports stdlib → third-party → first-party (`schema.*`).

## Mapping rules

| Schema construct | Pydantic v2 emission |
|---|---|
| `type: string`, `pattern: P` | `Annotated[str, Field(pattern=P)]` |
| `type: string`, `minLength: 1` | `Annotated[str, Field(min_length=1)]` |
| `type: string`, `format: date-time` | `pydantic.AwareDatetime` |
| `type: string`, `enum: [...]` | `class X(StrEnum): ...` (preserve string values verbatim) |
| `type: number`, `default: V` | `float = V` |
| `type: boolean`, `default: V` | `bool = V` |
| `type: object`, `additionalProperties: false` | `model_config = ConfigDict(extra="forbid")` |
| `type: object`, `additionalProperties: true` (or unspecified for an extensible object) | `model_config = ConfigDict(extra="allow")` |
| Required field | bare type, no default |
| Optional field, no default | `<Type> \| None = None` |
| Optional field with `default: V` | `<Type> = V` (no `\| None`) |
| `$ref: "#/$defs/foo"` | use the generated `Foo` class as the field type |
| `$ref: "<other>_v<N>.json#/$defs/foo"` | import `Foo` from `schema.types.<other>` |
| Top-level schema `additionalProperties: false` | `Event` (or equivalent root) gets `extra="forbid"` |

### Rule A — Encode in-place schema constraints in the field type, preferably not in a validator

Anything that constrains a single value in isolation — `pattern`, `minLength`, `maximum`, `format`, `enum`, `propertyNames` on a dict — must be expressed in the field's `Annotated[...]` type. Validators (`@field_validator`, `@model_validator`) are **only** for cross-field constraints.

For `propertyNames: { $ref: "#/$defs/<id_def>" }` on a dict-shaped property, embed the constraint into the dict key annotation.
For example:

```python
instances: dict[
    Annotated[str, Field(pattern=_INSTANCE_ID_REGEX)], WorkflowInstance
]
```

See [`mapping-rules.md`](mapping-rules.md) §A for the full example.

### Rule B — `<prefix>://<UUID>` strings always pair `RootModel` with a `<def>_from_uuid` helper

For every `$defs.<x>_id` whose `pattern` matches `^<prefix>://<UUID>$`:

1. Emit `class <X>Id(RootModel[str])` with the `pattern=` constraint.
2. Emit `def <x>_id_from_uuid(<x>_uuid: UUID) -> <X>Id:` immediately below the class. Use `f"<prefix>://{<x>_uuid!s}"` to build the string.

Helper name is always `<schema_def_name>_from_uuid`, even if the prefix differs from the def name (e.g. `stable_agent_id` → prefix `agent://` → helper `stable_agent_id_from_uuid`).

### Rule C — `allOf [partial, {required: [...]}]` → standalone full class, not a subclass

When a `$def` is `allOf [partial_<X>, { required: [<all_fields>] }]`, generate **two unrelated** classes (`Partial<X>` and `<X>`) with their fields re-declared. Do not subclass: `Optional`/`| None` types from the partial would leak into the full form.

```python
class PartialThing(BaseModel):
    model_config = ConfigDict(extra="allow")
    a: SomeType | None = None
    b: SomeType | None = None

class Thing(BaseModel):  # NOT (PartialThing) — fields are required here
    model_config = ConfigDict(extra="allow")
    a: SomeType
    b: SomeType
```

### Rule D — `anyOf` discriminated by sibling-key presence → `Discriminator` callable

When the `anyOf` branches differ by *which keys are present* (typically one branch has `not { anyOf: [{ required: [k1] }, { required: [k2] }, ...] }` and another `allOf`s in a sibling extension `$def` that requires those keys), encode the choice with a callable `pydantic.Discriminator` whose **only** job is to mirror that sibling-key presence test. Leave any *full vs. partial* sub-choice to Pydantic's smart union inside each branch.

```python
def _kind_discriminator(value: Any) -> str | None:
    if isinstance(value, (FullExt, PartialExt)):
        return "with_extension"
    if isinstance(value, (FullPlain, PartialPlain)):
        return "plain"
    if not isinstance(value, dict):
        return None
    if "ext_required_key" in value or "ext_optional_key" in value:
        return "with_extension"
    return "plain"

ItemUnion = Annotated[
    Union[
        Annotated[Union[FullPlain, PartialPlain], Tag("plain")],
        Annotated[Union[FullExt, PartialExt], Tag("with_extension")],
    ],
    Discriminator(_kind_discriminator),
]
```

Why this shape:

- The discriminator does **one** thing: encode the schema's actual `anyOf` decision. Never put field-count or per-field validity checks in it.
- Each tagged branch is a `Union[Full, Partial]`. Smart union picks `Full` when all the extra required fields are populated, else `Partial`.
- Bad inputs surface clean errors from the chosen branch's own `Field` / `pattern` constraints (e.g. `String should match pattern '^agent://...'`) instead of a custom "extra fields not allowed" message.
- Do **not** add an `@model_validator(mode="after")` that polices `__pydantic_extra__` for sibling-extension keys leaking into a non-extension variant. The discriminator already routes them to the right branch.

See [`mapping-rules.md`](mapping-rules.md) §D for the full worked example covering schemas with `not { required }` clauses.

### Rule E — Cross-field constraints from `schema/json_schema.py`

JSON Schema can't express "dict key X must equal nested value's `id` field" or similar relationships. Look in `coffeeAGNTCY/coffee_agents/lungo/schema/json_schema.py` for functions called from `validate_version_specific_criteria` (and any equivalent module). Each schema-name-gated check there must be re-implemented as a Pydantic `@model_validator(mode="after")`.

**Where to attach the validator**: place it on the *smallest* class that owns every field the check reads. Do not push it up to the root just because the source helper happens to start its traversal at the root.

Example: `_enforce_workflow_instance_map_key_id_match` reads `workflow.instances` keys and `workflow_instance.id`. Both live inside the `Workflow` class (the dict is its `instances` field; each value is a `WorkflowInstance` whose `id` it can dereference). So the validator goes on `Workflow`, not on `Event` or `Data`.

The validator's docstring must point back at the source helper, e.g.:

```
mirrors ``schema.json_schema._enforce_workflow_instance_map_key_id_match``
```

## `__init__.py` regeneration

`schema/types/__init__.py` re-exports every public symbol from each generated module. Keep three groups, each alphabetised:

1. Imports from each `schema.types.<module>`.
2. The `__all__` tuple/list in the same order as the imports.
3. A short module docstring noting that the modules under this package are generated by this skill and pointing at it.

Public symbols include: every `class` declared at module level, every type alias (e.g. `TopologyNodeItem`, `Node`, `PartialNode`), and every `<name>_from_uuid` helper.

## Verification

After generating, both must pass:

```
cd coffeeAGNTCY/coffee_agents/lungo
uv run --frozen pytest tests/unit/schemas/  # schema-types parity
uv run --frozen pytest tests/unit/          # consumer compatibility
```

If a consumer fails because of a rename you introduced (e.g. it imported the old class name), report the failure to the user and ask before touching non-generated code.

## Anti-patterns

- ❌ Reading an existing `schema/types/<name>.py` to decide naming.
- ❌ Subclassing `Partial<X>` from `<X>` (or vice versa) when `allOf` only adds required fields.
- ❌ Using `@model_validator(mode="after")` to police `__pydantic_extra__` for fields that should belong to a sibling union variant.
- ❌ Putting field-count or per-field validity checks inside a `Discriminator` callable. The discriminator answers exactly one question: which schema `anyOf` branch.
- ❌ Adding `@field_validator` for a constraint that fits in `Annotated[..., Field(...)]`.
- ❌ Inventing class names (`AgentId` for `stable_agent_id`, `Node` for `regular_node`). Names come straight from `$defs` keys.
- ❌ Hand-editing a small portion of the generated file in response to a test failure or a request for a tweak. Re-emit the whole file end-to-end via the skill instead — partial patches drift from the rules over time.

## Reference

- [`mapping-rules.md`](mapping-rules.md) — full worked examples for the trickier rules (A, C, D), including the schema fragment and the corresponding emitted Pydantic code.
