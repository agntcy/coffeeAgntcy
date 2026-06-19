# Project Setup and Docker Instructions

Lungo services are containerized using shared Dockerfiles under [`coffeeAGNTCY/docker/common/`](../../../docker/common/). Per-service differences are supplied via build args in `docker-compose.yaml`.

---

## Prerequisites
- **Ensure you are in the root directory of the repository before running any commands.**
- Install [Docker](https://www.docker.com/) and ensure it is running.
- Install [Docker Compose](https://docs.docker.com/compose/) (optional, if using `docker-compose`).

---

## Shared Dockerfiles

| Dockerfile | Used for |
|------------|----------|
| `Dockerfile.python-uv` | All Python agents (farms, supervisors, MCP servers, logistics, recruiter-supervisor) |
| `Dockerfile.node-frontend` | Lungo React UI |

The standalone recruiter agent uses `Dockerfile.python-uv` with target `python-uv-with-dirctl` (bundles `dirctl`).

See [`coffeeAGNTCY/docker/common/README.md`](../../../docker/common/README.md) for the full build-arg reference.

---

## Build and Run Instructions

### Docker Compose (recommended)

From the lungo project directory:

```bash
docker compose --profile farms up --build
```

### Manual build examples (from repo root)

#### Brazil farm
```bash
docker build -f coffeeAGNTCY/docker/common/Dockerfile.python-uv \
  --build-arg PROJECT_PATH=coffeeAGNTCY/coffee_agents/lungo \
  --build-arg UV_CACHE_ID=lungo-uv \
  --build-arg RUN_COMMAND="uv run python agents/farms/brazil/farm_server.py" \
  -t brazil-farm .
```

#### Auction supervisor (with build metadata)
```bash
docker build -f coffeeAGNTCY/docker/common/Dockerfile.python-uv \
  --build-arg PROJECT_PATH=coffeeAGNTCY/coffee_agents/lungo \
  --build-arg UV_CACHE_ID=lungo-uv \
  --build-arg RUN_COMMAND="uv run python agents/supervisors/auction/main.py" \
  --build-arg APP_NAME=lungo-exchange \
  --build-arg APP_SERVICE=lungo-exchange \
  -t auction-supervisor .
```

#### UI
```bash
docker build -f coffeeAGNTCY/docker/common/Dockerfile.node-frontend \
  --build-arg FRONTEND_PATH=coffeeAGNTCY/coffee_agents/lungo/frontend \
  --build-arg NPM_CACHE_ID=lungo-npm \
  -t lungo-ui .
```
