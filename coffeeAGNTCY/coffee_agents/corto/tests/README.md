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
uv sync
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
uv run pytest tests/integration/test_sommelier.py::TestAuctionFlows::test_sommelier -s
```