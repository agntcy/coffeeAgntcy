# SPIRE Agent Installation and Directory Access Setup

Complete guide for setting up SPIRE agent on a new host to access the federated directory servers (sn-dir1 and sn-dir2).

## Overview

This guide covers:
1. Installing SPIRE agent on a new host
2. Registering the agent with SPIRE server
3. Configuring applications to use the agent
4. Two options: Direct SDK access or via MCP server

## Prerequisites

- Docker and Docker Compose installed on the host
- Access to SPIRE server on sn-dir1 (kubectl access)
- Network connectivity to sn-dir1.labs.outshift.com:8081 (SPIRE) and :8888 (Directory)

---

## Part 1: SPIRE Agent Installation

### Step 1: Create SPIRE Agent Configuration Directory

On your new host:

```bash
sudo mkdir -p /opt/spire/conf/agent
sudo mkdir -p /opt/spire/data/agent
```

### Step 2: Create Agent Configuration File

Create `/opt/spire/conf/agent/agent.conf`:

```bash
sudo tee /opt/spire/conf/agent/agent.conf > /dev/null << 'EOF'
agent {
    data_dir = "/opt/spire/data/agent"
    log_level = "INFO"
    server_address = "sn-dir1.labs.outshift.com"
    server_port = "8081"
    socket_path = "/run/spire/sockets/agent.sock"
    trust_domain = "sn-dir1.labs.outshift.com"
    insecure_bootstrap = true
}

plugins {
    NodeAttestor "join_token" {
        plugin_data {}
    }
    KeyManager "disk" {
        plugin_data {
            directory = "/opt/spire/data/agent"
        }
    }
    WorkloadAttestor "unix" {
        plugin_data {}
    }
    WorkloadAttestor "docker" {
        plugin_data {
            docker_socket_path = "unix:///var/run/docker.sock"
        }
    }
}
EOF
```

**Configuration explained:**
- `server_address`: SPIRE server location
- `trust_domain`: Must match the SPIRE server's trust domain
- `insecure_bootstrap`: Allows initial connection (secure after first attestation)
- `unix` attestor: For attesting processes by UID/GID
- `docker` attestor: For attesting Docker containers

### Step 3: Generate Join Token on SPIRE Server

On a machine with kubectl access to sn-dir1:

```bash
# Generate a join token (valid for 1 hour)
kubectl exec -n dir-prod-spire spire-server-0 -- \
  /opt/spire/bin/spire-server token generate \
  -spiffeID spiffe://sn-dir1.labs.outshift.com/spire/agent/join_token/$(uuidgen) \
  -ttl 3600
```

**Output example:**
```
Token: 12345678-abcd-1234-5678-1234567890ab
```

Save this token - you'll need it in the next step.

### Step 4: Add SPIRE Agent to Docker Compose

In your project's `docker-compose.yaml`, add:

```yaml
services:
  spire-agent:
    image: ghcr.io/spiffe/spire-agent:1.9.0
    container_name: spire-agent
    command: ["-config", "/opt/spire/conf/agent/agent.conf", "-joinToken", "YOUR_JOIN_TOKEN_HERE"]
    pid: host
    volumes:
      - spire-agent-socket:/run/spire/sockets
      - /opt/spire/conf/agent:/opt/spire/conf/agent:ro
      - /opt/spire/data/agent:/opt/spire/data/agent
      - /var/run/docker.sock:/var/run/docker.sock:ro
    restart: unless-stopped

volumes:
  spire-agent-socket:
```

**Important settings:**
- `pid: host` - Required for agent to attest containers
- `spire-agent-socket` - Docker volume for sharing Unix socket
- Docker socket mounted - Allows Docker workload attestation
- `-joinToken` - Use the token from Step 3 (only needed for first run)

**Note:** After the first successful attestation, the agent persists its SVID in `/opt/spire/data/agent`. You can remove the `-joinToken` argument after the first run, or leave it (it will be ignored once the agent is attested).

### Step 5: Start SPIRE Agent

```bash
docker compose up -d spire-agent
```

Verify it's running:

```bash
docker logs spire-agent --tail 20
```

Look for:
```
level=info msg="Successfully rotated agent SVID"
```

---

## Part 2: Register Workload Entries

For each application that needs directory access, create a workload entry on the SPIRE server.

### Get Your Agent's SPIFFE ID

```bash
docker logs spire-agent 2>&1 | grep "agent SVID" | tail -1
```

**Output example:**
```
spiffe_id="spiffe://sn-dir1.labs.outshift.com/spire/agent/join_token/12345678-abcd-1234-5678-1234567890ab"
```

Save this as `AGENT_SPIFFE_ID` for the next steps.

### Create Workload Entry for Your App

On the SPIRE server:

```bash
kubectl exec -n dir-prod-spire spire-server-0 -- \
  /opt/spire/bin/spire-server entry create \
  -spiffeID spiffe://sn-dir1.labs.outshift.com/my-app \
  -parentID AGENT_SPIFFE_ID \
  -selector unix:uid:0 \
  -federatesWith sn-dir2.labs.outshift.com
```

