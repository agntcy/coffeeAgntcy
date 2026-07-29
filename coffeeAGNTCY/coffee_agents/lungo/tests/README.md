# Lungo Test Suite

## Scope

The suite validates:

- Auction Supervisor flows (inventory, orders, invalid prompts) over SLIM and NATS — LLM cases in `tests/integration/llm/`, docker-only checks in `tests/integration/general/`.
- Logistics Supervisor (farm, accountant, shipper, helpdesk) — health in `tests/integration/general/`, prompt flows in `tests/integration/llm/`.
- Agentic Workflows API (unit), subprocess uvicorn/SSE live tests (`tests/integration/live/`).
- Agent process orchestration, startup readiness gating, and HTTP supervisor APIs.

## Directory layout

| Directory | Purpose |
|-----------|---------|
| `tests/unit/` | Mocks only |
| `tests/integration/general/` | Docker-compose session; no live webserver; no LLM |
| `tests/integration/live/` | Subprocess uvicorn/A2A HTTP; no LLM |
| `tests/integration/llm/` | Docker + LLM credentials (needs `.env`) |
| `tests/integration/helpers/` | Docker/process helpers (not collected as tests) |

Key files:

- Session / infra fixtures: [`tests/integration/conftest.py`](integration/conftest.py)
- Docker Compose helpers: [`tests/integration/helpers/docker_helpers.py`](integration/helpers/docker_helpers.py)
- Subprocess runner: [`tests/integration/helpers/process_helper.py`](integration/helpers/process_helper.py)
- Auction docker-only tests: [`tests/integration/general/test_auction.py`](integration/general/test_auction.py)
- Auction LLM flows (parametrized SLIM + NATS): [`tests/integration/llm/test_auction_flows.py`](integration/llm/test_auction_flows.py)
- Logistics health (SLIM): [`tests/integration/general/test_logistics_supervisor.py`](integration/general/test_logistics_supervisor.py)
- Logistics LLM flows: [`tests/integration/llm/test_logistics_supervisor_flows.py`](integration/llm/test_logistics_supervisor_flows.py)
- Uvicorn/SSE helpers: [`tests/helpers/agentic_uvicorn_helpers.py`](helpers/agentic_uvicorn_helpers.py)
- Live workflow-instance pipeline: [`tests/integration/live/test_workflow_instance_live_pipeline.py`](integration/live/test_workflow_instance_live_pipeline.py)

## Execution prerequisites

1. Install dependencies (lungo package root):

```bash
uv sync --extra dev
```

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
uv run pytest tests/unit -q
uv run pytest tests/integration/general -q
uv run pytest tests/integration/live -q
uv run pytest tests/integration/llm -q   # needs LLM settings in .env
```

LLM proxy chat smoke test: `tests/integration/llm/test_pattern_chat_proxy.py` (skipped unless `LITELLM_PROXY_*` env vars are set).

### Targeted runs

Docker-only auction tests:

```bash
uv run pytest tests/integration/general/test_auction.py -q
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
uv run pytest tests/integration/general/test_logistics_supervisor.py -q
```

Logistics agent roles:

```bash
uv run pytest tests/integration/general/test_logistics_farm.py tests/integration/general/test_logistics_accountant.py tests/integration/general/test_logistics_shipper.py tests/integration/general/test_logistics_helpdesk.py -q
```

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

An example caller is provided in [`version-override-test.yaml`](../../../../.github/workflows/version-override-test.yaml). Trigger it (Workflow Dispatch) or via UI.

Minimal invocation pattern:

```yaml
name: Custom Integration
on:
  workflow_dispatch: {}
jobs:
  integration:
    uses: agntcy/coffeeAgntcy/.github/workflows/test.yaml@integration-hook
    with:
      pip_overrides: |
        httpx==0.27.2
      pip_constraints: |
        grpcio<1.65
      docker_overrides: |
        slim=ghcr.io/agntcy/slim:1.4.0
```
