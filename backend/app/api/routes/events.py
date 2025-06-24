# Event Sourcing API Routes for Brain2Gain
# Provides endpoints for event history and aggregate reconstruction

from datetime import datetime, timedelta
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query

from app.api.deps import get_current_admin_user, get_current_user
from app.core.event_sourcing import EventRepository, get_db
from app.models import User
from app.services.event_integration_service import (
    AggregateReconstructionService,
    EventQueryService,
)

router = APIRouter()


@router.get("/events/product/{product_id}/history")
async def get_product_event_history(
    product_id: UUID, _current_user: User = Depends(get_current_admin_user)
) -> list[dict[str, Any]]:
    """
    Get complete event history for a product.
    Requires admin privileges.
    """
    try:
        history = await EventQueryService.get_product_history(product_id)
        return history
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error retrieving product history: {str(e)}"
        )


@router.get("/events/order/{order_id}/history")
async def get_order_event_history(
    order_id: UUID, current_user: User = Depends(get_current_user)
) -> list[dict[str, Any]]:
    """
    Get complete event history for an order.
    Users can only access their own orders, admins can access all.
    """
    try:
        history = await EventQueryService.get_order_history(order_id)

        # Check if user has permission to access this order
        if not current_user.is_admin:
            # Check if any event in the history belongs to this user
            user_authorized = any(
                event.get("metadata", {}).get("user_id") == str(current_user.id)
                or event.get("metadata", {}).get("created_by") == str(current_user.id)
                for event in history
            )
            if not user_authorized:
                raise HTTPException(
                    status_code=403, detail="Not authorized to access this order"
                )

        return history
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error retrieving order history: {str(e)}"
        )


@router.get("/events/user/{user_id}/history")
async def get_user_event_history(
    user_id: UUID, current_user: User = Depends(get_current_user)
) -> list[dict[str, Any]]:
    """
    Get complete event history for a user.
    Users can only access their own history, admins can access all.
    """
    # Check authorization
    if not current_user.is_admin and current_user.id != user_id:
        raise HTTPException(
            status_code=403, detail="Not authorized to access this user's history"
        )

    try:
        history = await EventQueryService.get_user_history(user_id)
        return history
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error retrieving user history: {str(e)}"
        )


@router.get("/events/cart/{cart_id}/history")
async def get_cart_event_history(
    cart_id: UUID, current_user: User = Depends(get_current_user)
) -> list[dict[str, Any]]:
    """
    Get complete event history for a cart.
    Users can only access their own carts, admins can access all.
    """
    try:
        history = await EventQueryService.get_cart_history(cart_id)

        # Check if user has permission to access this cart
        if not current_user.is_admin:
            user_authorized = any(
                event.get("metadata", {}).get("user_id") == str(current_user.id)
                for event in history
            )
            if not user_authorized:
                raise HTTPException(
                    status_code=403, detail="Not authorized to access this cart"
                )

        return history
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error retrieving cart history: {str(e)}"
        )


@router.get("/events/reconstruct/product/{product_id}")
async def reconstruct_product_state(
    product_id: UUID, _current_user: User = Depends(get_current_admin_user)
) -> dict[str, Any]:
    """
    Reconstruct current product state from event history.
    Requires admin privileges.
    """
    try:
        state = await AggregateReconstructionService.reconstruct_product_state(
            product_id
        )
        return {
            "aggregate_id": str(product_id),
            "aggregate_type": "Product",
            "reconstructed_state": state,
            "reconstructed_at": datetime.utcnow().isoformat(),
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error reconstructing product state: {str(e)}"
        )


@router.get("/events/reconstruct/order/{order_id}")
async def reconstruct_order_state(
    order_id: UUID, current_user: User = Depends(get_current_user)
) -> dict[str, Any]:
    """
    Reconstruct current order state from event history.
    Users can only access their own orders, admins can access all.
    """
    try:
        state = await AggregateReconstructionService.reconstruct_order_state(order_id)

        # Check authorization for non-admin users
        if not current_user.is_admin:
            # If there are events, check if user created/owns this order
            if state.get("events_count", 0) > 0:
                # Get the actual events to check ownership
                history = await EventQueryService.get_order_history(order_id)
                user_authorized = any(
                    event.get("metadata", {}).get("user_id") == str(current_user.id)
                    or event.get("metadata", {}).get("created_by")
                    == str(current_user.id)
                    for event in history
                )
                if not user_authorized:
                    raise HTTPException(
                        status_code=403, detail="Not authorized to access this order"
                    )

        return {
            "aggregate_id": str(order_id),
            "aggregate_type": "Order",
            "reconstructed_state": state,
            "reconstructed_at": datetime.utcnow().isoformat(),
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error reconstructing order state: {str(e)}"
        )


