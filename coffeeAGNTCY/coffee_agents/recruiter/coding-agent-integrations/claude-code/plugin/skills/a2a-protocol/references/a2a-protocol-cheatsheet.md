# A2A Protocol Cheat Sheet

A2A uses **JSON-RPC 2.0** over HTTP POST. This plugin supports **protocol version 0.3.0+** and **1.0** (via the a2a-go SDK).

## Protocol Version Detection

Fetch the agent card first to confirm compatibility:
```bash
curl -s <ENDPOINT_URL>/.well-known/agent-card.json
```
Check `protocolVersion` — must be `"0.3.0"` or higher.

## a2a-send CLI Tool (Recommended)

The `a2a-send` Go binary handles protocol details automatically — agent card discovery, JSON-RPC, streaming, and multi-turn. Prefer this over raw curl.

**Send a message (blocking):**
```bash
plugin/scripts/a2a-send/a2a-send --peer-url <ENDPOINT_URL> --message "<MESSAGE>"
```

**Send with context (multi-turn):**
```bash
plugin/scripts/a2a-send/a2a-send --peer-url <ENDPOINT_URL> --task-id <TASK_ID> --context-id <CONTEXT_ID> --message "<MESSAGE>"
```

**Stream a message (SSE):**
```bash
plugin/scripts/a2a-send/a2a-send --peer-url <ENDPOINT_URL> --stream --message "<MESSAGE>"
```

**Non-blocking with polling (for long tasks):**
```bash
plugin/scripts/a2a-send/a2a-send --peer-url <ENDPOINT_URL> --non-blocking --wait --timeout-ms 600000 --message "<MESSAGE>"
```

**Output:** stdout = response text, stderr = info/task handles, exit 1 = error with JSON on stderr.

## Methods

| Method | Purpose |
|--------|---------|
| `message/send` | Send a message to an agent (synchronous) |
| `message/stream` | Send + subscribe to SSE stream |

## Message Format

- Messages require a `messageId` field (UUID)
- Parts use `"kind": "text"`
- For multi-turn, use `contextId` from the response to continue the conversation

**Task lifecycle (via `message/stream` SSE):**
```
submitted -> working -> completed | failed | input-required
```

## Curl Templates (Legacy)

These raw curl templates are kept for reference and debugging. For normal use, prefer the `a2a-send` CLI above.

**Send a message (synchronous):**
```bash
MSG_ID=$(uuidgen | tr '[:upper:]' '[:lower:]')
curl -s -X POST <ENDPOINT_URL> \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "message/send",
    "params": {
      "message": {
        "messageId": "'$MSG_ID'",
        "role": "user",
        "parts": [{ "kind": "text", "text": "<MESSAGE>" }]
      }
    }
  }'
```

**Send with context (multi-turn continuation):**
```bash
MSG_ID=$(uuidgen | tr '[:upper:]' '[:lower:]')
curl -s -X POST <ENDPOINT_URL> \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "message/send",
    "params": {
      "message": {
        "messageId": "'$MSG_ID'",
        "role": "user",
        "parts": [{ "kind": "text", "text": "<MESSAGE>" }]
      },
      "configuration": {
        "contextId": "<CONTEXT_ID_FROM_PREVIOUS_RESPONSE>"
      }
    }
  }'
```

**Stream a message (SSE — returns task lifecycle events):**
```bash
MSG_ID=$(uuidgen | tr '[:upper:]' '[:lower:]')
curl -s -N -X POST <ENDPOINT_URL> \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "message/stream",
    "params": {
      "message": {
        "messageId": "'$MSG_ID'",
        "role": "user",
        "parts": [{ "kind": "text", "text": "<MESSAGE>" }]
      }
    }
  }'
```

## Response Format

**Synchronous (`message/send`) — direct message response:**
```json
{
  "id": 1,
  "jsonrpc": "2.0",
  "result": {
    "kind": "message",
    "messageId": "<uuid>",
    "role": "agent",
    "parts": [{ "kind": "text", "text": "response text" }],
    "metadata": { "name": "Agent Name" }
  }
}
```

**Streaming (`message/stream`) — SSE events with task lifecycle:**
```
data: {"id":1,"jsonrpc":"2.0","result":{"kind":"task","id":"<task_id>","contextId":"<ctx>","status":{"state":"submitted"},...}}
data: {"id":1,"jsonrpc":"2.0","result":{"kind":"message","messageId":"<uuid>","role":"agent","parts":[{"kind":"text","text":"response"}]}}
```
