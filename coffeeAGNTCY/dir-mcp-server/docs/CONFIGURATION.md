# Directory MCP Server - Configuration Guide

## Overview

This MCP server provides directory operations for agent federation networks. It uses the stdio transport protocol for communication with MCP clients and supports multiple authentication methods for secure directory access.

## Transport Protocol

The server uses **stdio (standard input/output)** transport, which is the standard for MCP servers running in containers. The client launches the server process and communicates via JSON-RPC messages over stdin/stdout.

## Deployment Architecture

### Recommended: Separate Container

MCP servers should run in **separate containers** from the agent for:
- **Security isolation** - Limits attack surface and credential exposure
- **Independent scaling** - Scale directory operations separately from agent logic
- **Resource management** - Dedicated resources for directory operations
- **Credential containment** - SPIFFE credentials isolated to directory container

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

## Authentication Methods

### 1. SPIFFE X.509 (Production - Recommended)

Uses SPIFFE Workload API to obtain X.509-SVID certificates for mutual TLS authentication.

**When to use:**
- Production deployments
- Multi-node federation with mutual authentication
- Enterprise environments with PKI infrastructure

**Configuration:**
```bash
DIRECTORY_SERVER_ADDRESS=dir1.example.com:8888
SPIFFE_SOCKET_PATH=/run/spire/sockets/agent.sock
AUTH_MODE=x509
```

**Requirements:**
- SPIRE agent running on the host
- SPIFFE socket mounted into container
- Workload registration in SPIRE server

**How it works:**
1. Server connects to SPIFFE socket on startup
2. Obtains X.509-SVID certificate with SPIFFE ID
3. Uses certificate for mTLS with directory nodes
4. Automatically rotates certificates before expiry

### 2. SPIFFE JWT (Alternative Production)

Uses SPIFFE Workload API to obtain JWT-SVID tokens for authentication.

**When to use:**
- Production deployments without mTLS support
- API gateway scenarios
- Token-based authentication requirements

**Configuration:**
```bash
DIRECTORY_SERVER_ADDRESS=dir1.example.com:8888
SPIFFE_SOCKET_PATH=/run/spire/sockets/agent.sock
AUTH_MODE=jwt
JWT_AUDIENCE=spiffe://example.org/directory-server
```

**Requirements:**
- SPIRE agent running on the host
- SPIFFE socket mounted into container
- JWT audience matching directory server configuration

**How it works:**
1. Server connects to SPIFFE socket on startup
2. Obtains JWT-SVID token with SPIFFE ID
3. Includes token in gRPC metadata for each request
4. Automatically refreshes tokens before expiry

### 3. Insecure (Development Only)

No authentication - connects directly without credentials.

**When to use:**
- Local development only
- Testing with local directory server
- Never use in production

**Configuration:**
```bash
DIRECTORY_SERVER_ADDRESS=localhost:8888
# No SPIFFE variables needed
```

**Security warning:** This mode transmits data in plaintext and provides no authentication. Only use on trusted local networks.

## Environment Variables

### Required

| Variable | Description | Example |
|----------|-------------|---------|
| `DIRECTORY_SERVER_ADDRESS` | Default directory node address | `dir1.example.com:8888` |

### Optional (Authentication)

| Variable | Description | Default | Required For |
|----------|-------------|---------|--------------|
| `SPIFFE_SOCKET_PATH` | Path to SPIFFE agent socket | `/run/spire/sockets/agent.sock` | X.509, JWT |
| `AUTH_MODE` | Authentication mode: `x509`, `jwt` | `x509` | X.509, JWT |
| `JWT_AUDIENCE` | JWT audience claim | - | JWT only |

## Multi-Node Operations

### Authentication Scope

Authentication is configured **once at server startup** and applies to **all directory nodes** in the federation.

**Why:** Federation nodes share a common trust domain. The SPIFFE credentials obtained at startup are valid for all nodes in the federation.

### Default Node

The `DIRECTORY_SERVER_ADDRESS` sets the default node for operations:

```bash
DIRECTORY_SERVER_ADDRESS=dir1.example.com:8888
```

All tool calls without an explicit `node` parameter use this default.

### Per-Call Node Override

Each tool accepts an optional `node` parameter to target a specific directory node:

