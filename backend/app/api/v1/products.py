from fastapi import APIRouter, Depends, status
from typing import List

from app.schemas.product import ProductCreate, ProductRead
from app.services.product_service import ProductService
from app.api.dependencies import get_product_service

router = APIRouter()

@router.post(
    "/", response_model=ProductRead, status_code=status.HTTP_201_CREATED
)
async def create_product(
    payload: ProductCreate,
    svc: ProductService = Depends(get_product_service),
):
    return await svc.create(payload)

@router.get("/", response_model=List[ProductRead])
async def list_products(
    svc: ProductService = Depends(get_product_service),
):
    return await svc.list()

