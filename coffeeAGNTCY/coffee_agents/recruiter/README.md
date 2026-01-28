# Agent Recruiter

Agent discovery, evaluation, and task/skill-based agent recruiting.

## Table of Contents

- [Overview](#overview)
- [Getting Started](#getting-started)
  - [Prerequisites](#prerequisites)
  - [Installation](#installation)
  - [Environment Variables](#environment-variables)
  - [Start Local Services](#start-local-services)
  - [ADK Web Development](#adk-web-development)
  - [A2A Server](#a2a-server)
  - [Response Format](#response-format)
- [Deployment](#deployment)
  - [Docker Compose](#docker-compose-recommended)
  - [Service Endpoints](#service-endpoints)
  - [Health Checks](#health-checks)
- [Testing](#testing)
  - [Run All Tests](#run-all-tests)
  - [Run Specific Test Files](#run-specific-test-files)
  - [Run Specific Tests](#run-specific-tests)
- [Benchmarking](#benchmarking)
  - [Caching Performance Benchmark](#caching-performance-benchmark)
  - [Cache Configuration](#cache-configuration)
- [Architecture](#architecture)
- [License](#license)

## Overview

Agent Recruiter is a multi-agent system that helps find, evaluate, and recruit agents from registries based on specified criteria:

1. **Request**: User asks the Recruiter to find agents based on skills, semantic query, or both
2. **Search**: Recruiter searches configured agent registries (AGNTCY Directory Service) for matching agents
3. **Evaluate**: Recruiter optionally interviews and evaluates agent candidates by creating A2A or MCP clients and running thourgh user provided evaluation scenarios.
4. **Return**: An overview of the search, list agent records (ex A2A cards), and optioinally a list of eval transcripts and scores.

## Getting Started

### Prerequisites

- Python 3.12+
- [uv](https://docs.astral.sh/uv/) package manager
- Docker (for local services and deployment)
- Litellm compatible LLM provider

### Installation

```bash
# Clone the repository
git clone https://github.com/agntcy/coffee_agents.git
cd coffee_agents/recruiter

# Install dependencies
uv sync

# Install with dev dependencies
uv pip install ".[dev]"

# Copy environment template and configure
cp .env.example .env
# Edit .env with your API keys
```

#### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `LLM_MODEL` | LiteLLM model identifier | `openai/gpt-4o` |
| `CACHE_MODE` | Caching mode: `tool`, `none` | `tool` |
| `MCP_CONNECTION_MODE` | MCP connection: `auto`, `binary`, `docker` | `auto` |
| `DIRECTORY_CLIENT_SERVER_ADDRESS` | Directory API server address | `localhost:8888` |


Agent Recruiter uses litellm to manage LLM connections. With litellm, you can seamlessly switch between different model providers using a unified configuration interface. Below are examples of environment variables for setting up various providers. For a comprehensive list of supported providers, see the [official litellm documentation](https://docs.litellm.ai/docs/providers).

Note that the environment variable for specifying the model is always LLM_MODEL, regardless of the provider.

   Update `.env` with your LLM provider and credentials. For example:

---

#### **OpenAI**

```env
LLM_MODEL="openai/<model_of_choice>"
OPENAI_API_KEY=<your_openai_api_key>
```

---

#### **Azure OpenAI**

```env
LLM_MODEL="azure/<your_deployment_name>"
AZURE_API_BASE=https://your-azure-resource.openai.azure.com/
AZURE_API_KEY=<your_azure_api_key>
AZURE_API_VERSION=<your_azure_api_version>
```

---

#### **GROQ**

```env
LLM_MODEL="groq/<model_of_choice>"
GROQ_API_KEY=<your_groq_api_key>
```

---

#### **NVIDIA NIM**

```env
LLM_MODEL="nvidia_nim/<model_of_choice>"
NVIDIA_NIM_API_KEY=<your_nvidia_api_key>
NVIDIA_NIM_API_BASE=<your_nvidia_nim_endpoint_url>
```

---

#### **LiteLLM Proxy**

If you're using a LiteLLM proxy to route requests to various LLM providers:

```env
LLM_MODEL="azure/<your_deployment_name>"
LITELLM_PROXY_BASE_URL=<your_litellm_proxy_base_url>
LITELLM_PROXY_API_KEY=<your_litellm_proxy_api_key>
```

---

#### **Custom OAuth2 Application Exposing OpenAI**

If you’re using a application secured with OAuth2 + refresh token that exposes an OpenAI endpoint:

```env
LLM_MODEL=oauth2/<your_llm_model_here>
OAUTH2_CLIENT_ID=<your_client_id>
OAUTH2_CLIENT_SECRET=<your_client_secret>
OAUTH_TOKEN_URL="https://your-auth-server.com/token"
OAUTH2_BASE_URL="https://your-openai-endpoint"
OAUTH2_APP_KEY=<your_app_key> #optional
```

### Start Local Services

The recruiter requires the AGNTCY Directory Service for agent discovery. Start the local services:

```bash
# Start directory services (ADS, Zot registry, OASF translation)
docker compose -f docker/docker-compose.yaml up -d dir-api-server zot oasf-translation-service

# Verify services are running
docker compose -f docker/docker-compose.yaml ps
```

Services exposed:
- **Directory API Server**: `localhost:8888` (gRPC), `localhost:8889` (health)
- **Zot Registry**: `localhost:5555`

### ADK Web Development

Run the agent locally using Google ADK's web interface for interactive development:

```bash
# Start the ADK web server
adk web

# Open browser at http://localhost:8000
```

Select `test` from the agent dropdown memu.

The ADK web interface provides:
- Interactive chat with the recruiter agent
- Tool call visualization
- Session state inspection
- Debug logging

<img src=./docs/adk_web.png >

### A2A Server

Run the agent as an A2A (Agent-to-Agent) protocol server for production use:

```bash
# Start the A2A server
uv run python src/agent_recruiter/server/server.py

# Server starts at http://localhost:8881
```

#### Verify the Server

```bash
# Check agent card
curl http://localhost:8881/.well-known/agent.json

# Expected response:
{
  "name": "RecruiterAgent",
  "url": "http://localhost:8881",
  "description": "An agent that helps find and recruit other agents based on specified criteria.",
  "version": "1.0.0",
  ...
}
```

#### Response Format

The A2A server returns messages with multiple parts:

| Part | Type | Description |
|------|------|-------------|
| `TextPart` | `text/plain` | Human-readable summary of the search results |
| `DataPart` | `application/json` | Structured agent records (when agents are found) |

**DataPart Structure:**

When agents are found, the `DataPart` contains:
- `metadata.type`: `"found_agent_records"`
- `data`: Dictionary of agent records keyed by CID (Content ID)

```python
# Example: Parsing the response
async for response in client.send_message(message):
    if isinstance(response, Message):
        for part in response.parts:
            if isinstance(part.root, TextPart):
                print(f"Summary: {part.root.text}")
            elif isinstance(part.root, DataPart):
                if part.root.metadata.get("type") == "found_agent_records":
                    for cid, record in part.root.data.items():
                        print(f"Agent CID: {cid}")
                        print(f"Agent Name: {record.get('name')}")
```

## Deployment

### Docker Compose (Recommended)

Deploy the full stack including the recruiter agent:

```bash
# Build and start all services
cd docker
docker compose up --build

# Or run in background
docker compose up --build -d
```

This starts:
- **dir-api-server**: Agent Directory Service API
- **zot**: OCI artifact registry for agent storage
- **recruiter-agent**: The recruiter agent A2A server

#### Service Endpoints

| Service | Port | Description |
|---------|------|-------------|
| recruiter-agent | 8881 | A2A server endpoint |
| dir-api-server | 8888 | Directory gRPC API |
| zot | 5555 | OCI registry |

#### Health Checks

```bash
# Check recruiter agent
curl http://localhost:8881/.well-known/agent.json
```

## Testing

### Run All Tests

```bash
# Run full test suite
uv run pytest

# Run with verbose output
uv run pytest -v
```

### Run Specific Test Files

```bash
# Integration tests
uv run pytest test/integration/ -v

# Caching tests
uv run pytest test/integration/test_caching.py -v

# A2A server tests
uv run pytest test/integration/test_a2a.py -v
```

### Run Specific Tests

```bash
# Run a single test
uv run pytest test/integration/test_caching.py::TestToolCaching::test_cache_hit_reduces_operation_time -v
```

## Benchmarking

### Caching Performance Benchmark

Run the caching benchmark to measure tool cache performance:

```bash
uv run python test/integration/benchmark_caching.py
```

Example output:

```
======================================================================
TOOL CACHING PERFORMANCE BENCHMARK
======================================================================

BENCHMARK RUNS
----------------------------------------------------------------------
Run 1: 8.095s | Hits: 0 | Misses: 3
Run 2: 6.757s | Hits: 3 | Misses: 0
Run 3: 6.019s | Hits: 3 | Misses: 0

REPORT CARD
----------------------------------------------------------------------
Cold Cache (Run 1):
  Latency                                  8.095s
  Cache Misses                                  3

Warm Cache (Runs 2-3):
  Avg Latency                              6.388s
  Total Cache Hits                              6

Performance Improvement:
  Latency Reduction                        1.707s
  Latency Reduction %                       21.1%
  Speedup Factor                            1.27x
```

### Cache Configuration

Control caching behavior via environment variables:

```bash
# Disable caching
export CACHE_MODE=none

# Enable tool caching (default)
export CACHE_MODE=tool

# Configure cache TTL (seconds)
export TOOL_CACHE_TTL=600

# Configure max cache entries
export TOOL_CACHE_MAX_ENTRIES=500

# Exclude specific tools from caching
export TOOL_CACHE_EXCLUDE=tool_a,tool_b
```

## Architecture

```
src/agent_recruiter/
├── recruiter/           # Main orchestrator (RecruiterTeam)
├── agent_registries/    # Registry search agent with MCP tools
├── plugins/             # ADK plugins (tool caching)
├── server/              # A2A server implementation
└── common/              # Logging and utilities
```

### Key Components

- **RecruiterTeam**: Main entry point, coordinates sub-agents using Google ADK
- **RegistrySearchAgent**: Searches AGNTCY Directory via MCP tools
- **ToolCachePlugin**: Caches tool results for performance
- **A2A Server**: Exposes the agent via A2A protocol

## License

Apache-2.0 - See [LICENSE](LICENSE) for details.
