# Corto Test Suite

## Scope

Tests cover Exchange ↔ Farm behavior across message transports (SLIM, NATS): unit tests with mocks, docker-backed integration tests, and LLM semantic validations (local only).

## Directory layout

| Directory | Purpose | CI |
|-----------|---------|-----|
| `tests/unit/` | Mocks only | Yes |
| `tests/integration/` | Docker-compose session; no LLM | Yes |
| `tests/integration_llm/` | Docker + LLM credentials | No (local manual) |

Key files:

- Session / infra fixtures: [`integration/conftest.py`](integration/conftest.py)
- Docker Compose helpers: [`integration/docker_helpers.py`](integration/docker_helpers.py)
- Subprocess runner: [`integration/process_helper.py`](integration/process_helper.py)
- Sommelier (flavor profile) LLM tests: [`integration_llm/test_sommelier.py`](integration_llm/test_sommelier.py)

## Execution prerequisites

1. Install dependencies (corto package root):

```bash
uv sync --extra dev
```

2. For LLM tests only, configure environment:

```bash
cp coffeeAGNTCY/coffee_agents/corto/.env.example .env
# Set LLM settings required by agents
```

3. Integration and LLM suites require Docker.

## Running tests

CI-equivalent (no secrets):

```bash
uv run pytest tests/unit tests/integration -q
```

LLM suite (needs `.env`, not run in CI):

```bash
uv run pytest tests/integration_llm -q
```

Single sommelier case:

```bash
uv run pytest tests/integration_llm/test_sommelier.py::TestAuctionFlows::test_sommelier -s
```

Do not run bare `pytest` or `pytest tests/` when both `integration/` and `integration_llm/` exist — session fixtures may load twice via `pytest_plugins`.

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
