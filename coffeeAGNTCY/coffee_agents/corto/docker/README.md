# Project Setup and Docker Instructions

This project consists of three main components:
1. **FastAPI Exchange Server** (Backend)
2. **React Frontend** (UI)
3. **Farm Server** (Agent Backend)

All components use shared Dockerfiles under [`coffeeAGNTCY/docker/common/`](../../../docker/common/). Per-service differences are supplied via build args in `docker-compose.yaml`.

---

## Prerequisites
- **Ensure you are in the root directory of the repository before running any commands.**
- Install [Docker](https://www.docker.com/) and ensure it is running.
- Install [Docker Compose](https://docs.docker.com/compose/) (optional, if using `docker-compose`).

---

## Shared Dockerfiles

| Service | Dockerfile | Key build args |
|---------|------------|----------------|
| Exchange server | `Dockerfile.python-uv` | `PROJECT_PATH`, `UV_CACHE_ID`, `RUN_COMMAND`, `APP_NAME` |
| Farm server | `Dockerfile.python-uv` | `PROJECT_PATH`, `UV_CACHE_ID`, `RUN_COMMAND` |
| UI | `Dockerfile.node-frontend` | `FRONTEND_PATH`, `NPM_CACHE_ID` |

See [`coffeeAGNTCY/docker/common/README.md`](../../../docker/common/README.md) for the full build-arg reference.

---

## Build and Run Instructions

### Docker Compose (recommended)

From this directory:

```bash
docker compose up --build
```

### Manual builds (from repo root)

#### Exchange server
```bash
docker build -f coffeeAGNTCY/docker/common/Dockerfile.python-uv \
  --build-arg PROJECT_PATH=coffeeAGNTCY/coffee_agents/corto \
  --build-arg UV_CACHE_ID=corto-uv \
  --build-arg RUN_COMMAND="uv run python exchange/main.py" \
  --build-arg APP_NAME=corto-exchange \
  --build-arg APP_SERVICE=corto-exchange \
  -t exchange-server .
```

#### UI
```bash
docker build -f coffeeAGNTCY/docker/common/Dockerfile.node-frontend \
  --build-arg FRONTEND_PATH=coffeeAGNTCY/coffee_agents/corto/exchange/frontend \
  --build-arg NPM_CACHE_ID=corto-npm \
  -t ui-server .
```

#### Farm server
```bash
docker build -f coffeeAGNTCY/docker/common/Dockerfile.python-uv \
  --build-arg PROJECT_PATH=coffeeAGNTCY/coffee_agents/corto \
  --build-arg UV_CACHE_ID=corto-uv \
  --build-arg RUN_COMMAND="uv run python farm/farm_server.py" \
  -t farm-server .
```
