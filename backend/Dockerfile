# ============================================================================
# Multi-stage Dockerfile for Brain2Gain Backend
# Optimized for production with security and performance in mind
# ============================================================================

# =============
# Builder Stage
# =============
FROM python:3.10-slim AS builder

# Install system dependencies required for building Python packages
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user for building
RUN addgroup --system builder && \
    adduser --system --ingroup builder builder

# Set working directory
WORKDIR /app

# Install uv - modern Python package manager
RUN pip install --no-cache-dir uv==0.4.18

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Install dependencies in virtual environment
RUN uv sync --frozen --compile-bytecode --no-dev

# Build arguments for environment mode
ARG APP_MODE=production
ARG API_MODE=full

# Copy source code
COPY app ./app
COPY alembic.ini ./

# Change ownership to builder user
RUN chown -R builder:builder /app
USER builder

# =============
# Runtime Stage
# =============
FROM python:3.10-slim AS runtime

# Metadata
LABEL maintainer="Brain2Gain Team" \
      version="1.0.0" \
      description="Brain2Gain API Backend"

# Environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH="/app" \
    PATH="/app/.venv/bin:$PATH" \
    PORT=8000

# Build arguments passed to runtime
ARG APP_MODE=production
ARG API_MODE=full
ENV APP_MODE=${APP_MODE}
ENV API_MODE=${API_MODE}

# Install only runtime system dependencies
RUN apt-get update && apt-get install -y \
    libpq5 \
    curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* \
    && rm -rf /tmp/*

# Create non-root user for runtime
RUN addgroup --system --gid 1001 app && \
    adduser --system --uid 1001 --ingroup app --home /app --no-create-home app

# Set working directory
WORKDIR /app

# Copy built application and dependencies from builder
COPY --from=builder --chown=app:app /app /app

# Create necessary directories with proper permissions
RUN mkdir -p /app/logs /app/tmp && \
    chown -R app:app /app

# Switch to non-root user
USER app

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:${PORT}/health || exit 1

# Expose port
EXPOSE ${PORT}

# Run application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
