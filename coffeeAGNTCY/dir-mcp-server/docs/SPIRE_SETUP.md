# SPIRE Authentication Setup for Directory Access

This guide explains how to configure any application to connect to the remote SPIRE-authenticated directory servers (sn-dir1 and sn-dir2).

## Prerequisites

- SPIRE agent running in docker-compose (already configured)
- Access to SPIRE server on sn-dir1/sn-dir2 via kubectl

## Steps to Add SPIRE Authentication to an App

### 1. Create Workload Entry on SPIRE Server

On sn-dir1, create a workload entry for your app:

```bash
kubectl exec -n dir-prod-spire spire-server-0 -- \
  /opt/spire/bin/spire-server entry create \
  -spiffeID spiffe://sn-dir1.labs.outshift.com/my-app \
  -parentID spiffe://sn-dir1.labs.outshift.com/spire/agent/join_token/eac97904-2b34-4609-9e73-49db28dddf3c \
  -selector unix:uid:0 \
  -federatesWith sn-dir2.labs.outshift.com
```

**Parameters:**
- `spiffeID`: Unique identity for your app (change `my-app` to your app name)
- `parentID`: Your SPIRE agent's ID (use the join token from your agent)
- `selector`: How to identify the app
  - `unix:uid:0` - for containers running as root
  - `unix:uid:1000` - for containers running as UID 1000
  - `docker:label:com.docker.compose.service:my-app` - by compose service name
- `federatesWith`: Add `sn-dir2.labs.outshift.com` to access both directories

### 2. Update docker-compose.yaml

Add these settings to your app service:

```yaml
  my-app:
    # ... your existing app configuration ...
    environment:
      - DIRECTORY_SERVER_ADDRESS=sn-dir1.labs.outshift.com:8888
      - SPIFFE_SOCKET_PATH=/run/spire/sockets/agent.sock
      - AUTH_MODE=x509
    volumes:
      - spire-agent-socket:/run/spire/sockets:ro
```

### 3. Ensure SPIRE Agent is Running

The spire-agent service must be configured in docker-compose.yaml with:
- `pid: host` - Required for the agent to attest containers
- `spire-agent-socket` volume - Shared Unix socket for SPIFFE credentials
- Docker socket mounted - Allows agent to inspect containers

Start/restart your app:
```bash
docker compose up -d my-app
```

## How It Works

1. **Shared Volume**: Both spire-agent and your app mount the `spire-agent-socket` Docker volume
2. **Unix Socket**: The SPIRE agent creates a Unix socket at `/run/spire/sockets/agent.sock`
3. **Attestation**: When your app connects to the socket, the agent verifies it matches the workload entry selector
4. **Credentials**: The agent provides X.509 SVID certificates to your app
5. **Directory Connection**: Your app uses these credentials to authenticate to the directory server

## Key Configuration Details

### SPIRE Agent Requirements
- **Must** have `pid: host` to see and attest processes in other containers
- **Must** mount Docker socket to use Docker workload attestor
- **Must** share `spire-agent-socket` volume with apps

### Application Requirements
- **Must** mount `spire-agent-socket:/run/spire/sockets:ro` volume
- **Must** set environment variables for directory connection
- **Must** have matching workload entry on SPIRE server

### Workload Entry Selectors
Choose the selector that matches how your app runs:
- `unix:uid:X` - Best for containers (use the UID the container runs as)
- `docker:label:KEY:VALUE` - Alternative for Docker containers
- `docker:image_id:IMAGE` - By container image

## Testing Connection

Test if your app can connect:

```bash
docker exec my-app python3 -c "
from agntcy.dir_sdk.client import Client, Config
from agntcy.dir_sdk.models import search_v1

config = Config(
    server_address='sn-dir1.labs.outshift.com:8888',
    auth_mode='x509',
    spiffe_socket_path='unix:///run/spire/sockets/agent.sock'
)
client = Client(config)
req = search_v1.SearchRecordsRequest(queries=[], limit=10)
results = list(client.search_client.SearchRecords(req))
print(f'✓ Connected: {len(results)} agents')
"
```

## Troubleshooting

### "Connection refused" on socket
- Ensure both spire-agent and your app use the `spire-agent-socket` volume (not host bind mount)
- Verify spire-agent is running: `docker ps | grep spire-agent`

### "Could not resolve caller information"
- Check spire-agent has `pid: host`
- Verify workload entry selector matches your app's UID or Docker labels
- Check agent logs: `docker logs spire-agent --tail 50`

### "Timeout waiting for first update"
- Verify workload entry exists on SPIRE server
- Check the selector matches your app
- Ensure parentID matches your agent's SPIFFE ID

## Example: directory-mcp-server

See the `directory-mcp-server` service in docker-compose.yaml for a working example.

Workload entry on sn-dir1:
```bash
Entry ID         : 969d6e10-2e3c-42fa-9f0f-3795ff37be9a
SPIFFE ID        : spiffe://sn-dir1.labs.outshift.com/directory-mcp-server-uid
Parent ID        : spiffe://sn-dir1.labs.outshift.com/spire/agent/join_token/eac97904-2b34-4609-9e73-49db28dddf3c
Selector         : unix:uid:1000
FederatesWith    : sn-dir2.labs.outshift.com
```
