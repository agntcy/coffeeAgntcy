# Proposal

## Why

Lungo agents resolve workflow metadata and emit workflow events through the
Agentic Workflows API, configured by `WORKFLOW_API_URL` and
`WORKFLOW_API_KEY`. Docker Compose wires both for the three supervisors, but
none of the agent Helm charts expose them. A Helm-deployed agent therefore
falls back to the code default (`http://localhost:9105`), cannot reach the API,
and logs `Workflow catalog GET failed (ConnectError: [Errno 111] Connection
refused)` followed by `no catalog match for propagated workflow_name=...;
skipping event emission`. Workflow topology events are silently lost on every
Helm deployment.

## What Changes

- Add `config.workflowApiUrl` and `config.workflowApiKey` to the `values.yaml`
  of the agent charts whose agents may call the Agentic Workflows API:
  `auction-supervisor`, `logistics-supervisor`, `recruiter-supervisor` (A2A
  event middleware, catalog lookups) and `colombia-farm` (MCP client calls
  that emit workflow events).
- Render them into each chart's ConfigMap as `WORKFLOW_API_URL` and
  `WORKFLOW_API_KEY`, only when set, so an unset value keeps the application's
  own default instead of becoming an empty string.
- Set both values for those four agents in the `local-cluster` overrides so the
  local Helm deployment works out of the box against the in-cluster
  `agentic-workflows-api`.
- Bump the **minor** version of each changed chart and of `local-cluster`
  (and its dependency pins), per the Helm chart version guard.
- Document the two new values and add a `CHANGELOG.md` entry.

## Capabilities

### New Capabilities

- `agent-workflow-api-config`: how agent Helm charts configure the Agentic
  Workflows API URL and key for the agent process.

### Modified Capabilities

None.

## Impact

- `coffeeAGNTCY/coffee_agents/lungo/deployment/helm/<agent>/{values.yaml,
  templates/configmap.tpl.yaml,Chart.yaml}` for the four charts above.
- `deployment/helm/local-cluster/{config-overrides.yaml.gotmpl,Chart.yaml}`.
- Not affected: agents that never call the API (`brazil-farm`, `vietnam-farm`,
  `logistics-farm`, `logistics-accountant`, `logistics-shipper`,
  `logistics-helpdesk`, `recruiter`), `agentic-workflows-api` (the server),
  `ui`, and the two MCP server charts (`payment-mcp-server`,
  `weather-mcp-server`), which are called, not callers.
- Not affected: application code and `docker-compose.yaml`.
- Upgrades are backward compatible: with both values unset, rendered output
  is unchanged.
