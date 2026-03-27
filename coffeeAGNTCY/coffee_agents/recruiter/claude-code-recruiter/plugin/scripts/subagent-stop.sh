#!/usr/bin/env bash
# subagent-stop.sh — SubagentStop hook
#
# Fires when any sub-agent finishes. Filters for A2A-recruited agents
# by checking if the agent file contains "message/send", then emits
# an agntcy.subagent.stop event.
#
# Hook input JSON shape (from Claude Code):
# {
#   "subagent_id": "...",
#   "subagent_type": "...",
#   "last_assistant_message": "...",
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
LAST_MESSAGE=$(echo "$HOOK_INPUT" | jq -r '.last_assistant_message // empty') || exit 0
SESSION_ID=$(echo "$HOOK_INPUT" | jq -r '.session_id // empty') || exit 0

if [[ -z "$SUBAGENT_TYPE" ]]; then
  exit 0
fi

# --- Filter: only A2A-recruited agents ---
AGENT_FILE=".claude/agents/${SUBAGENT_TYPE}.md"
if [[ ! -f "$AGENT_FILE" ]]; then
  exit 0
fi

if ! grep -q "message/send" "$AGENT_FILE" 2>/dev/null; then
  exit 0
fi

# --- Truncate last message to 500 chars ---
LAST_MESSAGE_PREVIEW=""
if [[ -n "$LAST_MESSAGE" ]]; then
  LAST_MESSAGE_PREVIEW=$(echo "$LAST_MESSAGE" | head -c 500)
fi

# --- Emit event ---
ATTRS=$(jq -n \
  --arg subagent_id "$SUBAGENT_ID" \
  --arg subagent_type "$SUBAGENT_TYPE" \
  --arg last_message_preview "$LAST_MESSAGE_PREVIEW" \
  '{
    "subagent.id": $subagent_id,
    "subagent.type": $subagent_type,
    "subagent.last_message_preview": $last_message_preview
  }')

jq -n \
  --arg event_name "agntcy.subagent.stop" \
  --arg session_id "$SESSION_ID" \
  --argjson attributes "$ATTRS" \
  '{ event_name: $event_name, session_id: $session_id, attributes: $attributes }' \
| bash "$SCRIPT_DIR/otel-emit.sh"

exit 0
