# Spec Delta

## Purpose

Lets the lungo integration suite run on a machine where a lungo
development stack is already running, without port or name collisions and
without touching any Docker resource the suite did not create.

## ADDED Requirements

### Requirement: The suite uses Docker resources of its own
The lungo integration suite SHALL start its Docker infrastructure under a
Compose project name generated for that test session, distinct from the
default `lungo` project and from any other session's project. The
containers it starts SHALL NOT use a fixed container name.

#### Scenario: A development stack is running
- **WHEN** the containers of `docker compose up` for lungo are running and
  the integration suite starts
- **THEN** the suite creates its own SLIM, NATS, OTel collector,
  ClickHouse and Grafana containers in its own project, and the session
  setup does not fail on a container name that is already in use

#### Scenario: Two sessions are started one after the other
- **WHEN** a session ends and another one starts
- **THEN** the second session uses a different project name from the first

### Requirement: The suite never changes resources it did not create
The suite's setup and teardown SHALL stop and remove only the containers,
networks and volumes of its own session project. It SHALL NOT stop,
remove or recreate a container, network or volume that belongs to another
Compose project, and SHALL NOT remove a container by name.

#### Scenario: Setup with a development stack running
- **WHEN** the suite's session setup runs while the development stack is up
- **THEN** every container, network and volume of the development stack is
  still present and in the same state afterwards

#### Scenario: Normal teardown
- **WHEN** the session ends, whether the tests passed or failed
- **THEN** the suite's own project is brought down with its volumes, and no
  other project is touched

#### Scenario: `--collect-only`
- **WHEN** pytest runs the integration suite with `--collect-only`
- **THEN** no container, network or volume of another project is stopped or
  removed

### Requirement: The suite uses host ports chosen per session
Every host port the suite binds, both the published ports of its
containers and the ports of the agent processes it starts, SHALL be chosen
when the session starts from ports that are free at that moment, and SHALL
be bound on the loopback interface only. Services that the tests do not
reach from the host SHALL NOT publish a host port.

#### Scenario: The development stack holds the default ports
- **WHEN** 46357, 4222, 4318, 9090 to 9099 and 9997 to 9999 are in use on
  the host and the suite runs
- **THEN** no test fails because a port is already in use

#### Scenario: Agents and in-process supervisors find the infrastructure
- **WHEN** an agent process or an in-process supervisor under test connects
  to SLIM, NATS or the OTLP endpoint
- **THEN** it uses the address chosen for this session, not a default port

#### Scenario: A test calls an agent's HTTP route
- **WHEN** a test checks the health route of an agent the suite started
- **THEN** it uses the port that agent was given in this session

### Requirement: The development stack is unchanged
The change SHALL NOT alter the published ports, container names, services
or profiles that `docker compose up` produces for the lungo development
stack.

#### Scenario: Developer starts the stack
- **WHEN** a developer runs `docker compose up` in the lungo directory with
  the same `.env` as before the change
- **THEN** the same containers start with the same names and host ports as
  before

### Requirement: The suite still runs on a clean CI runner
On a machine with no lungo containers, the suite SHALL run with the same
command and the same results as before the change, and SHALL leave no
container, network or volume behind after a normal exit.

#### Scenario: CI run
- **WHEN** the reusable test workflow runs `uv run pytest tests
  --ignore=tests/integration/llm` for lungo
- **THEN** the tests that passed before the change pass, and `docker ps -a`
  shows no container of the suite's project afterwards
