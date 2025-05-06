# backend/app/repositories/product_repository.py

from typing import Optional
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from app.models import Product

class ProductRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_sku(self, sku: str) -> Optional[Product]:
        q = select(Product).where(Product.sku == sku)
        result = await self.session.execute(q)      # ← await session.execute
        return result.scalars().first()             # ← scalars() → ORM objects

    async def add(self, product: Product) -> None:
        self.session.add(product)

