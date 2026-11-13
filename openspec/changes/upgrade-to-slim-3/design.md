# Design

## Context

See proposal.md for why. What the code looks like today, as observed:

- Lungo and corto each pin `agntcy-app-sdk==0.6.1` and
  `slim-bindings==2.2.0` in `pyproject.toml`, with
  `exclude-newer = "14 days"` and a `[tool.uv.exclude-newer-package]` table
  whose comments call the SDK and `slima2a` a "deliberate early adoption".
  `recruiter` is on app-sdk 0.5.5, slim-bindings 1.1.0 and a2a-sdk 0.3.x
  (see decision 7).
- The SLIM node runs from `ghcr.io/agntcy/slim:2.2.0@sha256:0d32...` in
  both `docker-compose.yaml` files, with a `server-config.yaml` under
  `config/docker/slim/`.
- Both `local-cluster` Helm charts depend on the `slim` chart `v2.2.0`.
  That chart defaults to node 2.3.0, so each `values.yaml` overrides
  `slim.slim.image.tag` to `"2.2.0"` to match the SDK.
- app-sdk 0.7.0 (checked on PyPI and its CHANGELOG) requires
  `slim-bindings==3.3.9`, `slima2a==0.9.3`, `a2a-sdk==1.2.3`,
  `ioa-observe-sdk==1.1.0`, `grpcio-tools>=1.85.1`. It names SLIM node
  3.4.6 as the tested node and says other 3.x nodes and 2.2.0 were not
  tested.
- Upload dates on PyPI: agntcy-app-sdk 0.7.0 on 2026-11-10, grpcio-tools
  1.85.1 on 2026-10-30, slim-bindings 3.3.9 on 2026-10-27, slima2a 0.9.3 and
  ioa-observe-sdk 1.1.0 on 2026-10-22, a2a-sdk 1.2.3 on 2026-10-19.
- Node images and charts on ghcr.io: the `slim` image has tags up to 3.4.6
  (3.4.6 resolves to `sha256:54fde7ce...`). The `slim` Helm chart has tags up
  to `v2.9.2`, and that chart's `appVersion` is 3.4.6. Chart tags do not
  track node versions, so there is no `v3.x` chart.
- The chart's default node config (`services.slim/0` with `dataplane`
  servers, `tls.insecure`, and a `controller` server) has the same shape as
  the repo's `server-config.yaml`, which is a first sign that the node config
  format did not change between 2.2.0 and 3.4.6. This still has to be
  confirmed by running the node.
- `SlimError` is imported from `slim_bindings` in
  `corto/exchange/errors.py` and
  `lungo/agents/supervisors/auction/graph/a2a_retry.py`, and used with
  `SlimError.SessionError` and `SlimError.Timeout` in both modules and in
  their unit tests. `lungo/tests/unit/supply_chain/test_shared_slim_connection.py`
  contains a stand-in for `slim_bindings.Service`.
- Farm and supplier cards build `AgentInterface(...)` without
  `protocol_version` (for example `corto/farm/card.py` and
  `lungo/agents/supply_chain/*/card.py`). a2a-sdk 1.2.3 logs a warning for
  that on startup and on every card request. The lungo supervisor's card
  for the recruiter (`RECRUITER_AGENT_CARD` in
  `lungo/agents/supervisors/recruiter/recruiter_service_card.py`) set
  `protocol_version="0.3"` at HEAD, and this change moves it to `"1.0"` (see
  Open Questions). The recruiter's own server card
  (`recruiter/.../server/card.py`) had no `protocol_version` at HEAD.
- Corto sets `filterwarnings = ["error"]` and lungo promotes some warnings
  to errors, so a new `DeprecationWarning` from the upgraded stack would
  fail the unit suites.

## Goals / Non-Goals

**Goals:**

- Lungo and corto run, in Docker Compose and in the local Kubernetes
  clusters, on app-sdk 0.7.0, slim-bindings 3.3.9 and SLIM node 3.4.6.
- The same node version everywhere: compose, Helm, CI overrides, docs.
- Supply-chain pins stay explicit and each exception is justified in a
  comment next to it.

**Non-Goals:**

- No change to agent behavior, topics or transports, and no change to the A2A
  protocol version except: the supervisor's recruiter card and the recruiter
  server move to A2A `"1.0"` (the server drops its v0.3 compatibility), and
  the lungo farms' HTTP JSON-RPC endpoint drops its v0.3 compatibility layer
  too (see decision 7).
