from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel.ext.asyncio.session import AsyncSession
from typing import List

from app.models import Product
from app.schemas.product import ProductCreate, ProductRead, ProductUpdate
from app.services.product_service import ProductService
from app.core.database import get_db

router = APIRouter(prefix="/products", tags=["Products"])

@router.get("/", response_model=List[ProductRead])
async def list_products(
    skip: int = 0,
    limit: int = 100,
    session: AsyncSession = Depends(get_db),
) -> List[Product]:
    service = ProductService(session)
    return await service.list(skip=skip, limit=limit)

@router.post("/", response_model=ProductRead, status_code=status.HTTP_201_CREATED)
async def create_product(
    product_data: ProductCreate, 
    session: AsyncSession = Depends(get_db)
) -> Product:
    service = ProductService(session)
    return await service.create(product_data)

@router.get("/{product_id}", response_model=ProductRead)
async def get_product(
    product_id: int, 
    session: AsyncSession = Depends(get_db)
) -> Product:
    service = ProductService(session)
    product = await service.get_by_id(product_id)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Product not found"
        )
    return product

@router.put("/{product_id}", response_model=ProductRead)
async def update_product(
    product_id: int, 
    product_data: ProductUpdate,
    session: AsyncSession = Depends(get_db)
) -> Product:
    service = ProductService(session)
    product = await service.update(product_id, product_data)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Product not found"
        )
    return product

@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_product(
    product_id: int,
    session: AsyncSession = Depends(get_db)
) -> None:
    service = ProductService(session)
    success = await service.delete(product_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Product not found"
        )