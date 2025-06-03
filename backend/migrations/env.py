# backend/migrations/env.py
from __future__ import annotations

import sys, os
from pathlib import Path
from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context

# 1) Asegúrate de que tu proyecto root esté en sys.path
sys.path.append(str(Path(__file__).resolve().parent.parent))

# 2) Importa SQLModel y todos tus modelos **desde** app.models
from sqlmodel import SQLModel
from app.models import *

# 3) Ahora sí
target_metadata = SQLModel.metadata

# 4) Override de la URL vía ENV (igual que antes)
from app.core.config import settings
db_url = str(settings.SQLALCHEMY_DATABASE_URI)
sync_url = db_url.replace("+asyncpg", "")
config = context.config
config.set_main_option("sqlalchemy.url", sync_url)

def run_migrations_offline() -> None:
    context.configure(
        url=sync_url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()

