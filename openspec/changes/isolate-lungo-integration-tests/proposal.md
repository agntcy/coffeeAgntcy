# Proposal

## Why

The lungo integration suite cannot run while a developer's lungo stack is
up. It publishes SLIM, NATS and the OTel collector on the same fixed host
ports as `docker-compose.yaml` (46357, 4222, 4318), starts every local agent
on the same fixed ports as the stack's containers (9090 to 9099, 9997 to
9999), and uses the default Compose project `lungo`. Its session setup also
runs `docker compose down -v --remove-orphans` for that project and
force-removes `lungo-slim`, `lungo-nats`, `lungo-otel-collector`,
`lungo-clickhouse-server` and `grafana-lungo` by name, so starting the
suite tears down the developer's stack and deletes its volumes. CI never
notices, because every runner is a clean machine.

The workaround in `tests/README.md` (`COMPOSE_PROJECT_NAME=lungo-it`) does
not work: the 29 fixed `container_name` entries in `docker-compose.yaml`
and the fixed host ports still collide. Current practice is the opposite
of what the suite does: tests use dynamic host ports and a project name
of their own, and tear down only what they started.

## What Changes

- **A per-run Compose project.** The session fixture starts its
  infrastructure under a generated project name (`lungo-it-<suffix>`) and
  `down -v` removes only that project. The force-removal of containers by
  name is dropped.
- **A test-only Compose override** (`tests/integration/docker-compose.it.yaml`)
  that resets `container_name` for the five infrastructure services the
  suite uses, publishes SLIM, NATS and the OTel collector's HTTP receiver
  on loopback host ports chosen per run, and publishes nothing for
  ClickHouse and Grafana, which only the collector reaches over the
  project network. `docker-compose.yaml` itself does not change, so the
  developer stack keeps its fixed ports and names.
- **Per-run agent ports.** Every local agent the suite starts gets a free
  port through `AGENT_PORT` or `FARM_AGENT_PORT`, and the tests that call
  an agent's HTTP health route read that port instead of a literal.
- **One source of addresses.** The SLIM, NATS and OTLP endpoints and the
  agent ports are allocated once per session in one helper module.
  `_base_env()`, the `transport_config` parameters (now literal
  `127.0.0.1:46357` and `nats://127.0.0.1:4222` in nine test modules) and
  the health tests all read from it.
- **Documentation.** `tests/README.md` states that the suite runs beside a
  running stack, drops the wrong `COMPOSE_PROJECT_NAME` advice, and says how
  to clean up a project left by an interrupted run.

Out of scope: the dev stack's own ports and container names, corto and
recruiter (their suites do not share this setup), and running two lungo
suites in parallel on one machine (enabled by this change, not promised).

## Capabilities

### New Capabilities
- `lungo-integration-test-isolation`: the lungo integration suite runs
  beside a running lungo development stack without port or name
  collisions and without stopping, removing or changing any container,
  network or volume it did not create.

### Modified Capabilities
None.

## Impact

- `coffeeAGNTCY/coffee_agents/lungo/tests/integration/conftest.py`: session
  setup and teardown, `_base_env()`, the `AGENTS` registry.
- `coffeeAGNTCY/coffee_agents/lungo/tests/integration/helpers/docker_helpers.py`:
  project name and extra compose file on every command; `down` scoped to it.
- New `tests/integration/helpers/ports.py` and
  `tests/integration/docker-compose.it.yaml`.
- Test modules with literal endpoints or ports: `_auction_helpers.py`,
  `test_logistics_{farm,accountant,shipper,helpdesk,supervisor}.py`,
  `llm/test_logistics_supervisor_flows.py`, `test_supply_chain_health.py`,
  `llm/test_supply_chain_flows.py`.
- `tests/README.md`.
- Requires Docker Compose 2.24 or newer (for `!reset` in the override).
  GitHub's `ubuntu-latest` and current Docker Desktop meet it.
- CI: no workflow change; the suite behaves the same on a clean runner.
