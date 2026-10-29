# Local cluster umbrella chart

This chart bundles Lungo services for a local KinD-style deployment.

## Secret store: `my-local-secret`

Charts that use `externalSecrets` expect a backing secret (for example in the cluster store) named **`my-local-secret`** with at least:

| Property | Purpose |
|----------|---------|
| `AZURE_API_KEY` | Azure OpenAI / LLM API access |
| `SLIM_SHARED_SECRET` | Shared secret of the SLIM peers (at least 32 characters; SLIM 2.x rejects shorter ones). Every SLIM peer, including the weather and payment MCP servers when they use SLIM, must get the same value |

The umbrella chart can render a development `Secret` from environment variables via `templates/external-secret/local-secret.yaml` when `localExternalSecret` is set (see `config-overrides.yaml.gotmpl`: `AZURE_API_KEY` from the environment and `SLIM_SHARED_SECRET` from `SLIM_SHARED_SECRET`, defaulting to the public app-sdk placeholder `slim-mls-secret-REPLACE_WITH_RANDOM_32PLUS_CHARS` for local use only; the app-sdk logs a warning when it sees that value). The farm and logistics agents start with that placeholder only because the Helmfile overlay (`config-overrides.yaml.gotmpl`, applied by `make apply`) defaults their `config.slimAllowPlaceholderSecret` to `true` (`SLIM_ALLOW_PLACEHOLDER_SECRET`); export `SLIM_ALLOW_PLACEHOLDER_SECRET=false` before `make apply` to see the agents refuse to start without a real secret; the per-agent charts default it to `false`, so a deployment of those charts without a real secret fails at startup. Set `SLIM_SHARED_SECRET` to a random value of your own for anything that is not a throwaway cluster.

After changing `SLIM_SHARED_SECRET` on an existing cluster, restart the SLIM peers so they all pick up the new value, for example `kubectl rollout restart deployment` in the release namespace (the ExternalSecrets refresh hourly and pods read the value only at start).

Transport-related **non-secret** settings are passed through each subchart’s `config` (for example `slimServer`, `natsServer`, `defaultMessageTransport`, `transportServerEndpoint`) from the same gotmpl merge.

## Supply Chain Commitment

The umbrella chart deploys the Supply Chain Commitment agents (see [Supply Chain Commitment](../../../docs/supply_chain_commitment.md)):

| Release | Chart | Role | Port |
|---------|-------|------|------|
| `supply-chain-buyer` | `supply-chain-buyer` | Moderator and HTTP API; NodePort **30085** | 9095 |
| `supply-chain-supplier-a`, `-b`, `-c` | `supply-chain-supplier` (one chart, three aliases) | Suppliers; each alias sets its own `appName`, `config.supplierId` and `service.port` in `values.yaml` | 9096 to 9098 |
| `supply-chain-logistics` | `supply-chain-logistics` | Carrier agent | 9099 |

- `kind-config.yaml` maps NodePort 30085 to the host. The `ui` chart sets `VITE_SUPPLY_CHAIN_APP_API_URL` to `http://127.0.0.1:9095`, the same style of value as for the other supervisors. `values.yaml` sets the Buyer's CORS origins.
- `config-overrides.yaml.gotmpl` gives the four members the same SLIM, LLM and secret settings as the logistics agents, and gives the Buyer the Agentic Workflows API settings (`workflowApiUrl`, `workflowApiKey`) as the other supervisors have.
- Every one of the three charts has `config.l9Enabled` (default `false`), rendered as `SUPPLY_CHAIN_L9_ENABLED`. With `false` the Buyer offers and accepts only baseline runs; set it to `true` on all three to allow L9 runs.
