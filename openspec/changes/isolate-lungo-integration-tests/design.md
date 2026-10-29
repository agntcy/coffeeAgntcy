# Design

## Context

See proposal.md (Why) for the problem. The parts of the current setup that
shape the approach:

- `tests/integration/conftest.py` starts five Compose services with
  `helpers/docker_helpers.up()`: `slim`, `nats`, `otel-collector`,
  `clickhouse-server` and `grafana`. Every compose command runs against
  `docker-compose.yaml` (plus `docker-compose.override.yaml` when present)
  with the default project name. `down()` runs `down -v --remove-orphans`.
  Before setup, `remove_container_if_exists()` force-removes the five
  containers by their fixed names.
- In `docker-compose.yaml` those services have fixed `container_name`
  values and publish fixed host ports: SLIM 46357 and 46358, NATS 4222,
  4223, 6222 and 8222, the collector 4317, 4318 and 13133, ClickHouse 9000
  and 8123, Grafana 3001. The collector reaches ClickHouse as
  `clickhouse-server:9000`, and Grafana does the same, over the project
  network. No test talks to ClickHouse or Grafana from the host.
- Agents are local subprocesses (`ProcessRunner`), not containers. Their
  environment is `_base_env()` plus the test's `transport_config` plus the
  agent's entry in `AGENTS`. `_base_env()` hard-codes `127.0.0.1:46357`,
  `127.0.0.1:4222` and `http://127.0.0.1:4318`. Each agent reads its HTTP
  port from `AGENT_PORT` (logistics and supply chain) or `FARM_AGENT_PORT`
  (farms), with the dev-stack port as default. The weather MCP server has
  no HTTP port, and the Open-Meteo stub already binds port 0.
- In-process supervisors (auction, logistics, recruiter, the supply chain
  Buyer) run under `TestClient`. Their fixtures set `_base_env()` and
  `transport_config` with `monkeypatch.setenv` and re-import the
  supervisor modules, so `config.config.SLIM_SERVER` and friends are read
  after the environment is set.
- Nine test modules put literal endpoints in `transport_config`
  parameters (`http://127.0.0.1:46357`, `nats://127.0.0.1:4222`).
  `test_supply_chain_health.py` also lists literal health ports. These
  values are needed at collection time, before any fixture runs.
- `tests/helpers/agentic_uvicorn_helpers.free_tcp_port()` already exists
  and is used by the `live` tests.
- Local Docker Compose is v5.5.1. GitHub's `ubuntu-latest` ships a Compose
  v2 release newer than 2.24.

## Goals / Non-Goals

**Goals:**
- Satisfy the requirements in
  `specs/lungo-integration-test-isolation/spec.md` with changes confined to
  `tests/` (plus one new compose file under `tests/integration/`).
- Keep one place that knows every address the session uses.

**Non-Goals:**
- Changing agent code, `config/config.py` or `docker-compose.yaml`.
- Making the suite safe to run twice in parallel on one machine. Per-run
  project names and free ports make that likely to work, but it is not
  tested or promised.
- Cleaning up projects left behind by a killed run automatically.

## Decisions

### D1. A test-only override file, not a parametrized `docker-compose.yaml`

`tests/integration/docker-compose.it.yaml` is passed as an extra `-f` to
every compose command of the suite. For each of the five services it sets
`container_name: !reset null` and replaces `ports` with `!override`:

| Service | Published by the suite |
|---|---|
| `slim` | `127.0.0.1:${LUNGO_IT_SLIM_PORT}:46357` |
| `nats` | `127.0.0.1:${LUNGO_IT_NATS_PORT}:4222` |
| `otel-collector` | `127.0.0.1:${LUNGO_IT_OTLP_HTTP_PORT}:4318` |
| `clickhouse-server` | nothing (`ports: !reset []`) |
| `grafana` | nothing (`ports: !reset []`) |

Alternative: make every host port and name in `docker-compose.yaml` an
`${VAR:-default}` expression. Rejected: it touches 29 services that the
suite never starts, changes the file every developer reads, and still
needs a way to drop `container_name`, which Compose cannot express as an
empty default. The override touches only what the suite uses and leaves the
dev stack byte-for-byte the same.