**Selector options:**
- `unix:uid:0` - For containers running as root
- `unix:uid:1000` - For containers running as UID 1000
- `docker:label:com.docker.compose.service:my-app` - By compose service name

**Important:** Include `-federatesWith sn-dir2.labs.outshift.com` to access both directories.

---

## Part 3: Application Configuration

You have two options for accessing the directory:

### Option A: Direct SDK Access (Recommended for custom apps)

Add to your app's service in `docker-compose.yaml`:

```yaml
  my-app:
    image: my-app:latest
    container_name: my-app
    environment:
      - DIRECTORY_SERVER_ADDRESS=sn-dir1.labs.outshift.com:8888
      - SPIFFE_SOCKET_PATH=/run/spire/sockets/agent.sock
      - AUTH_MODE=x509
    volumes:
      - spire-agent-socket:/run/spire/sockets:ro
    # ... rest of your app config
```

**In your application code:**

```python
from agntcy.dir_sdk.client import Client, Config
from agntcy.dir_sdk.models import search_v1

# Create client
config = Config(
    server_address='sn-dir1.labs.outshift.com:8888',
    auth_mode='x509',
    spiffe_socket_path='unix:///run/spire/sockets/agent.sock'
)
client = Client(config)

# Search directory
req = search_v1.SearchRecordsRequest(
    queries=[
        search_v1.RecordQuery(
            type=search_v1.RECORD_QUERY_TYPE_NAME,
            value='my-agent'
        )
    ],
    limit=100
)
results = list(client.search_client.SearchRecords(req))
```

### Option B: Via MCP Server (Recommended for AI agents)

The MCP server provides a Model Context Protocol interface to the directory, useful for AI agents like Claude.

#### Step 1: Create Workload Entry for MCP Server

```bash
kubectl exec -n dir-prod-spire spire-server-0 -- \
  /opt/spire/bin/spire-server entry create \
  -spiffeID spiffe://sn-dir1.labs.outshift.com/directory-mcp-server \
  -parentID AGENT_SPIFFE_ID \
  -selector unix:uid:0 \
  -federatesWith sn-dir2.labs.outshift.com
```

#### Step 2: Add MCP Server to Docker Compose

```yaml
  directory-mcp-server:
    image: ghcr.io/agntcy/coffee-agntcy/directory-mcp-server:latest
    container_name: directory-mcp-server
    stdin_open: true
    tty: true
    environment:
      - DIRECTORY_SERVER_ADDRESS=sn-dir1.labs.outshift.com:8888
      - SPIFFE_SOCKET_PATH=/run/spire/sockets/agent.sock
      - AUTH_MODE=x509
    volumes:
      - spire-agent-socket:/run/spire/sockets:ro
    restart: unless-stopped
```

#### Step 3: Configure Your App to Use MCP Server

Your app connects to the MCP server via `docker exec`:

```python
import subprocess
import json

def search_directory(query):
    """Search directory via MCP server"""
    cmd = [
        'docker', 'exec', 'directory-mcp-server',
        'python3', '-c',
        f'''
import asyncio, sys, json
sys.path.insert(0, "/app")
from server import DirectoryMCPServer

async def search():
    server = DirectoryMCPServer()
    result = await server.search(name="{query}")
    print(json.dumps(result))

asyncio.run(search())
        '''
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    return json.loads(result.stdout)
```

**MCP Server provides these tools:**
- `search` - Search for agents by name or skill
- `get` - Get agent details by CID
- `push` - Publish new agent records
- `delete` - Delete agent records
- `routing_search` - Search across federated directories
- `routing_publish` - Publish to routing network
- `routing_unpublish` - Unpublish from routing network

---

## Part 4: Testing the Setup

### Test 1: Verify SPIRE Agent is Working

```bash
# Check agent logs
docker logs spire-agent --tail 30

# Should see:
# - "Successfully rotated agent SVID"
# - "Starting Workload and SDS APIs"
# - No "Connection refused" errors
```

### Test 2: Test Direct SDK Access

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
print(f'✓ Connected to sn-dir1: {len(results)} agents')
"
```

### Test 3: Test MCP Server Access

```bash
docker exec directory-mcp-server python3 -c "
import asyncio, sys
sys.path.insert(0, '/app')
from server import DirectoryMCPServer

async def test():
    server = DirectoryMCPServer()
    
    # Test sn-dir1
    result1 = await server.search(name='*', node='sn-dir1.labs.outshift.com:8888')
    print(f'✓ sn-dir1: {result1[\"count\"]} agents')
    
    # Test sn-dir2 (federation)
    result2 = await server.search(name='*', node='sn-dir2.labs.outshift.com:8888')
    print(f'✓ sn-dir2: {result2[\"count\"]} agents')

