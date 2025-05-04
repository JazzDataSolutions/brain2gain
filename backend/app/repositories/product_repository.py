from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.product import Product
from app.repositories.base import IRepository

class ProductRepository(IRepository[Product]):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def add(self, obj: Product) -> Product:
        self.session.add(obj)
        await self.session.commit()
        await self.session.refresh(obj)
        return obj

    async def get_all(self) -> List[Product]:
        result = await self.session.execute(select(Product))
        return result.scalars().all()

