# backend/app/api/routes/orders.py
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlmodel import Session

from app.api.deps import get_current_active_superuser, get_current_user
from app.core.db import get_session
from app.models import OrderStatus, PaymentStatus, User
from app.schemas.order import (
    CheckoutCalculation,
    CheckoutConfirmation,
    CheckoutInitiate,
    CheckoutValidation,
    OrderFilters,
    OrderList,
    OrderRead,
    OrderStats,
    OrderSummary,
    OrderUpdate,
)
from app.services.cart_service import CartService
from app.services.order_service import OrderService
from app.services.payment_service import PaymentService

router = APIRouter()


# ─── PUBLIC ENDPOINTS ─────────────────────────────────────────────────
@router.post("/checkout/calculate", response_model=CheckoutCalculation)
async def calculate_checkout(
    checkout_data: CheckoutInitiate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
) -> CheckoutCalculation:
    """
    Calculate checkout totals (subtotal, tax, shipping, total)
    """
    order_service = OrderService(session)
    cart_service = CartService(session)

    # Get user's cart
    cart = await cart_service.get_user_cart(current_user.id)
    if not cart or not cart.items:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cart is empty"
        )

    # Calculate totals
    calculation = await order_service.calculate_order_totals(
        cart_items=cart.items,
        shipping_address=checkout_data.shipping_address,
        payment_method=checkout_data.payment_method
    )

    return calculation


@router.post("/checkout/validate", response_model=CheckoutValidation)
async def validate_checkout(
    checkout_data: CheckoutInitiate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
) -> CheckoutValidation:
    """
    Validate checkout data before processing
    """
    order_service = OrderService(session)
    cart_service = CartService(session)

    # Get user's cart
    cart = await cart_service.get_user_cart(current_user.id)
    if not cart or not cart.items:
        return CheckoutValidation(
            valid=False,
            errors=["Cart is empty"]
        )

    # Validate checkout
    validation = await order_service.validate_checkout(
        cart=cart,
        checkout_data=checkout_data
    )

    return validation


@router.post("/checkout/confirm", response_model=CheckoutConfirmation)
async def confirm_checkout(
    checkout_data: CheckoutInitiate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
) -> CheckoutConfirmation:
    """
    Create order from cart and initiate payment
    """
    order_service = OrderService(session)
    cart_service = CartService(session)
    payment_service = PaymentService(session)

    # Get user's cart
    cart = await cart_service.get_user_cart(current_user.id)
    if not cart or not cart.items:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cart is empty"
        )

    # Validate checkout first
    validation = await order_service.validate_checkout(cart, checkout_data)
    if not validation.valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Checkout validation failed: {', '.join(validation.errors)}"
        )

    try:
        # Create order from cart
        order = await order_service.create_order_from_cart(
            user_id=current_user.id,
            cart=cart,
            checkout_data=checkout_data
        )

        # Clear cart after successful order creation
        await cart_service.clear_cart(current_user.id)

        # Initiate payment if required
        confirmation = CheckoutConfirmation(
            order_id=order.order_id,
            payment_required=True
        )

        if checkout_data.payment_method != "bank_transfer":
            payment_response = await payment_service.initiate_payment(
                order_id=order.order_id,
                payment_method=checkout_data.payment_method,
                amount=order.total_amount
            )

            if checkout_data.payment_method == "stripe":
                confirmation.payment_intent_id = payment_response.get("payment_intent_id")
            elif checkout_data.payment_method == "paypal":
                confirmation.payment_url = payment_response.get("approval_url")

        return confirmation

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create order: {str(e)}"
        )


