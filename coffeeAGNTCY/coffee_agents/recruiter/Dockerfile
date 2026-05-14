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

# Silences warnings about not being able to link files since the cache and sync target are on separate file systems
ENV UV_LINK_MODE=copy

# Install python dependencies
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=coffeeAGNTCY/coffee_agents/recruiter/uv.lock,target=uv.lock \
    --mount=type=bind,source=coffeeAGNTCY/coffee_agents/recruiter/pyproject.toml,target=pyproject.toml \
    uv sync --locked --no-install-project

COPY coffeeAGNTCY/coffee_agents/recruiter/ .

# Sync the project
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked

# Expose the A2A server port
EXPOSE 8881

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV ENABLE_HTTP=true

# Run the A2A server
CMD ["uv", "run", "python", "src/agent_recruiter/server/server.py"]
