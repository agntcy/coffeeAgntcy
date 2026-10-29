# Tasks

All paths are under `coffeeAGNTCY/coffee_agents/lungo/`.

## 1. Confirm what the suite uses

- [ ] 1.1 Confirm that no integration test or agent started by the suite
      uses SLIM 46358, NATS 4223/6222/8222, collector 4317/13133, or the
      host ports of ClickHouse and Grafana, and that the auction tests
      never use a farm card's HTTP interface. Verify: `rg` over `tests/`,
      `agents/` and `config/` finds no such use; record the result in the
      PR description. If something does use one, publish that port too
      (D1) before continuing.

## 2. Session addresses and project name

- [ ] 2.1 Add `tests/integration/helpers/ports.py` (D2, D3): picks the
      SLIM, NATS and OTLP HTTP ports, one port per `AGENTS` name and the
      `lungo-it-<hex>` project name once per process, using
      `free_tcp_port()`, and exposes the endpoint constants,
      `agent_port(name)`, `PROJECT_NAME` and `compose_env()` (the
      `LUNGO_IT_*` variables). Verify: new
      `tests/unit/test_integration_ports.py` passes, covering distinct
      ports, loopback endpoints, the project-name pattern, the same values
      on repeated access, and an unknown agent name raising.
- [ ] 2.2 Add `tests/integration/docker-compose.it.yaml` (D1). Verify:
      `docker compose -p lungo-it-check -f docker-compose.yaml -f
      tests/integration/docker-compose.it.yaml config` with the three
      `LUNGO_IT_*` variables set shows no `container_name` and only the
      three loopback ports for the five services, and the same command
      without the override still shows the dev ports and names.

## 3. Compose helpers

- [ ] 3.1 Make every command in `helpers/docker_helpers.py` use
      `-p ports.PROJECT_NAME`, the override file and `ports.compose_env()`;
      remove `remove_container_if_exists()`. Verify: extend
      `tests/unit/test_docker_helpers_diagnostics.py` (or a sibling
      module) so that `up`, `down` and the service lookups are asserted to
      pass the project name and both files, and that `down` never runs
      without `-p`.

## 4. Conftest and test modules

- [ ] 4.1 In `tests/integration/conftest.py`, import `ports` before
      `config.config`, set `SLIM_SERVER`, `NATS_SERVER`,
      `TRANSPORT_SERVER_ENDPOINT` and `OTLP_HTTP_ENDPOINT` from it
      (overwriting), build `_base_env()` from it, drop the five
      `remove_container_if_exists()` calls, and give each `AGENTS` entry
      its port through `FARM_AGENT_PORT` or `AGENT_PORT` (D4). Verify:
      `uv run pytest tests/integration --collect-only -q` lists the same
      test ids as before the change.
- [ ] 4.2 Replace the literal endpoints in `_auction_helpers.py`,
      `test_logistics_{farm,accountant,shipper,helpdesk,supervisor}.py`,
      `llm/test_logistics_supervisor_flows.py`, `llm/test_supply_chain_flows.py`
      and `test_supply_chain_health.py` with the `ports` constants, and the
      health-port table in `test_supply_chain_health.py` with
      `ports.agent_port()`. Verify: `rg -n '127\.0\.0\.1:(46357|4222|4318)|909[0-9]|999[7-9]' tests/integration`
      finds nothing outside `ports.py` and comments.
- [ ] 4.3 Update `tests/README.md`: replace the `COMPOSE_PROJECT_NAME`
      paragraph with how the suite isolates itself, the Compose 2.24
      minimum, and how to find and remove a `lungo-it-*` project left by a
      killed run. Verify: `task links:check` and `task dashes:check` pass.

## 5. Integration checks

- [ ] 5.1 With no lungo containers running, run
      `WORKFLOW_API_KEY=TheAnswerIs42 uv run pytest tests --ignore=tests/integration/llm`.
      Verify: the same pass count as before the change (1086 on this
      branch), and `docker ps -a --filter label=com.docker.compose.project`
      shows no `lungo-it-*` project afterwards.
- [ ] 5.2 Start the full dev stack (`docker compose up -d` with the
      developer `.env`), record `docker ps --format '{{.ID}} {{.Names}}
      {{.Status}}'` and `docker volume ls`, run the same suite, and record
      both again. Verify: every test passes, and the stack's container
      ids, names, states and volumes are unchanged.
- [ ] 5.3 Run `uv run pytest tests/integration --collect-only -q` with the
      dev stack up. Verify: the stack is unchanged afterwards (same
      comparison as 5.2).
- [ ] 5.4 Run `task check:all` from the repo root. Verify: every check
      passes.
