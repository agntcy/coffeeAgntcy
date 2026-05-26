# AGNTCY Skills for CLI-Native Agents

A set of [Agent Skills](https://agentskills.io/home) that enable Agent Skill-capable CLI agents to discover, verify, and communicate with remote A2A agents using [AGNTCY](https://docs.agntcy.org) standards and components.

## Overview

Use these skills in your workflow to:

1. **Discover** remote agents through the [AGNTCY Directory Service](https://docs.agntcy.org/dir/overview/)
2. **Verify** their published OASF records with `dirctl`
3. **Inspect** identity badges and TBAC policies with the [AGNTCY Identity Service](https://docs.agntcy.org/identity/identity/)
4. **Connect** to recruited agents over [SLIM A2A](https://docs.agntcy.org/slim/overview/)

## Skills

| Skill | Description |
|-------|-------------|
| `/agntcy-dir-recruit` | Search the AGNTCY directory for remote agents, present candidates, and install them as local skills |
| `/agntcy-id-verification` | Inspect the identity-service badge and policies attached to a recruited agent |
| `/a2a-messaging` | Send a message directly to a known A2A agent endpoint via the bundled `a2a-send` CLI |

## Supported Agents

- `claude-code`
- `codex`
- `opencode`
- `copilot-cli`

## Prerequisites

- One of the supported CLI-native agents listed above
- [`dirctl`](https://github.com/agntcy/dir-ctl) — AGNTCY directory CLI
- [Go 1.25+](https://go.dev/dl/) — to build the `a2a-send` binary
- [`jq`](https://stedolan.github.io/jq/) — for directory record parsing
- `python3` (≥ 3.7, stdlib only) — used by `/agntcy-id-verification`

## Installation

Run the installer interactively:

```bash
make install
```

Or specify an agent directly:

```bash
make install AGENT=claude-code
```

The installer will:

1. Validate the target CLI-native agent name
2. Build `skills/a2a-messaging/scripts/a2a-send/a2a-send.bin`
3. Install bundled skills into the agent-specific skills directory
4. Write a project config to `.agntcy/cli-native-agents/config.env`

Default skill directories per agent:

| Agent | Skills directory |
|-------|-----------------|
| `claude-code` | `.claude/skills` |
| `codex` | `.agents/skills` |
| `opencode` | `.opencode/skills` |
| `copilot-cli` | Pass `--skill-root <path>` |

## Configuration

Environment variables are documented in [`.env.example`](./.env.example). Set only the ones you need:

| Variable | Required by | Purpose |
|----------|-------------|---------|
| `IDENTITY_API_SERVER_URL` | `/agntcy-id-verification` | Base URL of the AGNTCY identity service |
| `IDENTITY_SERVICE_API_KEY` | `/agntcy-id-verification` | API key sent as `x-id-api-key` header |
| `SLIM_SHARED_SECRET` | `/a2a-messaging` (SLIM targets only) | Shared secret matching the target agent |

## Tutorial

### Overview

This flow shows how to start the local AGNTCY demo stack, install the skills into your CLI agent, recruit a remote agent as a new skill, and exchange messages over A2A.

### Step 1 — Start local infrastructure

From `coffee_agents/lungo`, copy the example environment file, start the farm agents, then start only the directory services needed for recruitment.

Copy the example .env, be sure to fill in your LLM credentials according to Lungo README.
```bash
cp .env.example .env
```

Bring up infrastructure and agents.
```bash
docker compose up postgres zot dir-api-server otel-collector -d
docker compose --profile farms up -d
```

Publish OASF records for lungo agents.
```bash
./scripts/push_oasf_records.sh
```

### Step 2 — Install the AGNTCY skills into your CLI agent

From `coffee_agents/cli-native-agents`, install the bundled skills into the well-known location for your CLI agent.

```bash
make install AGENT=claude-code
```

Agent messaging uses SLIM by default, so export the shared secret from `coffee_agents/lungo/.env`:

```bash
export SLIM_SHARED_SECRET="slim-shared-secret-REPLACE_WITH_RANDOM_32PLUS_CHARS"
```

Use one of: `claude-code`, `codex`, `opencode`, or `copilot-cli`.

### Step 3 — Recruit a remote agent skill

Inside your agent session, run:

```text
/agntcy-dir-recruit Find an agent named Colombia Coffee Farm
```

> For `opencode`, run `/skills` first to confirm the installed skills are visible.

Follow the prompts from the recruiter skill. The result should be a newly generated local skill for the selected remote agent.

### Step 4 — Message the recruited agent

Once recruitment completes, invoke the generated skill directly. For example:

```text
/colombia-coffee-farm can you create an order for 100 lbs of coffee for $4 a pound?
```

The generated slash command name is based on the recruited agent slug.

### Step 5 — Verify identity (optional)

If `IDENTITY_API_SERVER_URL` and `IDENTITY_SERVICE_API_KEY` are set, inspect the recruited skill's badge and policy metadata:

```text
/check-identity <skill-name>
```