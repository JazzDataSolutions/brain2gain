# backend/app/api/v1/products.py

from fastapi import APIRouter, Depends, status
from sqlmodel.ext.asyncio.session import AsyncSession

from app.schemas.product import ProductCreate, ProductRead
from app.services.product_service import ProductService
from app.core.database import get_db

router = APIRouter(prefix="/products", tags=["Products"])

@router.post(
    "/",
    response_model=ProductRead,
    status_code=status.HTTP_201_CREATED
)
async def create_product(
    payload: ProductCreate,
    session: AsyncSession = Depends(get_db),
):
    svc = ProductService(session)
    return await svc.create(payload)

