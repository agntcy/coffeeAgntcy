# Directory Federation Manager UI

Web-based UI for managing AGNTCY Directory federation.

## Features

- **Local Search**: Search agents on specific directory nodes
- **Federation Search**: P2P search across all federated nodes
- **Agent Management**: Push, publish, unpublish, delete agents
- **OASF Integration**: Auto-load skills and domains from OASF catalog
- **Schema Support**: Multiple OASF schema versions (1.0.0, 0.8.0, 0.7.0)
- **Sync Operations**: Sync records between nodes
- **Real-time Operations**: View full agent details, manage federation

## Quick Start

1. **Configure federation nodes** in `.env`:
```bash
cp .env.example .env
# Edit FEDERATION_NODES with your directory nodes
```

2. **Start services**:
```bash
docker compose up -d
```

3. **Access UI**: http://localhost:8090

## Configuration

All configuration is in `.env`:

### Federation Nodes
```bash
# Comma-separated: name:address,name:address,...
FEDERATION_NODES=Node 1:sn-dir1.labs.outshift.com:8888,Node 2:sn-dir2.labs.outshift.com:8888
DEFAULT_NODE_ADDRESS=sn-dir1.labs.outshift.com:8888
```

### Authentication
```bash
# Modes: x509 (SPIRE), insecure, token
AUTH_MODE=x509
SPIFFE_SOCKET_PATH=unix:///run/spire/sockets/agent.sock

# For token mode:
# AUTH_MODE=token
# AUTH_TOKEN=your-token-here

# For insecure mode (testing only):
# AUTH_MODE=insecure
```

### Frontend API
```bash
# Leave empty for default (window.location.origin + '/api')
FRONTEND_API_URL=
```

## Architecture

- **Frontend**: Nginx serving static HTML/CSS/JS with dynamic config injection
- **Backend**: Flask API with agntcy-dir Python SDK (v1.0.0)
- **Auth**: SPIFFE X.509, token-based, or insecure mode

## API Endpoints

- `GET /api/nodes` - List federation nodes
- `GET /api/skills` - OASF skills catalog (proxied)
- `GET /api/domains` - OASF domains catalog (proxied)
- `POST /api/search` - Local node search
- `POST /api/routing-search` - Federation-wide search
- `POST /api/pull` - Get full record
- `POST /api/push` - Upload new agent
- `POST /api/publish` - Publish to federation
- `POST /api/unpublish` - Remove from federation
- `POST /api/delete` - Delete record
- `POST /api/sync` - Create sync job
- `POST /api/sync-status` - Check sync status

## Requirements

### For x509 Auth Mode
- SPIRE agent running with socket at `/run/spire/sockets/agent.sock`
- Workload entry for uid 1000
- Network access to directory nodes

### For Other Auth Modes
- Network access to directory nodes
- Valid token (if using token mode)

## Deployment

### Local Development
```bash
docker compose up -d
```

### Remote Server with Nginx Reverse Proxy
```nginx
server {
    listen 9443 ssl;
    server_name your-server.com;
    
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;
    
    location / {
        proxy_pass http://localhost:8090;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
    
    location /api/ {
        proxy_pass http://localhost:5000/api/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## Ports

- `5000` - Backend API
- `8090` - Frontend UI
