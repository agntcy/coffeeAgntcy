# Proposal

## Why

`agntcy-app-sdk` 0.7.0 (uploaded 2026-11-10) moves to SLIM 3: it requires
`slim-bindings` 3.3.9, drops support for installing 2.x next to it, and was
tested against a SLIM 3.4.6 node. Lungo and corto are on `agntcy-app-sdk`
0.6.1, `slim-bindings` 2.2.0 and a SLIM 2.2.0 node. Staying there means no
further app-sdk fixes. The SDK says a 3.x client against a 2.2.0 node was
not tested, so the clients and the node have to move together.

## What Changes

- **Python dependencies (lungo, corto).** `agntcy-app-sdk` 0.6.1 to 0.7.0,
  `slim-bindings` 2.2.0 to 3.3.9. The SDK pulls in `slima2a` 0.9.3,
  `ioa-observe-sdk` 1.1.0, `grpcio-tools>=1.85.1` (so `grpcio>=1.85.1`) and
  `protobuf>=7.36.2`. Regenerate both `uv.lock` files. Move the
  `[tool.uv.exclude-newer-package]` dates forward for the packages the
  14-day window would otherwise block, and update the comments that
  justify them.
- **SLIM node image.** `ghcr.io/agntcy/slim:2.2.0@sha256:0d32...` to
  `ghcr.io/agntcy/slim:3.4.6@sha256:54fde7ce...` in both
  `docker-compose.yaml` files, keeping the digest pin.
- **Helm local clusters (lungo, corto).** The `slim` chart dependency from
  `v2.2.0` (image tag overridden to `2.2.0`) to `v2.9.2`, whose `appVersion`
  is 3.4.6, and set the image-tag override to `3.4.6`. Update `Chart.lock`,
  bump the `local-cluster` chart `version`, and update the comments that
  say "SLIM 2.x".
- **Code and tests that touch SLIM.** Check the `SlimError` handling in
  `corto/exchange/errors.py` and `lungo/agents/supervisors/auction/graph/a2a_retry.py`
  and their unit tests against slim-bindings 3.x. Check the farm and
  supplier agent cards for the a2a-sdk 1.2.3 "AgentCard is not
  spec-compliant" warning (an `AgentInterface` built without
  `protocol_version`) and fix it where it applies.
- **Docs.** The version table in `README.md`, the `docker_overrides`
  examples in `.github/workflows/README.md` and the corto and lungo
  `tests/README.md` files, the `docker run` examples in lungo integration
  scripts and docs, and any prose that says SLIM 2.
- **Recruiter (drops app-sdk, moves to a2a-sdk 1.2.3).** `recruiter` is on
  app-sdk 0.5.5 and slim-bindings 1.1.0, but it only uses app-sdk to serve
  one JSON-RPC card and to build one JSON-RPC client. Remove
  `agntcy-app-sdk` and `slim-bindings` from `recruiter/pyproject.toml`, move
  `a2a-sdk` to 1.2.3 (with the `http-server` extra) and serve and call A2A
  through `a2a-sdk` directly. This is a port from a2a 0.3 types to the 1.x
  protobuf types in the recruiter server, executor, evaluator client, card
  parsing and tests. The server speaks A2A v1.0 only (v0.3 compat off, one
  `1.0` interface in the card) and keeps serving the card at both
  `/.well-known/agent-card.json` and `/.well-known/agent.json`.
  Google ADK moves with it if its a2a module needs it (see design.md).
- **Lungo local-cluster fix found on kind.** `payment-mcp-server` gets an
  explicit NATS transport and its HTTP probes disabled in
  `local-cluster/values.yaml`: the chart's empty defaults crash-looped the pod
  and the server opens no HTTP port. Not caused by SLIM 3, bundled into the
  same chart version bump.
- **BREAKING (for anyone running the demos).** SLIM nodes must run 3.x
  before or together with the clients. A stack that mixes a 2.2.0 node with
  upgraded clients, or the reverse, is unsupported. Anyone with a local
  `.env`, compose override or cluster pinned to the 2.2.0 image has to
  update it.

