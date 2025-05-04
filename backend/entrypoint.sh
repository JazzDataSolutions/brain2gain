#!/usr/bin/env bash
# 1) Espera a Postgres
python - <<'PY'
import os, time, psycopg2, sys
dsn = os.getenv("DATABASE_URL")
for _ in range(30):
    try:
        psycopg2.connect(dsn).close(); break
    except Exception: time.sleep(2)
else:
    sys.exit("Postgres no disponible")
PY
# 2) Migraciones
alembic upgrade head
# 3) Arranca app FastAPI + Dash (gunicorn)
gunicorn app.main:app \
    --worker-class uvicorn.workers.UvicornWorker \
    --bind 0.0.0.0:8000 --workers 4

