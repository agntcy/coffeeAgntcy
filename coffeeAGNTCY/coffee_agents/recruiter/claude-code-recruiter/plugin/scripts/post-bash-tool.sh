#!/usr/bin/env bash
# post-bash-tool.sh — PostToolUse hook for Bash tool calls
#
# Receives PostToolUse JSON on stdin for every Bash tool call.
# Classifies A2A-related commands and emits structured OTel events
# via otel-emit.sh. Non-A2A commands are silently skipped.
#
# Hook input JSON shape (from Claude Code):
# {
#   "tool_name": "Bash",
#   "tool_input": { "command": "..." },
#   "tool_response": "...",
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
TOOL_CMD=$(echo "$HOOK_INPUT" | jq -r '.tool_input.command // empty') || exit 0
TOOL_RESPONSE=$(echo "$HOOK_INPUT" | jq -r '.tool_response // empty') || exit 0
SESSION_ID=$(echo "$HOOK_INPUT" | jq -r '.session_id // empty') || exit 0

if [[ -z "$TOOL_CMD" ]]; then
  exit 0
fi

# --- Classify command and emit event ---

# Helper: emit an event via otel-emit.sh
emit_event() {
  local event_name="$1"
  local attributes_json="$2"

  jq -n \
    --arg event_name "$event_name" \
    --arg session_id "$SESSION_ID" \
    --argjson attributes "$attributes_json" \
    '{ event_name: $event_name, session_id: $session_id, attributes: $attributes }' \
  | bash "$SCRIPT_DIR/otel-emit.sh"
}

# --- Pattern: dirctl search (not routing search) ---
if [[ "$TOOL_CMD" =~ dirctl[[:space:]]+search ]] && [[ ! "$TOOL_CMD" =~ dirctl[[:space:]]+routing ]]; then
  # Determine search strategy from flags
  STRATEGY="unknown"
  if [[ "$TOOL_CMD" =~ --skill ]] && [[ "$TOOL_CMD" =~ --domain ]]; then
    STRATEGY="domain"
  elif [[ "$TOOL_CMD" =~ --skill ]]; then
    STRATEGY="skill_match"
  elif [[ "$TOOL_CMD" =~ --name ]]; then
    STRATEGY="name_wildcard"
  elif [[ "$TOOL_CMD" =~ --module ]]; then
    STRATEGY="module_search"
  fi

  # Check if results were returned
  HAS_RESULTS="false"
  RESULT_COUNT=0
  if [[ -n "$TOOL_RESPONSE" ]] && echo "$TOOL_RESPONSE" | jq -e 'if type == "array" then length > 0 elif type == "object" then true else false end' &>/dev/null; then
    HAS_RESULTS="true"
    RESULT_COUNT=$(echo "$TOOL_RESPONSE" | jq 'if type == "array" then length elif type == "object" then 1 else 0 end' 2>/dev/null || echo "0")
  fi

  ATTRS=$(jq -n \
    --arg strategy "$STRATEGY" \
    --arg has_results "$HAS_RESULTS" \
    --argjson result_count "$RESULT_COUNT" \
    --arg command "$TOOL_CMD" \
    '{
      "dirctl.search.strategy": $strategy,
      "dirctl.search.has_results": $has_results,
      "dirctl.search.result_count": $result_count,
      "dirctl.command": $command
    }')

  emit_event "agntcy.dirctl.search" "$ATTRS"
  exit 0
fi

# --- Pattern: dirctl routing search ---
if [[ "$TOOL_CMD" =~ dirctl[[:space:]]+routing[[:space:]]+search ]]; then
  ATTRS=$(jq -n \
    --arg command "$TOOL_CMD" \
    '{
      "dirctl.routing.command": $command
    }')

  emit_event "agntcy.dirctl.routing_search" "$ATTRS"
  exit 0
fi

# --- Pattern: dirctl pull ---
if [[ "$TOOL_CMD" =~ dirctl[[:space:]]+pull[[:space:]] ]]; then
  # Extract CID (the argument after "pull")
  CID=""
  if [[ "$TOOL_CMD" =~ dirctl[[:space:]]+pull[[:space:]]+([^[:space:]]+) ]]; then
    CID="${BASH_REMATCH[1]}"
  fi

  ATTRS=$(jq -n \
    --arg cid "$CID" \
    --arg command "$TOOL_CMD" \
    '{
      "dirctl.pull.cid": $cid,
      "dirctl.command": $command
    }')

  emit_event "agntcy.dirctl.pull" "$ATTRS"
  exit 0
fi