Unused ports (SLIM 46358, NATS 4223/6222/8222, collector 4317 and 13133)
are not published. Task 1.1 confirms nothing in the suite uses them.

### D2. Ports are chosen in Python before anything else runs

A new module, `tests/integration/helpers/ports.py`, picks every port once
when it is first imported, using `free_tcp_port()`: the three
infrastructure ports and one port per agent in `AGENTS`. It exposes them as
constants (`SLIM_ENDPOINT`, `NATS_ENDPOINT`, `OTLP_HTTP_ENDPOINT`,
`agent_port(name)`). `conftest.py` imports it before `config.config` and
writes `SLIM_SERVER`, `NATS_SERVER`, `TRANSPORT_SERVER_ENDPOINT` and
`OTLP_HTTP_ENDPOINT` into `os.environ` (overwriting, not `setdefault`, so a
developer's `.env` cannot point the suite at the dev stack). Test modules
import the constants for their `transport_config` parameters.

Alternative: publish on ephemeral host ports (`127.0.0.1::46357`) and read
them back with `docker compose port`. Rejected: the addresses are only
known after the session fixture runs, but the `transport_config`
parameters are evaluated at collection time, and `config.config` is
imported at the top of `conftest.py`. Pre-allocation keeps the addresses
known from the first line.

### D3. One project name per session

`docker_helpers` builds every compose command with
`-p lungo-it-<8 random hex chars>`, generated once per session in
`ports.py` next to the ports, and the compose environment carries the
`LUNGO_IT_*` port variables. `down()` keeps `-v --remove-orphans`: scoped
to the session project, both only affect what the session created.
`remove_container_if_exists()` and its five calls are removed. With no
fixed names left, there is nothing by name to clean.

The suite still loads the developer's `.env` (through `config.config`),
including `COMPOSE_PROFILES`. Because `up` names its services explicitly
and every command is scoped to the session project, the profiles no
longer select anything outside the session.

### D4. Agents get their port through the variable they already read

`AGENTS` entries get their port from `ports.agent_port(name)` when the
fixture builds the agent's environment: `FARM_AGENT_PORT` for the three
farms, `AGENT_PORT` for the logistics and supply chain agents. The literal
`AGENT_PORT` values in the supply chain entries go away.
`test_supply_chain_health.py` reads `ports.agent_port(member)` instead of
its own table.

## Risks / Trade-offs

- [A chosen port is taken between allocation and bind] → The window is
  seconds. `up()` already prints Docker's stderr. On "port is already
  allocated" the session fails with that message and the next run picks
  new ports. A retry loop is not added unless it shows up in practice.
- [Compose older than 2.24 does not understand `!reset` / `!override`] →
  `up()` fails at the first `config --images` with a parse error. The
  README states the minimum version.
- [A run killed with SIGKILL leaves a `lungo-it-*` project behind] → atexit
  covers normal exits, failures and Ctrl-C. The README documents
  `docker compose ls --filter name=lungo-it` and `docker compose -p <name>
  down -v`. Automatic cleanup of other `lungo-it-*` projects is not done,
  because it could remove a parallel session.
- [Farm cards advertise `http://0.0.0.0:${FARM_AGENT_PORT}`, and the three
  farms share that variable name] → each farm subprocess gets its own value,
  so each advertises its own port. In the test process the variable is not
  set, so an in-process import of a farm card shows the default port. The
  auction tests use SLIM and NATS only, so the HTTP URL is not used. Task
  1.1 confirms it.
- [The suite's ClickHouse and Grafana are no longer reachable from the
  host] → nothing in the suite reads them. A developer who wants to look at
  a test run's traces can still `docker compose -p <name> port` after adding
  a port locally, or use the dev stack.

## Migration Plan

No data or deployment migration. The change is test-only. A developer who
used to stop the stack before running the suite no longer needs to.
Rollback is reverting the change; the dev stack is never modified.