```python
# Uses default node (dir1.example.com:8888)
await session.call_tool("search", {"name": "agent-name"})

# Override to use different node
await session.call_tool("search", {
    "name": "agent-name",
    "node": "dir2.example.com:8888"
})
```

**Use cases:**
- Query multiple nodes in federation
- Direct operations to specific geographic regions
- Load balancing across directory nodes
- Failover to backup nodes

## Container Deployment

### Dockerfile

```dockerfile
FROM python:3.10-slim

RUN pip install --no-cache-dir uv

WORKDIR /app
COPY pyproject.toml server.py ./
RUN uv sync

CMD ["uv", "run", "python", "server.py"]
```

### Build Image

```bash
docker build -t directory-mcp-server .
```

### Run Container

**Development (no auth):**
```bash
docker run -i \
  -e DIRECTORY_SERVER_ADDRESS=localhost:8888 \
  directory-mcp-server
```

**Production (SPIFFE X.509):**
```bash
docker run -i \
  -e DIRECTORY_SERVER_ADDRESS=dir1.example.com:8888 \
  -e SPIFFE_SOCKET_PATH=/run/spire/sockets/agent.sock \
  -e AUTH_MODE=x509 \
  -v /run/spire/sockets:/run/spire/sockets:ro \
  directory-mcp-server
```

**Production (SPIFFE JWT):**
```bash
docker run -i \
  -e DIRECTORY_SERVER_ADDRESS=dir1.example.com:8888 \
  -e SPIFFE_SOCKET_PATH=/run/spire/sockets/agent.sock \
  -e AUTH_MODE=jwt \
  -e JWT_AUDIENCE=spiffe://example.org/directory-server \
  -v /run/spire/sockets:/run/spire/sockets:ro \
  directory-mcp-server
```

**Important flags:**
- `-i` - Required for stdio transport (keeps stdin open)
- `-v` - Mounts SPIFFE socket into container (read-only)

### Docker Compose

```yaml
version: '3.8'

services:
  directory-mcp-server:
    build: .
    container_name: directory-mcp-server
    stdin_open: true  # Required for stdio transport
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

**Environment file (.env):**
```bash
DIRECTORY_SERVER_ADDRESS=dir1.example.com:8888
SPIFFE_SOCKET_PATH=/run/spire/sockets/agent.sock
AUTH_MODE=x509
```

**Start:**
```bash
docker-compose up -d
```

## Client Connection

### From Agent Container

Agents connect to the MCP server using `docker exec` with stdio transport:

```python
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

server_params = StdioServerParameters(
    command="docker",
    args=["exec", "-i", "directory-mcp-server", "python", "server.py"]
)

async with stdio_client(server_params) as (read, write):
    async with ClientSession(read, write) as session:
        await session.initialize()
        
        # Call tools
        result = await session.call_tool("search", {"name": "agent-name"})
```

### From Host Process

For development or testing from host:

```python
server_params = StdioServerParameters(
    command="python",
    args=["server.py"],
    env={
        "DIRECTORY_SERVER_ADDRESS": "localhost:8888"
    }
)
```

## Available Tools

The server provides 8 tools for directory operations:

### Read Operations

**search** - Search local directory
```python
await session.call_tool("search", {
    "name": "agent-name",      # Optional: filter by name
    "skill": "nlp",            # Optional: filter by skill
    "node": "dir1.example.com:8888"  # Optional: target node
})
```

**pull** - Retrieve record by CID
```python
await session.call_tool("pull", {
    "cid": "baeareig...",
    "node": "dir1.example.com:8888"
})
```

**export** - Export record to specific format
```python
await session.call_tool("export", {
    "cid": "baeareig...",
    "target_format": "a2a",    # Default: a2a
    "node": "dir1.example.com:8888"
})
```

### Write Operations

**push** - Upload OASF record
```python
await session.call_tool("push", {
    "record": {
        "schema_version": "0.8.0",
        "name": "my-agent",
        "version": "v1.0.0",
        # ... full OASF record
    },
    "node": "dir1.example.com:8888"
})
```

**routing_publish** - Publish record to federation network
```python
await session.call_tool("routing_publish", {
    "cid": "baeareig...",
    "node": "dir1.example.com:8888"
})
```

### Network Operations

**routing_search** - Search across federation
```python
await session.call_tool("routing_search", {
    "skill": "natural_language_processing",  # Optional
    "domain": "technology",                  # Optional
    "limit": 50,                             # Optional: default 10
    "node": "dir1.example.com:8888"
})
```

### Sync Operations

**sync_create** - Pull records from remote directory
```python
await session.call_tool("sync_create", {
    "remote_url": "dir2.example.com:8888",
    "cids": ["baeareig...", "baeareif..."],  # Optional: specific CIDs
    "node": "dir1.example.com:8888"
})
```

**sync_status** - Monitor sync operation
```python
await session.call_tool("sync_status", {
    "sync_id": "uuid-here",
    "node": "dir1.example.com:8888"
})
```

## SPIFFE Setup

### Prerequisites

1. **SPIRE Server** running in your infrastructure
2. **SPIRE Agent** running on the host
3. **Workload registration** for the MCP server

### Workload Registration

Register the MCP server container with SPIRE:

```bash
spire-server entry create \
  -parentID spiffe://example.org/agent/node1 \
  -spiffeID spiffe://example.org/directory-mcp-server \
  -selector docker:label:app:directory-mcp-server \
  -ttl 3600
