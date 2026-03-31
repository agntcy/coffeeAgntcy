---
name: a2a-protocol
description: Use this skill when the user asks about A2A (Agent-to-Agent) protocol communication, OASF record formats, AGNTCY directory operations, agent card parsing, or dirctl CLI usage. It provides comprehensive reference material for A2A integrations.
---

# A2A Protocol Skill

This skill provides knowledge about the **A2A (Agent-to-Agent) protocol**, the **AGNTCY directory**, and the **OASF (Open Agent Standard Format)** — everything needed to discover, connect to, and communicate with remote agents.

## Recruited Agents

The `/recruit` command discovers agents from the AGNTCY directory and connects them to Claude Code. Two creation modes are available:

### Skills (Recommended)

Skills create a `/slash-command` that the parent model executes directly. This is the most reliable way to proxy requests because the parent model runs the `a2a-send` command itself — no intermediary model to refuse.

**Workflow:**
1. `/recruit <query>` — discover agents, pick which to create, choose "skill" mode
2. Invoke with: `/<agent-name> <message>` — e.g., `/brazil-coffee-farm What is the current yield?`
3. Delete by removing the directory: `rm -rf .claude/skills/<agent-name>/`

Skills are available immediately after creation — no restart needed.

### Sub-Agents

Sub-agents create a `.claude/agents/<name>.md` file. Claude Code spawns a separate model to handle requests. This is useful when you want the sub-agent to have its own model (haiku/sonnet/opus) and reasoning, but note that sub-agent models may refuse to forward requests they deem outside the agent's advertised capabilities.

**Workflow:**
1. `/recruit <query>` — discover agents, pick which to create, choose "subagent" mode
2. Use them: "use the coffee-farm agent to check the yield" → Claude Code dispatches the sub-agent automatically
3. Delete by removing the file: `rm .claude/agents/coffee-farm.md`

Sub-agents require a restart to load — run `/exit` and relaunch `claude`.

## Core Concepts

### A2A Protocol
A2A (Agent-to-Agent) is a JSON-RPC 2.0 protocol for inter-agent communication over HTTP. This plugin uses **v0.3.0+** (`message/send` method). Always check the `protocolVersion` in an agent's card to confirm compatibility.

### OASF (Open Agent Standard Format)
OASF records are the standard format for describing agents in the AGNTCY directory. Each record contains metadata (name, description, skills, domains) and modules — including the `integration/a2a` module that holds the Agent Card.

### AGNTCY Directory
A directory where agents register their OASF records. The `dirctl` CLI is the primary interface:
- `dirctl search` — find agents by skill, name, domain, or module → returns CIDs
- `dirctl pull <CID>` — fetch the full OASF record for a CID

The directory server address is configured via `DIRECTORY_CLIENT_SERVER_ADDRESS` (default `0.0.0.0:8888`).

### Agent Card
The A2A Agent Card (found inside the `integration/a2a` module of an OASF record) describes an agent's communication interface: endpoint URL, supported protocol version, skills, capabilities, and transport options. It can also be fetched directly at `<endpoint>/.well-known/agent.json`.

## Protocol

A2A uses **JSON-RPC 2.0** over HTTP POST with the `message/send` method (v0.3.0+). Key format details:

- Messages require a `messageId` field (UUID)
- Parts use `"kind": "text"`
- Multi-turn uses `contextId` in configuration
- Response: `result.kind: "message"` with `result.parts[]`

### Version Detection
```bash
curl -s <ENDPOINT_URL>/.well-known/agent.json
```
Check `protocolVersion` — must be `"0.3.0"` or higher.

## Reference Files

For detailed information, see these reference files in the `references/` directory:

| File | Contents |
|------|----------|
| `oasf-structure.md` | OASF record fields, Agent Card fields, HTTP endpoint resolution |
| `a2a-protocol-cheatsheet.md` | Protocol version detection, method tables, curl templates, response formats |
| `error-handling.md` | Timeouts, retry policy, structured error format |
| `dirctl-search.md` | dirctl search and pull command examples |
