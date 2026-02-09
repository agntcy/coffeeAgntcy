# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

# SLIM v0.7+ requires to use debian trixie distribution
FROM python:3.13.11-slim-trixie

# Install system dependencies, including ping, curl, and wget
RUN apt-get update && \
    apt-get install -y --no-install-recommends git curl wget iputils-ping && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Install dirctl binary for MCP toolset (detect architecture for multi-platform builds)
# Note: Using specific version as /releases/latest/ points to GUI release which doesn't include dirctl
RUN ARCH=$(dpkg --print-architecture) && \
    curl -L https://github.com/agntcy/dir/releases/download/v1.0.0-rc.3/dirctl-linux-${ARCH} -o /usr/local/bin/dirctl && \
    chmod +x /usr/local/bin/dirctl

# Install uv and create virtual environment
RUN pip install --no-cache-dir uv && \
    uv venv -q /venv
ENV PATH="/venv/bin:$PATH"

# Set PYTHONPATH to include the application directory
ENV PYTHONPATH="/app"

WORKDIR /app
COPY coffeeAGNTCY/coffee_agents/recruiter/pyproject.toml coffeeAGNTCY/coffee_agents/recruiter/uv.lock coffeeAGNTCY/coffee_agents/recruiter/README.md ./
RUN uv sync --locked --no-editable

COPY coffeeAGNTCY/coffee_agents/recruiter/ .

# Expose the A2A server port
EXPOSE 8881

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV ENABLE_HTTP=true

# Run the A2A server
CMD ["uv", "run", "python", "src/agent_recruiter/server/server.py"]
