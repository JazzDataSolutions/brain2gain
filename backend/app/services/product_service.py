# backend/app/services/product_service.py

from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models import Product
from app.schemas.product import ProductCreate
from app.repositories.product_repository import ProductRepository

class ProductService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = ProductRepository(session)

    async def create(self, payload: ProductCreate) -> Product:
        # 1) Validar duplicado
        if await self.repo.get_by_sku(payload.sku):
            raise HTTPException(status_code=409, detail="SKU duplicado")

        # 2) Crear entidad
        product = Product(**payload.dict())
        await self.repo.add(product)

        # 3) Commit / rollback
        try:
            await self.session.commit()
            await self.session.refresh(product)
            return product
        except IntegrityError:
            await self.session.rollback()
            raise HTTPException(status_code=409, detail="SKU ya registrado")

