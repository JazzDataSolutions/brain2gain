from uuid import UUID

from fastapi import APIRouter, Depends, Request, status
from sqlmodel.ext.asyncio.session import AsyncSession

from app.api.deps import get_current_user
from app.core.database import get_db
from app.middlewares.advanced_rate_limiting import apply_endpoint_limits
from app.models import User
from app.schemas.cart import AddToCartRequest, CartRead, UpdateCartItemRequest
from app.services.cart_service import CartService

router = APIRouter(prefix="/cart", tags=["Cart"])


def get_cart_identifier(
    request: Request, current_user: User | None = Depends(get_current_user)
) -> tuple[UUID | None, str | None]:
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
# # # @apply_endpoint_limits # Temporary # Temporary("cart")  # Temporary
async def get_cart(
    request: Request,
    cart_ids: tuple = Depends(get_cart_identifier),
    session: AsyncSession = Depends(get_db),
) -> CartRead:
    """
    Retrieve shopping cart for authenticated user or guest session.

    This endpoint supports both authenticated users (via JWT token) and
    guest users (via session ID in headers). Cart state is maintained
    separately for each context to ensure seamless shopping experience.

    Args:
        cart_ids (tuple): Contains (user_id, session_id) from dependency
        session (AsyncSession): Database session for cart operations

    Returns:
        CartRead: Complete cart information including items, quantities,
                 prices, and total calculations

    Headers:
        X-Session-ID: Required for guest users to maintain cart state
        Authorization: Bearer token for authenticated users (optional)

    Rate Limiting:
        Applied via # # # @apply_endpoint_limits # Temporary # Temporary("cart")  # Temporary decorator
        Standard cart limits apply per user/session

    Note:
        Guest carts are identified by session ID and will be merged
        with user cart upon authentication.
    """
    user_id, session_id = cart_ids
    service = CartService(session)
    return await service.get_cart(user_id, session_id)


@router.post("/items", response_model=CartRead, status_code=status.HTTP_201_CREATED)
# # # @apply_endpoint_limits # Temporary # Temporary("cart")  # Temporary
async def add_to_cart(
    request: Request,
    add_request: AddToCartRequest,
    cart_ids: tuple = Depends(get_cart_identifier),
    session: AsyncSession = Depends(get_db),
) -> CartRead:
    """
    Add product to shopping cart with specified quantity.

    This endpoint handles adding new products to cart or updating
    quantity if product already exists. Supports both authenticated
    users and guest sessions with proper validation.

    Args:
        request (AddToCartRequest): Contains product_id and quantity
        cart_ids (tuple): Contains (user_id, session_id) from dependency
        session (AsyncSession): Database session for cart operations

    Returns:
        CartRead: Updated cart information with new item included

    Raises:
        HTTPException: 404 if product not found or out of stock
        HTTPException: 400 if quantity exceeds available stock
        HTTPException: 422 if invalid product or quantity data

    Request Body:
        {
            "product_id": int,
            "quantity": int (min: 1, max: 999)
        }

    Rate Limiting:
        Applied via # # # @apply_endpoint_limits # Temporary # Temporary("cart")  # Temporary decorator
        Higher limits for add operations due to user interaction patterns

    Business Rules:
        - Quantity is additive (adds to existing if product already in cart)
        - Stock validation performed before adding
        - Price locked at time of addition to cart
    """
    user_id, session_id = cart_ids
    service = CartService(session)
    return await service.add_to_cart(add_request, user_id, session_id)


@router.put("/items/{product_id}", response_model=CartRead)
# # # @apply_endpoint_limits # Temporary # Temporary("cart")  # Temporary
async def update_cart_item(
    request: Request,
    product_id: int,
    update_request: UpdateCartItemRequest,
    cart_ids: tuple = Depends(get_cart_identifier),
    session: AsyncSession = Depends(get_db),
) -> CartRead:
    """Update cart item quantity"""
    user_id, session_id = cart_ids
    service = CartService(session)
    return await service.update_cart_item(product_id, update_request, user_id, session_id)


@router.delete("/items/{product_id}", response_model=CartRead)
async def remove_from_cart(
    product_id: int,
    cart_ids: tuple = Depends(get_cart_identifier),
    session: AsyncSession = Depends(get_db),
) -> CartRead:
    """Remove item from cart"""
    user_id, session_id = cart_ids
    service = CartService(session)
    return await service.remove_from_cart(product_id, user_id, session_id)


@router.delete("/", status_code=status.HTTP_204_NO_CONTENT)
async def clear_cart(
    cart_ids: tuple = Depends(get_cart_identifier),
    session: AsyncSession = Depends(get_db),
) -> None:
    """Clear all items from cart"""
    user_id, session_id = cart_ids
    service = CartService(session)
    await service.clear_cart(user_id, session_id)