# --- Pattern: a2a-send binary invocation ---
if [[ "$TOOL_CMD" =~ a2a-send[[:space:]]+--peer-url ]]; then
  # Extract endpoint URL from --peer-url flag
  ENDPOINT=""
  if [[ "$TOOL_CMD" =~ --peer-url[[:space:]]+([^[:space:]]+) ]]; then
    ENDPOINT="${BASH_REMATCH[1]}"
  fi

  # Detect mode from flags
  MODE="blocking"
  if [[ "$TOOL_CMD" =~ --stream ]]; then
    MODE="streaming"
  elif [[ "$TOOL_CMD" =~ --non-blocking ]]; then
    if [[ "$TOOL_CMD" =~ --wait ]]; then
      MODE="non-blocking-wait"
    else
      MODE="non-blocking"
    fi
  fi

  # Determine response status from tool_response
  RESPONSE_STATUS="unknown"
  if [[ -n "$TOOL_RESPONSE" ]]; then
    # Check for error JSON on stderr (captured in tool_response)
    if echo "$TOOL_RESPONSE" | jq -e '.error' &>/dev/null; then
      RESPONSE_STATUS="error"
    else
      RESPONSE_STATUS="success"
    fi
  fi

  ATTRS=$(jq -n \
    --arg endpoint "$ENDPOINT" \
    --arg method "message/send" \
    --arg mode "$MODE" \
    --arg response_status "$RESPONSE_STATUS" \
    '{
      "a2a.endpoint": $endpoint,
      "a2a.method": $method,
      "a2a.mode": $mode,
      "a2a.response.status": $response_status
    }')

  emit_event "agntcy.a2a.message_send" "$ATTRS"
  exit 0
fi

# --- Pattern: curl ... message/send (legacy A2A message send) ---
if [[ "$TOOL_CMD" =~ curl ]] && [[ "$TOOL_CMD" =~ message/send ]]; then
  # Extract endpoint URL from the curl command
  ENDPOINT=""
  # Match -X POST <url> or just the URL after curl flags
  if [[ "$TOOL_CMD" =~ -X[[:space:]]+POST[[:space:]]+([^[:space:]]+) ]]; then
    ENDPOINT="${BASH_REMATCH[1]}"
  fi

  # Determine response status from tool_response
  RESPONSE_STATUS="unknown"
  if [[ -n "$TOOL_RESPONSE" ]]; then
    # Check for JSON-RPC result
    RESULT_KIND=$(echo "$TOOL_RESPONSE" | jq -r '.result.kind // empty' 2>/dev/null) || true
    ERROR_CODE=$(echo "$TOOL_RESPONSE" | jq -r '.error.code // empty' 2>/dev/null) || true

    if [[ -n "$RESULT_KIND" ]]; then
      RESPONSE_STATUS="$RESULT_KIND"  # "message" or "task"
    elif [[ -n "$ERROR_CODE" ]]; then
      RESPONSE_STATUS="error"
    fi
  fi

  # Extract error code if present
  ERR_CODE=$(echo "$TOOL_RESPONSE" | jq -r '.error.code // empty' 2>/dev/null) || true

  ATTRS=$(jq -n \
    --arg endpoint "$ENDPOINT" \
    --arg method "message/send" \
    --arg response_status "$RESPONSE_STATUS" \
    --arg error_code "${ERR_CODE:-}" \
    '{
      "a2a.endpoint": $endpoint,
      "a2a.method": $method,
      "a2a.response.status": $response_status,
      "a2a.error.code": $error_code
    }')

  emit_event "agntcy.a2a.message_send" "$ATTRS"
  exit 0
fi

# --- Pattern: curl ... .well-known/agent (agent card fetch) ---
if [[ "$TOOL_CMD" =~ curl ]] && [[ "$TOOL_CMD" =~ well-known/agent ]]; then
  # Extract endpoint URL
  ENDPOINT=""
  # Try to find the URL in the curl command
  if [[ "$TOOL_CMD" =~ (https?://[^[:space:]\"\']+) ]]; then
    ENDPOINT="${BASH_REMATCH[1]}"
  fi

  # Determine if fetch was successful
  FETCH_SUCCESS="false"
  AGENT_NAME=""
  if [[ -n "$TOOL_RESPONSE" ]]; then
    AGENT_NAME=$(echo "$TOOL_RESPONSE" | jq -r '.name // empty' 2>/dev/null) || true
    if [[ -n "$AGENT_NAME" ]]; then
      FETCH_SUCCESS="true"
    fi
  fi

  ATTRS=$(jq -n \
    --arg endpoint "$ENDPOINT" \
    --arg fetch_success "$FETCH_SUCCESS" \
    --arg agent_name "${AGENT_NAME:-}" \
    '{
      "a2a.agent_card.endpoint": $endpoint,
      "a2a.agent_card.fetch_success": $fetch_success,
      "a2a.agent_card.agent_name": $agent_name
    }')

  emit_event "agntcy.a2a.agent_card_fetch" "$ATTRS"
  exit 0
fi

# --- No match: not an A2A-related command ---
exit 0
