# Error Handling Conventions

## Timeouts

All curl calls use `--connect-timeout 10 --max-time 30` (10s to connect, 30s total).

## Retry Policy

- **Max retries:** 2 (3 total attempts)
- **Backoff:** 3 seconds between retries
- **Retryable:** curl exit 7 (connection refused), 28 (timeout), 56 (recv failure), HTTP 500-504, JSON-RPC -32603
- **Non-retryable:** HTTP 404 (not found), 429 (rate limit — special: wait 5s, retry once), JSON-RPC -32601 (protocol mismatch), -32602 (bad params)

## Structured Error Format

Both `/a2a-send` and generated sub-agents report failures in a consistent format:
```json
{
  "status": "failed",
  "error_type": "<connection_refused|timeout|not_found|rate_limited|server_error|protocol_mismatch|invalid_params|json_rpc_error>",
  "error_detail": "<last error message>",
  "attempts": 3,
  "notes": "<actionable suggestion>"
}
```
