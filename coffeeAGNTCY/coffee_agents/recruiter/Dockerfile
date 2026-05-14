# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

# SLIM v0.7+ requires to use debian trixie distribution
FROM astral/uv:0.11.14-python3.12-trixie-slim@sha256:13b5883729ec534af5863facf5c40ac0869f2c124ad5620c9ed36fe7c03fa87d

# Install dirctl binary for MCP toolset (detect architecture for multi-platform builds)
# Note: Using specific version as /releases/latest/ points to GUI release which doesn't include dirctl
RUN ARCH=$(dpkg --print-architecture) && \
    curl -L https://github.com/agntcy/dir/releases/download/v1.0.0/dirctl-linux-${ARCH} -o /usr/local/bin/dirctl && \
    chmod +x /usr/local/bin/dirctl

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
