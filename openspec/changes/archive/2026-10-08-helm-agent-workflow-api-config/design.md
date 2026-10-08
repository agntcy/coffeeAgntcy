# Design

## Context

Each agent chart has a near-identical `templates/configmap.tpl.yaml` whose
keys come from `config.*` in `values.yaml`; the deployment loads the ConfigMap
via `envFrom`. The agent reads `WORKFLOW_API_URL` / `WORKFLOW_API_KEY` in
`config/config.py`, with `os.getenv("WORKFLOW_API_URL", "http://localhost:9105")`.
`os.getenv` only applies its default when the variable is absent, not when it
is the empty string. `local-cluster/config-overrides.yaml.gotmpl` injects
per-chart config for the umbrella. The `agentic-workflows-api` chart serves on
port 9105 under the service name `agentic-workflows-api` and defaults its key
to `TheAnswerIs42` (secret `agentic-workflows-api-api-key-secret`).

## Goals / Non-Goals

**Goals:**
- Agents deployed through Helm reach the workflows API with no manual patching of the ConfigMap.
- Zero rendered diff for existing installs that set nothing.

**Non-Goals:**
- Moving the key to a Secret or `valueFrom` reference (see Decisions).
- Changing application code or `docker-compose.yaml`.
- Touching the API, UI, or MCP server charts.

## Decisions

**Conditional rendering, not always-render.** Wrap each key in
`{{- if .Values.config.workflowApiUrl }}`. Always rendering would emit
`WORKFLOW_API_URL: ""`, which `os.getenv` returns as `""`, breaking the
`localhost:9105` default and producing a URL-less httpx error. Alternative
considered: change `config.py` to treat empty as unset; rejected as it widens
scope to application code for a chart concern.

**Key in the ConfigMap, per the request.** The key is requested as a ConfigMap
env var sourced from `values.yaml`, matching how `recruiter-supervisor`
already carries `IDENTITY_API_KEY`. This is the weaker option: ConfigMaps are
not secret-grade. The API chart itself uses a Secret. Alternative: render the
key into the existing `{app}-secrets`/transport Secret and `secretRef` it.
Rejected for now to follow the stated approach and keep one uniform pattern;
the key is a shared dev-style token, and chart consumers can leave
`workflowApiKey` empty and supply `WORKFLOW_API_KEY` through `externalSecrets`
since the deployment already `envFrom`s that Secret.

**Scope = agents that may call the API: four charts.** Determined from the
code: the auction, logistics and recruiter supervisors use the A2A event
middleware, catalog lookups and `WorkflowAPIEventSink`; the Colombia farm
calls MCP tools through `common.mcp_client.call_mcp_tool`, whose
`wrap_mcp_client` does catalog lookups and event emission, and registers the
in-flight cleanup span processor. No other agent imports these paths (Brazil
and Vietnam farms, the logistics farm/accountant/shipper/helpdesk, and the
recruiter agent do not), so their charts stay untouched. The MCP server
charts are called, not callers, and `agentic-workflows-api` and `ui` are the
producer and consumer of the API. If another agent later gains workflow
event emission, its chart adds the same two values then.

**Local cluster values.** URL `http://agentic-workflows-api:9105` (service
name equals `appName`, same namespace, so the short name resolves). Key from
`env "WORKFLOW_API_KEY"` with fallback `TheAnswerIs42`, so it matches the API
chart's default unless an operator overrides both. Because the override file
builds config per target group from a shared dict and Brazil/Vietnam must not
receive these keys, they are defined in a separate `$workflowApi` dict merged
only into `auction-supervisor`, `colombia-farm`, `logistics-supervisor` and
`recruiter-supervisor`.

**Version bumps.** Minor bump each of the four charts and `local-cluster`
(new configuration surface, not a fix), and update the `local-cluster`
dependency pins, as the version guard requires. `colombia-farm` goes
0.1.3 -> 0.2.0, the other three 0.1.2 -> 0.2.0, `local-cluster` 0.5.0 -> 0.6.0.

## Risks / Trade-offs

- [Key readable via ConfigMap] -> documented; empty default, secrets path via `externalSecrets` remains available.
- [Local-cluster key drifts from the API key] -> both default to `TheAnswerIs42` and are overridden together via the same env var; verify by rendering.
- [Pin mismatch after bumps fails `helm dependency` / guard] -> task verifies with `helm template` and the version check.
