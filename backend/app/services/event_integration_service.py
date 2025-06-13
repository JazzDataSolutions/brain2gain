# Event Integration Service for Brain2Gain Microservices
# Integrates event sourcing with existing services

from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4
from datetime import datetime

from app.core.event_sourcing import (
    DomainEvent, EventType, EventSourcingMixin, 
    publish_event, get_aggregate_events
)
from app.models import User, Product, SalesOrder, Cart
from app.schemas.product import ProductCreate, ProductUpdate
from app.schemas.cart import CartItemCreate, CartItemUpdate


class ProductEventService:
    """Service to integrate product operations with event sourcing"""
    
    @staticmethod
    async def create_product_with_events(product_data: ProductCreate, user_id: UUID) -> Dict[str, Any]:
        """Create product and publish domain event"""
        # Create the product event
        event = DomainEvent(
            id=uuid4(),
            event_type=EventType.PRODUCT_CREATED,
            aggregate_id=uuid4(),  # This would be the actual product ID
            aggregate_type="Product",
            data={
                "name": product_data.name,
                "description": product_data.description,
                "price": float(product_data.price),
                "stock": product_data.stock,
                "sku": product_data.sku,
                "category": product_data.category,
                "is_active": product_data.is_active
            },
            metadata={
                "created_by": str(user_id),
                "source": "product_service",
                "version": "1.0"
            },
            occurred_at=datetime.utcnow()
        )
        
        # Publish the event
        await publish_event(event)
        
        return {
            "event_id": str(event.id),
            "aggregate_id": str(event.aggregate_id),
            "event_type": event.event_type.value,
            "occurred_at": event.occurred_at
        }
    
    @staticmethod
    async def update_product_with_events(
        product_id: UUID, 
        product_data: ProductUpdate, 
        user_id: UUID
    ) -> Dict[str, Any]:
        """Update product and publish domain event"""
        event = DomainEvent(
            id=uuid4(),
            event_type=EventType.PRODUCT_UPDATED,
            aggregate_id=product_id,
            aggregate_type="Product",
            data=product_data.dict(exclude_unset=True),
            metadata={
                "updated_by": str(user_id),
                "source": "product_service",
                "version": "1.0"
            },
            occurred_at=datetime.utcnow()
        )
        
        await publish_event(event)
        
        return {
            "event_id": str(event.id),
            "aggregate_id": str(event.aggregate_id),
            "event_type": event.event_type.value,
            "occurred_at": event.occurred_at
        }
    
    @staticmethod
    async def update_stock_with_events(
        product_id: UUID, 
        new_stock: int, 
        reason: str,
        user_id: UUID
    ) -> Dict[str, Any]:
        """Update product stock and publish domain event"""
        event = DomainEvent(
            id=uuid4(),
            event_type=EventType.PRODUCT_STOCK_UPDATED,
            aggregate_id=product_id,
            aggregate_type="Product",
            data={
                "new_stock": new_stock,
                "reason": reason,
                "timestamp": datetime.utcnow().isoformat()
            },
            metadata={
                "updated_by": str(user_id),
                "source": "inventory_service",
                "version": "1.0"
            },
            occurred_at=datetime.utcnow()
        )
        
        await publish_event(event)
        
        return {
            "event_id": str(event.id),
            "aggregate_id": str(event.aggregate_id),
            "event_type": event.event_type.value,
            "occurred_at": event.occurred_at
        }


