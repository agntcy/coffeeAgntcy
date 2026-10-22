# Corto Test Suite

## Scope

Tests cover Exchange ↔ Farm behavior across message transports (SLIM, NATS): unit tests with mocks, docker-backed integration tests, and LLM semantic validations.

## Directory layout

| Directory | Purpose |
|-----------|---------|
| `tests/unit/` | Mocks only |
| `tests/integration/` | Docker-compose session; no live webserver; no LLM |
| `tests/integration/llm/` | Docker + LLM credentials (needs `.env`) |
| `tests/integration/helpers/` | Docker/process helpers (not collected as tests) |

<!-- alphabetize-exempt: directories follow the test-tree hierarchy (parent before children) -->

Key files:

- Session / infra fixtures: [`tests/integration/conftest.py`](integration/conftest.py)
- Docker Compose helpers: [`tests/integration/helpers/docker_helpers.py`](integration/helpers/docker_helpers.py)
- Subprocess runner: [`tests/integration/helpers/process_helper.py`](integration/helpers/process_helper.py)
- Sommelier (flavor profile) LLM tests: [`tests/integration/llm/test_sommelier.py`](integration/llm/test_sommelier.py)

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

From the corto package root:

```bash
uv run pytest -q
```

Run a subset by directory:

```bash
uv run pytest tests --ignore=tests/integration/llm -q
uv run pytest tests/integration/llm -q   # needs LLM settings in .env
```

Single sommelier case:

```bash
uv run pytest tests/integration/llm/test_sommelier.py::TestAuctionFlows::test_sommelier -s
```

## Version overrides

CoffeeAGNTCY serves as a reference environment for multiple integrated components. To support continuous compatibility testing and faster integration validation, we've added functionality that allows remote triggering of CI pipelines with version overrides.

The reusable test workflow [`test.yaml`](../../../../.github/workflows/test.yaml) accepts three optional multiline inputs to test new dependency or container image versions **without changing the repo**:

- `pip_overrides` (exact PEP 508 specs, one per line)
- `pip_constraints` (constraint lines)
- `docker_overrides` (service=image[:tag] mappings applied to the demo docker-compose)

A line applies to every demo that declares the service (compose) or package (`pyproject.toml`). Prefix a line with `<project>:` (`corto`, `lungo`, `recruiter`) to apply it to one demo only. Each demo runs its own SLIM server, so scope SLIM overrides per demo.

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
        corto:slim=ghcr.io/agntcy/slim:2.2.0
        lungo:slim=ghcr.io/agntcy/slim:2.2.0
```
