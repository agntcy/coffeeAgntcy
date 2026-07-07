# Corto Docker Build Instructions

All Dockerfiles for corto images are shared common templates located in this directory (`coffeeAGNTCY/docker/`).
Build arguments specify the project path and entrypoint for each service.

## Prerequisites

- **Run all commands from the repository root directory.**
- Install [Docker](https://www.docker.com/) and ensure it is running.

---

## Services

### Farm Server (`Dockerfile.python-agent`)

```bash
docker build \
  --build-arg PROJECT_PATH=coffeeAGNTCY/coffee_agents/corto \
  --build-arg UV_CACHE_ID=corto \
  --build-arg APP_NAME=corto-farm \
  --build-arg AGENT_SCRIPT=farm/farm_server.py \
  -f coffeeAGNTCY/docker/Dockerfile.python-agent \
  -t corto-farm .
```

### Exchange Server (`Dockerfile.python-agent`)

```bash
docker build \
  --build-arg PROJECT_PATH=coffeeAGNTCY/coffee_agents/corto \
  --build-arg UV_CACHE_ID=corto \
  --build-arg APP_NAME=corto-exchange \
  --build-arg AGENT_SCRIPT=exchange/main.py \
  -f coffeeAGNTCY/docker/Dockerfile.python-agent \
  -t corto-exchange .
```

### UI (`Dockerfile.ui`)

```bash
docker build \
  --build-arg PROJECT_PATH=coffeeAGNTCY/coffee_agents/corto/exchange/frontend \
  --build-arg NPM_CACHE_ID=corto \
  -f coffeeAGNTCY/docker/Dockerfile.ui \
  -t corto-ui .
```

---

Alternatively, use `docker compose up` from `coffeeAGNTCY/coffee_agents/corto/` — the `docker-compose.yaml` already passes all required build args.
