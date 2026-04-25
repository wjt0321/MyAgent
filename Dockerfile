# MyAgent Production Dockerfile
# Multi-stage build for minimal image size

# ---------------------------------------------------------------------------
# Stage 1: Builder
# ---------------------------------------------------------------------------
FROM python:3.12-slim AS builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency files
COPY pyproject.toml ./

# Create virtual environment and install dependencies
RUN python -m venv /app/.venv
RUN /app/.venv/bin/pip install --no-cache-dir --upgrade pip
RUN /app/.venv/bin/pip install --no-cache-dir -e ".[web,gateway]"

# ---------------------------------------------------------------------------
# Stage 2: Production
# ---------------------------------------------------------------------------
FROM python:3.12-slim AS production

WORKDIR /app

# Create non-root user for security
RUN groupadd -r myagent && useradd -r -g myagent myagent

# Install runtime dependencies only
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy virtual environment from builder
COPY --from=builder /app/.venv /app/.venv

# Copy application code
COPY src/ ./src/
COPY README.md ./
COPY pyproject.toml ./

# Install the package in production mode
RUN /app/.venv/bin/pip install --no-cache-dir -e .

# Set environment variables
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV MYAGENT_HOME=/app/data

# Create data directory
RUN mkdir -p /app/data && chown -R myagent:myagent /app/data

# Switch to non-root user
USER myagent

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD myagent --version || exit 1

# Default command
CMD ["myagent", "web", "--host", "0.0.0.0", "--port", "8000", "--json-log"]
