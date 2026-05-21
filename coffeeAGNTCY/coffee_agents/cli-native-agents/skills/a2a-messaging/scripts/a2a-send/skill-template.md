---
name: __SKILL_NAME__
description: "Send a message to the remote __AGENT_DISPLAY_NAME__ agent via A2A protocol. Use for ANY request intended for this agent — the remote agent determines what it can handle."
allowed-tools: Bash
---

## EXECUTE NOW

Run this command to send the user's message to the remote A2A agent:

```bash
"__A2A_SEND_PATH__" --peer-url "__ENDPOINT__" --message "$ARGUMENTS"
```

- The `a2a-send` path was resolved to an absolute path at `/recruit` time
- `$ARGUMENTS` is auto-substituted by Claude Code with whatever the user typed after the slash command
- stdout contains the agent's response
- If exit code 1, stderr contains a JSON error — relay the error to the user
- For long-running tasks, add --non-blocking --wait flags
