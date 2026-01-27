# ============================
# Builder Stage
# ============================
FROM python:3.12-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

# Optional system packages

# Install uv
RUN pip install --no-cache-dir uv

WORKDIR /app

# Layer 1: Copy only dependency files
COPY pyproject.toml uv.lock* ./

# Layer 2: Install dependencies only (cached until pyproject.toml/uv.lock changes)
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-install-project --no-dev

# Layer 3: Copy source code, excluding .venv if it exists locally
COPY . /tmp/src
RUN find /tmp/src -mindepth 1 -maxdepth 1 ! -name '.venv' -exec cp -r {} . \;

# Layer 4: Install only the project itself (dependencies already in .venv)
RUN --mount=type=cache,target=/root/.cache/uv \
    uv pip install --no-deps -e .


# ============================
# Runtime Stage
# ============================
FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Copy venv from builder
COPY --from=builder /app/.venv /app/.venv

# Copy application code from builder
COPY --from=builder /app /app

# Runtime environment variables

# Create non-root user
RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 9999

# Use venv's python directly
ENTRYPOINT ["/app/.venv/bin/python", "__main__.py"]
