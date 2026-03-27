#!/usr/bin/env bash
# subagent-start.sh — SubagentStart hook
#
# Fires when any sub-agent is spawned. Filters for A2A-recruited agents
# by checking if the agent file contains "message/send", then emits
# an agntcy.subagent.start event.
#
# Hook input JSON shape (from Claude Code):
# {
#   "subagent_id": "...",
#   "subagent_type": "...",
#   "session_id": "..."
# }

set -euo pipefail

# --- Opt-in gate (fast exit) ---
if [[ "${AGNTCY_OTEL_ENABLED:-}" != "1" ]]; then
  exit 0
fi

# --- Dependency check ---
if ! command -v jq &>/dev/null; then
  exit 0
fi

# --- Resolve script directory ---
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# --- Read hook input from stdin ---
HOOK_INPUT="$(cat)"
if [[ -z "$HOOK_INPUT" ]]; then
  exit 0
fi

# --- Extract fields ---
SUBAGENT_ID=$(echo "$HOOK_INPUT" | jq -r '.subagent_id // empty') || exit 0
SUBAGENT_TYPE=$(echo "$HOOK_INPUT" | jq -r '.subagent_type // empty') || exit 0
SESSION_ID=$(echo "$HOOK_INPUT" | jq -r '.session_id // empty') || exit 0

if [[ -z "$SUBAGENT_TYPE" ]]; then
  exit 0
fi

# --- Filter: only A2A-recruited agents ---
# Check if the agent file exists and contains "message/send" (A2A indicator)
AGENT_FILE=".claude/agents/${SUBAGENT_TYPE}.md"
if [[ ! -f "$AGENT_FILE" ]]; then
  exit 0
fi

if ! grep -q "message/send" "$AGENT_FILE" 2>/dev/null; then
  exit 0
fi

# --- Extract endpoint from agent file ---
ENDPOINT=""
# Look for the Endpoint: line in the agent file
ENDPOINT_LINE=$(grep -m1 "^Endpoint:" "$AGENT_FILE" 2>/dev/null || true)
if [[ -n "$ENDPOINT_LINE" ]]; then
  ENDPOINT=$(echo "$ENDPOINT_LINE" | sed 's/^Endpoint:[[:space:]]*//')
fi

# --- Emit event ---
ATTRS=$(jq -n \
  --arg subagent_id "$SUBAGENT_ID" \
  --arg subagent_type "$SUBAGENT_TYPE" \
  --arg subagent_endpoint "$ENDPOINT" \
  '{
    "subagent.id": $subagent_id,
    "subagent.type": $subagent_type,
    "subagent.endpoint": $subagent_endpoint
  }')

jq -n \
  --arg event_name "agntcy.subagent.start" \
  --arg session_id "$SESSION_ID" \
  --argjson attributes "$ATTRS" \
  '{ event_name: $event_name, session_id: $session_id, attributes: $attributes }' \
| bash "$SCRIPT_DIR/otel-emit.sh"

exit 0
