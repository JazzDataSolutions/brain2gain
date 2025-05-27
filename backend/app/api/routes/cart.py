from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlmodel.ext.asyncio.session import AsyncSession
from typing import Optional
from uuid import UUID

from app.models import User
from app.schemas.cart import CartRead, AddToCartRequest, UpdateCartItemRequest
from app.services.cart_service import CartService
from app.core.database import get_db
from app.api.deps import get_current_user

router = APIRouter(prefix="/cart", tags=["Cart"])

def get_cart_identifier(
    request: Request,
    current_user: Optional[User] = Depends(get_current_user)
) -> tuple[Optional[UUID], Optional[str]]:
    """Get cart identifier - either user_id or session_id"""
    if current_user:
        return current_user.id, None
    else:
        # For guest users, use session from headers or generate one
        session_id = request.headers.get("X-Session-ID")
        if not session_id:
            # In a real app, you'd generate a proper session ID
            session_id = f"guest_{request.client.host}_{hash(request.headers.get('user-agent', ''))}"
        return None, session_id

@router.get("/", response_model=CartRead)
async def get_cart(
    cart_ids: tuple = Depends(get_cart_identifier),
    session: AsyncSession = Depends(get_db)
) -> CartRead:
    """Get current cart"""
    user_id, session_id = cart_ids
    service = CartService(session)
    return await service.get_cart(user_id, session_id)

@router.post("/items", response_model=CartRead, status_code=status.HTTP_201_CREATED)
async def add_to_cart(
    request: AddToCartRequest,
    cart_ids: tuple = Depends(get_cart_identifier),
    session: AsyncSession = Depends(get_db)
) -> CartRead:
    """Add item to cart"""
    user_id, session_id = cart_ids
    service = CartService(session)
    return await service.add_to_cart(request, user_id, session_id)

@router.put("/items/{product_id}", response_model=CartRead)
async def update_cart_item(
    product_id: int,
    request: UpdateCartItemRequest,
    cart_ids: tuple = Depends(get_cart_identifier),
    session: AsyncSession = Depends(get_db)
) -> CartRead:
    """Update cart item quantity"""
    user_id, session_id = cart_ids
    service = CartService(session)
    return await service.update_cart_item(product_id, request, user_id, session_id)

@router.delete("/items/{product_id}", response_model=CartRead)
async def remove_from_cart(
    product_id: int,
    cart_ids: tuple = Depends(get_cart_identifier),
    session: AsyncSession = Depends(get_db)
) -> CartRead:
    """Remove item from cart"""
    user_id, session_id = cart_ids
    service = CartService(session)
    return await service.remove_from_cart(product_id, user_id, session_id)

@router.delete("/", status_code=status.HTTP_204_NO_CONTENT)
async def clear_cart(
    cart_ids: tuple = Depends(get_cart_identifier),
    session: AsyncSession = Depends(get_db)
) -> None:
    """Clear all items from cart"""
    user_id, session_id = cart_ids
    service = CartService(session)
    await service.clear_cart(user_id, session_id)