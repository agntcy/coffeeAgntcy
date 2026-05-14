# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

# SLIM v0.7+ requires to use debian trixie distribution
FROM astral/uv:0.11.16-python3.13-trixie-slim@sha256:d57fc364ed714127c162a01b316bfb7b9a3fd09d97c665781a5607acaa35d254

# Install dirctl binary for MCP toolset (detect architecture for multi-platform builds)
# Note: Using specific version as /releases/latest/ points to GUI release which doesn't include dirctl
RUN ARCH=$(dpkg --print-architecture) && \
    curl -L https://github.com/agntcy/dir/releases/download/v1.0.0/dirctl-linux-${ARCH} -o /usr/local/bin/dirctl && \
    chmod +x /usr/local/bin/dirctl

WORKDIR /app
COPY coffeeAGNTCY/coffee_agents/recruiter/pyproject.toml coffeeAGNTCY/coffee_agents/recruiter/uv.lock coffeeAGNTCY/coffee_agents/recruiter/README.md ./

ENV UV_LINK_MODE=copy
RUN --mount=type=cache,target=/root/.cache/uv uv sync --locked --no-editable

COPY coffeeAGNTCY/coffee_agents/recruiter/ .

# Expose the A2A server port
EXPOSE 8881

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV ENABLE_HTTP=true

# Run the A2A server
CMD ["uv", "run", "python", "src/agent_recruiter/server/server.py"]
