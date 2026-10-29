# Lungo Test Suite

## Scope

The suite validates:

- Auction Supervisor flows (inventory, orders, invalid prompts) over SLIM and NATS: LLM cases in `tests/integration/llm/`, docker-only checks in `tests/integration/`.
- Logistics Supervisor (farm, accountant, shipper, helpdesk): health in `tests/integration/`, prompt flows in `tests/integration/llm/`.
- Supply Chain Commitment (Buyer, three suppliers, Logistics): health in `tests/integration/`, baseline runs against the real model in `tests/integration/llm/`. The L9 cases there are skipped until the L9 bridge is built.
- Agentic Workflows API (unit), subprocess uvicorn/SSE live tests (`tests/integration/live/`).
- Agent process orchestration, startup readiness gating, and HTTP supervisor APIs.

## Directory layout

| Directory | Purpose |
|-----------|---------|
| `tests/unit/` | Mocks only |
| `tests/integration/` | Docker-compose session; no live webserver; no LLM |
| `tests/integration/live/` | Subprocess uvicorn/A2A HTTP; no LLM |
| `tests/integration/llm/` | Docker + LLM credentials (needs `.env`) |
| `tests/integration/helpers/` | Docker/process helpers (not collected as tests) |

<!-- alphabetize-exempt: directories follow the test-tree hierarchy (parent before children) -->

Key files:

- Session / infra fixtures: [`tests/integration/conftest.py`](integration/conftest.py)
- Docker Compose helpers: [`tests/integration/helpers/docker_helpers.py`](integration/helpers/docker_helpers.py)
- Subprocess runner: [`tests/integration/helpers/process_helper.py`](integration/helpers/process_helper.py)
- Auction docker-only tests: [`tests/integration/test_auction.py`](integration/test_auction.py)
- Auction LLM flows (parametrized SLIM + NATS): [`tests/integration/llm/test_auction_flows.py`](integration/llm/test_auction_flows.py)
- Logistics health (SLIM): [`tests/integration/test_logistics_supervisor.py`](integration/test_logistics_supervisor.py)
- Logistics LLM flows: [`tests/integration/llm/test_logistics_supervisor_flows.py`](integration/llm/test_logistics_supervisor_flows.py)
- Supply Chain Commitment health (SLIM): [`tests/integration/test_supply_chain_health.py`](integration/test_supply_chain_health.py)
- Supply Chain Commitment LLM flows: [`tests/integration/llm/test_supply_chain_flows.py`](integration/llm/test_supply_chain_flows.py)
- Uvicorn/SSE helpers: [`tests/helpers/agentic_uvicorn_helpers.py`](helpers/agentic_uvicorn_helpers.py)
- Live workflow-instance pipeline: [`tests/integration/live/test_workflow_instance_live_pipeline.py`](integration/live/test_workflow_instance_live_pipeline.py)

## Execution prerequisites

1. Install dependencies (lungo package root):

```bash
uv sync --extra dev
```

   The `dev` extra is required: it installs `httpx2`, without which starlette's
   `TestClient` raises a deprecation warning that pytest turns into an error
   (`filterwarnings = ["error"]`). Plain `uv run pytest` keeps the extra once this
   step has run; in a fresh environment, skip the step by passing it explicitly
   (`uv run --extra dev pytest ...`).

2. For LLM tests only, configure environment:

```bash
cp coffeeAGNTCY/coffee_agents/lungo/.env.example .env
# Set LLM settings required by agents
```

3. Integration and LLM suites require Docker.

## Running tests

From the lungo package root:

```bash
uv run pytest -q
```

Run a subset by directory:

```bash
uv run pytest tests --ignore=tests/integration/llm -q
uv run pytest tests/integration/llm -q   # needs LLM settings in .env
```

LLM proxy chat smoke test: `tests/integration/llm/test_pattern_chat_proxy.py` (skipped unless `LITELLM_PROXY_*` env vars are set).

### Targeted runs

Docker-only auction tests:

```bash
uv run pytest tests/integration/test_auction.py -q
```

LLM auction flows (both transports):

```bash
uv run pytest tests/integration/llm/test_auction_flows.py -q
```

Single LLM auction case (Brazil inventory):

```bash
uv run pytest tests/integration/llm/test_auction_flows.py::TestAuctionFlows::test_auction_brazil_inventory -q
```

Logistics docker health:

```bash
uv run pytest tests/integration/test_logistics_supervisor.py -q
```

Logistics agent roles:

```bash
uv run pytest tests/integration/test_logistics_farm.py tests/integration/test_logistics_accountant.py tests/integration/test_logistics_shipper.py tests/integration/test_logistics_helpdesk.py -q
```

Supply Chain Commitment health, and one baseline run per case:

```bash
uv run pytest tests/integration/test_supply_chain_health.py -q
uv run pytest tests/integration/llm/test_supply_chain_flows.py -q
```

The flow test sends about 20 to 40 calls per run to the configured model and
never asserts PASS: a baseline run may fail silently, which is the finding. It
asserts a record, a verdict, and that every step's addressees replied exactly
once. The Buyer runs in-process with L9 off and writes its run files to a
temporary directory, so `runs/supply_chain/` is untouched.

The grading is deterministic and covered by unit tests with hand-built records
(`tests/unit/supply_chain/test_checker.py`). The model runs are not, which is why
the flow test never asserts a verdict. How the checker decides is in
[How a run is judged to have failed](../docs/supply_chain_commitment.md#how-a-run-is-judged-to-have-failed).

The session fixture runs `docker compose down -v --remove-orphans` for the
compose project when pytest starts and again when it exits, including on
`--collect-only`. To keep a running development stack, run the integration
tests under another project name, for example
`COMPOSE_PROJECT_NAME=lungo-it uv run pytest tests/integration/test_supply_chain_health.py -q`.

Live uvicorn/SSE:

```bash
uv run pytest tests/integration/live -q
```

Run only NATS parametrized LLM cases:

```bash
uv run pytest tests/integration/llm/test_auction_flows.py -k NATS -q
```

## Version overrides

CoffeeAGNTCY serves as a reference environment for multiple integrated components. To support continuous compatibility testing and faster integration validation, we've added functionality that allows remote triggering of CI pipelines with version overrides.

The reusable test workflow [`test.yaml`](../../../../.github/workflows/test.yaml) accepts three optional multiline inputs to test new dependency or container image versions **without changing the repo**:

- `pip_overrides` (exact PEP 508 specs, one per line)
- `pip_constraints` (constraint lines)
- `docker_overrides` (service=image[:tag] mappings applied to the demo docker-compose)

A line applies to every demo that declares the service (compose) or package (`pyproject.toml`). Prefix a line with `<project>:` (`corto`, `lungo`, `recruiter`) to apply it to one demo only, for example when demos are on different SLIM major versions.

Minimal invocation pattern:

```yaml
name: Custom Integration
on:
  workflow_dispatch: {}
jobs:
  integration:
    uses: agntcy/coffeeAgntcy/.github/workflows/test.yaml@<ref>
    with:
      pip_overrides: |
        httpx==0.27.2
      pip_constraints: |
        grpcio<1.65
      docker_overrides: |
        lungo:slim=ghcr.io/agntcy/slim:2.2.0
```
