---
name: __SKILL_NAME__
description: "Send a message to the remote __AGENT_DISPLAY_NAME__ agent via A2A protocol. Use for ANY request intended for this agent — the remote agent determines what it can handle."
allowed-tools: Bash
---

## EXECUTE NOW

Load the project config and send the user's message to the remote A2A agent:

```bash
. "$(pwd)/.agntcy/cli-native-agents/env.sh" || exit 1
"$AGNTCY_A2A_SEND" --peer-url "__ENDPOINT__" --message "$ARGUMENTS"
```

- `env.sh` was written by `cli-native-agents/install.sh` and exports `AGNTCY_A2A_SEND`.
- `$ARGUMENTS` is the substitution token for the user's input (Claude Code syntax; other hosts may differ).
- stdout contains the agent's response.
- If exit code 1, stderr contains a JSON error — relay the error to the user.
- For long-running tasks, add `--non-blocking --wait` flags.

