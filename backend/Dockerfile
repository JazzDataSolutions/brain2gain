FROM python:3.10-slim AS builder
WORKDIR /app

# Install uv tool and sync dependencies
RUN pip install --no-cache-dir uv
COPY pyproject.toml uv.lock alembic.ini ./
RUN uv sync --frozen --compile-bytecode

# Copy application source code
COPY app app

FROM python:3.10-slim AS runtime
ENV PYTHONUNBUFFERED=1
WORKDIR /app

# Copy built artifacts and dependencies from builder
COPY --from=builder /app /app
ENV PATH="/app/.venv/bin:$PATH"

# Use non-root user for security
RUN addgroup --system app && \
    adduser --system --ingroup app --home /app --no-create-home app && \
    chown -R app /app
USER app

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
