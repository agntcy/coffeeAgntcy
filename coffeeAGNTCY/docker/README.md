# Docker layout

| Path | Contents |
|------|----------|
| [`common/`](common/) | Shared parameterized Dockerfiles (`Dockerfile.python-uv`, `Dockerfile.node-frontend`) |
| [`corto/`](corto/) | Corto `docker-compose.yaml` |
| [`lungo/`](lungo/) | Lungo `docker-compose.yaml` |
| [`recruiter/`](recruiter/) | Recruiter `docker-compose.yaml` and Directory config |

Run Compose from the demo directory (agent `.env` must exist there):

```bash
# Corto
cd coffeeAGNTCY/docker/corto && docker compose up --build

# Lungo
cd coffeeAGNTCY/docker/lungo && docker compose up --build

# Recruiter
cd coffeeAGNTCY/docker/recruiter && docker compose up --build
```

Or from a demo agent directory:

```bash
docker compose -f ../../docker/corto/docker-compose.yaml up --build
```

See [`common/README.md`](common/README.md) for manual `docker build` examples.
