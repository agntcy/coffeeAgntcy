# Lungo Test Suite

## Scope

The suite validates:
- Auction Supervisor flows (inventory queries per farm, aggregated inventory, order creation success / failure paths, invalid prompt handling) over multiple message transports (SLIM, NATS).
- Logistics Supervisor flow (multi‑agent fulfillment: logistics-farm + accountant + shipper) currently over SLIM transport.
- Agent process orchestration, startup readiness gating, and HTTP supervisor APIs.
- Cross‑transport parity for auction flows (see TRANSPORT_MATRIX in [`test_auction.py`](coffeeAGNTCY/coffee_agents/lungo/tests/integration/test_auction.py:1)).

## Directory Layout

- Session / infra orchestration fixtures & agent/client fixtures: [`conftest.py`](coffeeAGNTCY/coffee_agents/lungo/tests/integration/conftest.py:1)
- Docker Compose lifecycle helpers (bring up transport and observability components): [`docker_helpers.py`](coffeeAGNTCY/coffee_agents/lungo/tests/integration/docker_helpers.py:1)
- Lightweight subprocess runner used for agent processes: [`process_helper.py`](coffeeAGNTCY/coffee_agents/lungo/tests/integration/process_helper.py:1)
- Auction supervisor integration tests (parametrized SLIM + NATS): [`test_auction.py`](coffeeAGNTCY/coffee_agents/lungo/tests/integration/test_auction.py:1)
- Logistics (order fulfillment) integration test (currently SLIM only): [`test_logistics.py`](coffeeAGNTCY/coffee_agents/lungo/tests/integration/test_logistics.py:1)

## Execution Prerequisites

1. Install dependencies (lungo package root):

```bash
uv sync
```

2. Configure environment:

```bash
cp coffeeAGNTCY/coffee_agents/lungo/.env.example .env
# Set LLM settings required by agents
```

3. Ensure Docker runtime is available

## Running Tests

All Lungo tests (auction + logistics):

```bash
bash
uv run pytest -s
```

Auction tests only:

```bash
uv run pytest coffeeAGNTCY/coffee_agents/lungo/tests/integration/test_auction.py -s
```

Logistics test only:

```bash
uv run pytest coffeeAGNTCY/coffee_agents/lungo/tests/integration/test_logistics.py -s
```

Single auction test (Brazil inventory over both transports):

```bash
uv run pytest coffeeAGNTCY/coffee_agents/lungo/tests/integration/test_auction.py::TestAuctionFlows::test_auction_brazil_inventory -s
```

Run only NATS parametrized cases:

```bash
uv run pytest -k NATS coffeeAGNTCY/coffee_agents/lungo/tests/integration/test_auction.py -s
```