- No SLIM or NATS transport for the recruiter. It is served and called over
  HTTP JSON-RPC only, as today.
- No adoption of new SLIM 3 features.
- No change to the 14-day policy itself. This change records exceptions.

## Decisions

**1. Pin node 3.4.6 exactly, everywhere.** The SDK tested only 3.4.6, so
compose and Helm use that exact version rather than "latest 3.x". Compose
keeps the digest pin the `pinned-external-references` rule needs:
`ghcr.io/agntcy/slim:3.4.6@sha256:54fde7ce...`. Alternative: follow the
newest 3.x tag. Rejected: untested against this SDK, and the pin rule wants
a fixed reference anyway.

**2. Helm: chart `v2.9.2` with an explicit image tag `"3.4.6"`.** The chart
default (`appVersion` 3.4.6) already matches, but the repo has so far set the
tag explicitly so that a chart bump cannot silently move the node. Keep that
practice and update the comment. Alternative: rely on the chart default.
Rejected: it couples the node version to a chart version that is versioned
separately. Alternative: stay on chart `v2.2.0` and only override the tag.
Rejected: the 2.2.0 chart renders the config for a 2.x node and has not been
checked against a 3.x node. The deliberate choice is to take the first chart
whose `appVersion` is 3.x and was published with the node, and `v2.9.2` is
the newest. Whether an older chart that already has `appVersion` 3.x is
better is an open question below.

**3. Per-package `exclude-newer` dates, minimal and commented.** Today's
global window is 14 days, which is 2026-10-27 as of this change. By upload
date that blocks `agntcy-app-sdk` 0.7.0 and `grpcio-tools` 1.85.1, and puts
`slim-bindings` 3.3.9 on the edge. `slima2a` 0.9.3 is older than the window
but newer than its current per-package date (2026-10-14). So:

| Package | Per-package date | Why |
|---|---|---|
| `agntcy-app-sdk` | after 2026-11-10 | 0.7.0 is the target |
| `slima2a` | on or after 2026-10-22 | 0.9.3 is what 0.7.0 pins |
| `slim-bindings` | on or after 2026-10-27 | edge of the window, would flip with the clock |
| `grpcio-tools` and `grpcio` | on or after 2026-10-30 | 1.85.1 is the SDK's floor |

The exact values are set while implementing, as the smallest dates that let
`uv lock` resolve, and each gets a comment. The dates are a ceiling for that
one package: later releases of it stay excluded until someone moves the
date. Alternative: widen the global window. Rejected: it drops the policy
for every package. Alternative: wait 14 days. Rejected: the user asked for
the upgrade now, and the exceptions are the same kind the repo already
makes for app-sdk 0.6.x.

**4. Fix what the upgrade breaks, not what it might break.** Run the unit
suites on the new stack first and change code only where something fails or
where a warning the stack now emits points at repo code. The `SlimError`
modules are the known candidates and the `protocol_version` warning is the
known warning. The set the first run produces is what the tasks cover.
Alternative: rewrite the retry helpers pre-emptively against the 3.x API.
Rejected: no evidence they are wrong, and corto and lungo carry copies of
the same logic, so a speculative change doubles the review.

**5. For the `protocol_version` warning, set it explicitly on the
interfaces the repo builds** (the value the SDK uses for interfaces it
creates, `"1.0"`). No interface the repo builds is deliberately a v0.3 one;
the only `"0.3"` left is the flat-record fallback in
`lungo/agents/supervisors/recruiter/models.py`, which describes outside
agents. Alternative: filter the warning in the
logging config. Rejected: it hides the same message for real mismatches.

**6. One change for lungo and corto, done in two steps.** They share the
decisions above and the root docs. Corto goes first because it is smaller
and proves the new stack. Lungo follows with the Helm and supply-chain
pieces that only it has. Nothing is staged or committed without the user
asking for it.

