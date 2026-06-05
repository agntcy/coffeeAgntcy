# Shared Docker Images

Parameterized Dockerfiles for coffee-agntcy agent and UI images. Per-service differences are supplied via build args in `docker-compose.yaml` or CI.

## Dockerfiles

| File | Use for |
|------|---------|
| `Dockerfile.python-uv` | Python agents built with `uv` (lungo, corto, recruiter) |
| `Dockerfile.node-frontend` | React UIs served with `npx serve` |

## Python/uv build args

| ARG | Required | Description |
|-----|----------|-------------|
| `PROJECT_PATH` | yes | Repo-relative path (e.g. `coffeeAGNTCY/coffee_agents/lungo`) |
| `UV_CACHE_ID` | yes | BuildKit cache id (`lungo-uv`, `corto-uv`, `recruiter-uv`) |
| `RUN_COMMAND` | yes | Container start command (e.g. `uv run python farm/farm_server.py`) |
| `APP_NAME` | no | When set, writes `about.properties` with CI metadata |
| `APP_SERVICE` | no | `about.properties` service name (defaults to `APP_NAME`) |
| `ENV_PORT` | no | Sets `PORT` env var |
| `ENV_PYTHONUNBUFFERED` | no | Sets `PYTHONUNBUFFERED` env var |
| `ENV_ENABLE_HTTP` | no | Sets `ENABLE_HTTP` env var |

**Targets:** `python-uv` (default) or `python-uv-with-dirctl` (recruiter; includes `dirctl` binary).

### Example: lungo brazil farm

```bash
docker build -f coffeeAGNTCY/docker/common/Dockerfile.python-uv \
  --build-arg PROJECT_PATH=coffeeAGNTCY/coffee_agents/lungo \
  --build-arg UV_CACHE_ID=lungo-uv \
  --build-arg RUN_COMMAND="uv run python agents/farms/brazil/farm_server.py" \
  -t brazil-farm .
```

### Example: recruiter (with dirctl)

```bash
docker build -f coffeeAGNTCY/docker/common/Dockerfile.python-uv \
  --target python-uv-with-dirctl \
  --build-arg PROJECT_PATH=coffeeAGNTCY/coffee_agents/recruiter \
  --build-arg UV_CACHE_ID=recruiter-uv \
  --build-arg RUN_COMMAND="uv run python src/agent_recruiter/server/server.py" \
  --build-arg ENV_PYTHONUNBUFFERED=1 \
  --build-arg ENV_ENABLE_HTTP=true \
  -t recruiter .
```

## Node frontend build args

| ARG | Required | Description |
|-----|----------|-------------|
| `FRONTEND_PATH` | yes | Repo-relative frontend directory |
| `NPM_CACHE_ID` | yes | BuildKit cache id (`lungo-npm`, `corto-npm`) |

### Example: lungo UI

```bash
docker build -f coffeeAGNTCY/docker/common/Dockerfile.node-frontend \
  --build-arg FRONTEND_PATH=coffeeAGNTCY/coffee_agents/lungo/frontend \
  --build-arg NPM_CACHE_ID=lungo-npm \
  -t lungo-ui .
```