asyncio.run(test())
"
```

---

## Troubleshooting

### Agent won't start

**Check logs:**
```bash
docker logs spire-agent
```

**Common issues:**
- Invalid join token (expired or wrong)
- Can't reach SPIRE server (check network/firewall)
- Config file syntax error

**Solution:**
- Generate new join token
- Verify `sn-dir1.labs.outshift.com:8081` is reachable
- Validate config file syntax

### "Connection refused" on socket

**Symptoms:**
```
ConnectionRefusedError: [Errno 111] Connection refused
```

**Cause:** App and agent not sharing the same socket volume

**Solution:**
- Ensure both use `spire-agent-socket` Docker volume (not host bind mount)
- Verify volume is defined in docker-compose.yaml
- Restart both containers

### "Could not resolve caller information"

**Symptoms:**
```
level=warning msg="Connection failed during accept" error="could not resolve caller information"
```

**Cause:** Agent can't attest the calling process

**Solutions:**
1. Verify agent has `pid: host`
2. Check workload entry selector matches your app:
   ```bash
   # Check what UID your app runs as
   docker exec my-app id
   
   # Update workload entry to match
   kubectl exec -n dir-prod-spire spire-server-0 -- \
     /opt/spire/bin/spire-server entry create \
     -spiffeID spiffe://sn-dir1.labs.outshift.com/my-app \
     -parentID AGENT_SPIFFE_ID \
     -selector unix:uid:ACTUAL_UID \
     -federatesWith sn-dir2.labs.outshift.com
   ```

### "Timeout waiting for first update"

**Symptoms:**
```
X509SourceError: Timeout waiting for the first update
```

**Cause:** No matching workload entry on SPIRE server

**Solution:**
1. Verify workload entry exists:
   ```bash
   kubectl exec -n dir-prod-spire spire-server-0 -- \
     /opt/spire/bin/spire-server entry show \
     -spiffeID spiffe://sn-dir1.labs.outshift.com/my-app
   ```

2. Check parentID matches your agent's SPIFFE ID

3. Verify selector matches your app's UID or Docker labels

### Can't connect to sn-dir2

**Cause:** Workload entry missing federation

**Solution:**
Add federation to existing entry:
```bash
kubectl exec -n dir-prod-spire spire-server-0 -- \
  /opt/spire/bin/spire-server entry update \
  -entryID YOUR_ENTRY_ID \
  -federatesWith sn-dir2.labs.outshift.com
```

---

## Security Notes

1. **Join Tokens**: Expire after use or TTL. Generate new tokens for each agent.

2. **insecure_bootstrap**: Only needed for initial connection. After first attestation, the agent uses its SVID.

3. **Socket Permissions**: The socket is only accessible to containers sharing the volume.

4. **Federation**: Only add `federatesWith` for apps that need multi-directory access.

5. **Workload Entries**: Create specific entries per app - don't use overly broad selectors like `unix:uid:0` for multiple apps.

---

## Complete Example: docker-compose.yaml

```yaml
services:
  # SPIRE Agent
  spire-agent:
    image: ghcr.io/spiffe/spire-agent:1.9.0
    container_name: spire-agent
    command: ["-config", "/opt/spire/conf/agent/agent.conf", "-joinToken", "YOUR_JOIN_TOKEN"]
    pid: host
    volumes:
      - spire-agent-socket:/run/spire/sockets
      - /opt/spire/conf/agent:/opt/spire/conf/agent:ro
      - /opt/spire/data/agent:/opt/spire/data/agent
      - /var/run/docker.sock:/var/run/docker.sock:ro
    restart: unless-stopped

  # Option A: Direct SDK Access
  my-app:
    image: my-app:latest
    container_name: my-app
    environment:
      - DIRECTORY_SERVER_ADDRESS=sn-dir1.labs.outshift.com:8888
      - SPIFFE_SOCKET_PATH=/run/spire/sockets/agent.sock
      - AUTH_MODE=x509
    volumes:
      - spire-agent-socket:/run/spire/sockets:ro
    depends_on:
      - spire-agent

  # Option B: MCP Server
  directory-mcp-server:
    image: ghcr.io/agntcy/coffee-agntcy/directory-mcp-server:latest
    container_name: directory-mcp-server
    stdin_open: true
    tty: true
    environment:
      - DIRECTORY_SERVER_ADDRESS=sn-dir1.labs.outshift.com:8888
      - SPIFFE_SOCKET_PATH=/run/spire/sockets/agent.sock
      - AUTH_MODE=x509
    volumes:
      - spire-agent-socket:/run/spire/sockets:ro
    restart: unless-stopped
    depends_on:
      - spire-agent

volumes:
  spire-agent-socket:
```

---

## Summary Checklist

- [ ] Create `/opt/spire/conf/agent/agent.conf` on host
- [ ] Generate join token on SPIRE server
- [ ] Add spire-agent to docker-compose.yaml with join token
- [ ] Start spire-agent: `docker compose up -d spire-agent`
- [ ] Get agent's SPIFFE ID from logs
- [ ] Create workload entry for each app on SPIRE server
- [ ] Add app to docker-compose.yaml with socket volume
- [ ] Start app: `docker compose up -d my-app`
- [ ] Test connection to sn-dir1 and sn-dir2

---

## Additional Resources

- SPIRE Documentation: https://spiffe.io/docs/latest/spire/
- Directory SDK: See `README.md`
- MCP Server: See `docs/CONFIGURATION.md`
- SPIRE Setup Details: See `docs/SPIRE_SETUP.md`
