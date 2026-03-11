FROM python:3.10-slim

WORKDIR /app

# Copy server file
COPY coffeeAGNTCY/dir-mcp-server/server.py ./

# Install dependencies from PyPI
RUN pip install --no-cache-dir mcp>=1.1.0 agntcy-dir==1.0.0

# Run as uid 1000 to match SPIRE workload entry
USER 1000:1000

# Run server
CMD ["python", "server.py"]
