# Local cluster umbrella chart

This chart bundles Lungo services for a local KinD-style deployment.

## Secret store: `my-local-secret`

Charts that use `externalSecrets` expect a backing secret (for example in the cluster store) named **`my-local-secret`** with at least:

| Property | Purpose |
|----------|---------|
| `AZURE_API_KEY` | Azure OpenAI / LLM API access |
| `SLIM_SHARED_SECRET` | SLIM gateway shared secret; must match the SLIM gateway password used by the in-cluster SLIM deployment |

The umbrella chart can render a development `Secret` from environment variables via `templates/external-secret/local-secret.yaml` when `localExternalSecret` is set (see `config-overrides.yaml.gotmpl`: `AZURE_API_KEY` from the environment and `SLIM_SHARED_SECRET` from `SLIM_SHARED_SECRET`, defaulting to `dummy_password` for local use only).

Transport-related **non-secret** settings are passed through each subchart’s `config` (for example `slimServer`, `natsServer`, `defaultMessageTransport`, `transportServerEndpoint`) from the same gotmpl merge.
