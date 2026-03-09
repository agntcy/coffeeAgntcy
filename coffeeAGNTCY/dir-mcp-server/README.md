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

### Deployment Pattern

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

## Usage Examples

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