@router.get("/events/statistics")
async def get_event_statistics(
    days: int = Query(default=7, ge=1, le=90),
    _event_types: list[str] | None = Query(default=None),
    _current_user: User = Depends(get_current_admin_user),
) -> dict[str, Any]:
    """
    Get event statistics for the specified time period.
    Requires admin privileges.
    """
    try:
        async with get_db() as db:
            EventRepository(db)

            # Calculate date range
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=days)

            # Get events in the specified period
            # Note: This would need additional methods in EventRepository
            # For now, returning a placeholder structure

            stats = {
                "period": {
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat(),
                    "days": days,
                },
                "event_counts": {
                    "total": 0,
                    "by_type": {},
                    "by_aggregate_type": {},
                    "by_day": [],
                },
                "processing_stats": {
                    "processed": 0,
                    "unprocessed": 0,
                    "error_rate": 0.0,
                },
            }

            return stats

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error retrieving event statistics: {str(e)}"
        )


@router.get("/events/unprocessed")
async def get_unprocessed_events(
    limit: int = Query(default=50, ge=1, le=1000),
    _current_user: User = Depends(get_current_admin_user),
) -> list[dict[str, Any]]:
    """
    Get unprocessed events for manual review.
    Requires admin privileges.
    """
    try:
        async with get_db() as db:
            event_repo = EventRepository(db)
            events = await event_repo.get_unprocessed_events(limit)

            return [event.to_dict() for event in events]

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error retrieving unprocessed events: {str(e)}"
        )


@router.post("/events/{event_id}/mark-processed")
async def mark_event_processed(
    event_id: UUID, current_user: User = Depends(get_current_admin_user)
) -> dict[str, Any]:
    """
    Manually mark an event as processed.
    Requires admin privileges.
    """
    try:
        async with get_db() as db:
            event_repo = EventRepository(db)
            await event_repo.mark_event_processed(event_id)

            return {
                "event_id": str(event_id),
                "marked_processed_at": datetime.utcnow().isoformat(),
                "marked_by": str(current_user.id),
            }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error marking event as processed: {str(e)}"
        )


@router.get("/events/health")
async def get_event_system_health(
    _current_user: User = Depends(get_current_admin_user),
) -> dict[str, Any]:
    """
    Get health status of the event sourcing system.
    Requires admin privileges.
    """
    try:
        async with get_db() as db:
            event_repo = EventRepository(db)

            # Get recent unprocessed events
            unprocessed_events = await event_repo.get_unprocessed_events(100)
            unprocessed_count = len(unprocessed_events)

            # Calculate health metrics
            health_status = "healthy"
            if unprocessed_count > 50:
                health_status = "warning"
            if unprocessed_count > 100:
                health_status = "critical"

            # Get oldest unprocessed event
            oldest_unprocessed = None
            if unprocessed_events:
                oldest_unprocessed = min(
                    unprocessed_events, key=lambda e: e.occurred_at
                ).occurred_at.isoformat()

            return {
                "status": health_status,
                "unprocessed_events_count": unprocessed_count,
                "oldest_unprocessed_event": oldest_unprocessed,
                "last_check": datetime.utcnow().isoformat(),
                "recommendations": {
                    "healthy": [],
                    "warning": ["Consider processing unprocessed events"],
                    "critical": ["URGENT: Process unprocessed events immediately"],
                }.get(health_status, []),
            }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error checking event system health: {str(e)}"
        )


@router.post("/events/replay/aggregate/{aggregate_id}")
async def replay_aggregate_events(
    aggregate_id: UUID,
    aggregate_type: str,
    from_version: int = Query(default=1, ge=1),
    current_user: User = Depends(get_current_admin_user),
) -> dict[str, Any]:
    """
    Replay events for a specific aggregate from a given version.
    This is useful for debugging or fixing data inconsistencies.
    Requires admin privileges.
    """
    try:
        # Get events for the aggregate
        events = (
            await EventQueryService.get_order_history(aggregate_id)
            if aggregate_type == "Order"
            else (
                await EventQueryService.get_product_history(aggregate_id)
                if aggregate_type == "Product"
                else (
                    await EventQueryService.get_user_history(aggregate_id)
                    if aggregate_type == "User"
                    else await EventQueryService.get_cart_history(aggregate_id)
                )
            )
        )

        # Filter events by version
        events_to_replay = [
            event for event in events if event.get("version", 1) >= from_version
        ]

        # For safety, we'll just return what would be replayed without actually replaying
        return {
            "aggregate_id": str(aggregate_id),
            "aggregate_type": aggregate_type,
            "total_events": len(events),
            "events_to_replay": len(events_to_replay),
            "from_version": from_version,
            "replay_requested_by": str(current_user.id),
            "replay_requested_at": datetime.utcnow().isoformat(),
            "status": "preview_only",
            "note": "This endpoint currently returns a preview. Implement actual replay logic as needed.",
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error during event replay: {str(e)}"
        )
