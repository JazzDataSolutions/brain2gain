# backend/app/api/v1/products.py
from typing import List
from fastapi         import APIRouter, Depends, HTTPException, Query, status
from sqlmodel.ext.asyncio.session import AsyncSession

from app.api.deps           import get_current_admin_user
from app.models             import User
from app.core.database      import get_db
from app.schemas.product    import ProductCreate, ProductRead, ProductUpdate
from app.services.product_service import ProductService

router = APIRouter(prefix="/products", tags=["Products"])

@router.post("/", response_model=ProductRead, status_code=status.HTTP_201_CREATED)
async def create_product(
    payload: ProductCreate,
    session: AsyncSession = Depends(get_db),
):
    return await ProductService(session).create(payload)

@router.get("/", response_model=List[ProductRead])
async def list_products(
    skip:  int           = Query(0, ge=0),
    limit: int           = Query(50, ge=1, le=200),
    session: AsyncSession = Depends(get_db),
):
    return await ProductService(session).list(skip=skip, limit=limit)

@router.get("/{product_id}", response_model=ProductRead)
async def get_product(
    product_id: int,
    session:    AsyncSession = Depends(get_db),
    _:          User        = Depends(get_current_admin_user),
):
    product = await ProductService(session).get_by_id(product_id)
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    return product

@router.put("/{product_id}", response_model=ProductRead)
async def update_product(
    product_id: int,
    payload:    ProductUpdate,
    session:    AsyncSession = Depends(get_db),
    _:          User        = Depends(get_current_admin_user),
):
    if payload.unit_price is not None and payload.unit_price < 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="unit_price must be non-negative")
    updated = await ProductService(session).update(product_id, payload)
    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    return updated

@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_product(
    product_id: int,
    session:    AsyncSession = Depends(get_db),
    _:          User        = Depends(get_current_admin_user),
):
    deleted = await ProductService(session).delete(product_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")


