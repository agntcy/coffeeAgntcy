# Lungo Docker Compose

Compose file: `docker-compose.yaml` in this directory.

Agent configuration (`.env`, `frontend/.env`) lives under [`../../coffee_agents/lungo/`](../../coffee_agents/lungo/).

## Quick start

From the repository root:

```bash
cd coffeeAGNTCY/docker/lungo
docker compose up --build
```

Or from `coffeeAGNTCY/coffee_agents/lungo/`:

```bash
docker compose -f ../../docker/lungo/docker-compose.yaml up --build
```

## Manual image builds

Use the shared Dockerfiles under [`../common/`](../common/). See [`../common/README.md`](../common/README.md) for build-arg reference and lungo-specific examples.
