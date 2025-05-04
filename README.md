# brain2gain
This repo is designed for the consulting project of the Brain2Gain Company

```bash

brain2gain/
│
├─ backend/
│	├─ app/                    # FastAPI
│	│  ├─ core/                # config, db engine, DI
│	│  │  ├─ config.py
│	│  │  └─ database.py
│	│  ├─ models/              # SQLAlchemy ORM
│	│  │  ├─ __init__.py
│	│  │  ├─ customer.py
│	│  │  ├─ product.py
│	│  │  ├─ sales.py
│	│  │  └─ ….py
│	│  ├─ schemas/             # Pydantic DTOs
│	│  ├─ repositories/        # CRUD aislado
│	│  ├─ services/            # lógica de negocio
│	│  ├─ api/                 # routers
│	│  │  ├─ __init__.py
│	│  │  ├─ v1/
│	│  │  │  ├─ __init__.py
│	│  │  │  ├─ customers.py
│	│  │  │  └─ products.py
│	│  │  └─ health.py
│	│  ├─ main.py
│	│  └─ alembic.ini
│
├─ frontend/
│  ├─ src/
│  │  ├─ api/            # clases ApiClient
│  │  ├─ models/         # Domain models (TS interfaces + opcional classes)
│  │  ├─ services/       # Facades → useXService hooks
│  │  ├─ pages/
│  │  ├─ components/
│  │  └─ hooks/
│  ├─ public/
│  └─ package.json
│
└─ dashboard/            # Dash (montado en backend)
│  ├─ app.py
│  └─ components/          # gráficos y layouts
│
├─ tests/
├─ .env.example
└─ pyproject.toml

```
