# Directory MCP Server

A Model Context Protocol (MCP) server providing directory operations for agent federation networks. Supports SPIFFE authentication, multi-node operations, and comprehensive directory management.

## Features

- **8 Directory Operations**: search, pull, export, push, routing_publish, routing_search, sync_create, sync_status
- **SPIFFE Authentication**: X.509 and JWT modes for secure federation access
- **Multi-Node Support**: Connect to multiple directory nodes with single authentication
- **Stdio Transport**: Standard MCP communication protocol
- **Container-Ready**: Designed for containerized deployment

## Quick Start

### Local Development

```bash
# Install dependencies
uv sync

# Run server (no authentication)
DIRECTORY_SERVER_ADDRESS=localhost:8888 python server.py
```

### Production Deployment

```bash
# Build container
docker build -t directory-mcp-server .

# Run with SPIFFE authentication
docker run -i \
  -e DIRECTORY_SERVER_ADDRESS=dir1.example.com:8888 \
  -e SPIFFE_SOCKET_PATH=/run/spire/sockets/agent.sock \
  -e AUTH_MODE=x509 \
  -v /run/spire/sockets:/run/spire/sockets:ro \
  directory-mcp-server
```

## Architecture

### CRITICAL: User ID Requirement

**The container MUST run as uid 1000** to match the SPIRE workload entry selector (`unix:uid:1000`).

The Dockerfile includes `USER 1000:1000` to ensure this. If you override this, SPIRE will refuse to issue certificates.

**Alternative**: Add a workload entry for root (uid 0) on the SPIRE server:
```bash
kubectl exec -n dir-prod-spire spire-server-0 -- /opt/spire/bin/spire-server entry create \
  -spiffeID spiffe://sn-dir1.labs.outshift.com/workload/dirctl \
  -parentID spiffe://sn-dir1.labs.outshift.com/agent/<AGENT_NAME> \
  -selector unix:uid:0 \
  -federatesWith sn-dir2.labs.outshift.com
```

## Deployment Pattern

The MCP server runs in a **separate container** from the agent for security isolation and independent scaling:

```
┌─────────────────┐         ┌──────────────────┐
│  Agent          │ stdio   │  MCP Server      │
│  Container      │────────▶│  Container       │
│                 │         │  (Directory)     │
└─────────────────┘         └──────────────────┘
                                     │
                                     ▼
                            ┌──────────────────┐
                            │  Directory       │
                            │  Federation      │
                            │  Network         │
                            └──────────────────┘
```

### Communication

- **Transport**: stdio (standard input/output)
- **Protocol**: JSON-RPC over stdio
- **Connection**: Agent uses `docker exec` to communicate with server

## Configuration

### Environment Variables

| Variable | Required | Description | Example |
|----------|----------|-------------|---------|
| `DIRECTORY_SERVER_ADDRESS` | Yes | Default directory node | `dir1.example.com:8888` |
| `SPIFFE_SOCKET_PATH` | No | SPIFFE agent socket path | `/run/spire/sockets/agent.sock` |
| `AUTH_MODE` | No | Authentication mode: `x509`, `jwt` | `x509` |
| `JWT_AUDIENCE` | No | JWT audience (required for JWT mode) | `spiffe://example.org/dir` |

### Authentication Modes

**SPIFFE X.509 (Production)**
```bash
DIRECTORY_SERVER_ADDRESS=dir1.example.com:8888
SPIFFE_SOCKET_PATH=/run/spire/sockets/agent.sock
AUTH_MODE=x509
```

**SPIFFE JWT (Alternative)**
```bash
DIRECTORY_SERVER_ADDRESS=dir1.example.com:8888
SPIFFE_SOCKET_PATH=/run/spire/sockets/agent.sock
AUTH_MODE=jwt
JWT_AUDIENCE=spiffe://example.org/directory-server
```

**Insecure (Development Only)**
```bash
DIRECTORY_SERVER_ADDRESS=localhost:8888
```

## Available Tools

### Read Operations

- **search** - Search local directory by name/skill
- **pull** - Retrieve record by CID
- **export** - Export record to specific format (A2A)

### Write Operations

- **push** - Upload OASF record to directory
- **routing_publish** - Publish record to federation network

### Network Operations

- **routing_search** - Search across federated directories

### Sync Operations

- **sync_create** - Pull records from remote directory
- **sync_status** - Monitor sync operation status

## Usage

### dirctl Command Line

