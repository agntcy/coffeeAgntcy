# Corto Test Suite

## Scope

Current tests are end‑to‑end semantic behavior validations for the Exchange ↔ Farm flow across multiple message transports (SLIM, NATS).

## Directory Layout

- Session / infra orchestration fixtures & agent/client fixtures: [`conftest.py`](coffeeAGNTCY/coffee_agents/corto/tests/integration/conftest.py:1)
- Docker Compose lifecycle helpers (bring up transport and observability components): [`docker_helpers.py`](coffeeAGNTCY/coffee_agents/corto/tests/integration/docker_helpers.py:1)
- Lightweight subprocess runner used for agent processes: [`process_helper.py`](coffeeAGNTCY/coffee_agents/corto/tests/integration/process_helper.py:13)
- Sommelier (flavor profile) integration test: [`test_sommelier.py`](coffeeAGNTCY/coffee_agents/corto/tests/integration/test_sommelier.py:1)

## Execution Prerequisites

1. Install dependencies (corto package root):

```bash
uv sync --extra dev
```

2. Configure environment:

```bash
cp coffeeAGNTCY/coffee_agents/corto/.env.example .env
# Set LLM settings required by agents
```

3. Ensure Docker runtime is available

## Running Tests

All Corto tests:

```bash
uv run pytest -s
```

Single test:

```bash
uv run pytest integration/test_sommelier.py::TestAuctionFlows::test_sommelier -s
```

## Version Overrides
CoffeeAGNTCY serves as a reference environment for multiple integrated components. To support continuous compatibility testing and faster integration validation, we've added functionality that allows remote triggering of CI pipelines with version overrides.

The reusable integration test workflow [`test.yaml`](.github/workflows/test.yaml:1) accepts three optional multiline inputs to test new dependency or container image versions **without changing the repo**:
- `pip_overrides` (exact PEP 508 specs, one per line)
- `pip_constraints` (constraint lines)
- `docker_overrides` (service=image[:tag] mappings applied to the demo docker-compose)

An example caller is provided in [`version-override-test.yaml`](.github/workflows/version-override-test.yaml:1). Trigger it (Workflow Dispatch) or via UI.

Minimal invocation pattern:

```yaml
name: Custom Integration
on:
  workflow_dispatch: {}
jobs:
  integration:
    uses: agntcy/coffeeAgntcy/.github/workflows/test.yaml@integration-hook
    secrets: inherit
    with:
      pip_overrides: |
        httpx==0.27.2
      pip_constraints: |
        grpcio&lt;1.65
      docker_overrides: |
        slim=ghcr.io/agntcy/slim:0.5.0
```