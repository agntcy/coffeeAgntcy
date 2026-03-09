# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

# SLIM v0.7+ requires to use debian trixie distribution
FROM python:3.13.11-slim-trixie

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends git curl wget iputils-ping ca-certificates gnupg && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Install Docker CLI
RUN install -m 0755 -d /etc/apt/keyrings && \
    curl -fsSL https://download.docker.com/linux/debian/gpg -o /etc/apt/keyrings/docker.asc && \
    chmod a+r /etc/apt/keyrings/docker.asc && \
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/debian trixie stable" > /etc/apt/sources.list.d/docker.list && \
    apt-get update && \
    apt-get install -y --no-install-recommends docker-ce-cli && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

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