```bash
# Set environment variables
export DIRECTORY_CLIENT_SPIFFE_SOCKET_PATH=unix:///run/spire/sockets/agent.sock
export DIRECTORY_SERVER_ADDRESS=sn-dir1.labs.outshift.com:8888

# Search (MUST specify --auth-mode x509)
dirctl search --auth-mode x509 --limit 10

# Pull specific record
dirctl pull --auth-mode x509 <CID>
```

**CRITICAL**: `--auth-mode x509` must be explicitly specified. Auto-detect does not work reliably with SPIFFE authentication.

### MCP Server Examples

### From Agent Container

```python
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

# Connect to MCP server container
server_params = StdioServerParameters(
    command="docker",
    args=["exec", "-i", "directory-mcp-server", "python", "server.py"]
)

async with stdio_client(server_params) as (read, write):
    async with ClientSession(read, write) as session:
        await session.initialize()
        
        # Search directory
        result = await session.call_tool("search", {
            "name": "agent-name",
            "skill": "nlp"
        })
        
        # Push record
        result = await session.call_tool("push", {
            "record": {
                "schema_version": "0.8.0",
                "name": "my-agent",
                "version": "v1.0.0",
                # ... full OASF record
            }
        })
        
        # Search federation
        result = await session.call_tool("routing_search", {
            "skill": "natural_language_processing",
            "limit": 50
        })
```

### Multi-Node Operations

```python
# Use default node
await session.call_tool("search", {"name": "test"})

# Override to specific node
await session.call_tool("search", {
    "name": "test",
    "node": "dir2.example.com:8888"
})
```

## Docker Deployment

### Dockerfile

```dockerfile
FROM python:3.10-slim

RUN pip install --no-cache-dir uv

WORKDIR /app
COPY pyproject.toml server.py ./
RUN uv sync

CMD ["uv", "run", "python", "server.py"]
```

### Docker Compose

```yaml
version: '3.8'

services:
  directory-mcp-server:
    build: .
    container_name: directory-mcp-server
    stdin_open: true
    tty: true
    environment:
      DIRECTORY_SERVER_ADDRESS: ${DIRECTORY_SERVER_ADDRESS}
      SPIFFE_SOCKET_PATH: ${SPIFFE_SOCKET_PATH:-}
      AUTH_MODE: ${AUTH_MODE:-}
      JWT_AUDIENCE: ${JWT_AUDIENCE:-}
    volumes:
      - /run/spire/sockets:/run/spire/sockets:ro
    restart: unless-stopped
```

## Testing

Run the included test suites:

```bash
# Cross-node operations test
python tests/test_mcp_crossnode.py

# Complete federation workflow test
python tests/test_mcp_complete.py
```

Both tests verify:
- Push and publish operations
- Federation search
- Cross-node pull
- Sync operations
- SPIFFE authentication

## SPIFFE Setup

### Prerequisites

1. SPIRE server running in infrastructure
2. SPIRE agent running on host
3. Workload registration for MCP server

### Register Workload

```bash
spire-server entry create \
  -parentID spiffe://example.org/agent/node1 \
  -spiffeID spiffe://example.org/directory-mcp-server \
  -selector docker:label:app:directory-mcp-server \
  -ttl 3600
```

### Verify Setup

```bash
# Check socket
ls -la /run/spire/sockets/agent.sock

# Test SPIFFE connection
spire-agent api fetch x509 -socketPath /run/spire/sockets/agent.sock
```

## Security

- **Container Isolation**: Run in separate container from agent
- **SPIFFE Authentication**: Use X.509 or JWT for production
- **Read-Only Mounts**: Mount SPIFFE socket as read-only
- **Minimal Permissions**: Run as non-root user
- **Credential Rotation**: Automatic via SPIFFE
- **Network Isolation**: Use Docker networks

## Troubleshooting

### Connection Issues

```bash
# Check directory server connectivity
ping dir1.example.com
telnet dir1.example.com 8888

# Verify SPIFFE socket
docker exec directory-mcp-server ls -la /run/spire/sockets/
```

### View Logs

```bash
docker logs -f directory-mcp-server
```

### Common Issues

- **SPIFFE socket not found**: Verify socket is mounted and SPIRE agent is running
- **Authentication failed**: Check workload registration and trust domain
- **Connection refused**: Verify directory server address and network connectivity

## Documentation

- `docs/CONFIGURATION.md` - Detailed configuration guide
- `docs/QUICKREF.md` - Quick reference card
- `docs/SPIRE_SETUP.md` - SPIRE authentication setup for apps
- `docs/SPIRE_AGENT_INSTALLATION.md` - Complete SPIRE agent installation guide