# ─── USER ORDERS ──────────────────────────────────────────────────────
@router.get("/my-orders", response_model=OrderList)
async def get_my_orders(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Items per page"),
    status: list[OrderStatus] | None = Query(None, description="Filter by status"),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
) -> OrderList:
    """
    Get current user's orders with pagination
    """
    order_service = OrderService(session)

    filters = OrderFilters(status=status) if status else None

    orders, total = await order_service.get_user_orders(
        user_id=current_user.id,
        page=page,
        page_size=page_size,
        filters=filters
    )

    return OrderList(
        orders=[OrderSummary(
            order_id=order.order_id,
            status=order.status,
            payment_status=order.payment_status,
            total_amount=order.total_amount,
            created_at=order.created_at,
            items_count=len(order.items)
        ) for order in orders],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=(total + page_size - 1) // page_size
    )


@router.get("/my-orders/{order_id}", response_model=OrderRead)
async def get_my_order(
    order_id: uuid.UUID,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
) -> OrderRead:
    """
    Get specific order details for current user
    """
    order_service = OrderService(session)

    order = await order_service.get_order_by_id(order_id)
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )

    # Check if order belongs to current user
    if order.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this order"
        )

    return OrderRead.from_orm(order)


# ─── ADMIN ENDPOINTS ──────────────────────────────────────────────────
@router.get("/", response_model=OrderList)
async def get_all_orders(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    status: list[OrderStatus] | None = Query(None, description="Filter by status"),
    payment_status: list[PaymentStatus] | None = Query(None, description="Filter by payment status"),
    search: str | None = Query(None, description="Search orders"),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_superuser)
) -> OrderList:
    """
    Get all orders (admin only) with pagination and filters
    """
    order_service = OrderService(session)

    filters = OrderFilters(
        status=status,
        payment_status=payment_status,
        search=search
    )

    orders, total = await order_service.get_all_orders(
        page=page,
        page_size=page_size,
        filters=filters
    )

    return OrderList(
        orders=[OrderSummary(
            order_id=order.order_id,
            status=order.status,
            payment_status=order.payment_status,
            total_amount=order.total_amount,
            created_at=order.created_at,
            items_count=len(order.items)
        ) for order in orders],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=(total + page_size - 1) // page_size
    )


@router.get("/{order_id}", response_model=OrderRead)
async def get_order_admin(
    order_id: uuid.UUID,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_superuser)
) -> OrderRead:
    """
    Get specific order details (admin only)
    """
    order_service = OrderService(session)

    order = await order_service.get_order_by_id(order_id)
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )

    return OrderRead.from_orm(order)


@router.patch("/{order_id}", response_model=OrderRead)
async def update_order(
    order_id: uuid.UUID,
    order_update: OrderUpdate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_superuser)
) -> OrderRead:
    """
    Update order (admin only)
    """
    order_service = OrderService(session)

    order = await order_service.get_order_by_id(order_id)
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )

    try:
        updated_order = await order_service.update_order(order_id, order_update)
        return OrderRead.from_orm(updated_order)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update order: {str(e)}"
        )


@router.post("/{order_id}/cancel", response_model=OrderRead)
async def cancel_order(
    order_id: uuid.UUID,
    reason: str = Query(..., description="Cancellation reason"),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
) -> OrderRead:
    """
    Cancel order (user can cancel their own pending orders, admin can cancel any)
    """
    order_service = OrderService(session)

    order = await order_service.get_order_by_id(order_id)
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )

    # Check permissions
    is_admin = current_user.is_superuser
    is_owner = order.user_id == current_user.id

    if not (is_admin or is_owner):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to cancel this order"
        )

    # Only allow cancellation of pending/confirmed orders
    if order.status not in [OrderStatus.PENDING, OrderStatus.CONFIRMED]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot cancel order with status: {order.status}"
        )

    try:
        cancelled_order = await order_service.cancel_order(order_id, reason)
        return OrderRead.from_orm(cancelled_order)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to cancel order: {str(e)}"
        )


@router.get("/stats/overview", response_model=OrderStats)
async def get_order_stats(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_superuser)
) -> OrderStats:
    """
    Get order statistics (admin only)
    """
    order_service = OrderService(session)

    stats = await order_service.get_order_statistics()
    return stats
