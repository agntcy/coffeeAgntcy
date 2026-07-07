# Recruiter Docker Build Instructions

The Dockerfile for the recruiter image is a dedicated template located in this directory (`coffeeAGNTCY/docker/Dockerfile.recruiter`).

## Prerequisites

- **Run all commands from the repository root directory.**
- Install [Docker](https://www.docker.com/) and ensure it is running.

---

## Services

### Recruiter Agent (`Dockerfile.recruiter`)

```bash
docker build \
  --build-arg PROJECT_PATH=coffeeAGNTCY/coffee_agents/recruiter \
  --build-arg UV_CACHE_ID=recruiter \
  --build-arg AGENT_SCRIPT=src/agent_recruiter/server/server.py \
  -f coffeeAGNTCY/docker/Dockerfile.recruiter \
  -t recruiter .
```

---

Alternatively, use `docker compose up` from `coffeeAGNTCY/coffee_agents/recruiter/docker/` or `coffeeAGNTCY/coffee_agents/lungo/` — the `docker-compose.yaml` files already pass all required build args.
