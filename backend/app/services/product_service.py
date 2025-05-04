from typing import List
from app.models.product import Product
from app.repositories.base import IRepository
from app.schemas.product import ProductCreate, ProductRead

class ProductService:
    def __init__(self, repo: IRepository[Product]):
        self.repo = repo

    async def create(self, data: ProductCreate) -> ProductRead:
        entity = Product(**data.model_dump())
        saved = await self.repo.add(entity)
        return ProductRead.model_validate(saved)

    async def list(self) -> List[ProductRead]:
        items = await self.repo.get_all()
        return [ProductRead.model_validate(i) for i in items]

