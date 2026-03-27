#!/usr/bin/env bash
# otel-emit.sh — Shared OTLP HTTP log event emitter
#
# Reads a JSON event object from stdin and POSTs it as an OTLP LogRecord
# to the configured collector endpoint.
#
# Environment variables:
#   AGNTCY_OTEL_ENABLED   — Must be "1" to emit (opt-in gate)
#   AGNTCY_OTEL_ENDPOINT  — OTLP HTTP endpoint (default: http://localhost:4318)
#   AGNTCY_OTEL_HEADERS   — Optional auth headers (key=value,key=value)
#
# The JSON event on stdin must have:
#   { "event_name": "...", "attributes": { ... }, "session_id": "..." }
#
# All errors are silently ignored (fire-and-forget).

set -euo pipefail

# --- Opt-in gate ---
if [[ "${AGNTCY_OTEL_ENABLED:-}" != "1" ]]; then
  exit 0
fi

# --- Dependency check ---
if ! command -v jq &>/dev/null; then
  exit 0
fi

if ! command -v curl &>/dev/null; then
  exit 0
fi

# --- Read event JSON from stdin ---
EVENT_JSON="$(cat)"
if [[ -z "$EVENT_JSON" ]]; then
  exit 0
fi

# --- Configuration ---
OTEL_ENDPOINT="${AGNTCY_OTEL_ENDPOINT:-http://localhost:4318}"
PLUGIN_NAME="agntcy-discover-connect"
PLUGIN_VERSION="1.0.0"

# --- Extract fields from event ---
EVENT_NAME=$(echo "$EVENT_JSON" | jq -r '.event_name // empty') || exit 0
SESSION_ID=$(echo "$EVENT_JSON" | jq -r '.session_id // empty') || exit 0
ATTRIBUTES_JSON=$(echo "$EVENT_JSON" | jq -c '.attributes // {}') || exit 0

if [[ -z "$EVENT_NAME" ]]; then
  exit 0
fi

# --- Build OTLP attribute key-value pairs from the event attributes ---
# Converts { "key1": "val1", "key2": 123 } into OTLP attribute array format
OTLP_ATTRIBUTES=$(echo "$ATTRIBUTES_JSON" | jq -c '
  [to_entries[] | {
    key: .key,
    value: (
      if .value == null then { stringValue: "" }
      elif (.value | type) == "number" then
        if (.value | floor) == .value then { intValue: (.value | tostring) }
        else { doubleValue: .value }
        end
      elif (.value | type) == "boolean" then { boolValue: .value }
      else { stringValue: (.value | tostring) }
      end
    )
  }]
') || exit 0

# --- Build the OTLP log record ---
TIMESTAMP_NS=$(date +%s)000000000

OTLP_BODY=$(jq -n \
  --arg event_name "$EVENT_NAME" \
  --arg session_id "$SESSION_ID" \
  --arg plugin_name "$PLUGIN_NAME" \
  --arg plugin_version "$PLUGIN_VERSION" \
  --arg timestamp "$TIMESTAMP_NS" \
  --argjson attributes "$OTLP_ATTRIBUTES" \
  '{
    resourceLogs: [{
      resource: {
        attributes: [
          { key: "service.name", value: { stringValue: $plugin_name } },
          { key: "plugin.version", value: { stringValue: $plugin_version } }
        ]
      },
      scopeLogs: [{
        scope: { name: $plugin_name, version: $plugin_version },
        logRecords: [{
          timeUnixNano: $timestamp,
          severityNumber: 9,
          severityText: "INFO",
          body: { stringValue: $event_name },
          attributes: (
            [
              { key: "event.name", value: { stringValue: $event_name } },
              { key: "plugin.name", value: { stringValue: $plugin_name } },
              { key: "plugin.version", value: { stringValue: $plugin_version } },
              { key: "session.id", value: { stringValue: $session_id } }
            ] + $attributes
          )
        }]
      }]
    }]
  }') || exit 0

# --- Build curl headers ---
CURL_HEADERS=(-H "Content-Type: application/json")

if [[ -n "${AGNTCY_OTEL_HEADERS:-}" ]]; then
  IFS=',' read -ra HEADER_PAIRS <<< "$AGNTCY_OTEL_HEADERS"
  for pair in "${HEADER_PAIRS[@]}"; do
    key="${pair%%=*}"
    value="${pair#*=}"
    CURL_HEADERS+=(-H "$key: $value")
  done
fi

# --- POST to collector (fire-and-forget) ---
curl -s --max-time 3 \
  -X POST \
  "${OTEL_ENDPOINT}/v1/logs" \
  "${CURL_HEADERS[@]}" \
  -d "$OTLP_BODY" \
  >/dev/null 2>&1 || true

exit 0
