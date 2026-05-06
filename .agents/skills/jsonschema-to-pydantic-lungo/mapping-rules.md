# Mapping rules — worked examples

Worked examples for the rules in [`SKILL.md`](SKILL.md) that are easy to get wrong. Each section shows a JSON Schema fragment and the Pydantic v2 emission for it.

## §A — Embed in-place constraints in the type, not in a validator

### Pattern on a string

Schema:

```json
"event_id": {
  "type": "string",
  "pattern": "^event://[0-9a-fA-F]{8}-...$",
  "description": "Unique id for an event message."
}
```

Emit:

```python
_EVENT_ID_REGEX = r"^event://[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$"

class EventId(RootModel[str]):
    """Generated from ``$defs.event_id``: <description>."""

    root: Annotated[
        str,
        Field(pattern=_EVENT_ID_REGEX, description="Unique id for an event message."),
    ]
```

### `propertyNames` on a dict-shaped property

Schema:

```json
"instances": {
  "type": "object",
  "propertyNames": { "$ref": "#/$defs/instance_id" },
  "additionalProperties": { "$ref": "#/$defs/workflow_instance" }
}
```

Emit (inside the parent class):

```python
instances: dict[
    Annotated[str, Field(pattern=_INSTANCE_ID_REGEX)], WorkflowInstance
]
```

Do not emit a separate `@field_validator` that loops the keys checking the pattern — the dict-key annotation is enforced by Pydantic on every validation pass.

## §C — `allOf [partial, {required: [...]}]` → standalone full class

Schema:

```json
"partial_regular_node": {
  "type": "object",
  "required": ["id", "operation"],
  "properties": {
    "id":          { "$ref": "#/$defs/node_id" },
    "operation":   { "$ref": "#/$defs/operation" },
    "type":        { "type": "string", "minLength": 1 },
    "label":       { "type": "string", "minLength": 1 },
    "size":        { "$ref": "#/$defs/size" },
    "layer_index": { "type": "number", "default": 0 }
  },
  "additionalProperties": true
},
"regular_node": {
  "allOf": [
    { "$ref": "#/$defs/partial_regular_node" },
    {
      "type": "object",
      "required": ["id", "operation", "type", "label", "size", "layer_index"]
    }
  ]
}
```

Emit two unrelated classes (no inheritance):

```python
class PartialRegularNode(BaseModel):
    model_config = ConfigDict(extra="allow")

    id: NodeId
    operation: Operation
    type: Annotated[str, Field(min_length=1)] | None = None
    label: Annotated[str, Field(min_length=1)] | None = None
    size: Size | None = None
    layer_index: float = 0


class RegularNode(BaseModel):  # NOT (PartialRegularNode)
    model_config = ConfigDict(extra="allow")

    id: NodeId
    operation: Operation
    type: Annotated[str, Field(min_length=1)]
    label: Annotated[str, Field(min_length=1)]
    size: Size
    layer_index: float
```

Why no subclassing: `type: ... | None = None` from `PartialRegularNode` would leak into `RegularNode` and `RegularNode(id=..., operation=...)` would silently validate.

## §D — `anyOf` discriminated by sibling-key presence

Schema (the canonical lungo case for `partial_node` / `node`). The agent-flavoured shapes are themselves first-class `$defs` (`partial_agent_node`, `agent_node`), so the `anyOf` branches reference them by name rather than composing them inline:

```json
"partial_node_agent_extension": {
  "type": "object",
  "required": ["agent_record_uri"],
  "properties": {
    "agent_record_uri": { "type": "string", "minLength": 1 },
    "stable_agent_id":  { "$ref": "#/$defs/stable_agent_id" }
  }
},
"node_agent_extension": {
  "allOf": [
    { "$ref": "#/$defs/partial_node_agent_extension" },
    { "type": "object", "required": ["agent_record_uri", "stable_agent_id"] }
  ]
},
"partial_agent_node": {
  "allOf": [
    { "$ref": "#/$defs/partial_regular_node" },
    { "$ref": "#/$defs/partial_node_agent_extension" }
  ]
},
"agent_node": {
  "allOf": [
    { "$ref": "#/$defs/regular_node" },
    { "$ref": "#/$defs/node_agent_extension" }
  ]
},
"partial_node": {
  "anyOf": [
    {
      "allOf": [
        { "$ref": "#/$defs/partial_regular_node" },
        { "not": { "anyOf": [
          { "required": ["agent_record_uri"] },
          { "required": ["stable_agent_id"] }
        ]}}
      ]
    },
    { "$ref": "#/$defs/partial_agent_node" }
  ]
},
"node": { /* same shape: regular branch + $ref agent_node */ },
"topology_node_item": {
  "anyOf": [{ "$ref": "#/$defs/partial_node" }, { "$ref": "#/$defs/node" }]
}
```