## Requirements

- Python 3.10+
- uv package manager
- agntcy-dir SDK v1.0.0
- mcp SDK v1.1.0+

## License

Apache 2.0
# Using Directory with SPIFFE Authentication

Two options for connecting your agent to the AGNTCY Directory with SPIFFE X.509 authentication.

## Prerequisites

1. **SPIRE Agent running** on your host with socket at `/run/spire/sockets/agent.sock`
2. **Workload entry registered** on SPIRE server with selector `unix:uid:1000`
3. **Directory MCP Server image** available: `ghcr.io/agntcy/coffee-agntcy/directory-mcp-server:latest`

## Option 1: Use MCP Server (Recommended)

The MCP server provides directory operations as MCP tools that your agent can call.

### Standard MCP Pattern: Spawn On-Demand

The standard MCP architecture spawns the server process on-demand when needed. The agent controls the server lifecycle and **specifies which directory server to connect to**.

#### Agent Running in Container (Standard)

```yaml
# docker-compose.yml
services:
  my-agent:
    image: my-agent:latest
    user: "1000:1000"  # CRITICAL: Must match SPIRE workload entry
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock  # For spawning MCP server
```

**Note:** The agent determines which directory to connect to in its own logic - it doesn't need to be in docker-compose. The directory address can be:
- Hardcoded in agent code
- Read from agent's config file
- Passed as parameter to agent methods
- Determined dynamically based on agent logic

Agent code:

```python
import os
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

class DirectoryClient:
    def __init__(self, directory_address: str = None):
        # Agent determines directory address - could be from config, parameter, or logic
        self.directory_address = directory_address or "sn-dir1.labs.outshift.com:8888"
    
    def _get_mcp_params(self):
        """Create MCP server parameters - spawns on-demand"""
        return StdioServerParameters(
            command="docker",
            args=[
                "run", "-i", "--rm",
                "--user", "1000:1000",
                "-v", "/run/spire/sockets:/run/spire/sockets:ro",
                "-e", f"DIRECTORY_SERVER_ADDRESS={self.directory_address}",  # Agent provides this
                "-e", "SPIFFE_SOCKET_PATH=unix:///run/spire/sockets/agent.sock",
                "-e", "AUTH_MODE=x509",
                "ghcr.io/agntcy/coffee-agntcy/directory-mcp-server:latest",
                "python", "server.py"
            ]
        )
    
    async def search(self, skill: str):
        """Search directory for agents"""
        async with stdio_client(self._get_mcp_params()) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                result = await session.call_tool("search", arguments={
                    "skill": skill,
                    "limit": 10
                })
                return result
```

**Key points:**
- Agent container only needs Docker socket mount
- Agent determines directory address in its own logic (config, parameter, hardcoded, etc.)
- Agent passes directory address to MCP server when spawning it
- MCP server has no default - agent must specify the directory
```

#### Agent Running on Host

If your agent runs directly on the host (not in a container):

```python
import os
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

class DirectoryClient:
    def __init__(self, directory_address: str = "sn-dir1.labs.outshift.com:8888"):
        # Agent determines directory address - from parameter, config, or default
        self.directory_address = directory_address
    
    def _get_mcp_params(self):
        """Create MCP server parameters - spawns on-demand"""
        return StdioServerParameters(
            command="docker",
            args=[
                "run", "-i", "--rm",
                "--user", "1000:1000",
                "-v", "/run/spire/sockets:/run/spire/sockets:ro",
                "-e", f"DIRECTORY_SERVER_ADDRESS={self.directory_address}",  # Agent provides this
                "-e", "SPIFFE_SOCKET_PATH=unix:///run/spire/sockets/agent.sock",
                "-e", "AUTH_MODE=x509",
                "ghcr.io/agntcy/coffee-agntcy/directory-mcp-server:latest",
                "python", "server.py"
            ]
        )
    
    async def search(self, skill: str):
        """Search directory for agents"""
        async with stdio_client(self._get_mcp_params()) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                result = await session.call_tool("search", arguments={
                    "skill": skill,
                    "limit": 10
                })
                return result
