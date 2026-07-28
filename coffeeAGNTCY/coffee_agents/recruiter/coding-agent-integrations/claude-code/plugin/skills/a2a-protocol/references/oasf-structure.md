# OASF Record Structure

OASF (Open Agent Standard Format) records describe agents in the AGNTCY directory.

**Key path to the A2A Agent Card:**
```
record.modules[] -> find where name == "integration/a2a" -> .data.card_data
```

## Top-level Record Fields

- `name` - agent name
- `description` - what the agent does
- `version` - semver version string
- `skills` - array of `{ id, name }` from OASF taxonomy
- `domains` - array of `{ id, name }` from OASF taxonomy
- `modules` - array of module objects, each with `{ name, data }` and module-specific fields
- `locators` - deployment info (docker images, URLs, etc.)

## A2A Agent Card Fields

Found inside `modules[name="integration/a2a"].data.card_data`:

- `name` - agent display name
- `description` - agent description
- `url` - primary endpoint URL (may be a non-HTTP transport like `slim://`)
- `skills` - array of `{ id, name, description, examples, tags }`
- `capabilities` - `{ streaming, pushNotifications, stateTransitionHistory }`
- `defaultInputModes` - e.g. `["text"]`
- `defaultOutputModes` - e.g. `["text"]`
- `provider` - `{ organization, url }`
- `version` - agent card version (e.g. "1.0.0")
- `protocolVersion` - A2A protocol version (e.g. "0.3.0") - **critical for choosing methods**
- `additionalInterfaces` - array of `{ transport, url }` - look for `transport: "jsonrpc"` to find the HTTP endpoint
- `preferredTransport` - which transport the agent prefers

## Finding the HTTP Endpoint (Important!)

The `url` field may point to a non-HTTP transport (e.g. `slim://...`). Always check:
1. `additionalInterfaces[]` - find the entry where `transport == "jsonrpc"` and use its `url`
2. If no `additionalInterfaces`, use the top-level `url` if it starts with `http`
3. For cards fetched from `.well-known/agent.json`, the HTTP URL is the host you fetched from
