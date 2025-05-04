# backend/Dockerfile
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Poetry + deps
COPY pyproject.toml poetry.lock ./
RUN pip install --upgrade pip \
 && pip install poetry \
 && poetry config virtualenvs.create false \
 && poetry install --no-interaction --no-root

# Código de la app
COPY app app
COPY migrations migrations
COPY alembic.ini entrypoint.sh ./

RUN chmod +x /app/entrypoint.sh

EXPOSE 8000
CMD ["/app/entrypoint.sh"]

