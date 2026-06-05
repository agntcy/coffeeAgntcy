# Corto Docker Compose

Compose file: `docker-compose.yaml` in this directory.

Agent configuration (`.env`) lives in [`../../coffee_agents/corto/`](../../coffee_agents/corto/).

## Quick start

From the repository root:

```bash
cd coffeeAGNTCY/docker/corto
docker compose up --build
```

Or from `coffeeAGNTCY/coffee_agents/corto/`:

```bash
docker compose -f ../../docker/corto/docker-compose.yaml up --build
```

## Manual image builds

Use the shared Dockerfiles under [`../common/`](../common/). Examples:

```bash
# Exchange server
docker build -f coffeeAGNTCY/docker/common/Dockerfile.python-uv \
  --build-arg PROJECT_PATH=coffeeAGNTCY/coffee_agents/corto \
  --build-arg UV_CACHE_ID=corto-uv \
  --build-arg RUN_COMMAND="uv run python exchange/main.py" \
  --build-arg APP_NAME=corto-exchange \
  --build-arg APP_SERVICE=corto-exchange \
  -t exchange-server .

# UI
docker build -f coffeeAGNTCY/docker/common/Dockerfile.node-frontend \
  --build-arg FRONTEND_PATH=coffeeAGNTCY/coffee_agents/corto/exchange/frontend \
  --build-arg NPM_CACHE_ID=corto-npm \
  -t ui-server .

# Farm server
docker build -f coffeeAGNTCY/docker/common/Dockerfile.python-uv \
  --build-arg PROJECT_PATH=coffeeAGNTCY/coffee_agents/corto \
  --build-arg UV_CACHE_ID=corto-uv \
  --build-arg RUN_COMMAND="uv run python farm/farm_server.py" \
  -t farm-server .
```
