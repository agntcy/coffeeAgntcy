# Skills-Driven Recruiter for Claude Code

**agntcy-discover-connect** is a [Claude Code](https://docs.anthropic.com/en/docs/claude-code) plugin for **discovering, verifying, and recruiting remote agents as reusable skills**.

It is built around a simple idea:

1. **Discover** remote agents through the **AGNTCY Directory Service**
2. **Verify** their published OASF records locally with `dirctl` and inspect identity and policies with the **AGNTCY Identity Service**
3. **Connect** to recruited agents over **HTTP or SLIM**
4. **Generate slash-command interaction skills automatically** so the recruited agent becomes part of your Claude Code workflow

## What this plugin emphasizes

- **Skills-driven interaction** — remote agents are turned into Claude Code slash-command skills under `.claude/skills/<name>/`
- **Verification before trust** — candidate records are checked locally with `dirctl` (Sigstore-based verification)
- **Identity-aware recruitment** — recruited agents can be inspected against the AGNTCY identity service for badges and policy metadata
- **Transport flexibility** — communicate with remote agents over standard HTTP JSON-RPC or **SLIM** when advertised by the agent card
- **Automatic skill generation** — recruiting an agent creates a ready-to-use interaction skill from the plugin template

## Core capabilities

- Search the AGNTCY directory for remote A2A agents
- Verify OASF record signatures locally with `dirctl` (Sigstore)
- Preview candidates before connecting them
- Generate slash-command skills automatically under `.claude/skills/<name>/`
- Send messages directly to any A2A endpoint over HTTP or SLIM transport
- Inspect identity-service badges and policies attached to recruited agents

**Prerequisites:** [Claude Code CLI](https://docs.anthropic.com/en/docs/claude-code), [`dirctl`](https://github.com/agntcy/dir-ctl), [Go 1.25+](https://go.dev/dl/) (to build `a2a-send`; required by `slim-a2a-go`), [`jq`](https://stedolan.github.io/jq/) for record parsing, and `python3` (≥3.7, stdlib only — used by `/check-identity`).

**Environment variables:** Different commands and options read different variables from the shell — set only the ones you need. All are documented in [`.env.example`](./.env.example):

| Variable | Required by | Purpose | Example |
|---|---|---|---|
| `IDENTITY_API_SERVER_URL` | `/check-identity` only | Base URL of the AGNTCY identity service | `https://api.agent-identity.outshift.com` (hosted) or `http://0.0.0.0:4000` (local) |
| `IDENTITY_SERVICE_API_KEY` | `/check-identity` only | Sent as the `x-id-api-key` header on every identity-service call | (your AGNTCY identity-service API key) |
| `SLIM_SHARED_SECRET` | `/a2a-send` and recruited skills, **only when the target agent advertises a `slim`/`slimrpc` interface** | Must match the secret the target agent was started with. Without it, the SLIM handshake fails with `Code=15, Session handshake failed: failed to add participant to session`. For the `coffee_agents/lungo` stack, copy the value from `coffee_agents/lungo/.env`. HTTP-only agents don't need this. | `slim-shared-secret-…` |

`/recruit` does not require any of these — you can discover and connect agents without identity-service credentials or a SLIM secret. Export the ones you need in the shell that runs `claude`, or load them from your `.env` before launch (e.g. `set -a; source .env; set +a`). The plugin commands read whatever is in the environment — they do not search for or auto-load any `.env` file. If a required variable is unset for the command you're running, that command exits with an error indicating which variable to set; other commands continue to work.

## How recruitment works

The recruiter is intentionally **skills-first**:

1. Search for a remote agent in the AGNTCY directory
2. Verify the candidate's OASF record locally with `dirctl`
3. Review the candidate summary in Claude Code
4. Select one or more agents to recruit
5. Generate a dedicated slash-command skill for each selected agent
6. Optionally inspect identity badges and policy attachments with `/agntcy-discover-connect:check-identity`
7. Interact with the recruited agent directly from Claude Code, using the generated skill

This means the output of recruitment is not just a one-off connection — it is a **persistent interaction surface** embedded in your local Claude Code environment.

## Plugin Installation

**Local development (from `recruiter/cli-agent-integrations/claude-code/`):**

```bash
cd cli-agent-integrations/claude-code

# Build the a2a-send CLI tool (binary is wrapped by the tracked `a2a-send` shell script)
pushd plugin/scripts/a2a-send && go build -o a2a-send.bin . && popd

# Launch Claude Code with the plugin
claude --plugin-dir ./plugin
```

## Plugin Commands

All commands live under the `agntcy-discover-connect` plugin namespace.

### `/agntcy-discover-connect:recruit <query>`

Search the AGNTCY directory for agents matching your query, verify each record's Sigstore signature with `dirctl`, preview candidates in a summary table, and connect selected agents as slash-command **skills** under `.claude/skills/<name>/`.

This is the main entry point for **skills-driven remote agent recruitment**.

### `/agntcy-discover-connect:a2a-send <url> <message>`

Send a message directly to any A2A agent endpoint for quick testing or one-off communication.

The underlying `a2a-send` CLI supports **both HTTP JSON-RPC and SLIM transports** (the latter via [`slim-a2a-go`](https://github.com/agntcy/slim-a2a-go)). By default `--transport auto` fetches the agent card and routes over SLIM if the card advertises a `slim`/`slimrpc` interface, otherwise falls back to HTTP. The A2A protocol version (`v0` for agents on `agntcy-app-sdk` 0.3.x, `v1` otherwise) is auto-detected from the card's `protocolVersion`.

Relevant flags:

| Flag | Default | Purpose |
|---|---|---|
| `--transport` | `auto` | `auto`, `http`, or `slim` |
| `--slim-endpoint` | `http://127.0.0.1:46357` | SLIM node address |
| `--slim-remote-name` | (from card) | 3-segment `org/ns/name`; derived from `slim://host/org/ns/name` in the agent card if omitted |
| `--slim-local-name` | `lungo/agents/a2a-send-cli` | Local identity |
| `--slim-secret` | `$SLIM_SHARED_SECRET` | Shared-secret identity (dev only — `NewInsecureClientConfig`) |
| `--a2a-version` | (from card) | `v0` or `v1` override |

### `/agntcy-discover-connect:check-identity <name>`

Inspect the AGNTCY identity-service badge and policies attached to a recruited skill. Read-only; does not modify the skill. Requires `IDENTITY_API_SERVER_URL` and `IDENTITY_SERVICE_API_KEY` to be exported — see [Environment variables](#environment-variables) above.

**Example usage:**

```
/agntcy-discover-connect:recruit Can you find an agent named Colombia Coffee Farm?
/agntcy-discover-connect:check-identity colombia-coffee-farm
```

**`/agntcy-discover-connect:recruit` workflow:**
1. Searches the directory using multiple strategies (skill match, domain match, name wildcard, DHT routing).
2. Pulls each matching OASF record and runs `dirctl verify` locally (Sigstore-based) — each candidate is marked `signed ✓` or `unsigned ✗` in the summary table.
3. Presents the candidates with name, description, skills, endpoint, verification status, and whether a skill already exists.
4. User picks which agents to connect (numeric, ranges, or `all`); selecting unsigned candidates triggers a confirmation prompt.
5. Creates one slash-command skill per selection at `.claude/skills/<name>/SKILL.md`. Skills are available immediately — no restart needed.

> **Note:** A `signed ✓` Sigstore signature confirms the OASF record itself is signed. It does **not** confirm the agent has a valid identity-service badge or any policies. Run `/agntcy-discover-connect:check-identity <name>` after recruiting to inspect the badge and policies.

> **Note:** If a newly created skill doesn't appear as a slash command, start a new Claude Code session (`/exit` or `Ctrl+C` twice, then relaunch `claude`) for it to be picked up.

**Managing recruited skills:**

```bash
# Remove a recruited skill
rm -rf .claude/skills/brazil-coffee-farm/
```

## Plugin Structure

```
plugin/
├── .claude-plugin/
│   └── plugin.json              # Plugin manifest
├── commands/
│   ├── recruit.md               # /agntcy-discover-connect:recruit
│   ├── a2a-send.md              # /agntcy-discover-connect:a2a-send
│   └── check-identity.md        # /agntcy-discover-connect:check-identity
├── scripts/
│   ├── a2a-send/                # Go CLI tool (a2a-go SDK + slim-a2a-go for SLIM transport)
│   │   ├── a2a-send              # wrapper script (sets GOLANG_PROTOBUF_REGISTRATION_CONFLICT=warn, execs the binary)
│   │   ├── a2a-send.bin          # compiled binary (gitignored; built via `go build -o a2a-send.bin .`)
│   │   ├── main.go
│   │   ├── go.mod
│   │   └── go.sum
│   ├── identity_client.py       # stdlib client for the AGNTCY identity service
│   └── skill-template.md        # template used to generate one interaction skill per recruited agent
└── skills/
    └── a2a-protocol/            # A2A protocol knowledge skill
        ├── SKILL.md
        └── references/
            ├── oasf-structure.md
            ├── a2a-protocol-cheatsheet.md
            ├── error-handling.md
            └── dirctl-search.md
```
