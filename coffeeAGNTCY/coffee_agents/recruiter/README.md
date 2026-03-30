# Agent Recruiter

Discover, evaluate, and dynamically recruit agents for on-demand task execution.

## Table of Contents

- [Overview](#overview)
- [Getting Started](#getting-started)
  - [Prerequisites](#prerequisites)
  - [Installation](#installation)
  - [LLM Configuration](#llm-configuration)
  - [Agent Directory Service](#agent-directory-service)
  - [A2A Server](#a2a-server)
- [Architecture](#architecture)
- [Deployment](#deployment)
  - [Docker Compose](#docker-compose-recommended)
  - [Service Endpoints](#service-endpoints)
- [Testing](#testing)
- [Claude Code Plugin](#claude-code-plugin)
  - [Plugin Installation](#plugin-installation)
  - [Plugin Commands](#plugin-commands)
  - [Skills vs Sub-Agents](#skills-vs-sub-agents)
  - [`a2a-send` CLI Tool](#a2a-send-cli-tool)
  - [Telemetry](#telemetry)

## Overview

Agent Recruiter is a multi-agent system that helps find, evaluate, and recruit agents from the [AGNTCY Directory Service](https://github.com/agntcy/dir) based on specified criteria:

1. **Request**: User asks the Recruiter to find agents based on skills, name, or semantic query
2. **Search**: Recruiter searches the directory for matching agents using MCP tools
3. **Evaluate**: Recruiter optionally evaluates candidates by connecting via A2A protocol and running user-provided evaluation scenarios
4. **Return**: Search results with agent records (A2A cards) and evaluation transcripts with pass/fail scores

Evaluation uses a two-level agentic architecture built on Google ADK: an outer orchestration agent discovers candidates and delegates to inner evaluator agents that conduct live conversations over A2A. A judge LLM scores each conversation for policy compliance. The system supports both single-turn fast evaluation and multi-turn deep testing, with real-time streaming of progress.

## Getting Started

### Prerequisites

- Python 3.12+
- [uv](https://docs.astral.sh/uv/) package manager
- Docker (for local services and deployment)
- Litellm compatible LLM provider

### Installation

```bash
# Clone the repository
git clone https://github.com/agntcy/coffee_agents.git
cd coffee_agents/recruiter

# Install dependencies
uv sync

# Install with dev dependencies
uv sync --extra dev

# Copy environment template and configure
cp .env.example .env
# Edit .env with your API keys
```

#### LLM Configuration

Agent Recruiter uses [LiteLLM](https://docs.litellm.ai/) to manage LLM connections. Configure your provider in `.env`:

```env
LLM_MODEL="openai/gpt-4o"
OPENAI_API_KEY=<your_api_key>
```

See [docs/llm_configuration.md](docs/llm_configuration.md) for more providers (Azure, GROQ, NVIDIA NIM, etc.).

### Agent Directory Service

The recruiter agent searches for agents in AGNTCY's [Directory Service (dir)](https://github.com/agntcy/dir) — a
decentralized platform for publishing, discovering, and exchanging agent information across a peer-to-peer network. It
enables agents to publish structured metadata describing their capabilities using OASF standards, with cryptographic
mechanisms for data integrity and provenance tracking. See the [dir
README](https://github.com/agntcy/dir/blob/main/README.md) for full documentation.

**Connect to an existing directory server:**

```bash
DIRECTORY_CLIENT_SERVER_ADDRESS="localhost:8888"
DIRECTORY_CLIENT_TLS_SKIP_VERIFY="true"
```

**Or run locally via docker-compose:**

```bash
# Start directory services (API server + Zot registry)
docker compose -f docker/docker-compose.yaml up -d dir-api-server zot
```

#### Tests

The Directory related tests need the Directory CLI.  
The integration tests automatically download a hardcoded version if they cannot find `dirctl` in `$PATH` or in the `recruiter/bin` folder.  
If you want to download it globally on your system, you can use Homebrew:

```bash
# MacOS
brew tap agntcy/dir https://github.com/agntcy/dir/ && brew install dirctl
```

### A2A Server

Run the agent as an A2A (Agent-to-Agent) protocol server for production use:

```bash
# Start the A2A server
uv run python src/agent_recruiter/server/server.py

# Server starts at http://localhost:8881
```

#### Verify the Server

```bash
# Check agent card
curl http://localhost:8881/.well-known/agent.json

# Expected response:
{
  "name": "RecruiterAgent",
  "url": "http://localhost:8881",
  "description": "An agent that helps find and recruit other agents based on specified criteria.",
  "version": "1.0.0",
  ...
}
```

## Architecture

<img src="./docs/architecture.svg" alt="Agent Recruiter Architecture Diagram" />

```
src/agent_recruiter/
├── recruiter/           # Main orchestrator (RecruiterTeam)
├── agent_registries/    # Registry search agent with MCP tools
├── interviewers/        # Main evaluation agent
├── plugins/             # ADK plugins (tool caching)
├── server/              # A2A server implementation
└── common/              # Logging and utilities
```

### Key Components

- **RecruiterTeam**: Main entry point, coordinates sub-agents using Google ADK
- **RegistrySearchAgent**: Searches AGNTCY Directory via MCP tools
- **EvaluationAgent**: Orchestrates LLM-driven agent evaluation against policy scenarios
- **A2A Server**: Exposes the agent via A2A protocol

## Deployment

### Docker Compose (Recommended)

Deploy the full stack including the recruiter agent:

```bash
# Build and start all services
cd docker
docker compose -f docker/docker-compose.yaml up --build

# Or run in background
docker compose -f docker/docker-compose.yaml up --build -d
```

This starts:
- **dir-api-server**: Agent Directory Service API
- **zot**: OCI artifact registry for agent storage
- **recruiter-agent**: The recruiter agent A2A server

#### Service Endpoints

| Service | Port | Description |
|---------|------|-------------|
| recruiter-agent | 8881 | A2A server endpoint |
| dir-api-server | 8888 | Directory gRPC API |
| zot | 5555 | OCI registry |

## Testing

Tests require the Directory services to be running. There are `pytest` fixtures that deal with setup and teardown automatically.

To manually start the required Directory services:

```bash
# Start directory services
docker compose -f docker/docker-compose.yaml up -d dir-api-server zot
```

### Run All Tests

```bash
uv run pytest
```

### Run Integration Tests

Integration tests require the Directory services and test against the A2A server:

```bash
# All integration tests
uv run pytest test/integration/ -v

# A2A server tests (search, streaming, evaluation)
uv run pytest test/integration/test_a2a.py -v

# Agent evaluator tests
uv run pytest test/integration/test_agent_evaluator.py -v
```

### Test Descriptions

| Test File | Description |
|-----------|-------------|
| `test_a2a.py` | A2A server integration tests (search, streaming, evaluation flow) |
| `test_agent_evaluator.py` | Agent evaluation scenario tests |

## Claude Code Plugin

The [`claude-code-recruiter/`](./claude-code-recruiter/) directory contains **agntcy-discover-connect** — a [Claude Code](https://docs.anthropic.com/en/docs/claude-code) plugin that brings the recruiter's agent discovery capabilities directly into the Claude Code CLI. Instead of running the recruiter as a standalone A2A service, this plugin lets you search the AGNTCY directory, preview candidates, and connect remote A2A agents as skills or sub-agents — all from within a Claude Code session.

### Plugin Installation

**Local development (from this repo):**

```bash
# Build the a2a-send CLI tool
cd claude-code-recruiter/plugin/scripts/a2a-send && go build -o a2a-send . && cd ../../..

# Launch Claude Code with the plugin
claude --plugin-dir ./claude-code-recruiter/plugin
```

**Prerequisites:** [Claude Code CLI](https://docs.anthropic.com/en/docs/claude-code), [`dirctl`](https://github.com/agntcy/dir-ctl), [Go 1.23+](https://go.dev/dl/) (to build `a2a-send`), and optionally [`jq`](https://stedolan.github.io/jq/) for telemetry hooks.

### Plugin Commands

| Command | Description |
|---------|-------------|
| **`/recruit <query>`** | Search the AGNTCY directory for agents matching your query, preview candidates in a summary table, and connect them as skills or sub-agents |
| **`/a2a-send <url> <message>`** | Send a message directly to any A2A agent endpoint for quick testing or one-off communication |

**Example usage:**

```
/recruit Can you find an agent named Brazil Coffee Farm?
/a2a-send http://localhost:9999 "What is the current coffee yield?"
```

**`/recruit` workflow:**
1. Searches the directory using multiple strategies (skill match, domain match, name wildcard, DHT routing)
2. Presents discovered agents in a summary table
3. User picks which agents to connect
4. User chooses creation mode: **skill** (recommended) or **sub-agent**

### Skills vs Sub-Agents

The plugin can connect remote agents in two modes:

| Mode | How it works | Invoke with | Pros |
|------|-------------|-------------|------|
| **Skill** (recommended) | Creates `.claude/skills/<name>/SKILL.md` — the parent model runs `a2a-send` directly | `/agent-name <message>` | Available immediately, no intermediary model to refuse requests |
| **Sub-agent** | Creates `.claude/agents/<name>.md` — Claude Code spawns a separate model | Natural language: "Use the agent to..." | More autonomous, but may refuse to forward out-of-scope requests |

> **Tip:** Start with skills. If a sub-agent refuses to forward requests the remote agent can handle, delete the sub-agent and re-run `/recruit` to create a skill instead.

> **Note:** If a newly created skill doesn't appear as a slash command, start a new Claude Code session (`/exit` or `Ctrl+C` twice, then relaunch `claude`) for it to be picked up.


**Managing recruited agents:**

```bash
# Remove a skill
rm -rf .claude/skills/brazil-coffee-farm/

# Remove a sub-agent
rm .claude/agents/brazil-coffee-farm.md
```

### `a2a-send` CLI Tool

The plugin bundles a standalone Go CLI built on the [a2a-go SDK](https://github.com/a2aproject/a2a-go) that handles A2A protocol details: agent card discovery, JSON-RPC transport, streaming (SSE), non-blocking polling, and multi-turn conversations.

| Mode | Flags | Description |
|------|-------|-------------|
| **Blocking** | _(default)_ | Send message, wait for response, print text |
| **Streaming** | `--stream` | SSE event stream with real-time status updates |
| **Non-blocking + poll** | `--non-blocking --wait` | Fire-and-forget, then poll until terminal state |
| **Multi-turn** | `--task-id <id> --context-id <id>` | Continue an existing conversation |

```bash
# Build
cd claude-code-recruiter/plugin/scripts/a2a-send && go build -o a2a-send .

# Simple blocking send
./a2a-send --peer-url http://localhost:9999 --message "What is your name?"

# Streaming mode
./a2a-send --peer-url http://localhost:9999 --stream --message "Tell me a story"

# Non-blocking with polling
./a2a-send --peer-url http://localhost:9999 --non-blocking --wait --message "Analyze this data"
```

### Telemetry

The plugin supports optional OpenTelemetry telemetry for monitoring A2A interactions:

```bash
export AGNTCY_OTEL_ENABLED=1
export AGNTCY_OTEL_ENDPOINT=http://localhost:4318
```

Events emitted: directory searches (`agntcy.dirctl.search`), A2A message sends (`agntcy.a2a.message_send`), agent card fetches (`agntcy.a2a.agent_card_fetch`), and sub-agent lifecycle (`agntcy.subagent.start` / `agntcy.subagent.stop`). Message content is not captured. See [`claude-code-recruiter/plugin/docs/telemetry.md`](./claude-code-recruiter/plugin/docs/telemetry.md) for the full event catalog and collector configuration.

### Plugin Structure

```
claude-code-recruiter/plugin/
├── .claude-plugin/
│   └── plugin.json              # Plugin manifest
├── commands/
│   ├── recruit.md               # /recruit slash command
│   └── a2a-send.md              # /a2a-send slash command
├── hooks/
│   └── hooks.json               # Hook configuration (telemetry)
├── scripts/
│   ├── a2a-send/                # Go CLI tool (a2a-go SDK)
│   │   ├── main.go
│   │   ├── go.mod
│   │   └── go.sum
│   ├── otel-emit.sh             # OTLP log emitter
│   ├── post-bash-tool.sh        # Bash tool call classifier
│   ├── subagent-start.sh        # Sub-agent start logger
│   └── subagent-stop.sh         # Sub-agent stop logger
├── skills/
│   └── a2a-protocol/            # A2A protocol knowledge skill
│       ├── SKILL.md
│       └── references/
│           ├── oasf-structure.md
│           ├── a2a-protocol-cheatsheet.md
│           ├── error-handling.md
│           └── dirctl-search.md
└── docs/
    └── telemetry.md             # Telemetry documentation
```
