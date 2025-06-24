# backend/app/api/routes/payments.py
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlmodel import Session

from app.api.deps import get_current_active_superuser, get_current_user
from app.core.db import get_session
from app.models import PaymentStatus, User
from app.schemas.payment import (
    PaymentFilters,
    PaymentMethodsList,
    PaymentProcess,
    PaymentProcessResponse,
    PaymentRead,
    PaymentStats,
    PaymentSummary,
    RefundCreate,
    RefundRead,
)
from app.services.payment_service import PaymentService

router = APIRouter()


# ─── PAYMENT PROCESSING ───────────────────────────────────────────────
@router.post("/process", response_model=PaymentProcessResponse)
async def process_payment(
    payment_data: PaymentProcess,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> PaymentProcessResponse:
    """
    Process payment for an order
    """
    payment_service = PaymentService(session)

    try:
        # Verify payment belongs to current user
        payment = await payment_service.get_payment_by_id(payment_data.payment_id)
        if not payment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Payment not found"
            )

        # Check if user owns the order
        from app.services.order_service import OrderService

        order_service = OrderService(session)
        order = await order_service.get_order_by_id(payment.order_id)

        if not order or order.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to process this payment",
            )

        response = await payment_service.process_payment(
            payment_id=payment_data.payment_id,
            payment_method_id=payment_data.stripe_payment_method_id,
            customer_id=payment_data.stripe_customer_id,
            paypal_order_id=payment_data.paypal_order_id,
        )

        return response

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Payment processing failed: {str(e)}",
        )


@router.get("/methods", response_model=PaymentMethodsList)
async def get_payment_methods(
    session: Session = Depends(get_session),
) -> PaymentMethodsList:
    """
    Get available payment methods
    """
    payment_service = PaymentService(session)
    methods = await payment_service.get_available_payment_methods()
    return methods


# ─── USER PAYMENTS ────────────────────────────────────────────────────
@router.get("/my-payments", response_model=list[PaymentSummary])
async def get_my_payments(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Items per page"),
    status: list[PaymentStatus] | None = Query(None, description="Filter by status"),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> list[PaymentSummary]:
    """
    Get current user's payments
    """
    payment_service = PaymentService(session)

    filters = PaymentFilters(status=status) if status else None

    payments = await payment_service.get_user_payments(
        user_id=current_user.id, page=page, page_size=page_size, filters=filters
    )

    return [PaymentSummary.from_orm(payment) for payment in payments]


@router.get("/my-payments/{payment_id}", response_model=PaymentRead)
async def get_my_payment(
    payment_id: uuid.UUID,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> PaymentRead:
    """
    Get specific payment details for current user
    """
    payment_service = PaymentService(session)

    payment = await payment_service.get_payment_by_id(payment_id)
    if not payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Payment not found"
        )

    # Verify ownership through order
    from app.services.order_service import OrderService

    order_service = OrderService(session)
    order = await order_service.get_order_by_id(payment.order_id)

    if not order or order.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this payment",
        )

    return PaymentRead.from_orm(payment)


# ─── ADMIN ENDPOINTS ──────────────────────────────────────────────────
@router.get("/", response_model=list[PaymentSummary])
async def get_all_payments(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    status: list[PaymentStatus] | None = Query(None, description="Filter by status"),
    payment_method: list[str] | None = Query(
        None, description="Filter by payment method"
    ),
    order_id: uuid.UUID | None = Query(None, description="Filter by order ID"),
    session: Session = Depends(get_session),
    _current_user: User = Depends(get_current_active_superuser),
) -> list[PaymentSummary]:
    """
    Get all payments (admin only)
    """
    payment_service = PaymentService(session)

    filters = PaymentFilters(
        status=status, payment_method=payment_method, order_id=order_id
    )

    payments = await payment_service.get_all_payments(
        page=page, page_size=page_size, filters=filters
    )

    return [PaymentSummary.from_orm(payment) for payment in payments]


@router.get("/{payment_id}", response_model=PaymentRead)
async def get_payment_admin(
    payment_id: uuid.UUID,
    session: Session = Depends(get_session),
    _current_user: User = Depends(get_current_active_superuser),
) -> PaymentRead:
    """
    Get specific payment details (admin only)
    """
    payment_service = PaymentService(session)

    payment = await payment_service.get_payment_by_id(payment_id)
    if not payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Payment not found"
        )

    return PaymentRead.from_orm(payment)


@router.get("/stats/overview", response_model=PaymentStats)
async def get_payment_stats(
    session: Session = Depends(get_session),
    _current_user: User = Depends(get_current_active_superuser),
) -> PaymentStats:
    """
    Get payment statistics (admin only)
    """
    payment_service = PaymentService(session)
    stats = await payment_service.get_payment_statistics()
    return stats


# ─── REFUNDS ──────────────────────────────────────────────────────────
@router.post("/refunds", response_model=RefundRead)
async def create_refund(
    refund_data: RefundCreate,
    session: Session = Depends(get_session),
    _current_user: User = Depends(get_current_active_superuser),
) -> RefundRead:
    """
    Create a refund (admin only)
    """
    payment_service = PaymentService(session)

    try:
        refund = await payment_service.create_refund(
            payment_id=refund_data.payment_id,
            amount=refund_data.amount,
            reason=refund_data.reason,
        )
        return RefundRead.from_orm(refund)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create refund: {str(e)}",
        )


@router.get("/refunds/{refund_id}", response_model=RefundRead)
async def get_refund(
    refund_id: uuid.UUID,
    session: Session = Depends(get_session),
    _current_user: User = Depends(get_current_active_superuser),
) -> RefundRead:
    """
    Get refund details (admin only)
    """
    payment_service = PaymentService(session)

    refund = await payment_service.get_refund_by_id(refund_id)
    if not refund:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Refund not found"
        )

    return RefundRead.from_orm(refund)


# ─── WEBHOOKS ─────────────────────────────────────────────────────────
@router.post("/webhooks/stripe")
async def stripe_webhook(request: Request, session: Session = Depends(get_session)):
    """
    Handle Stripe webhook events
    """
    payment_service = PaymentService(session)

    try:
        # Get raw body for signature verification
        body = await request.body()
        signature = request.headers.get("stripe-signature")

        # Verify and process webhook
        event = await payment_service.verify_stripe_webhook(body, signature)
        await payment_service.process_stripe_webhook(event)

        return {"status": "success"}

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Webhook processing failed: {str(e)}",
        )


@router.post("/webhooks/paypal")
async def paypal_webhook(request: Request, session: Session = Depends(get_session)):
    """
    Handle PayPal webhook events
    """
    payment_service = PaymentService(session)

    try:
        # Get raw body for signature verification
        body = await request.body()
        headers = dict(request.headers)

        # Verify and process webhook
        event = await payment_service.verify_paypal_webhook(body, headers)
        await payment_service.process_paypal_webhook(event)

        return {"status": "success"}

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Webhook processing failed: {str(e)}",
        )
