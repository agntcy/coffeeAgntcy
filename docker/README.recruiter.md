# Recruiter Docker Build Instructions

The recruiter image is built from the shared `Dockerfile.python-agent` using the `agent-with-dirctl` target, which adds the `dirctl` binary, exposes port `8881`, and sets `ENABLE_HTTP=true`.

## Prerequisites

- **Run all commands from the repository root directory.**
- Install [Docker](https://www.docker.com/) and ensure it is running.

---

## Services

### Recruiter Agent (`Dockerfile.python-agent`, target `agent-with-dirctl`)

```bash
docker build \
  --target agent-with-dirctl \
  --build-arg PROJECT_PATH=coffeeAGNTCY/coffee_agents/recruiter \
  --build-arg UV_CACHE_ID=recruiter \
  --build-arg AGENT_SCRIPT=src/agent_recruiter/server/server.py \
  --build-arg APP_NAME=recruiter \
  -f docker/Dockerfile.python-agent \
  -t recruiter .
```

---

Alternatively, use `docker compose up` from `coffeeAGNTCY/coffee_agents/recruiter/docker/` or `coffeeAGNTCY/coffee_agents/lungo/` — the `docker-compose.yaml` files already pass all required build args and set the correct target.
