# Event Sourcing Infrastructure for Brain2Gain
# Phase 1: Domain Event Management

import json
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.ext.declarative import declarative_base

from app.core.database import get_db


class EventType(str, Enum):
    """Domain event types for the system"""
    # Product Events
    PRODUCT_CREATED = "product.created"
    PRODUCT_UPDATED = "product.updated"
    PRODUCT_DELETED = "product.deleted"
    PRODUCT_STOCK_UPDATED = "product.stock_updated"

    # Order Events
    ORDER_CREATED = "order.created"
    ORDER_UPDATED = "order.updated"
    ORDER_CANCELLED = "order.cancelled"
    ORDER_SHIPPED = "order.shipped"
    ORDER_DELIVERED = "order.delivered"

    # User Events
    USER_REGISTERED = "user.registered"
    USER_UPDATED = "user.updated"
    USER_DELETED = "user.deleted"

    # Cart Events
    CART_ITEM_ADDED = "cart.item_added"
    CART_ITEM_REMOVED = "cart.item_removed"
    CART_UPDATED = "cart.updated"

    # Inventory Events
    INVENTORY_STOCK_DECREASED = "inventory.stock_decreased"
    INVENTORY_STOCK_INCREASED = "inventory.stock_increased"
    INVENTORY_LOW_STOCK_ALERT = "inventory.low_stock_alert"

    # Payment Events
    PAYMENT_INITIATED = "payment.initiated"
    PAYMENT_COMPLETED = "payment.completed"
    PAYMENT_FAILED = "payment.failed"
    PAYMENT_REFUNDED = "payment.refunded"


@dataclass
class DomainEvent:
    """Base domain event class"""
    id: UUID
    event_type: EventType
    aggregate_id: UUID
    aggregate_type: str
    data: dict[str, Any]
    metadata: dict[str, Any]
    occurred_at: datetime
    version: int = 1

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": str(self.id),
            "event_type": self.event_type.value,
            "aggregate_id": str(self.aggregate_id),
            "aggregate_type": self.aggregate_type,
            "data": self.data,
            "metadata": self.metadata,
            "occurred_at": self.occurred_at.isoformat(),
            "version": self.version
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "DomainEvent":
        return cls(
            id=UUID(data["id"]),
            event_type=EventType(data["event_type"]),
            aggregate_id=UUID(data["aggregate_id"]),
            aggregate_type=data["aggregate_type"],
            data=data["data"],
            metadata=data["metadata"],
            occurred_at=datetime.fromisoformat(data["occurred_at"]),
            version=data["version"]
        )


Base = declarative_base()


class EventStore(Base):
    """Event store table for persisting domain events"""
    __tablename__ = "event_store"

    id = Column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid4)
    event_type = Column(String(100), nullable=False, index=True)
    aggregate_id = Column(PostgresUUID(as_uuid=True), nullable=False, index=True)
    aggregate_type = Column(String(50), nullable=False, index=True)
    data = Column(Text, nullable=False)
    event_metadata = Column("metadata", Text, nullable=False)
    occurred_at = Column(DateTime, nullable=False, index=True)
    version = Column(Integer, nullable=False, default=1)
    processed = Column(Boolean, default=False, index=True)


class EventHandler(ABC):
    """Abstract event handler"""

    @abstractmethod
    async def handle(self, event: DomainEvent) -> None:
        pass

    @abstractmethod
    def can_handle(self, event_type: EventType) -> bool:
        pass


class EventBus:
    """Event bus for publishing and subscribing to domain events"""

    def __init__(self):
        self._handlers: dict[EventType, list[EventHandler]] = {}
        self._subscribers: list[EventHandler] = []

    def subscribe(self, handler: EventHandler, event_types: list[EventType] = None):
        """Subscribe a handler to specific event types or all events"""
        if event_types:
            for event_type in event_types:
                if event_type not in self._handlers:
                    self._handlers[event_type] = []
                self._handlers[event_type].append(handler)
        else:
            self._subscribers.append(handler)

    async def publish(self, event: DomainEvent):
        """Publish an event to all subscribed handlers"""
        # Handle specific event type handlers
        if event.event_type in self._handlers:
            for handler in self._handlers[event.event_type]:
                try:
                    await handler.handle(event)
                except Exception as e:
                    # Log error but don't stop other handlers
                    print(f"Error handling event {event.id}: {e}")

        # Handle general subscribers
        for handler in self._subscribers:
            if handler.can_handle(event.event_type):
                try:
                    await handler.handle(event)
                except Exception as e:
                    print(f"Error handling event {event.id}: {e}")