**7. Recruiter: drop app-sdk, use a2a-sdk 1.2.3 directly.** The recruiter
only uses app-sdk in `server/server.py` (serve a card over HTTP) and
`interviewers/a2a/remote_agent_connection.py` (build a JSON-RPC client).
Server: assemble a Starlette app from `create_agent_card_routes` and
`create_jsonrpc_routes(...)` (the same ten lines app-sdk's
`A2AServerConfig.build_app()` uses, without `enable_v0_3_compat`) and run it
with uvicorn.
Client: `a2a.client` `ClientFactory` and `ClientConfig`. The 0.3.x server
served the card at both `/.well-known/agent-card.json` and
`/.well-known/agent.json`; the 1.x route factory serves one path, so the
recruiter mounts the card routes twice (second one with
`card_url="/.well-known/agent.json"`) and no caller has to change. The
recruiter drops `slim-bindings` and every transitive dependency only
app-sdk needed. Google ADK 2.8.0 needed no bump: its `to_a2a` works with a2a-sdk 1.2.3 (checked
end to end with a fake LLM), and the recruiter's only use of `google.adk.a2a`
is the test sample agent. With app-sdk gone, the spiffe cap on `pyjwt` is
gone too, so the `pyjwt` override became a floor constraint and the spiffe
compat test was deleted. The unused `buf.build` uv index was dropped. The
recruiter card gained one `AgentSkill` because a2a-sdk 1.2.3 warns on empty
skills, and interfaces declare `protocol_version="1.0"`. Alternative: migrate to app-sdk 0.7.0.
Rejected: it keeps a SLIM stack the recruiter does not use. Alternative:
leave the recruiter on a2a 0.3. Rejected: the user asked to upgrade it, and
lungo's supervisor now talks to it in v1.0.

The recruiter server speaks A2A v1.0 only: its card lists one JSON-RPC
interface at `1.0`, and `enable_v0_3_compat` is off, so a v0.3 `message/send`
gets "method not found" and the served card has no v0.3-only fields (`url`,
`protocolVersion`, `preferredTransport`). The only caller of its JSON-RPC
endpoint in this repo is the lungo recruiter supervisor, which moved to
`"1.0"` in the same change. Alternative: keep a second `0.3` interface and
the compat routes for outside v0.3 clients. Rejected: nothing in the repo needs
them, and the user asked for the server on 1.0. The recruiter's evaluator
client still speaks v0.3 to agents that declare it or declare nothing (outside
agents), and its tests use a v0.3-compat stand-in app for that.

The lungo farms (Brazil, Colombia, Vietnam) also dropped
`enable_v0_3_compat`, which #846 had switched on as a migration aid. Their
HTTP JSON-RPC endpoint is now A2A v1.0 only, like the recruiter's, and nothing
in the repo calls it with v0.3 once the recruiter image is rebuilt. Rollout
consequence: the recruiter image published before this change is an a2a 0.3
client, so it cannot evaluate the new farms over HTTP until the recruiter
image is republished from the same release.

The recruiter has no SLIM or NATS code, so the settings that configured them
are gone: the lungo compose `recruiter` service no longer passes the transport,
SLIM and NATS variables, and the recruiter Helm chart (0.1.2 to 0.2.0) lost the
`defaultMessageTransport`, `transportServerEndpoint`, `slimServer`, `natsServer`
and `slimSharedSecret` values, the transport secret template and the matching
`secretRef`. The local-cluster overlay stopped merging `$nats.config` into the
recruiter and no longer asks for `SLIM_SHARED_SECRET` for it.

The card used to advertise the bind address `http://0.0.0.0:8881`, which no
other container can dial, and `server.py` derived its listen address from that
same URL. The two are now separate: the card URL comes from
`RECRUITER_AGENT_URL` (default `http://localhost:8881`; compose and the
local-cluster overlay set `http://recruiter:8881`), and the server listens on
`RECRUITER_BIND_HOST` (default `0.0.0.0`) and `RECRUITER_PORT` (default
`8881`). Both card interfaces use the same URL. An empty `RECRUITER_AGENT_URL`
(what the chart renders when `recruiterAgentUrl` is unset) falls back to the
default. At startup the server refuses a wildcard advertised host (exit code 1)
and warns about a loopback host inside a container or pod.

