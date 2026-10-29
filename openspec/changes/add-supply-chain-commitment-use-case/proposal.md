# Proposal

## Why

The Supply Chain Commitment use case (`cisco-eti/ioc-app-mas-patterns-implementations`,
pinned at `238e99d`) predicts that LLM agents from different organizations
can agree on a shipment plan that is wrong or infeasible, for example when
each party means something different by "delivery". The use case lists four
assumed cognitive failures: `DR-1`, `CE-1`, `IE-1` and `CC-4`. No
implementation exists to test whether they occur, nor whether the L9 ACCORD
and CONCORD protocols (`cisco-eti/ioc-core-l9-skills`, pinned at `948730e`)
prevent them.

This change adds the use case to Lungo so that we can run it, observe the
outcome, and compare a plain group negotiation against an L9-structured one.

The purpose is to show, on purpose and repeatably, a **silent cognitive
failure** between agents: every message is delivered, every agent agrees,
nothing looks wrong to the agents, and the commitment is still wrong. The
first scenario (case `ambiguous`) runs without ACCORD and CONCORD to show
that failure. The failure is the aim, not an outcome to wait for: the
four failures from the use case are only assumptions, so each example is
first tried, and where the baseline does not fail silently the example is
**refined until it does**. The refinement is done on the baseline alone,
every step is logged, and the refined scenario is then frozen. Only that
proves what ACCORD and CONCORD are worth, because a protocol cannot be shown
to help against a failure that never happens. The frozen scenario then runs
with them, to see whether they prevent the failure. Prevention is the
hypothesis, not a promise: if the protocols do not prevent it, that is
reported as the result. Runs are counted, not picked. Scoping decisions are
recorded in
`coffeeAGNTCY/coffee_agents/lungo/docs/supply_chain_commitment_decisions.md`.

## What Changes

- **New Lungo workflow "Supply Chain Commitment".** It is pattern `Secure
  Group Collaboration` in the "Multi-Agent Communication & Collaboration"
  category, with use case "Coffee Agntcy" and scenario "Supply Chain
  Commitment". Its graph mirrors Group Messaging: one negotiation group
  containing the Buyer, Supplier A, Supplier B, Supplier C and Logistics,
  joined through the A2A SLIM transport. The deterministic checker and the
  commitment record are not graph nodes.
- **Five LLM agents.** Each holds only its own scenario data and negotiates
  over a SLIM group channel. The Buyer is the supervisor that exposes the chat
  API.
- **Four scenario cases from synthetic fixtures.** The cases are ambiguous
  language, explicit language, infeasible (expedited transport unavailable),
  and disruption after commitment.
- **Negotiation configurations, selectable per run.**
  - `baseline`: plain group negotiation.
  - `l9_hybrid`: the Buyer's code runs the vendored ACCORD and CONCORD
    initiator scripts and relays their messages unchanged. Every agent's LLM
    produces the protocol content as a receiver.
  - `l9_full`: reserved as an interface. The LLMs drive the skills
    themselves. It is declared but returns "not implemented" until a
    follow-up change.
- **Keeping ACCORD and CONCORD out of the failing run.** The per-run
  `configuration` is the main control: in a `baseline` run no L9 message
  exists, so no skill text or tool ever reaches a model. A deployment switch,
  `SUPPLY_CHAIN_L9_ENABLED` (default off), sits above it. When it is off,
  every agent refuses L9 messages, never reads the skills directory and never
  creates the forge tool, and the Buyer rejects `l9_hybrid`. Each run records
  whether L9 was available.
- **Suggested prompts that follow the switch.** The chat offers one request
  for each of the four assumed failures (`DR-1`, `CE-1`, `IE-1`, `CC-4`) and
  each run type, written as an order a person would give, for example "I'd
  like to have a 1,000-tonne coffee shipment delivered by November 18, with
  total transport cost at or below $20,000 (ambiguous/baseline)". The closing
  tag `(<case>/<run type>)` sets the case and the configuration with a fixed
  rule. When `SUPPLY_CHAIN_L9_ENABLED` is off, only the 4 `baseline` prompts
  are offered. When it is on, the 12 prompts cover `baseline`, `L9 hybrid`
  and `L9 full`, and each L9 prompt sets its configuration through its tag.
  The prompts and the run-type differences are in
  `coffeeAGNTCY/coffee_agents/lungo/docs/supply_chain_suggested_prompts.md`.