class EventRepository:
    """Repository for storing and retrieving events"""

    def __init__(self, db_session: AsyncSession):
        self.db = db_session

    async def save_event(self, event: DomainEvent) -> None:
        """Save a domain event to the event store"""
        db_event = EventStore(
            id=event.id,
            event_type=event.event_type.value,
            aggregate_id=event.aggregate_id,
            aggregate_type=event.aggregate_type,
            data=json.dumps(event.data),
            event_metadata=json.dumps(event.metadata),
            occurred_at=event.occurred_at,
            version=event.version
        )
        self.db.add(db_event)
        await self.db.commit()

    async def get_events_by_aggregate(
        self,
        aggregate_id: UUID,
        aggregate_type: str = None
    ) -> list[DomainEvent]:
        """Get all events for a specific aggregate"""
        query = self.db.query(EventStore).filter(
            EventStore.aggregate_id == aggregate_id
        )

        if aggregate_type:
            query = query.filter(EventStore.aggregate_type == aggregate_type)

        events = await query.order_by(EventStore.occurred_at).all()

        return [
            DomainEvent(
                id=event.id,
                event_type=EventType(event.event_type),
                aggregate_id=event.aggregate_id,
                aggregate_type=event.aggregate_type,
                data=json.loads(event.data),
                metadata=json.loads(event.event_metadata),
                occurred_at=event.occurred_at,
                version=event.version
            )
            for event in events
        ]

    async def get_unprocessed_events(self, limit: int = 100) -> list[DomainEvent]:
        """Get unprocessed events for batch processing"""
        events = await self.db.query(EventStore).filter(
            EventStore.processed == False
        ).order_by(EventStore.occurred_at).limit(limit).all()

        return [
            DomainEvent(
                id=event.id,
                event_type=EventType(event.event_type),
                aggregate_id=event.aggregate_id,
                aggregate_type=event.aggregate_type,
                data=json.loads(event.data),
                metadata=json.loads(event.event_metadata),
                occurred_at=event.occurred_at,
                version=event.version
            )
            for event in events
        ]

    async def mark_event_processed(self, event_id: UUID) -> None:
        """Mark an event as processed"""
        await self.db.query(EventStore).filter(
            EventStore.id == event_id
        ).update({"processed": True})
        await self.db.commit()


class EventSourcingMixin:
    """Mixin to add event sourcing capabilities to aggregates"""

    def __init__(self):
        self._events: list[DomainEvent] = []

    def add_event(self, event: DomainEvent):
        """Add a domain event to the aggregate"""
        self._events.append(event)

    def get_events(self) -> list[DomainEvent]:
        """Get all uncommitted events"""
        return self._events.copy()

    def clear_events(self):
        """Clear all uncommitted events"""
        self._events.clear()

    def create_event(
        self,
        event_type: EventType,
        data: dict[str, Any],
        metadata: dict[str, Any] = None
    ) -> DomainEvent:
        """Create a new domain event"""
        return DomainEvent(
            id=uuid4(),
            event_type=event_type,
            aggregate_id=getattr(self, 'id', uuid4()),
            aggregate_type=self.__class__.__name__,
            data=data,
            metadata=metadata or {},
            occurred_at=datetime.utcnow()
        )


# Specific Event Handlers

class InventoryEventHandler(EventHandler):
    """Handler for inventory-related events"""

    async def handle(self, event: DomainEvent) -> None:
        if event.event_type == EventType.ORDER_CREATED:
            # Decrease inventory when order is created
            await self._decrease_inventory(event)
        elif event.event_type == EventType.ORDER_CANCELLED:
            # Increase inventory when order is cancelled
            await self._increase_inventory(event)

    def can_handle(self, event_type: EventType) -> bool:
        return event_type in [
            EventType.ORDER_CREATED,
            EventType.ORDER_CANCELLED,
            EventType.INVENTORY_STOCK_DECREASED,
            EventType.INVENTORY_STOCK_INCREASED
        ]

    async def _decrease_inventory(self, event: DomainEvent):
        # Implementation would decrease inventory based on order items
        pass

    async def _increase_inventory(self, event: DomainEvent):
        # Implementation would increase inventory based on cancelled order items
        pass


class NotificationEventHandler(EventHandler):
    """Handler for sending notifications based on events"""

    async def handle(self, event: DomainEvent) -> None:
        if event.event_type == EventType.ORDER_CREATED:
            await self._send_order_confirmation(event)
        elif event.event_type == EventType.ORDER_SHIPPED:
            await self._send_shipping_notification(event)
        elif event.event_type == EventType.INVENTORY_LOW_STOCK_ALERT:
            await self._send_low_stock_alert(event)

    def can_handle(self, event_type: EventType) -> bool:
        return event_type in [
            EventType.ORDER_CREATED,
            EventType.ORDER_SHIPPED,
            EventType.ORDER_DELIVERED,
            EventType.INVENTORY_LOW_STOCK_ALERT,
            EventType.USER_REGISTERED
        ]

    async def _send_order_confirmation(self, event: DomainEvent):
        # Implementation would send order confirmation email/SMS
        pass

    async def _send_shipping_notification(self, event: DomainEvent):
        # Implementation would send shipping notification
        pass

    async def _send_low_stock_alert(self, event: DomainEvent):
        # Implementation would send low stock alert to admins
        pass


# Global event bus instance
event_bus = EventBus()

# Register default event handlers
inventory_handler = InventoryEventHandler()
notification_handler = NotificationEventHandler()

event_bus.subscribe(inventory_handler)
event_bus.subscribe(notification_handler)


async def publish_event(event: DomainEvent, persist: bool = True):
    """Publish an event and optionally persist it"""
    if persist:
        async with get_db() as db:
            event_repo = EventRepository(db)
            await event_repo.save_event(event)

    await event_bus.publish(event)


async def get_aggregate_events(aggregate_id: UUID, aggregate_type: str = None) -> list[DomainEvent]:
    """Get all events for an aggregate"""
    async with get_db() as db:
        event_repo = EventRepository(db)
        return await event_repo.get_events_by_aggregate(aggregate_id, aggregate_type)


# Event Processing Service
class EventProcessor:
    """Service for processing unprocessed events in batches"""

    def __init__(self, batch_size: int = 100):
        self.batch_size = batch_size

    async def process_unprocessed_events(self):
        """Process all unprocessed events"""
        async with get_db() as db:
            event_repo = EventRepository(db)

            while True:
                events = await event_repo.get_unprocessed_events(self.batch_size)

                if not events:
                    break

                for event in events:
                    try:
                        await event_bus.publish(event)
                        await event_repo.mark_event_processed(event.id)
                    except Exception as e:
                        print(f"Error processing event {event.id}: {e}")
                        # Could implement retry logic here


# Initialize event processor
event_processor = EventProcessor()