class OrderEventService:
    """Service to integrate order operations with event sourcing"""
    
    @staticmethod
    async def create_order_with_events(order_data: Dict[str, Any], user_id: UUID) -> Dict[str, Any]:
        """Create order and publish domain events"""
        order_id = uuid4()
        
        # Create order created event
        order_event = DomainEvent(
            id=uuid4(),
            event_type=EventType.ORDER_CREATED,
            aggregate_id=order_id,
            aggregate_type="Order",
            data=order_data,
            metadata={
                "created_by": str(user_id),
                "source": "order_service",
                "version": "1.0"
            },
            occurred_at=datetime.utcnow()
        )
        
        # Publish order event (this will trigger inventory updates)
        await publish_event(order_event)
        
        # Create inventory events for each order item
        if "items" in order_data:
            for item in order_data["items"]:
                inventory_event = DomainEvent(
                    id=uuid4(),
                    event_type=EventType.INVENTORY_STOCK_DECREASED,
                    aggregate_id=UUID(item["product_id"]),
                    aggregate_type="Product",
                    data={
                        "quantity_decreased": item["quantity"],
                        "order_id": str(order_id),
                        "reason": "order_created"
                    },
                    metadata={
                        "triggered_by": str(order_event.id),
                        "source": "order_service",
                        "version": "1.0"
                    },
                    occurred_at=datetime.utcnow()
                )
                
                await publish_event(inventory_event)
        
        return {
            "event_id": str(order_event.id),
            "aggregate_id": str(order_id),
            "event_type": order_event.event_type.value,
            "occurred_at": order_event.occurred_at
        }
    
    @staticmethod
    async def update_order_status_with_events(
        order_id: UUID, 
        new_status: str, 
        user_id: UUID,
        additional_data: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Update order status and publish domain event"""
        # Determine event type based on status
        event_type_mapping = {
            "cancelled": EventType.ORDER_CANCELLED,
            "shipped": EventType.ORDER_SHIPPED,
            "delivered": EventType.ORDER_DELIVERED
        }
        
        event_type = event_type_mapping.get(new_status.lower(), EventType.ORDER_UPDATED)
        
        event = DomainEvent(
            id=uuid4(),
            event_type=event_type,
            aggregate_id=order_id,
            aggregate_type="Order",
            data={
                "new_status": new_status,
                "previous_status": additional_data.get("previous_status") if additional_data else None,
                "updated_at": datetime.utcnow().isoformat(),
                **(additional_data or {})
            },
            metadata={
                "updated_by": str(user_id),
                "source": "order_service",
                "version": "1.0"
            },
            occurred_at=datetime.utcnow()
        )
        
        await publish_event(event)
        
        return {
            "event_id": str(event.id),
            "aggregate_id": str(event.aggregate_id),
            "event_type": event.event_type.value,
            "occurred_at": event.occurred_at
        }


class CartEventService:
    """Service to integrate cart operations with event sourcing"""
    
    @staticmethod
    async def add_item_to_cart_with_events(
        cart_id: UUID, 
        item_data: CartItemCreate, 
        user_id: UUID
    ) -> Dict[str, Any]:
        """Add item to cart and publish domain event"""
        event = DomainEvent(
            id=uuid4(),
            event_type=EventType.CART_ITEM_ADDED,
            aggregate_id=cart_id,
            aggregate_type="Cart",
            data={
                "product_id": str(item_data.product_id),
                "quantity": item_data.quantity,
                "price": float(item_data.price) if hasattr(item_data, 'price') else None
            },
            metadata={
                "user_id": str(user_id),
                "source": "cart_service",
                "version": "1.0"
            },
            occurred_at=datetime.utcnow()
        )
        
        await publish_event(event)
        
        return {
            "event_id": str(event.id),
            "aggregate_id": str(event.aggregate_id),
            "event_type": event.event_type.value,
            "occurred_at": event.occurred_at
        }
    
    @staticmethod
    async def remove_item_from_cart_with_events(
        cart_id: UUID, 
        product_id: UUID, 
        user_id: UUID
    ) -> Dict[str, Any]:
        """Remove item from cart and publish domain event"""
        event = DomainEvent(
            id=uuid4(),
            event_type=EventType.CART_ITEM_REMOVED,
            aggregate_id=cart_id,
            aggregate_type="Cart",
            data={
                "product_id": str(product_id),
                "removed_at": datetime.utcnow().isoformat()
            },
            metadata={
                "user_id": str(user_id),
                "source": "cart_service",
                "version": "1.0"
            },
            occurred_at=datetime.utcnow()
        )
        
        await publish_event(event)
        
        return {
            "event_id": str(event.id),
            "aggregate_id": str(event.aggregate_id),
            "event_type": event.event_type.value,
            "occurred_at": event.occurred_at
        }


class UserEventService:
    """Service to integrate user operations with event sourcing"""
    
    @staticmethod
    async def register_user_with_events(user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Register user and publish domain event"""
        user_id = uuid4()
        
        event = DomainEvent(
            id=uuid4(),
            event_type=EventType.USER_REGISTERED,
            aggregate_id=user_id,
            aggregate_type="User",
            data={
                "email": user_data.get("email"),
                "full_name": user_data.get("full_name"),
                "is_active": user_data.get("is_active", True),
                "role": user_data.get("role", "user")
            },
            metadata={
                "source": "auth_service",
                "registration_method": user_data.get("registration_method", "email"),
                "version": "1.0"
            },
            occurred_at=datetime.utcnow()
        )
        
        await publish_event(event)
        
        return {
            "event_id": str(event.id),
            "aggregate_id": str(user_id),
            "event_type": event.event_type.value,
            "occurred_at": event.occurred_at
        }


class PaymentEventService:
    """Service to integrate payment operations with event sourcing"""
    
    @staticmethod
    async def initiate_payment_with_events(
        order_id: UUID, 
        payment_data: Dict[str, Any], 
        user_id: UUID
    ) -> Dict[str, Any]:
        """Initiate payment and publish domain event"""
        payment_id = uuid4()
        
        event = DomainEvent(
            id=uuid4(),
            event_type=EventType.PAYMENT_INITIATED,
            aggregate_id=payment_id,
            aggregate_type="Payment",
            data={
                "order_id": str(order_id),
                "amount": payment_data.get("amount"),
                "currency": payment_data.get("currency", "USD"),
                "payment_method": payment_data.get("payment_method"),
                "gateway": payment_data.get("gateway", "stripe")
            },
            metadata={
                "user_id": str(user_id),
                "source": "payment_service",
                "version": "1.0"
            },
            occurred_at=datetime.utcnow()
        )
        
        await publish_event(event)
        
        return {
            "event_id": str(event.id),
            "aggregate_id": str(payment_id),
            "event_type": event.event_type.value,
            "occurred_at": event.occurred_at
        }
    
    @staticmethod
    async def complete_payment_with_events(
        payment_id: UUID, 
        transaction_data: Dict[str, Any], 
        user_id: UUID
    ) -> Dict[str, Any]:
        """Complete payment and publish domain event"""
        event = DomainEvent(
            id=uuid4(),
            event_type=EventType.PAYMENT_COMPLETED,
            aggregate_id=payment_id,
            aggregate_type="Payment",
            data={
                "transaction_id": transaction_data.get("transaction_id"),
                "gateway_response": transaction_data.get("gateway_response"),
                "amount_paid": transaction_data.get("amount_paid"),
                "completed_at": datetime.utcnow().isoformat()
            },
            metadata={
                "user_id": str(user_id),
                "source": "payment_service",
                "version": "1.0"
            },
            occurred_at=datetime.utcnow()
        )
        
        await publish_event(event)
        
        return {
            "event_id": str(event.id),
            "aggregate_id": str(event.aggregate_id),
            "event_type": event.event_type.value,
            "occurred_at": event.occurred_at
        }


# Event Query Service for retrieving event history
class EventQueryService:
    """Service for querying event history"""
    
    @staticmethod
    async def get_product_history(product_id: UUID) -> List[Dict[str, Any]]:
        """Get complete event history for a product"""
        events = await get_aggregate_events(product_id, "Product")
        return [event.to_dict() for event in events]
    
    @staticmethod
    async def get_order_history(order_id: UUID) -> List[Dict[str, Any]]:
        """Get complete event history for an order"""
        events = await get_aggregate_events(order_id, "Order")
        return [event.to_dict() for event in events]
    
    @staticmethod
    async def get_user_history(user_id: UUID) -> List[Dict[str, Any]]:
        """Get complete event history for a user"""
        events = await get_aggregate_events(user_id, "User")
        return [event.to_dict() for event in events]
    
    @staticmethod
    async def get_cart_history(cart_id: UUID) -> List[Dict[str, Any]]:
        """Get complete event history for a cart"""
        events = await get_aggregate_events(cart_id, "Cart")
        return [event.to_dict() for event in events]


# Event-driven aggregate reconstruction
class AggregateReconstructionService:
    """Service for reconstructing aggregate state from events"""
    
    @staticmethod
    async def reconstruct_product_state(product_id: UUID) -> Dict[str, Any]:
        """Reconstruct product state from events"""
        events = await get_aggregate_events(product_id, "Product")
        
        # Initialize state
        state = {
            "id": str(product_id),
            "name": None,
            "description": None,
            "price": None,
            "stock": None,
            "sku": None,
            "category": None,
            "is_active": True,
            "created_at": None,
            "updated_at": None,
            "events_count": len(events)
        }
        
        # Apply events in chronological order
        for event in events:
            if event.event_type == EventType.PRODUCT_CREATED:
                state.update(event.data)
                state["created_at"] = event.occurred_at.isoformat()
            elif event.event_type == EventType.PRODUCT_UPDATED:
                state.update(event.data)
                state["updated_at"] = event.occurred_at.isoformat()
            elif event.event_type == EventType.PRODUCT_STOCK_UPDATED:
                state["stock"] = event.data.get("new_stock")
                state["updated_at"] = event.occurred_at.isoformat()
        
        return state
    
    @staticmethod
    async def reconstruct_order_state(order_id: UUID) -> Dict[str, Any]:
        """Reconstruct order state from events"""
        events = await get_aggregate_events(order_id, "Order")
        
        state = {
            "id": str(order_id),
            "status": "pending",
            "items": [],
            "total": 0.0,
            "created_at": None,
            "updated_at": None,
            "status_history": [],
            "events_count": len(events)
        }
        
        for event in events:
            if event.event_type == EventType.ORDER_CREATED:
                state.update(event.data)
                state["created_at"] = event.occurred_at.isoformat()
                state["status_history"].append({
                    "status": "created",
                    "timestamp": event.occurred_at.isoformat()
                })
            elif event.event_type in [EventType.ORDER_UPDATED, 
                                      EventType.ORDER_CANCELLED, 
                                      EventType.ORDER_SHIPPED, 
                                      EventType.ORDER_DELIVERED]:
                if "new_status" in event.data:
                    state["status"] = event.data["new_status"]
                    state["status_history"].append({
                        "status": event.data["new_status"],
                        "timestamp": event.occurred_at.isoformat()
                    })
                state["updated_at"] = event.occurred_at.isoformat()
        
        return state