## Release notes input

CHANGELOG.md is written in release commits, so the items a release author
needs are listed here:

- SLIM node 3.4.6 is required with the new clients; a 2.2.0 node with upgraded
  clients, or the reverse, is unsupported. `docker compose pull`, `uv sync`
  and `make apply` are needed. Any `docker_overrides` line pinning
  `slim:2.2.0` has to move to 3.4.6.
- Corto also moves `a2a-sdk` 1.1.0 to 1.2.3, `protobuf` 6.33.5 to 7.36.2 and
  `grpcio` 1.78.0 to 1.85.1; its lock resolves `griffe` 1.15.0 (was 2.3.0).
- Helm: `slim` chart `v2.9.2` with image tag `3.4.6`; corto `local-cluster`
  0.5.0, lungo `local-cluster` 0.9.0; new `payment-mcp-server` values.
- The recruiter chart is `0.2.0`: the SLIM and NATS values and the transport
  secret are removed and `recruiterAgentUrl` is new. The recruiter card now
  advertises `RECRUITER_AGENT_URL` instead of `http://0.0.0.0:8881`, and the
  listen address comes from `RECRUITER_BIND_HOST` and `RECRUITER_PORT`.
- The lungo farm servers (Brazil, Colombia, Vietnam) serve a card copy that
  advertises `FARM_AGENT_HOST` instead of `0.0.0.0`. Charts `brazil-farm` and
  `vietnam-farm` are `0.3.0` and `colombia-farm` is `0.4.0`, each with a new
  `farmAgentHost` value.
- The recruiter drops `agntcy-app-sdk`, `slim-bindings` and SLIM/NATS
  serving, and serves A2A through `a2a-sdk` 1.2.3. **BREAKING:** its JSON-RPC endpoint
  speaks A2A v1.0 only (a v0.3 `message/send` gets "method not found") and
  its card has a single `1.0` interface and no v0.3-only fields. The lungo
  recruiter supervisor card moves to `protocol_version="1.0"` with it, so the
  `recruiter` and `recruiter-supervisor` images must be deployed together.
- The corto and lungo farm and agent cards now declare `protocol_version`
  `"1.0"` on every interface. Their served card has no v0.3-only fields
  (`url`, `protocolVersion`, `preferredTransport`); an outside v0.3 client that
  resolves such a card fails to parse it.
- The recruiter's spiffe/pyjwt compat test and the unused `buf.build` uv
  index were removed; `pyjwt` is now a floor constraint there.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

None. This is a dependency and deployment version upgrade. It adds no
requirement and changes no behavior that an existing spec describes, so the
change sets `skip_specs: true`.

## Impact

- `coffeeAGNTCY/coffee_agents/lungo` and `coffeeAGNTCY/coffee_agents/corto`:
  `pyproject.toml`, `uv.lock`, `docker-compose.yaml`,
  `deployment/helm/local-cluster/{Chart.yaml,Chart.lock,values.yaml,config-overrides.yaml.gotmpl}`,
  `tests/README.md`, and the SLIM-touching code and tests listed above.
- `coffeeAGNTCY/coffee_agents/recruiter`: `pyproject.toml`, `uv.lock`,
  `src/agent_recruiter/**`, `tests/**`, `README.md`, `.env.example`, and the
  agent-card path callers in lungo (`agents/supervisors/recruiter/main.py`).
- Repo root: `README.md` and `.github/workflows/README.md`.
- CI: the unit and integration suites run against the new image and the new
  bindings. `task helm:check-locks`, `task helm:check-version-bumps` and
  `task locks:check` gate the Helm and lock changes.
- Supply chain: the SDK and its new transitive dependencies are less than
  14 days old, which the repo's `exclude-newer = "14 days"` policy would
  block. This change adopts them on purpose, with per-package dates (see
  design.md).
