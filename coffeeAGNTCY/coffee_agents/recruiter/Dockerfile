# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

FROM python:3.12-slim

WORKDIR /app

# Install curl for downloading dirctl
RUN apt-get update && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

# Install dirctl binary for MCP toolset
RUN curl -L https://github.com/agntcy/dir/releases/latest/download/dirctl-linux-amd64 -o /usr/local/bin/dirctl \
    && chmod +x /usr/local/bin/dirctl

# Install uv for fast dependency management
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Copy dependency files first for better layer caching
COPY pyproject.toml uv.lock* README.md ./

# Install dependencies
RUN uv sync --frozen --no-dev --no-install-project

# Copy application code
COPY src/ ./src/

# Install the project itself
RUN uv sync --frozen --no-dev

# Expose the A2A server port
EXPOSE 8881

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV ENABLE_HTTP=true

# Run the A2A server
CMD ["uv", "run", "python", "src/agent_recruiter/server/server.py"]
