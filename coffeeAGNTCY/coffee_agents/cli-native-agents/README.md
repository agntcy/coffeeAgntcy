

1. **Discover** remote agents through the **AGNTCY Directory Service**
2. **Verify** their published OASF records locally with `dirctl` and inspect identity and policies with the **AGNTCY Identity Service**
3. **Connect** to recruited agents over **HTTP or SLIM**
4. **Observe** 


**Prerequisites:** [Claude Code CLI](https://docs.anthropic.com/en/docs/claude-code), [`dirctl`](https://github.com/agntcy/dir-ctl), [Go 1.25+](https://go.dev/dl/) (to build `a2a-send`; required by `slim-a2a-go`), [`jq`](https://stedolan.github.io/jq/) for record parsing, and `python3` (≥3.7, stdlib only — used by `/check-identity`).

**Environment variables:** Different commands and options read different variables from the shell — set only the ones you need. All are documented in [`.env.example`](./.env.example):

| Variable | Required by | Purpose | Example |
|---|---|---|---|
| `IDENTITY_API_SERVER_URL` | `/check-identity` only | Base URL of the AGNTCY identity service | `https://api.agent-identity.outshift.com` (hosted) or `http://0.0.0.0:4000` (local) |
| `IDENTITY_SERVICE_API_KEY` | `/check-identity` only | Sent as the `x-id-api-key` header on every identity-service call | (your AGNTCY identity-service API key) |
| `SLIM_SHARED_SECRET` | `/a2a-send` and recruited skills, **only when the target agent advertises a `slim`/`slimrpc` interface** | Must match the secret the target agent was started with. Without it. For the `coffee_agents/lungo` stack, copy the value from `coffee_agents/lungo/.env`. HTTP-only can ignore. | `slim-shared-secret-…` |


* setup wizard script - set env vars etc
* otel integration
* event emission

Supported CLI-native agents:
- `claude-code`
- `codex`
- `opencode`
- `copilot-cli`