- **Structured commitment record and checker.** Every run produces a
  commitment record. A deterministic checker evaluates it against the
  fixtures after the run, in the background of the run, and never sends
  anything to the agents. The verdict and the record are streamed to the chat
  feed and saved with the run's transcript. The checker is not a graph node.
  - The verdict is `PASS`, `FAIL` or `INVALID`. `INVALID` marks a run that
    ended by `timeout` or `protocol_error`, so an outage is not counted as a
    cognitive failure.
  - A run is flagged `silent` when the process was clean, the plan was
    committed, all five parties confirmed it, nobody rejected anything, and
    the verdict is `FAIL`.
- **Paired demo.** The headline result is one pair, `ambiguous` with
  `baseline` against `ambiguous` with `l9_hybrid`, on the same model. The
  baseline is probed against the real model before the L9 bridge is built,
  because the demo depends on the failure actually occurring.
- **Vendored skills.** A pinned, unmodified snapshot of the four L9 skills is
  added under `coffeeAGNTCY/coffee_agents/lungo/third_party/l9_skills/`,
  with a provenance note. The work stays local and is not pushed, because
  the upstream repo is private and has no licence file.
- **Frontend.**
  - A new `chat_api_target` value, `supply_chain`, and its base URL setting.
  - A generalized group streaming feed that renders the negotiation events,
    the record and the verdict.
  - The group node's directory slug is no longer hardcoded to logistics.
- **Deployment.** A Docker Compose profile `supply_chain`, Makefile targets,
  Helm charts (`supply-chain-buyer`, `supply-chain-supplier` deployed three
  times, `supply-chain-logistics`), `local-cluster` wiring, CI image builds
  and chart push.
- **Repo tooling.** `task dashes:check` and `task dashes:fix` exclude the
  vendored skills directory, so the third-party text stays identical to
  upstream.

## Capabilities

### New Capabilities
- `supply-chain-commitment`: the Lungo Supply Chain Commitment workflow. It
  covers the agents and their information boundaries, the scenario cases,
  the negotiation configurations, the commitment record, the deterministic
  checker, the streamed feed, the catalog entry and the graph.

### Modified Capabilities
- `agent-workflow-api-config`: the new Buyer chart is a workflow-calling
  agent chart and gains the `workflowApiUrl` and `workflowApiKey` values.
  The supplier and logistics charts are added to the list of charts that
  never call the API.
- `repo-tooling`: the dash check and the dash fix skip the vendored
  third-party skills directory.

## Impact

- **Backend (`coffeeAGNTCY/coffee_agents/lungo`).**
  - New packages: `agents/supervisors/supply_chain/` and
    `agents/supply_chain/`.
  - New fixtures, checker and vendored `third_party/l9_skills/`.
  - Catalog updates: `api/agentic_workflows/starting_workflows.json`,
    `catalog_types.py`, `transport_ui_enrichment.py` and `patterns.py`.
  - OpenAPI enum in `schema/openapi/components/schemas.yaml`.
- **Frontend (`lungo/frontend`).**
  - The generated OpenAPI types and the `chat_api_target` union and
    parsers.
  - `urls.ts`, `.env.example`, `vite-env.d.ts`, the group streaming store
    and feed, the topology identity map, the slug and icon heuristics, and
    the sidebar SLIM set.
- **Deployment.**
  - `docker-compose.yaml`, `.env.example` and `Makefile`.
  - Three new Helm charts, plus `local-cluster` (`Chart.yaml`,
    `Chart.lock`, values, overrides and a kind NodePort for 30085) and the
    UI chart values.
  - The CI workflows `docker-build-push.yaml` and `helm-push.yaml`, and
    `scripts/push_oasf_records.sh`.
- **Tooling.** `scripts/checks/check_dashes.bash`,
  `scripts/checks/fix_dashes.bash` and their bats tests.
- **Dependencies.** None new. The vendored scripts use only the Python
  standard library and run as subprocesses with argument lists, never
  through a shell.
- **Cost and runtime.** Every run makes many LLM calls, roughly five agents
  times several phases. The L9 runs make more calls than the baseline.
- **Docs.**
  - Lungo `README.md`, a new `docs/supply_chain_commitment.md`, a new
    `docs/supply_chain_suggested_prompts.md` (run types and prompts) and a
    workflow doc under `api/agentic_workflows/docs/workflows/`.
  - `docs/workflow-instance_api.md`, the frontend env docs,
    `docs/TERMINOLOGY.md`, `CHANGELOG.md` and `tests/README.md`.