Step 1 — emit the four leaf classes. Names come straight from the `$defs` keys (no merged-class invention — see [`SKILL.md`](SKILL.md)). The agent variants subclass their regular counterparts because the extension is purely *additive* fields (no required-vs-optional drift, unlike §C):

```python
class PartialAgentNode(PartialRegularNode):
    agent_record_uri: Annotated[str, Field(min_length=1)]
    stable_agent_id: StableAgentId | None = None


class AgentNode(RegularNode):
    agent_record_uri: Annotated[str, Field(min_length=1)]
    stable_agent_id: StableAgentId
```

`partial_node_agent_extension` and `node_agent_extension` are **not** emitted as standalone classes: they are only ever referenced inside the `allOf`s that build `partial_agent_node` / `agent_node`, so their fields appear directly on the agent classes.

Step 2 — discriminator that mirrors **only** the sibling-key presence test that the regular branch's `not { anyOf: [...required...] }` clause is making:

```python
_REGULAR_TAG = "regular"
_AGENT_TAG = "agent"


def _node_kind_discriminator(value: Any) -> str | None:
    if isinstance(value, (AgentNode, PartialAgentNode)):
        return _AGENT_TAG
    if isinstance(value, (RegularNode, PartialRegularNode)):
        return _REGULAR_TAG
    if not isinstance(value, dict):
        return None
    if "agent_record_uri" in value or "stable_agent_id" in value:
        return _AGENT_TAG
    return _REGULAR_TAG
```

Step 3 — emit each `anyOf`-shaped `$def` as an `Annotated[Union[...], Discriminator(...)]`. Inside each tagged branch use a plain `Union[Full, Partial]` and let smart-union pick the right one based on field population:

```python
TopologyNodeItem = Annotated[
    Union[
        Annotated[Union[RegularNode, PartialRegularNode], Tag(_REGULAR_TAG)],
        Annotated[Union[AgentNode, PartialAgentNode], Tag(_AGENT_TAG)],
    ],
    Discriminator(_node_kind_discriminator),
]

PartialNode = Annotated[
    Union[
        Annotated[PartialRegularNode, Tag(_REGULAR_TAG)],
        Annotated[PartialAgentNode, Tag(_AGENT_TAG)],
    ],
    Discriminator(_node_kind_discriminator),
]

Node = Annotated[
    Union[
        Annotated[RegularNode, Tag(_REGULAR_TAG)],
        Annotated[AgentNode, Tag(_AGENT_TAG)],
    ],
    Discriminator(_node_kind_discriminator),
]
```

### Validation outcomes this produces

| Input | Routes to | Outcome |
|---|---|---|
| All regular fields, no extension keys | `RegularNode` | OK |
| Only `id`+`operation` | `PartialRegularNode` | OK |
| All fields + `agent_record_uri` + valid `stable_agent_id` | `AgentNode` | OK |
| `agent_record_uri` only (partial) | `PartialAgentNode` | OK |
| `stable_agent_id` only, no `agent_record_uri` | agent branch → `PartialAgentNode` | rejected: `agent_record_uri` is required |
| Bogus `stable_agent_id` prefix (e.g. `"blabla://..."`) with `agent_record_uri` | `AgentNode` | rejected: `String should match pattern '^agent://...'` |

The error messages come straight from each branch's own `Field` constraints — no custom "agent fields not allowed" message anywhere.

### Anti-pattern this replaces

The earlier (incorrect) approach was an `@model_validator(mode="after")` on `PartialRegularNode` / `RegularNode` that walked `__pydantic_extra__` and raised if `agent_record_uri` or `stable_agent_id` had leaked through `extra="allow"`. That approach:

- Required a parallel `_AGENT_EXTENSION_FIELDS` allow-list.
- Hid the schema's `pattern` / `min_length` errors behind a generic message.
- Coupled `RegularNode` to knowledge of its sibling extension class.

The discriminator solves all three problems at once: routing alone is sufficient because each variant's own field constraints handle the rest.
