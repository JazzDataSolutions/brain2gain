import sys
import os
import pytest
# Asegurar que el directorio 'backend' está en el path para importar el módulo 'app'
sys.path.insert(0, os.path.abspath(
    os.path.join(os.path.dirname(__file__), os.pardir, 'backend')
))
from decimal import Decimal

from sqlmodel import SQLModel, create_engine
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models import Product
from app.services.product_service import ProductService
from app.schemas.product import ProductCreate, ProductUpdate


@pytest.fixture(name="async_session")
async def async_session_fixture():
    """
    Crea una sesión asíncrona en SQLite en memoria para pruebas.
    """
    engine = create_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
        future=True
    )
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
    async with AsyncSession(engine) as session:
        yield session


@pytest.mark.asyncio
async def test_create_and_get_by_id(async_session):
    svc = ProductService(async_session)
    payload = ProductCreate(sku="SKU1", name="Test Product", unit_price=Decimal("9.99"))
    product = await svc.create(payload)
    assert product.product_id is not None
    fetched = await svc.get_by_id(product.product_id)
    assert fetched is not None
    assert fetched.sku == "SKU1"
    assert fetched.name == "Test Product"


@pytest.mark.asyncio
async def test_update_product(async_session):
    svc = ProductService(async_session)
    payload = ProductCreate(sku="SKU2", name="Another Product", unit_price=Decimal("19.99"))
    product = await svc.create(payload)
    update_payload = ProductUpdate(name="Updated Name", unit_price=Decimal("29.99"))
    updated = await svc.update(product.product_id, update_payload)
    assert updated is not None
    assert updated.name == "Updated Name"
    assert updated.unit_price == Decimal("29.99")