# Quick Reference

## Start Server

### Development
```bash
DIRECTORY_SERVER_ADDRESS=localhost:8888 python server.py
```

### Production (X.509)
```bash
DIRECTORY_SERVER_ADDRESS=dir1.example.com:8888 \
SPIFFE_SOCKET_PATH=/run/spire/sockets/agent.sock \
AUTH_MODE=x509 \
python server.py
```

### Docker
```bash
docker run -i \
  -e DIRECTORY_SERVER_ADDRESS=dir1.example.com:8888 \
  -e SPIFFE_SOCKET_PATH=/run/spire/sockets/agent.sock \
  -e AUTH_MODE=x509 \
  -v /run/spire/sockets:/run/spire/sockets:ro \
  directory-mcp-server
```

## Authentication

| Mode | Variables | Use Case |
|------|-----------|----------|
| **Insecure** | None | Local dev only |
| **X.509** | `SPIFFE_SOCKET_PATH`<br>`AUTH_MODE=x509` | Production |
| **JWT** | `SPIFFE_SOCKET_PATH`<br>`AUTH_MODE=jwt`<br>`JWT_AUDIENCE` | Alternative |

## Environment Variables

```bash
# Required
DIRECTORY_SERVER_ADDRESS=dir1.example.com:8888

# Optional (SPIFFE)
SPIFFE_SOCKET_PATH=/run/spire/sockets/agent.sock
AUTH_MODE=x509
JWT_AUDIENCE=spiffe://example.org/dir  # JWT only
```

## Tools

### Read
```python
search(name, skill, node)
pull(cid, node)
export(cid, target_format, node)
```

### Write
```python
push(record, node)
routing_publish(cid, node)
```

### Network
```python
routing_search(skill, domain, limit, node)
```

### Sync
```python
sync_create(remote_url, cids, node)
sync_status(sync_id, node)
```

## Multi-Node

```python
# Default node
call_tool("search", {"name": "test"})

# Specific node
call_tool("search", {"name": "test", "node": "dir2.example.com:8888"})
```

## Agent Connection

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
        result = await session.call_tool("search", {"name": "agent"})
```

## Docker Compose

```yaml
services:
  directory-mcp-server:
    build: .
    stdin_open: true
    tty: true
    environment:
      DIRECTORY_SERVER_ADDRESS: ${DIRECTORY_SERVER_ADDRESS}
      SPIFFE_SOCKET_PATH: ${SPIFFE_SOCKET_PATH:-}
      AUTH_MODE: ${AUTH_MODE:-}
    volumes:
      - /run/spire/sockets:/run/spire/sockets:ro
```

## SPIFFE Setup

```bash
# Register workload
spire-server entry create \
  -parentID spiffe://example.org/agent/node1 \
  -spiffeID spiffe://example.org/directory-mcp-server \
  -selector docker:label:app:directory-mcp-server

# Verify
spire-agent api fetch x509 -socketPath /run/spire/sockets/agent.sock
```

## Troubleshooting

```bash
# Check connectivity
ping dir1.example.com
telnet dir1.example.com 8888

# View logs
docker logs -f directory-mcp-server

# Verify SPIFFE socket
docker exec directory-mcp-server ls -la /run/spire/sockets/
```

## Key Concepts

✅ **Separate container** - Run isolated from agent  
✅ **Stdio transport** - Standard MCP communication  
✅ **Auth at startup** - Applies to all nodes  
✅ **Multi-node support** - Override per call  
✅ **SPIFFE credentials** - Automatic rotation  

## Documentation

- `README.md` - Overview and quick start
- `CONFIGURATION.md` - Detailed configuration
- `SPIRE_SETUP.md` - SPIRE authentication setup
- `SPIRE_AGENT_INSTALLATION.md` - Complete installation guide