```

### Alternative: Sidecar Pattern (Non-Standard)

If you prefer a persistent MCP server (useful for existing container orchestration setups):

**Why sidecar needs `DIRECTORY_SERVER_ADDRESS`:** The sidecar is a persistent container that starts once and waits for connections. It needs to know its default directory at startup. The agent doesn't spawn it - it just connects to it.

```yaml
# docker-compose.yml
services:
  my-agent:
    image: my-agent:latest
    user: "1000:1000"
    depends_on:
      - directory-mcp-server
  
  directory-mcp-server:
    image: ghcr.io/agntcy/coffee-agntcy/directory-mcp-server:latest
    user: "1000:1000"
    stdin_open: true
    tty: true
    volumes:
      - /run/spire/sockets:/run/spire/sockets:ro
    environment:
      - DIRECTORY_SERVER_ADDRESS=sn-dir1.labs.outshift.com:8888  # Required: sidecar's default directory
      - SPIFFE_SOCKET_PATH=unix:///run/spire/sockets/agent.sock
      - AUTH_MODE=x509
```

Agent code for sidecar:

```python
server_params = StdioServerParameters(
    command="docker",
    args=["exec", "-i", "directory-mcp-server", "python", "server.py"]
)
```

**Multi-directory support with sidecar:**

The sidecar has a default directory from `DIRECTORY_SERVER_ADDRESS`, but can connect to other directories using the `node` parameter:

```python
# Search default directory
await session.call_tool("search", {"skill": "coffee"})

# Search different directory (federation)
await session.call_tool("search", {
    "skill": "coffee",
    "node": "sn-dir2.labs.outshift.com:8888"
})
```

### Complete Agent Example with MCP

```python
import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
import json

