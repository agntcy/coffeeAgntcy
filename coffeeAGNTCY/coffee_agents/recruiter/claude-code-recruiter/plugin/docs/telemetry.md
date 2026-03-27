# Telemetry

The agntcy-discover-connect plugin supports optional [OpenTelemetry](https://opentelemetry.io/) telemetry for monitoring A2A interactions. When enabled, the plugin emits structured events for agent discovery, A2A messaging, and sub-agent lifecycle — giving you semantic observability beyond Claude Code's built-in generic telemetry.

## Prerequisites

- **OTel collector running** — e.g., [Jaeger](https://www.jaegertracing.io/), [Grafana Alloy](https://grafana.com/oss/alloy/), or any OTLP-compatible collector accepting HTTP on port 4318
- **`jq`** installed and in PATH ([stedolan.github.io/jq](https://stedolan.github.io/jq/))
- **`curl`** available (standard on macOS/Linux)

If `jq` is not installed, telemetry hooks exit silently with no errors — the plugin continues to work normally.

## Quick Start

Set these environment variables before launching Claude Code:

```bash
# Enable plugin telemetry
export AGNTCY_OTEL_ENABLED=1

# OTLP HTTP endpoint (default: http://localhost:4318)
export AGNTCY_OTEL_ENDPOINT=http://localhost:4318

# Start Claude Code with the plugin
claude --plugin-dir ./plugin
```

That's it. The plugin will emit structured events to your collector for every A2A-related operation.

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `AGNTCY_OTEL_ENABLED` | Yes (gate) | *(off)* | Set to `1` to enable telemetry |
| `AGNTCY_OTEL_ENDPOINT` | No | `http://localhost:4318` | OTLP HTTP collector endpoint |
| `AGNTCY_OTEL_HEADERS` | No | *(empty)* | Auth headers in `key=value,key=value` format |

## Combined Setup with Claude Code Built-in OTel

Claude Code has its own built-in OpenTelemetry support that captures generic tool calls, API costs, and token usage. For comprehensive observability, enable **both**:

```bash
# --- Plugin's A2A-specific events ---
export AGNTCY_OTEL_ENABLED=1
export AGNTCY_OTEL_ENDPOINT=http://localhost:4318

# --- Claude Code's generic tool/API/cost telemetry ---
export CLAUDE_CODE_ENABLE_TELEMETRY=1
export OTEL_LOGS_EXPORTER=otlp
export OTEL_METRICS_EXPORTER=otlp
export OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4317
export OTEL_LOG_TOOL_DETAILS=1
```

Both systems use `session.id` for correlation. In your collector backend, you can join plugin events (e.g., `agntcy.a2a.message_send`) with Claude Code events (e.g., tool call duration, token costs) to get the full picture.

## Event Catalog

### Directory Operations

#### `agntcy.dirctl.search`

Emitted when a `dirctl search` command completes.

| Attribute | Type | Description |
|-----------|------|-------------|
| `dirctl.search.strategy` | string | Search strategy used: `skill_match`, `domain`, `name_wildcard`, `module_search`, or `unknown` |
| `dirctl.search.has_results` | string | `"true"` if results were returned |
| `dirctl.search.result_count` | int | Number of results returned |
| `dirctl.command` | string | Full dirctl command executed |

#### `agntcy.dirctl.routing_search`

Emitted when a `dirctl routing search` (DHT network search) completes.

| Attribute | Type | Description |
|-----------|------|-------------|
| `dirctl.routing.command` | string | Full dirctl routing command executed |

#### `agntcy.dirctl.pull`

Emitted when a `dirctl pull` (CID record fetch) completes.

| Attribute | Type | Description |
|-----------|------|-------------|
| `dirctl.pull.cid` | string | The CID that was fetched |
| `dirctl.command` | string | Full dirctl command executed |

### A2A Protocol Operations

#### `agntcy.a2a.message_send`

Emitted when a `curl` command targeting `message/send` (A2A JSON-RPC) completes.

| Attribute | Type | Description |
|-----------|------|-------------|
| `a2a.endpoint` | string | Target agent endpoint URL |
| `a2a.method` | string | Always `message/send` |
| `a2a.response.status` | string | `message`, `task`, `error`, or `unknown` |
| `a2a.error.code` | string | JSON-RPC error code (if error) |

#### `agntcy.a2a.agent_card_fetch`

Emitted when a `curl` command fetching `.well-known/agent` completes.

| Attribute | Type | Description |
|-----------|------|-------------|
| `a2a.agent_card.endpoint` | string | URL of the agent card fetch |
| `a2a.agent_card.fetch_success` | string | `"true"` if the card was parsed successfully |
| `a2a.agent_card.agent_name` | string | Agent name from the card (if fetch succeeded) |

### Sub-Agent Lifecycle

#### `agntcy.subagent.start`

Emitted when an A2A-recruited sub-agent is spawned.

| Attribute | Type | Description |
|-----------|------|-------------|
| `subagent.id` | string | Sub-agent instance ID |
| `subagent.type` | string | Sub-agent type (matches the `.md` filename) |
| `subagent.endpoint` | string | A2A endpoint URL (extracted from agent file) |

#### `agntcy.subagent.stop`

Emitted when an A2A-recruited sub-agent finishes.

| Attribute | Type | Description |
|-----------|------|-------------|
| `subagent.id` | string | Sub-agent instance ID |
| `subagent.type` | string | Sub-agent type |
| `subagent.last_message_preview` | string | Last assistant message (truncated to 500 chars) |

### Standard Attributes (on all events)

| Attribute | Value |
|-----------|-------|
| `event.name` | The event name (e.g., `agntcy.a2a.message_send`) |
| `plugin.name` | `agntcy-discover-connect` |
| `plugin.version` | `1.0.0` |
| `session.id` | Claude Code session ID |
| `service.name` (resource) | `agntcy-discover-connect` |

## How to Disable

Remove or unset the environment variable:

```bash
unset AGNTCY_OTEL_ENABLED
```

When `AGNTCY_OTEL_ENABLED` is not set to `1`, all hook scripts exit immediately with zero overhead. No network calls are made, no data is collected.

## Example: What a `/recruit` Flow Looks Like

When you run `/recruit I need a coffee farm agent`, the following events appear in your collector:

```
1. agntcy.dirctl.search
   strategy=skill_match, has_results=false, result_count=0

2. agntcy.dirctl.search
   strategy=name_wildcard, has_results=true, result_count=2

3. agntcy.a2a.agent_card_fetch
   endpoint=http://0.0.0.0:9999/.well-known/agent.json
   fetch_success=true, agent_name=CoffeeFarmAgent
```

This tells you: the skill-based search found nothing, but a name wildcard search found 2 agents, and the plugin successfully fetched the agent card for the selected one.

## Example: What a Sub-Agent Invocation Looks Like

When you ask Claude to "use the coffee-farm agent to check yields":

```
1. agntcy.subagent.start
   subagent.type=coffee-farm
   subagent.endpoint=http://0.0.0.0:9999

2. agntcy.a2a.message_send
   endpoint=http://0.0.0.0:9999
   method=message/send
   response.status=message

3. agntcy.subagent.stop
   subagent.type=coffee-farm
   subagent.last_message_preview="The current yield is 1,250 lbs..."
```

This tells you: the sub-agent was spawned, sent one A2A message that got a direct response, and then completed.

## Example: Quick Jaeger Setup

To test telemetry locally with [Jaeger](https://www.jaegertracing.io/):

```bash
# Start Jaeger all-in-one (accepts OTLP on 4317/gRPC and 4318/HTTP)
docker run -d --name jaeger \
  -p 4317:4317 \
  -p 4318:4318 \
  -p 16686:16686 \
  jaegertracing/jaeger:2

# Enable telemetry
export AGNTCY_OTEL_ENABLED=1
export AGNTCY_OTEL_ENDPOINT=http://localhost:4318

# Launch Claude Code
claude --plugin-dir ./plugin

# Use /recruit or /a2a-send, then check:
# http://localhost:16686 → Service: agntcy-discover-connect
```

## Security Considerations

- **No message content** — Only endpoint URLs, agent names, status codes, and operation metadata are sent. Message bodies and user content are never included in telemetry.
- **Response truncation** — `last_message_preview` is capped at 500 characters.
- **Opt-in only** — Zero telemetry data is collected or transmitted unless you explicitly set `AGNTCY_OTEL_ENABLED=1`.
- **Fire-and-forget** — If the collector is down or unreachable, hooks silently fail. User experience is completely unaffected.
- **Async hooks** — All telemetry hooks run asynchronously and never block Claude Code's workflow.
- **Local by default** — The default endpoint (`localhost:4318`) means data stays on your machine unless you configure an external collector.

## Architecture

```
Claude Code (PostToolUse / SubagentStart / SubagentStop)
    │
    ├──stdin──▶ post-bash-tool.sh   ──classifies──▶ otel-emit.sh ──curl──▶ OTLP Collector
    ├──stdin──▶ subagent-start.sh   ──filters────▶ otel-emit.sh ──curl──▶ OTLP Collector
    └──stdin──▶ subagent-stop.sh    ──filters────▶ otel-emit.sh ──curl──▶ OTLP Collector
```

All hooks are async with a 5-second timeout. The shared `otel-emit.sh` utility builds OTLP LogRecords and POSTs them with a 3-second `curl` timeout.
