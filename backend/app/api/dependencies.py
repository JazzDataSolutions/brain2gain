from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.repositories.product_repository import ProductRepository
from app.services.product_service import ProductService

async def get_product_service(
    db: AsyncSession = Depends(get_db)
) -> ProductService:
    repo = ProductRepository(db)
    return ProductService(repo)

