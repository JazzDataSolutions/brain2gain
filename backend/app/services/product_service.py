from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from typing import List, Optional

from app.models import Product
from app.schemas.product import ProductCreate, ProductUpdate
from app.repositories.product_repository import ProductRepository

class ProductService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = ProductRepository(session)

    async def list(self, skip: int = 0, limit: int = 100) -> List[Product]:
        statement = select(Product).offset(skip).limit(limit)
        result = await self.session.exec(statement)
        return result.all()

    async def create(self, payload: ProductCreate) -> Product:
        # Check for duplicate SKU
        existing_product = await self.repo.get_by_sku(payload.sku)
        if existing_product:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT, 
                detail="Product with this SKU already exists"
            )

        # Create new product
        product_data = payload.model_dump()
        product = Product(**product_data)
        
        try:
            self.session.add(product)
            await self.session.commit()
            await self.session.refresh(product)
            return product
        except IntegrityError:
            await self.session.rollback()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Product with this SKU already exists"
            )

    async def get_by_id(self, product_id: int) -> Optional[Product]:
        return await self.repo.get_by_id(product_id)

    async def get_by_sku(self, sku: str) -> Optional[Product]:
        return await self.repo.get_by_sku(sku)

    async def update(self, product_id: int, payload: ProductUpdate) -> Optional[Product]:
        product = await self.repo.get_by_id(product_id)
        if not product:
            return None

        # Update only provided fields
        update_data = payload.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(product, field, value)

        try:
            self.session.add(product)
            await self.session.commit()
            await self.session.refresh(product)
            return product
        except IntegrityError:
            await self.session.rollback()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Product with this SKU already exists"
            )

    async def delete(self, product_id: int) -> bool:
        product = await self.repo.get_by_id(product_id)
        if not product:
            return False

        await self.session.delete(product)
        await self.session.commit()
        return True