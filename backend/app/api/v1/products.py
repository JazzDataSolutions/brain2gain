"""
Products API endpoints.

This module provides CRUD operations for products with proper authentication,
authorization, and business validation.
"""

from fastapi import APIRouter, HTTPException, Query, Request, status

from app.api.deps import AdminUser, SessionDep
from app.middlewares.advanced_rate_limiting import apply_endpoint_limits
from app.schemas.product import ProductCreate, ProductRead, ProductUpdate
from app.services.product_service import ProductService

router = APIRouter(prefix="/products", tags=["Products"])


@router.get("/", response_model=list[ProductRead])
@apply_endpoint_limits("products")
async def list_products(
    request: Request,
    session: SessionDep,
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(
        50, ge=1, le=200, description="Maximum number of records to return"
    ),
) -> list[ProductRead]:
    """
    List active products with pagination.

    This endpoint is public and doesn't require authentication.
    Use it to display products in the catalog. Only shows ACTIVE products.
    """
    service = ProductService(session)
    return await service.get_active_products(skip=skip, limit=limit)


@router.post("/", response_model=ProductRead, status_code=status.HTTP_201_CREATED)
async def create_product(
    product_data: ProductCreate,
    session: SessionDep,
    _current_user: AdminUser,
) -> ProductRead:
    """
    Create a new product.

    Requires ADMIN or MANAGER role.
    Validates business rules including SKU uniqueness and minimum price.
    """
    service = ProductService(session)
    try:
        return await service.create(product_data)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/{product_id}", response_model=ProductRead)
@apply_endpoint_limits("products")
async def get_product(
    request: Request,
    product_id: int,
    session: SessionDep,
) -> ProductRead:
    """
    Get a product by ID.

    Public endpoint - returns only ACTIVE products.
    Returns 404 if product not found or not active.
    """
    service = ProductService(session)
    product = await service.get_by_id(product_id)

    if not product or product.status != "ACTIVE":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product with ID {product_id} not found",
        )

    return product


@router.get("/admin/{product_id}", response_model=ProductRead)
async def get_product_admin(
    product_id: int,
    session: SessionDep,
    _current_user: AdminUser,
) -> ProductRead:
    """
    Get a product by ID (Admin).

    Requires ADMIN or MANAGER role.
    Returns product regardless of status.
    """
    service = ProductService(session)
    product = await service.get_by_id(product_id)

    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product with ID {product_id} not found",
        )

    return product


@router.put("/{product_id}", response_model=ProductRead)
async def update_product(
    product_id: int,
    product_data: ProductUpdate,
    session: SessionDep,
    _current_user: AdminUser,
) -> ProductRead:
    """
    Update a product.

    Requires ADMIN or MANAGER role.
    Validates business rules before updating.
    """
    # Validate price is not negative
    if product_data.unit_price is not None and product_data.unit_price < 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Product price cannot be negative",
        )

    service = ProductService(session)
    try:
        updated_product = await service.update(product_id, product_data)
        if not updated_product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Product with ID {product_id} not found",
            )
        return updated_product
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_product(
    product_id: int,
    session: SessionDep,
    _current_user: AdminUser,
) -> None:
    """
    Delete a product.

    Requires ADMIN or MANAGER role.
    Returns 404 if product not found.
    """
    service = ProductService(session)
    success = await service.delete(product_id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product with ID {product_id} not found",
        )