The lungo farm cards (Brazil, Colombia, Vietnam) keep `http://0.0.0.0:<port>`
in the module card because the app SDK binds the HTTP server to the host and
port of the card's JSON-RPC interface (`card_bootstrap`), so that URL is the
bind address. The copy of the card that the farm server hands to the SDK's
`jsonrpc` override (the one served to clients) has the wildcard host replaced
by `FARM_AGENT_HOST` through `common/card_public_url.py`; `FARM_AGENT_HOST`
(already set by compose, newly read by lungo code) defaults to `localhost`, the
farm Helm charts take `config.farmAgentHost`, and the local-cluster overlay
sets it to the chart name. The same two guards apply: a wildcard
`FARM_AGENT_HOST` stops the farm, a loopback one inside a container warns.
Directory records already published still say `0.0.0.0`, so the supervisor's
`_UNROUTABLE_ADVERTISED_HOSTS` rewrite stays. The logistics and supply-chain
cards have no HTTP interface, and corto's farm card already used
`FARM_AGENT_HOST`.

## Risks / Trade-offs

- [The a2a 0.3 to 1.x port is large (protobuf types, `Part` oneof, no
  `card.url`, `Message.metadata` as `Struct`)] → Port module by module with
  the unit suite as the check, reuse the helper style from lungo's
  `common/a2a_helpers.py`, and run the recruiter integration tests.
- [The supervisor dials the recruiter at v1.0 and the server no longer answers
  v0.3, so any v0.3 client of the recruiter, and any supervisor image built
  before this change, fails against it] → Verify against lungo's recruiter
  supervisor with a real request, not only unit tests, and roll the two
  images out together.

- [The SDK and its new transitive dependencies are days old] → Keep the
  exceptions per package and commented, review the lock diff, and let the
  existing renovate and lock checks run. The exceptions expire when someone
  next moves the dates.
- [A 3.4.6 node with the 2.2.0-era `server-config.yaml` may not start or may
  behave differently] → Run the node from the new image with each existing
  config as the first implementation task, before any other change, and
  look at its log. The chart default config having the same shape lowers
  the risk but does not remove it.
- [slim-bindings 3.x changes `SlimError` or the `Service` API the repo's
  retry helpers and one test rely on] → The unit suites are the check;
  tasks cover fixing what they report.
- [`filterwarnings = ["error"]` turns a new warning into a failing suite] →
  Same approach: run the suites first, fix at the source, and do not add
  blanket ignores. Any `ignore` entry that is unavoidable names the exact
  message and carries a comment.
- [Mixed versions during rollout: a developer with a cached 2.2.0 image, or
  a CI override still pointing at 2.2.0] → The docs name 3.4.6 as the only
  supported node, and the `docker_overrides` examples are updated.
  `compose pull` is part of the migration notes.
- [The Helm chart jumps from `v2.2.0` to `v2.9.2`, which is more than the
  node change needs] → Render both charts' values with the repo's overrides
  and compare before and after, and confirm in a local cluster that the
  node pod starts and a client connects.

## Migration Plan

1. Land the change on the branch, corto first, then lungo.
2. For a developer: pull the branch, run `docker compose pull` (or
   `docker compose up --build`), run `uv sync` in each project, and for the
   local cluster rerun `make apply` so the new chart and image roll out.
   Nothing in `.env` needs to change.
3. For CI or external callers of the reusable `test.yaml` workflow: any
   `docker_overrides` line that pins the SLIM image to 2.2.0 has to move to
   3.4.6 or be removed.
4. Rollback is a revert of the branch. The 2.2.0 node and the 0.6.1 SDK are
   a matched pair, so they must be reverted together.

## Open Questions

- Is a Helm chart older than `v2.9.2` that already has `appVersion` 3.x
  preferable to the newest one? Checking chart tags between `v2.2.0` and
  `v2.9.2` does not change the specs or the task breakdown, so it can be
  answered during task 3.1.
- Rollout order for `RECRUITER_AGENT_CARD` (now `protocol_version="1.0"`,
  decided in this change). The published `:latest` recruiter image is still
  the old a2a 0.3 server and the recruiter chart pulls `:latest`, so a
  supervisor image built from this change fails against it until the
  recruiter image built from this change is deployed. Publish and roll out
  the `recruiter` and `recruiter-supervisor` images together. In Docker
  Compose, `docker compose up --build` builds both from this branch.
- `_restore_known_ints` in `recruiter_client.py` stays. Moving to `"1.0"` does
  not remove the need for it: a data part is a protobuf `Struct`, and the
  JSON-RPC body carries `10201.0` over v1.0 and v0.3 alike (checked against
  the in-process recruiter app with both client versions).
