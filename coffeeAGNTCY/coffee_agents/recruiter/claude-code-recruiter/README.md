# agntcy-discover-connect

A Claude Code plugin that discovers remote A2A (Agent-to-Agent) agents from the [AGNTCY](https://github.com/agntcy) directory and connects to them — enabling multi-agent workflows directly from Claude Code.

**What it does:**
- **`/recruit`** — Search the AGNTCY directory for agents, preview candidates, and connect them as **skills** (recommended) or **sub-agents**
- **`/a2a-send`** — Send a message directly to any A2A agent endpoint for quick testing or one-off communication
- **`a2a-send` CLI** — Go binary built on the [a2a-go SDK](https://github.com/a2aproject/a2a-go) that handles protocol details: agent card discovery, JSON-RPC, streaming (SSE), non-blocking polling, and multi-turn conversations
- **A2A Protocol skill** — Provides Claude with deep knowledge of the A2A protocol, OASF records, and dirctl CLI so it can help you debug and build integrations

## Prerequisites

- [Claude Code](https://docs.anthropic.com/en/docs/claude-code) CLI installed
- [`dirctl`](https://github.com/agntcy/dir-ctl) CLI installed and in PATH
- [Go 1.23+](https://go.dev/dl/) — to build the `a2a-send` CLI tool
- [`jq`](https://stedolan.github.io/jq/) — required for telemetry hooks (optional; plugin works without it)

## Installation

### From marketplace (recommended)

```bash
claude plugin marketplace add agntcy/claude-code-remote-agent-team
claude plugin install agntcy-discover-connect
```

### Local development

```bash
git clone https://github.com/agntcy/claude-code-remote-agent-team.git
cd claude-code-remote-agent-team

# Build the a2a-send CLI tool
cd plugin/scripts/a2a-send && go build -o a2a-send . && cd ../../..

claude --plugin-dir ./plugin
```

### Manual

Copy the `plugin/` directory into your project and point Claude Code at it:

```bash
cp -r plugin/ /path/to/your/project/.claude-plugins/agntcy-discover-connect/

# Build the a2a-send binary
cd /path/to/your/project/.claude-plugins/agntcy-discover-connect/scripts/a2a-send
go build -o a2a-send .
```

## Required Permissions

Add these to your project's `.claude/settings.local.json` to allow the plugin's commands to run without prompting:

```json
{
  "permissions": {
    "allow": [
      "Bash(dirctl *)",
      "Bash(plugin/scripts/a2a-send/a2a-send *)"
    ]
  }
}
```

## Configuration

### Directory Server Address

The `dirctl` CLI connects to a directory server. By default it uses `0.0.0.0:8888`. To point it to a different server, set the environment variable before starting Claude Code:

```bash
export DIRECTORY_CLIENT_SERVER_ADDRESS=your-directory-host:9999
claude --plugin-dir ./plugin
```

## Usage: `/recruit`

Discover agents from the AGNTCY directory and connect them to Claude Code.

```
/recruit I need an agent that can tell me coffee farm yields
/recruit Find me an agent for code review
/recruit I need a summarization agent for long documents
```

**Workflow:**
1. `/recruit <query>` — searches the directory using multiple strategies (skill match, domain match, name wildcard, DHT routing)
2. Review discovered agents in a summary table
3. Pick which agents to connect
4. Choose creation mode: **skill** (recommended) or **sub-agent**

### Skills (Recommended)

Skills create a `/slash-command` that the parent model executes directly. This is the most reliable mode because the parent model runs the `a2a-send` command itself — no intermediary model to refuse.

```
/brazil-coffee-farm What is the current yield?
/brazil-coffee-farm Order 100lbs of coffee for $4 a pound
```

Skills are available immediately after creation — no restart needed.

### Sub-Agents

Sub-agents create a `.claude/agents/<name>.md` file. Claude Code spawns a separate model to handle requests. Invoke them naturally:

```
Use the coffee-farm agent to check the current yield
Ask the weather-bot for tomorrow's forecast in São Paulo
```

> **Note:** Sub-agent models may refuse to forward requests they deem outside the agent's advertised capabilities, even when the remote agent can handle them. If this happens, delete the sub-agent and re-run `/recruit` to create a skill instead.

## Usage: `/a2a-send`

Send a message directly to a known A2A endpoint — useful for testing or one-off requests.

```
/a2a-send http://localhost:9999 "What is the coffee yield?"
/a2a-send https://agent.example.com "Translate 'hello' to French"
```

The command uses the `a2a-send` Go binary under the hood, which handles agent card discovery, protocol negotiation, retries, and response parsing automatically.

## `a2a-send` CLI Tool

A standalone Go CLI built on the official [a2a-go SDK](https://github.com/a2aproject/a2a-go) (`github.com/a2aproject/a2a-go/v2`). Inspired by [openclaw-a2a-gateway](https://github.com/win4r/openclaw-a2a-gateway)'s `a2a-send.mjs` but written in Go.

### Build

```bash
cd plugin/scripts/a2a-send
go build -o a2a-send .
```

### Features

| Mode | Flags | Description |
|------|-------|-------------|
| **Blocking** | _(default)_ | Send message, wait for response, print text |
| **Streaming** | `--stream` | SSE event stream with real-time status updates |
| **Non-blocking + poll** | `--non-blocking --wait` | Fire-and-forget, then poll until terminal state |
| **Multi-turn** | `--task-id <id> --context-id <id>` | Continue an existing conversation |

### Examples

```bash
# Simple blocking send
./a2a-send --peer-url http://localhost:9999 --message "What is your name?"

# Streaming mode (real-time task lifecycle events)
./a2a-send --peer-url http://localhost:9999 --stream --message "Tell me a story"

# Non-blocking with polling (for long-running tasks)
./a2a-send --peer-url http://localhost:9999 --non-blocking --wait --timeout-ms 600000 --message "Analyze this data"

# Multi-turn conversation
./a2a-send --peer-url http://localhost:9999 --message "Follow up" --task-id abc123 --context-id ctx456
```

### Output

- **stdout** — agent's response text (or JSON for non-text parts)
- **stderr** — debug messages (with `--verbose`), `[task]`/`[stream]` status, and errors (`{"error": "..."}`)
- **Exit 0** — success
- **Exit 1** — error (JSON error object on stderr)

### How it works

1. Discovers the agent card at `<peer-url>/.well-known/agent-card.json`
2. Negotiates transport (JSON-RPC preferred, REST fallback) via the a2a-go SDK
3. Sends the message using the A2A protocol
4. Extracts and prints the response text

If agent card discovery fails, it falls back to direct JSON-RPC at the provided URL.

## Using Recruited Agents

### Skills (Recommended)

When `/recruit` creates a skill, it writes a `SKILL.md` file to `.claude/skills/<name>/`. Claude Code automatically discovers these and makes them available as slash commands. Here's an example of what a generated skill looks like:

```markdown
---
name: brazil-coffee-farm
description: "Send a message to the remote Brazil Coffee Farm agent via A2A protocol. Use for ANY request intended for this agent — the remote agent determines what it can handle."
allowed-tools: Bash
---

## EXECUTE NOW

Run this command to send the user's message to the remote A2A agent:

\`\`\`bash
plugin/scripts/a2a-send/a2a-send --peer-url http://0.0.0.0:9999 --message "$ARGUMENTS"
\`\`\`

- stdout contains the agent's response
- If exit code 1, stderr contains a JSON error — relay the error to the user
- For long-running tasks, add --non-blocking --wait flags
```

Invoke with: `/brazil-coffee-farm What is the current yield?`

To remove a recruited skill, delete its directory:

```bash
rm -rf .claude/skills/brazil-coffee-farm/
```

### Sub-Agents

When `/recruit` creates a sub-agent, it writes a file to `.claude/agents/<name>.md`. Claude Code spawns a separate model to handle requests.

> **Note:** Subagents are loaded at session start. After `/recruit` creates a new agent, type `/exit` (or press `Ctrl+C` twice) and relaunch `claude` to use it.

> **Note:** Sub-agent models may refuse to forward requests they consider outside the agent's advertised capabilities. If this happens, delete the sub-agent and re-run `/recruit` to create a skill instead.

To remove a recruited sub-agent, delete its file:

```bash
rm .claude/agents/brazil-coffee-farm.md
```

## Plugin Structure

```
plugin/
├── .claude-plugin/
│   └── plugin.json              # Plugin manifest (name, version, metadata)
├── commands/
│   ├── a2a-send.md              # /a2a-send slash command
│   └── recruit.md               # /recruit slash command
├── hooks/
│   └── hooks.json               # Hook configuration (telemetry)
├── scripts/
│   ├── a2a-send/                # Go CLI tool (a2a-go SDK)
│   │   ├── main.go              # CLI entrypoint
│   │   ├── go.mod               # Go module definition
│   │   └── go.sum               # Dependency checksums
│   ├── otel-emit.sh             # Shared OTLP log emitter
│   ├── post-bash-tool.sh        # Bash tool call classifier
│   ├── subagent-start.sh        # Sub-agent start logger
│   └── subagent-stop.sh         # Sub-agent stop logger
├── skills/
│   └── a2a-protocol/            # A2A protocol knowledge skill
│       ├── SKILL.md             # Skill overview and quick reference
│       └── references/
│           ├── oasf-structure.md           # OASF record format
│           ├── a2a-protocol-cheatsheet.md  # Protocol versions, CLI + curl templates
│           ├── error-handling.md           # Timeouts, retries, error format
│           └── dirctl-search.md            # Directory search patterns
└── docs/
    └── telemetry.md             # Telemetry documentation
```

## Troubleshooting

### `dirctl: command not found`
Install `dirctl` from [github.com/agntcy/dir-ctl](https://github.com/agntcy/dir-ctl) and ensure it's in your PATH.

### `a2a-send: command not found` or binary missing
Build the CLI tool:
```bash
cd plugin/scripts/a2a-send && go build -o a2a-send .
```
Requires Go 1.23+.

### No agents found
- Try broader search terms: `/recruit Find me any available agent`
- Verify directory connectivity: `dirctl info`
- Check if agents are registered in the directory

### Connection refused / timeout
- Verify the agent is running and accessible at the endpoint URL
- Test manually: `plugin/scripts/a2a-send/a2a-send --peer-url <endpoint> --message "ping"`
- For long-running tasks, use `--non-blocking --wait` to avoid timeouts
- Check firewall/network settings

### Protocol mismatch
The `a2a-send` tool uses the a2a-go SDK which supports A2A protocol v1.0 and can negotiate compatible transports automatically. For older agents (v0.3.0+), the tool falls back to JSON-RPC. Check the agent card:
```bash
curl -s <endpoint>/.well-known/agent-card.json | jq .protocolVersion
```

### Commands not loading
- Verify the plugin is installed: `claude plugin list`
- For local development, ensure you're using `claude --plugin-dir ./plugin`

### Subagent not found after /recruit
Subagents are loaded at session start. Type `/exit` (or press `Ctrl+C` twice) and relaunch `claude` after creating agents with `/recruit`. Alternatively, use skill mode — skills are available immediately.

### Subagent refuses to forward requests
Sub-agent models may refuse to forward requests they deem outside the agent's capabilities. This is a known limitation of the sub-agent architecture. Fix: delete the sub-agent file and re-run `/recruit` choosing **skill** mode instead.

## Telemetry

The plugin supports optional OpenTelemetry telemetry for monitoring A2A interactions. Enable with:

```bash
export AGNTCY_OTEL_ENABLED=1
export AGNTCY_OTEL_ENDPOINT=http://localhost:4318
```

Events emitted include directory searches (`agntcy.dirctl.search`), A2A message sends (`agntcy.a2a.message_send`) — both via the Go binary and legacy curl — agent card fetches (`agntcy.a2a.agent_card_fetch`), and sub-agent lifecycle (`agntcy.subagent.start` / `agntcy.subagent.stop`).

See [plugin/docs/telemetry.md](plugin/docs/telemetry.md) for the full event catalog, combined setup with Claude Code's built-in OTel, and example collector configurations.

## Roadmap

- **Rich output modes** — handle non-text parts (FilePart, DataPart) in responses
- **Conversation persistence** — save task/context IDs across sessions for long-running conversations
- **OAuth2 authentication** — support A2A's OAuth2 auth flow for secured agents
- **Agent card caching** — cache discovered cards to avoid repeated fetches
- **gRPC transport** — add gRPC support via the a2a-go SDK's gRPC transport factory

## License

[MIT](LICENSE)
