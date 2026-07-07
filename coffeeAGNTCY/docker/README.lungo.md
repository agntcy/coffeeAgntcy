# Lungo Docker Build Instructions

All Dockerfiles for lungo images are shared common templates located in this directory (`coffeeAGNTCY/docker/`).
Build arguments specify the project path and entrypoint for each service.

## Prerequisites

- **Run all commands from the repository root directory.**
- Install [Docker](https://www.docker.com/) and ensure it is running.

---

## Services

### Farm Agents (`Dockerfile.python-agent`)

```bash
# Brazil Farm
docker build \
  --build-arg PROJECT_PATH=coffeeAGNTCY/coffee_agents/lungo \
  --build-arg UV_CACHE_ID=lungo \
  --build-arg APP_NAME=brazil-farm \
  --build-arg AGENT_SCRIPT=agents/farms/brazil/farm_server.py \
  -f coffeeAGNTCY/docker/Dockerfile.python-agent -t brazil-farm .

# Colombia Farm
docker build \
  --build-arg PROJECT_PATH=coffeeAGNTCY/coffee_agents/lungo \
  --build-arg UV_CACHE_ID=lungo \
  --build-arg APP_NAME=colombia-farm \
  --build-arg AGENT_SCRIPT=agents/farms/colombia/farm_server.py \
  -f coffeeAGNTCY/docker/Dockerfile.python-agent -t colombia-farm .

# Vietnam Farm
docker build \
  --build-arg PROJECT_PATH=coffeeAGNTCY/coffee_agents/lungo \
  --build-arg UV_CACHE_ID=lungo \
  --build-arg APP_NAME=vietnam-farm \
  --build-arg AGENT_SCRIPT=agents/farms/vietnam/farm_server.py \
  -f coffeeAGNTCY/docker/Dockerfile.python-agent -t vietnam-farm .
```

### Logistics Agents (`Dockerfile.python-agent`)

```bash
docker build \
  --build-arg PROJECT_PATH=coffeeAGNTCY/coffee_agents/lungo \
  --build-arg UV_CACHE_ID=lungo \
  --build-arg APP_NAME=logistics-shipper \
  --build-arg AGENT_SCRIPT=agents/logistics/shipper/server.py \
  -f coffeeAGNTCY/docker/Dockerfile.python-agent -t logistics-shipper .

docker build \
  --build-arg PROJECT_PATH=coffeeAGNTCY/coffee_agents/lungo \
  --build-arg UV_CACHE_ID=lungo \
  --build-arg APP_NAME=logistics-accountant \
  --build-arg AGENT_SCRIPT=agents/logistics/accountant/server.py \
  -f coffeeAGNTCY/docker/Dockerfile.python-agent -t logistics-accountant .

docker build \
  --build-arg PROJECT_PATH=coffeeAGNTCY/coffee_agents/lungo \
  --build-arg UV_CACHE_ID=lungo \
  --build-arg APP_NAME=logistics-farm \
  --build-arg AGENT_SCRIPT=agents/logistics/farm/server.py \
  -f coffeeAGNTCY/docker/Dockerfile.python-agent -t logistics-farm .

docker build \
  --build-arg PROJECT_PATH=coffeeAGNTCY/coffee_agents/lungo \
  --build-arg UV_CACHE_ID=lungo \
  --build-arg APP_NAME=logistics-helpdesk \
  --build-arg AGENT_SCRIPT=agents/logistics/helpdesk/server.py \
  -f coffeeAGNTCY/docker/Dockerfile.python-agent -t logistics-helpdesk .

docker build \
  --build-arg PROJECT_PATH=coffeeAGNTCY/coffee_agents/lungo \
  --build-arg UV_CACHE_ID=lungo \
  --build-arg APP_NAME=logistics-supervisor \
  --build-arg AGENT_SCRIPT=agents/supervisors/logistics/main.py \
  -f coffeeAGNTCY/docker/Dockerfile.python-agent -t logistics-supervisor .
```

### MCP Servers (`Dockerfile.python-agent`)

```bash
docker build \
  --build-arg PROJECT_PATH=coffeeAGNTCY/coffee_agents/lungo \
  --build-arg UV_CACHE_ID=lungo \
  --build-arg APP_NAME=weather-mcp-server \
  --build-arg AGENT_SCRIPT=agents/mcp_servers/weather_service.py \
  -f coffeeAGNTCY/docker/Dockerfile.python-agent -t weather-mcp-server .

docker build \
  --build-arg PROJECT_PATH=coffeeAGNTCY/coffee_agents/lungo \
  --build-arg UV_CACHE_ID=lungo \
  --build-arg APP_NAME=payment-mcp-server \
  --build-arg AGENT_SCRIPT=agents/mcp_servers/payment_service.py \
  -f coffeeAGNTCY/docker/Dockerfile.python-agent -t payment-mcp-server .
```

### Supervisors (`Dockerfile.python-agent`)

```bash
docker build \
  --build-arg PROJECT_PATH=coffeeAGNTCY/coffee_agents/lungo \
  --build-arg UV_CACHE_ID=lungo \
  --build-arg APP_NAME=lungo-auction-supervisor \
  --build-arg AGENT_SCRIPT=agents/supervisors/auction/main.py \
  -f coffeeAGNTCY/docker/Dockerfile.python-agent -t auction-supervisor .

docker build \
  --build-arg PROJECT_PATH=coffeeAGNTCY/coffee_agents/lungo \
  --build-arg UV_CACHE_ID=lungo \
  --build-arg APP_NAME=agentic-workflows-api \
  --build-arg AGENT_SCRIPT="-m api.agentic_workflows.server" \
  -f coffeeAGNTCY/docker/Dockerfile.python-agent -t agentic-workflows-api .

docker build \
  --build-arg PROJECT_PATH=coffeeAGNTCY/coffee_agents/lungo \
  --build-arg UV_CACHE_ID=lungo \
  --build-arg APP_NAME=lungo-recruiter-supervisor \
  --build-arg AGENT_SCRIPT=agents/supervisors/recruiter/main.py \
  -f coffeeAGNTCY/docker/Dockerfile.python-agent -t recruiter-supervisor .
```

### UI (`Dockerfile.ui`)

```bash
docker build \
  --build-arg PROJECT_PATH=coffeeAGNTCY/coffee_agents/lungo/frontend \
  --build-arg NPM_CACHE_ID=lungo \
  -f coffeeAGNTCY/docker/Dockerfile.ui -t lungo-ui .
```

---

Alternatively, use `docker compose up` from `coffeeAGNTCY/coffee_agents/lungo/` — the `docker-compose.yaml` already passes all required build args.