```

### Verify SPIFFE Socket

```bash
# Check socket exists
ls -la /run/spire/sockets/agent.sock

# Test connection
spire-agent api fetch x509 -socketPath /run/spire/sockets/agent.sock
```

### Trust Domain

Ensure the MCP server and directory nodes share the same SPIFFE trust domain. The trust domain is embedded in SPIFFE IDs:

```
spiffe://example.org/directory-mcp-server
        └─────┬─────┘
         trust domain
```

## Troubleshooting

### Connection Refused

**Symptom:** `failed to connect to all addresses`

**Solutions:**
1. Verify directory server address is correct
2. Check network connectivity: `ping dir1.example.com`
3. Verify port is open: `telnet dir1.example.com 8888`
4. Check firewall rules

### SPIFFE Socket Not Found

**Symptom:** `Using insecure mode (SPIFFE socket not found)`

**Solutions:**
1. Verify SPIRE agent is running: `ps aux | grep spire-agent`
2. Check socket path: `ls -la /run/spire/sockets/agent.sock`
3. Verify socket is mounted in container: `docker exec <container> ls -la /run/spire/sockets/`
4. Check socket permissions

### Authentication Failed

**Symptom:** `authentication failed` or `permission denied`

**Solutions:**
1. Verify workload is registered in SPIRE
2. Check SPIFFE ID matches directory server expectations
3. Verify trust domain matches
4. For JWT: check audience claim matches server configuration

### Tool Call Errors

**Symptom:** Tool returns error response

**Solutions:**
1. Check server logs: `docker logs directory-mcp-server`
2. Verify record format for push operations
3. Check CID format for pull operations
4. Verify node address is correct

## Security Best Practices

1. **Always use SPIFFE in production** - Never deploy with insecure mode
2. **Mount socket read-only** - Use `:ro` flag when mounting SPIFFE socket
3. **Separate containers** - Run MCP server in dedicated container
4. **Minimal permissions** - Run container as non-root user
5. **Network isolation** - Use Docker networks to limit connectivity
6. **Credential rotation** - SPIFFE handles automatic rotation
7. **Audit logging** - Monitor MCP server access and operations

## Performance Tuning

### Connection Pooling

The server maintains a connection pool for directory nodes. Connections are cached per node address.

### Concurrent Operations

The server uses asyncio for concurrent operations. Multiple tool calls can execute in parallel.

### Resource Limits

Set container resource limits:

```yaml
services:
  directory-mcp-server:
    deploy:
      resources:
        limits:
          cpus: '1.0'
          memory: 512M
        reservations:
          cpus: '0.5'
          memory: 256M
```

## Monitoring

### Health Checks

The server runs as long as stdin is open. Monitor container health:

```bash
docker ps --filter name=directory-mcp-server
```

### Logs

View server logs:

```bash
docker logs -f directory-mcp-server
```

Log levels:
- `INFO` - Normal operations
- `ERROR` - Operation failures
- `DEBUG` - Detailed debugging (set via logging config)

## Examples

See test files for complete examples:
- `tests/test_mcp_crossnode.py` - Cross-node operations
- `tests/test_mcp_complete.py` - Full federation workflow
