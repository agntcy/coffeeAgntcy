# Lungo Test Suite

## Scope

The suite validates:

- Auction Supervisor flows (inventory, orders, invalid prompts) over SLIM and NATS — LLM cases in `integration_llm/`, docker-only checks in `integration/`.
- Logistics Supervisor (farm, accountant, shipper, helpdesk) — health in `integration/`, prompt flows in `integration_llm/`.
- Agentic Workflows API (unit), subprocess uvicorn/SSE live tests (`tests/live/`).
- Agent process orchestration, startup readiness gating, and HTTP supervisor APIs.

## Directory layout

| Directory | Purpose | CI |
|-----------|---------|-----|
| `tests/unit/` | Mocks only | Yes |
| `tests/live/` | Subprocess uvicorn/A2A HTTP | Yes |
| `tests/integration/` | Docker-compose session; no LLM | Yes |
| `tests/integration_llm/` | Docker + LLM credentials | No (local manual) |

Key files:

- Session / infra fixtures: [`integration/conftest.py`](integration/conftest.py)
- Docker Compose helpers: [`integration/docker_helpers.py`](integration/docker_helpers.py)
- Subprocess runner: [`integration/process_helper.py`](integration/process_helper.py)
- Auction docker-only tests: [`integration/test_auction.py`](integration/test_auction.py)
- Auction LLM flows (parametrized SLIM + NATS): [`integration_llm/test_auction_flows.py`](integration_llm/test_auction_flows.py)
- Logistics health (SLIM): [`integration/test_logistics_supervisor.py`](integration/test_logistics_supervisor.py)
- Logistics LLM flows: [`integration_llm/test_logistics_supervisor_flows.py`](integration_llm/test_logistics_supervisor_flows.py)
- Uvicorn/SSE helpers: [`helpers/agentic_uvicorn_helpers.py`](helpers/agentic_uvicorn_helpers.py)
- Live workflow-instance pipeline: [`live/test_workflow_instance_live_pipeline.py`](live/test_workflow_instance_live_pipeline.py)

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

### CI and local suites (directories)

| Suite | Paths | CI | Secrets |
|-------|-------|-----|---------|
| **no-secrets** | `tests/unit`, `tests/live`, `tests/integration` | Yes | No (`WORKFLOW_API_KEY` env in CI for live tests) |
| **LLM** | `tests/integration_llm` | No (local manual) | Yes (`.env`) |

From the lungo package root:

```bash
uv run pytest tests/unit tests/live tests/integration -q   # CI-equivalent
uv run pytest tests/integration_llm -q                       # LLM (needs .env)
```

LLM proxy chat smoke test: `tests/integration_llm/test_pattern_chat_proxy.py` (skipped unless `LITELLM_PROXY_*` env vars are set).

Do not run bare `pytest` or `pytest tests/` when both `integration/` and `integration_llm/` exist — session fixtures may load twice via `pytest_plugins`.

### Targeted runs

Docker-only auction tests:

```bash
uv run pytest tests/integration/test_auction.py -q
```

LLM auction flows (both transports):

```bash
uv run pytest tests/integration_llm/test_auction_flows.py -q
```

Single LLM auction case (Brazil inventory):

```bash
uv run pytest tests/integration_llm/test_auction_flows.py::TestAuctionFlows::test_auction_brazil_inventory -q
```

Logistics docker health:

```bash
uv run pytest tests/integration/test_logistics_supervisor.py -q
```

Logistics agent roles:

```bash
uv run pytest tests/integration/test_logistics_farm.py tests/integration/test_logistics_accountant.py tests/integration/test_logistics_shipper.py tests/integration/test_logistics_helpdesk.py -q
```

Live uvicorn/SSE:

```bash
uv run pytest tests/live -q
```

Run only NATS parametrized LLM cases:

```bash
uv run pytest tests/integration_llm/test_auction_flows.py -k NATS -q
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
