---
name: a2a-messaging
description: Send a message directly to a known A2A agent endpoint via the bundled a2a-send CLI. Use when the user wants to talk to a remote A2A agent at a specific URL, test an endpoint, or invoke an agent ad-hoc without recruiting it as a skill first.
compatibility: Requires the bundled a2a-send binary (built by cli-native-agents/install.sh).
---

# A2A Send — Direct Agent Messaging

Send a message directly to a known A2A agent endpoint. Uses the `a2a-send` Go CLI tool (built on the official a2a-go SDK) for proper protocol handling, agent card discovery, streaming, and multi-turn conversations.

**Usage:** `/a2a-send <endpoint_url> <message>`

**Examples:**
- `/a2a-send http://localhost:9999 "What is the yield?"`
- `/a2a-send https://agent.example.com "Translate 'hello' to French"`

> **Host invocation note:** Examples below use the Claude Code `/skill-name` slash-command syntax and `$ARGUMENTS` substitution. Other CLI-native agent hosts may invoke skills differently — adapt as needed.

---

## Instructions

You are an A2A protocol client. Parse `$ARGUMENTS` to extract the endpoint URL and the message, then use the `a2a-send` binary to communicate with the remote agent.

### Step 1 — Parse arguments

Extract from `$ARGUMENTS`:
- **endpoint_url**: The first token (a URL)
- **message**: Everything after the URL (may be quoted or unquoted)

If arguments are missing or malformed, show the usage examples above and stop.

### Step 2 — Resolve the `a2a-send` binary

Load the project config written by `cli-native-agents/install.sh`. This exports `AGNTCY_A2A_SEND` (the absolute path to the bundled a2a-send binary). Pre-set env vars override the config file.

```bash
. "$(pwd)/.agntcy/cli-native-agents/env.sh" || exit 1
```

Reuse `"$AGNTCY_A2A_SEND"` for every invocation below.

### Step 3 — Send message

Use the `a2a-send` Go binary to send the message. The binary handles agent card discovery, JSON-RPC protocol, UUID generation, and response parsing automatically.

**Simple blocking send:**
```bash
"$AGNTCY_A2A_SEND" --peer-url <endpoint_url> --message "<message>"
```

Make sure to properly shell-escape the message text (handle single quotes, double quotes, newlines, backslashes).

**The binary outputs:**
- **stdout**: The agent's response text (or JSON for non-text parts)
- **stderr**: Informational messages like `[info] Agent: <name>`, `[task] id=... contextId=...`

### Step 4 — Handle the response

The binary extracts text from the response automatically. Check the **exit code**:
- `0` — success, stdout contains the response
- `1` — error, stderr contains a JSON error object: `{"error": "..."}`

#### For multi-turn (if the agent needs more info):
If the response indicates the agent needs input, check stderr for `[task] id=<task_id> contextId=<context_id>`. Send a follow-up using those IDs:
```bash
"$AGNTCY_A2A_SEND" --peer-url <endpoint_url> --task-id <task_id> --context-id <context_id> --message "<follow_up_message>"
```

#### For long-running tasks:
Use non-blocking mode with polling — the binary will wait for the task to complete:
```bash
"$AGNTCY_A2A_SEND" --peer-url <endpoint_url> --non-blocking --wait --timeout-ms 600000 --message "<message>"
```

#### For streaming (SSE):
Use streaming mode to see real-time progress:
```bash
"$AGNTCY_A2A_SEND" --peer-url <endpoint_url> --stream --message "<message>"
```

### Step 5 — Error handling

The binary handles retries internally and outputs structured errors on failure. If the command fails:

| Exit code | Meaning | Suggestion |
|-----------|---------|------------|
| 1 (connection error) | Agent unreachable | Is the agent running? Check the URL and port. |
| 1 (card not found) | Falls back to direct endpoint automatically | Usually fine — the binary retries without the card. |
| 1 (timeout) | Agent didn't respond in time | Try `--non-blocking --wait` for long tasks. |
| 1 (protocol error) | JSON-RPC or A2A protocol error | Check the error message in stderr. |

### Step 6 — Summary

After the interaction is complete, show a clean summary:

```
--- A2A Communication Summary ---
Endpoint:  <url>
Status:    <success | error>
Turns:     <number_of_send_requests>
Response:  <extracted text content from stdout>
```