class DirectoryAgent:
    def __init__(self):
        # Standard MCP pattern - spawn on-demand
        self.server_params = StdioServerParameters(
            command="docker",
            args=[
                "run", "-i", "--rm",
                "--user", "1000:1000",
                "-v", "/run/spire/sockets:/run/spire/sockets:ro",
                "-e", "DIRECTORY_SERVER_ADDRESS=sn-dir1.labs.outshift.com:8888",
                "-e", "SPIFFE_SOCKET_PATH=unix:///run/spire/sockets/agent.sock",
                "-e", "AUTH_MODE=x509",
                "ghcr.io/agntcy/coffee-agntcy/directory-mcp-server:latest",
                "python", "server.py"
            ]
        )
    
    async def search_agents(self, skill: str):
        """Search for agents with specific skill"""
        async with stdio_client(self.server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                
                # Call search tool
                result = await session.call_tool("search", arguments={
                    "skill": skill,
                    "limit": 10
                })
                
                # Parse result
                search_data = json.loads(result.content[0].text)
                return search_data.get("results", [])
    
    async def get_agent_details(self, cid: str):
        """Get full agent record"""
        async with stdio_client(self.server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                
                # Call pull tool
                result = await session.call_tool("pull", arguments={"cid": cid})
                
                # Parse result
                record_data = json.loads(result.content[0].text)
                return record_data

# Usage
async def main():
    agent = DirectoryAgent()
    
    # Search for agents
    agents = await agent.search_agents("coffee_processing")
    print(f"Found {len(agents)} agents")
    
    # Get details for first agent
    if agents:
        cid = agents[0]["cid"]
        details = await agent.get_agent_details(cid)
        print(f"Agent: {details['name']}")
        print(f"Skills: {[s['name'] for s in details.get('skills', [])]}")

if __name__ == "__main__":
    asyncio.run(main())
```

### Available MCP Tools

- `search` - Search for agents by name, skill, domain
- `pull` - Get full record by CID
- `export` - Export record to A2A format
- `push` - Upload OASF record
- `delete` - Delete record by CID
- `routing_search` - P2P search across federation
- `routing_publish` - Publish to federation
- `routing_unpublish` - Remove from federation
- `sync_create` - Pull from remote directory
- `sync_status` - Monitor sync progress

### Example: Search and Pull

```python
# Search for agents
search_result = await session.call_tool("search", arguments={
    "skill": "coffee_processing",
    "limit": 5
})

# Extract CIDs from result
cids = search_result.content[0].text  # Parse JSON response

# Pull full records
for cid in cids:
    record = await session.call_tool("pull", arguments={"cid": cid})
    # Process record...
```

## Option 2: Use Python SDK Directly

For direct API access without MCP layer.

### Installation

```bash
pip install agntcy-dir==1.0.0
```

### Basic Usage

```python
from agntcy.dir_sdk.client import Client, Config
from agntcy.dir_sdk.models import search_v1
from google.protobuf.json_format import MessageToDict

# Configure client
config = Config(
    server_address="sn-dir1.labs.outshift.com:8888",
    spiffe_socket_path="unix:///run/spire/sockets/agent.sock",
    auth_mode="x509"  # CRITICAL: Must specify x509
)

# Create client
client = Client(config)

# Search for agents
search_req = search_v1.SearchRecordsRequest(
    queries=[
        search_v1.RecordQuery(
            type=search_v1.RECORD_QUERY_TYPE_SKILL_NAME,
            value="agent_orchestration"
        )
    ],
    limit=10
)

# Execute search
results = list(client.search_records(search_req))

# Process results
for result in results:
    # Convert protobuf Struct to dict
    record_data = MessageToDict(result.record.data)
    
    print(f"Name: {record_data.get('name')}")
    print(f"CID: {result.cid}")
    print(f"Skills: {[s.get('name') for s in record_data.get('skills', [])]}")
```

### Search by Different Criteria

```python
from agntcy.dir_sdk.models import search_v1

# By name
search_v1.RecordQuery(
    type=search_v1.RECORD_QUERY_TYPE_NAME,
    value="Coffee*"  # Supports wildcards
)

# By skill
search_v1.RecordQuery(
    type=search_v1.RECORD_QUERY_TYPE_SKILL_NAME,
    value="coffee_processing"
)

# By domain
search_v1.RecordQuery(
    type=search_v1.RECORD_QUERY_TYPE_DOMAIN,
    value="agriculture"
)
```

### Pull Specific Record

```python
# Pull by CID
record = client.pull_record(cid="bafyreiabc123...")

# Access record data
data = MessageToDict(record.data)
print(f"Name: {data.get('name')}")
print(f"Description: {data.get('description')}")
```

### Push New Record

```python
from agntcy.dir_sdk.models import core_v1

# Create record
record_dict = {
    "name": "My Agent",
    "description": "Agent description",
    "skills": [{"name": "skill1"}, {"name": "skill2"}],
    "domains": ["domain1"],
    "locators": [{"url": "http://my-agent:8080"}]
}

record = core_v1.Record(data=record_dict)

# Push to directory
refs = client.push([record])
print(f"Pushed with CID: {refs[0].cid}")
```

### Federation Operations

```python
from agntcy.dir_sdk.models import routing_v1

# Publish to federation
publish_req = routing_v1.PublishRequest(
    record_refs=routing_v1.RecordRefs(refs=refs)
)
client.publish(publish_req)

# Search across federation
routing_search_req = routing_v1.SearchRequest(
    queries=[
        routing_v1.RecordQuery(
            type=routing_v1.RECORD_QUERY_TYPE_SKILL,
            value="skill_name"
        )
    ]
)
results = list(client.routing_client.Search(routing_search_req))
```

### Running in Docker Container

If your agent runs in a container, ensure it:

1. **Runs as uid 1000**: `--user 1000:1000`
2. **Mounts SPIRE socket**: `-v /run/spire/sockets:/run/spire/sockets:ro`
3. **Has network access** to directory server

```dockerfile
FROM python:3.10-slim

# Install SDK
RUN pip install agntcy-dir==1.0.0

# CRITICAL: Run as uid 1000 to match SPIRE workload entry
USER 1000:1000

# Your agent code
COPY agent.py .
CMD ["python", "agent.py"]
```

## Troubleshooting

### "No identity issued" Error

**Cause**: Process UID doesn't match SPIRE workload entry selector.

**Solution**: Ensure process runs as uid 1000, or add workload entry for your UID:

```bash
kubectl exec -n dir-prod-spire spire-server-0 -- /opt/spire/bin/spire-server entry create \
  -spiffeID spiffe://sn-dir1.labs.outshift.com/workload/my-agent \
  -parentID spiffe://sn-dir1.labs.outshift.com/agent/<AGENT_NAME> \
  -selector unix:uid:1000 \
  -federatesWith sn-dir2.labs.outshift.com
```

### "Socket closed" or Connection Hangs

**Cause**: Container running as wrong user (root instead of uid 1000).

**Solution**: Add `--user 1000:1000` to docker run or `USER 1000:1000` in Dockerfile.

### "TLS handshake failed" or "EOF" Error

**Cause**: Auth mode not specified or auto-detect failing.

**Solution**: Explicitly set `auth_mode="x509"` in SDK Config or `--auth-mode x509` for dirctl.

### SDK Methods Blocking

**Cause**: SDK methods are synchronous but called in async context.

**Solution**: Run in executor:

```python
import asyncio

loop = asyncio.get_event_loop()
results = await loop.run_in_executor(None, lambda: client.search_records(req))
```

## Complete Example: Agent with Directory Search

```python
import asyncio
from agntcy.dir_sdk.client import Client, Config
from agntcy.dir_sdk.models import search_v1
from google.protobuf.json_format import MessageToDict

class MyAgent:
    def __init__(self):
        config = Config(
            server_address="sn-dir1.labs.outshift.com:8888",
            spiffe_socket_path="unix:///run/spire/sockets/agent.sock",
            auth_mode="x509"
        )
        self.dir_client = Client(config)
    
    async def find_agents(self, skill: str):
        """Search for agents with specific skill"""
        req = search_v1.SearchRecordsRequest(
            queries=[
                search_v1.RecordQuery(
                    type=search_v1.RECORD_QUERY_TYPE_SKILL_NAME,
                    value=skill
                )
            ],
            limit=10
        )
        
        # Run synchronous SDK call in executor
        loop = asyncio.get_event_loop()
        results = await loop.run_in_executor(
            None, 
            lambda: list(self.dir_client.search_records(req))
        )
        
        # Process results
        agents = []
        for result in results:
            data = MessageToDict(result.record.data)
            agents.append({
                "cid": result.cid,
                "name": data.get("name"),
                "skills": [s.get("name") for s in data.get("skills", [])],
                "locators": data.get("locators", [])
            })
        
        return agents

# Usage
async def main():
    agent = MyAgent()
    agents = await agent.find_agents("coffee_processing")
    print(f"Found {len(agents)} agents")
    for agent_info in agents:
        print(f"  - {agent_info['name']} ({agent_info['cid']})")

if __name__ == "__main__":
    asyncio.run(main())
```

## Summary

**Use MCP Server when:**
- You want standardized tool interface
- Your agent already uses MCP
- You need isolation between agent and directory client

**Use Python SDK when:**
- You need direct API access
- You want more control over operations
- You're building custom directory integrations

Both options use the same SPIFFE X.509 authentication and connect to the same directory servers.
# CRITICAL: User ID Configuration for SPIRE

## The Problem

SPIRE workload attestation uses **Unix UID selectors** to determine which processes can receive X.509 certificates. If your process runs as a different UID than what's registered in the SPIRE server, it will be **denied certificates**.

## Default Configuration

- **Workload Entry Selector**: `unix:uid:1000`
- **Container User**: `USER 1000:1000` (set in Dockerfile)
- **Host dirctl User**: `ubuntu` (uid 1000)

## Symptoms of UID Mismatch

- SPIRE agent logs: `"No identity issued" registered=false`
- SDK errors: `"Socket closed"` or connection hangs
- Containers block indefinitely when trying to get certificates

## Solutions

### Option 1: Run Container as uid 1000 (Default)

The Dockerfile includes `USER 1000:1000`. This is the **recommended approach**.

```dockerfile
# Dockerfile already has this:
USER 1000:1000
CMD ["python", "server.py"]
```

### Option 2: Add Workload Entry for Root (uid 0)

If you need to run as root, add this entry on the SPIRE server:

```bash
kubectl exec -n dir-prod-spire spire-server-0 -- /opt/spire/bin/spire-server entry create \
  -spiffeID spiffe://sn-dir1.labs.outshift.com/workload/dirctl \
  -parentID spiffe://sn-dir1.labs.outshift.com/agent/<AGENT_NAME> \
  -selector unix:uid:0 \
  -federatesWith sn-dir2.labs.outshift.com
```

Replace `<AGENT_NAME>` with your agent's name (e.g., `ubuntu`, `lab-3li6682`).

### Option 3: Add Multiple UID Selectors

To support both uid 0 and uid 1000, create separate workload entries for each.

## Verification

Check what workload entries exist for your agent:

```bash
kubectl exec -n dir-prod-spire spire-server-0 -- /opt/spire/bin/spire-server entry show \
  -parentID spiffe://sn-dir1.labs.outshift.com/agent/<AGENT_NAME>
```

Look for the `Selector` field - it should match your process's UID.

## Testing

Test if your process can get certificates:

```bash
# As uid 1000
docker run --rm --user 1000:1000 \
  -v /run/spire/sockets:/run/spire/sockets:ro \
  ghcr.io/agntcy/coffee-agntcy/directory-mcp-server:latest \
  python -c "from agntcy.dir_sdk.client import Client, Config; \
    c = Client(Config(server_address='sn-dir1.labs.outshift.com:8888', \
    spiffe_socket_path='unix:///run/spire/sockets/agent.sock', auth_mode='x509')); \
    print('✅ Works')"
```

If this succeeds, your UID configuration is correct.
