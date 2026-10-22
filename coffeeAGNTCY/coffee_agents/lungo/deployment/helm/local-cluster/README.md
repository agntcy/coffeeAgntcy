# Local cluster umbrella chart

This chart bundles Lungo services for a local KinD-style deployment.

## Secret store: `my-local-secret`

Charts that use `externalSecrets` expect a backing secret (for example in the cluster store) named **`my-local-secret`** with at least:

| Property | Purpose |
|----------|---------|
| `AZURE_API_KEY` | Azure OpenAI / LLM API access |
| `SLIM_SHARED_SECRET` | Shared secret of the SLIM peers (at least 32 characters; SLIM 2.x rejects shorter ones). Every agent must get the same value |

The umbrella chart can render a development `Secret` from environment variables via `templates/external-secret/local-secret.yaml` when `localExternalSecret` is set (see `config-overrides.yaml.gotmpl`: `AZURE_API_KEY` from the environment and `SLIM_SHARED_SECRET` from `SLIM_SHARED_SECRET`, defaulting to the public app-sdk placeholder `slim-mls-secret-REPLACE_WITH_RANDOM_32PLUS_CHARS` for local use only; the app-sdk logs a warning when it sees that value). Set `SLIM_SHARED_SECRET` to a random value of your own for anything that is not a throwaway cluster.

Transport-related **non-secret** settings are passed through each subchart’s `config` (for example `slimServer`, `natsServer`, `defaultMessageTransport`, `transportServerEndpoint`) from the same gotmpl merge.
