"""
Order Service - Microservice for order processing functionality
Part of Phase 2: Core Microservices Architecture

Handles:
- Order creation and validation
- Order status management
- Order fulfillment workflow
- Order history and tracking
- Integration with inventory and payment services
"""

import logging
from datetime import datetime, timezone
from decimal import Decimal
from typing import List, Optional, Dict, Any
from enum import Enum
import uuid
import asyncio

from sqlalchemy.exc import IntegrityError
from sqlmodel import select, and_, or_
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.config import settings
from app.core.cache import cache_key_wrapper, invalidate_cache_pattern, invalidate_cache_key
from app.models import Product, User  # TODO: Add Order and OrderItem models
from app.schemas.product import ProductCreate, ProductUpdate
from app.services.notification_service import NotificationService

logger = logging.getLogger(__name__)


class OrderStatus(str, Enum):
    """Order status enumeration"""
    PENDING = "PENDING"
    CONFIRMED = "CONFIRMED"
    PROCESSING = "PROCESSING"
    SHIPPED = "SHIPPED"
    DELIVERED = "DELIVERED"
    CANCELLED = "CANCELLED"
    REFUNDED = "REFUNDED"


class OrderService:
    """Service for order business logic and data operations."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.notification_service = NotificationService(session)
    
    async def create_order(
        self, 
        user_id: uuid.UUID,
        items: List[Dict[str, Any]],
        shipping_address: Dict[str, str],
        payment_method: str,
        notes: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a new order with validation.
        
        Args:
            user_id: ID of the user placing the order
            items: List of order items with {product_id, quantity, unit_price}
            shipping_address: Shipping address details
            payment_method: Payment method identifier
            notes: Optional order notes
            
        Returns:
            Created order details
            
        Raises:
            ValueError: If validation fails
        """
        # Validate user exists
        user = await self._get_user_by_id(user_id)
        if not user:
            raise ValueError("User not found")
        
        # Validate order items
        validated_items = await self._validate_order_items(items)
        
        # Calculate order totals
        order_totals = await self._calculate_order_totals(validated_items)
        
        # Validate shipping address
        self._validate_shipping_address(shipping_address)
        
        # Create order record (placeholder structure)
        order_data = {
            "order_id": str(uuid.uuid4()),
            "user_id": str(user_id),
            "status": OrderStatus.PENDING,
            "items": validated_items,
            "subtotal": order_totals["subtotal"],
            "tax_amount": order_totals["tax_amount"],
            "shipping_cost": order_totals["shipping_cost"],
            "total_amount": order_totals["total_amount"],
            "shipping_address": shipping_address,
            "payment_method": payment_method,
            "notes": notes,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        
        try:
            # TODO: Save to database when Order model is implemented
            # For now, simulate order creation
            logger.info(f"Order created successfully: {order_data['order_id']}")
            
            # TODO: Trigger inventory reservation
            await self._reserve_inventory(validated_items)
            
            # TODO: Send order confirmation notification
            await self._send_order_confirmation(order_data)
            
            return order_data
            
        except Exception as e:
            logger.error(f"Error creating order: {e}")
            raise ValueError(f"Failed to create order: {str(e)}")
    
    async def get_order_by_id(self, order_id: str) -> Optional[Dict[str, Any]]:
        """
        Get order by ID.
        
        Args:
            order_id: Order ID
            
        Returns:
            Order details or None if not found
        """
        # TODO: Implement database query when Order model exists
        # For now, return placeholder
        return {
            "order_id": order_id,
            "status": OrderStatus.PENDING,
            "message": "Order lookup not yet implemented - requires Order model"
        }
    
    async def get_user_orders(
        self, 
        user_id: uuid.UUID, 
        skip: int = 0, 
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Get orders for a specific user.
        
        Args:
            user_id: User ID
            skip: Pagination offset
            limit: Maximum results
            
        Returns:
            List of user's orders
        """
        # TODO: Implement database query when Order model exists
        return []
    
    async def update_order_status(
        self, 
        order_id: str, 
        new_status: OrderStatus,
        notes: Optional[str] = None
    ) -> bool:
        """
        Update order status with business logic validation.
        
        Args:
            order_id: Order ID
            new_status: New status
            notes: Optional status change notes
            
        Returns:
            True if updated successfully
            
        Raises:
            ValueError: If status transition is invalid
        """
        # Get current order
        current_order = await self.get_order_by_id(order_id)
        if not current_order:
            raise ValueError("Order not found")
        
        current_status = current_order.get("status")
        
        # Validate status transition
        if not self._is_valid_status_transition(current_status, new_status):
            raise ValueError(f"Invalid status transition from {current_status} to {new_status}")
        
        # TODO: Update database when Order model exists
        logger.info(f"Order {order_id} status updated from {current_status} to {new_status}")
        
        # Handle status-specific actions
        await self._handle_status_change_actions(order_id, new_status, current_order)
        
        return True
    
    async def cancel_order(
        self, 
        order_id: str, 
        reason: str,
        refund_amount: Optional[Decimal] = None
    ) -> bool:
        """
        Cancel an order with proper cleanup.
        
        Args:
            order_id: Order ID
            reason: Cancellation reason
            refund_amount: Amount to refund (if applicable)
            
        Returns:
            True if cancelled successfully
        """
        order = await self.get_order_by_id(order_id)
        if not order:
            raise ValueError("Order not found")
        
        current_status = order.get("status")
        
        # Check if order can be cancelled
        if current_status in [OrderStatus.SHIPPED, OrderStatus.DELIVERED]:
            raise ValueError("Cannot cancel shipped or delivered orders")
        
        try:
            # Update status to cancelled
            await self.update_order_status(order_id, OrderStatus.CANCELLED)
            
            # TODO: Release reserved inventory
            await self._release_inventory_reservation(order_id)
            
            # TODO: Process refund if payment was made
            if refund_amount and refund_amount > 0:
                await self._process_refund(order_id, refund_amount)
            
            # TODO: Send cancellation notification
            await self._send_cancellation_notification(order_id, reason)
            
            logger.info(f"Order {order_id} cancelled successfully. Reason: {reason}")
            return True
            
        except Exception as e:
            logger.error(f"Error cancelling order {order_id}: {e}")
            raise ValueError(f"Failed to cancel order: {str(e)}")
    
    async def get_order_summary(self, order_id: str) -> Dict[str, Any]:
        """
        Get comprehensive order summary including items, payments, and status history.
        
        Args:
            order_id: Order ID
            
        Returns:
            Detailed order summary
        """
        order = await self.get_order_by_id(order_id)
        if not order:
            raise ValueError("Order not found")
        
        # TODO: Implement when models are available
        return {
            "order": order,
            "items": [],  # TODO: Get order items
            "payments": [],  # TODO: Get payment history
            "status_history": [],  # TODO: Get status change history
            "shipping_tracking": None  # TODO: Get shipping info
        }
    
    async def search_orders(
        self,
        filters: Dict[str, Any],
        skip: int = 0,
        limit: int = 50
    ) -> Dict[str, Any]:
        """
        Search orders with various filters.
        
        Args:
            filters: Search filters (status, date_range, user_id, etc.)
            skip: Pagination offset
            limit: Maximum results
            
        Returns:
            Search results with pagination info
        """
        # TODO: Implement database search when Order model exists
        return {
            "orders": [],
            "total": 0,
            "skip": skip,
            "limit": limit,
            "filters": filters
        }
    
    # Private helper methods
    
    async def _get_user_by_id(self, user_id: uuid.UUID) -> Optional[User]:
        """Get user by ID."""
        statement = select(User).where(User.id == user_id)
        result = await self.session.exec(statement)
        return result.first()
    
    async def _validate_order_items(self, items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Validate order items and enrich with product data.
        
        Args:
            items: Raw order items
            
        Returns:
            Validated and enriched order items
            
        Raises:
            ValueError: If validation fails
        """
        if not items:
            raise ValueError("Order must contain at least one item")
        
        validated_items = []
        
        for item in items:
            product_id = item.get("product_id")
            quantity = item.get("quantity", 0)
            
            if not product_id:
                raise ValueError("Product ID is required for all items")
            
            if quantity <= 0:
                raise ValueError("Quantity must be greater than zero")
            
            # Get product details
            statement = select(Product).where(Product.product_id == product_id)
            result = await self.session.exec(statement)
            product = result.first()
            
            if not product:
                raise ValueError(f"Product with ID {product_id} not found")
            
            if product.status != "ACTIVE":
                raise ValueError(f"Product {product.name} is not available")
            
            if product.stock_quantity < quantity:
                raise ValueError(f"Insufficient stock for {product.name}. Available: {product.stock_quantity}")
            
            # Create validated item
            validated_item = {
                "product_id": product_id,
                "product_name": product.name,
                "product_sku": product.sku,
                "quantity": quantity,
                "unit_price": product.unit_price,
                "line_total": product.unit_price * quantity
            }
            
            validated_items.append(validated_item)
        
        return validated_items
    
    async def _calculate_order_totals(self, items: List[Dict[str, Any]]) -> Dict[str, Decimal]:
        """
        Calculate order totals including taxes and shipping.
        
        Args:
            items: Validated order items
            
        Returns:
            Dictionary with subtotal, tax, shipping, and total amounts
        """
        subtotal = sum(Decimal(str(item["line_total"])) for item in items)
        
        # Calculate tax (configurable rate)
        tax_rate = Decimal(str(getattr(settings, 'TAX_RATE', 0.08)))  # 8% default
        tax_amount = subtotal * tax_rate
        
        # Calculate shipping (simplified logic)
        shipping_cost = self._calculate_shipping_cost(subtotal, items)
        
        total_amount = subtotal + tax_amount + shipping_cost
        
        return {
            "subtotal": subtotal,
            "tax_amount": tax_amount,
            "shipping_cost": shipping_cost,
            "total_amount": total_amount
        }
    
    def _calculate_shipping_cost(self, subtotal: Decimal, items: List[Dict[str, Any]]) -> Decimal:
        """
        Calculate shipping cost based on order value and items.
        
        Args:
            subtotal: Order subtotal
            items: Order items
            
        Returns:
            Shipping cost
        """
        # Free shipping threshold
        free_shipping_threshold = Decimal(str(getattr(settings, 'FREE_SHIPPING_THRESHOLD', 100)))
        
        if subtotal >= free_shipping_threshold:
            return Decimal('0.00')
        
        # Base shipping rate
        base_shipping = Decimal(str(getattr(settings, 'BASE_SHIPPING_COST', 10)))
        
        # Additional cost per item (if needed)
        additional_per_item = Decimal('0.50')
        item_count = sum(item["quantity"] for item in items)
        
        return base_shipping + (additional_per_item * max(0, item_count - 1))
    
    def _validate_shipping_address(self, address: Dict[str, str]) -> None:
        """
        Validate shipping address completeness.
        
        Args:
            address: Shipping address dictionary
            
        Raises:
            ValueError: If address is incomplete
        """
        required_fields = ["name", "street", "city", "state", "zip_code", "country"]
        
        for field in required_fields:
            if not address.get(field):
                raise ValueError(f"Shipping address missing required field: {field}")
        
        # Additional validations can be added here
        if len(address.get("zip_code", "")) < 5:
            raise ValueError("Invalid zip code")
    
    def _is_valid_status_transition(self, current_status: str, new_status: OrderStatus) -> bool:
        """
        Check if a status transition is valid based on business rules.
        
        Args:
            current_status: Current order status
            new_status: Proposed new status
            
        Returns:
            True if transition is valid
        """
        # Define valid transitions
        valid_transitions = {
            OrderStatus.PENDING: [OrderStatus.CONFIRMED, OrderStatus.CANCELLED],
            OrderStatus.CONFIRMED: [OrderStatus.PROCESSING, OrderStatus.CANCELLED],
            OrderStatus.PROCESSING: [OrderStatus.SHIPPED, OrderStatus.CANCELLED],
            OrderStatus.SHIPPED: [OrderStatus.DELIVERED],
            OrderStatus.DELIVERED: [OrderStatus.REFUNDED],
            OrderStatus.CANCELLED: [],  # Cannot transition from cancelled
            OrderStatus.REFUNDED: []   # Cannot transition from refunded
        }
        
        return new_status in valid_transitions.get(current_status, [])
    
    async def _handle_status_change_actions(
        self, 
        order_id: str, 
        new_status: OrderStatus,
        order_data: Dict[str, Any]
    ) -> None:
        """
        Handle actions that need to be performed when order status changes.
        
        Args:
            order_id: Order ID
            new_status: New status
            order_data: Order data
        """
        if new_status == OrderStatus.CONFIRMED:
            # Send confirmation email, charge payment
            await self._process_payment(order_id, order_data)
            await self._send_order_confirmation(order_data)
        
        elif new_status == OrderStatus.PROCESSING:
            # Update inventory, prepare for shipping
            await self._update_inventory_for_order(order_id)
        
        elif new_status == OrderStatus.SHIPPED:
            # Send tracking information
            await self._send_shipping_notification(order_id)
        
        elif new_status == OrderStatus.DELIVERED:
            # Send delivery confirmation
            await self._send_delivery_confirmation(order_id)
    
    # Integration methods (placeholders for now)
    
    async def _reserve_inventory(self, items: List[Dict[str, Any]]) -> None:
        """Reserve inventory for order items."""
        # TODO: Integrate with Inventory Service
        logger.info(f"Reserving inventory for {len(items)} items")
    
    async def _release_inventory_reservation(self, order_id: str) -> None:
        """Release inventory reservation for cancelled order."""
        # TODO: Integrate with Inventory Service
        logger.info(f"Releasing inventory reservation for order {order_id}")
    
    async def _update_inventory_for_order(self, order_id: str) -> None:
        """Update inventory when order is being processed."""
        # TODO: Integrate with Inventory Service
        logger.info(f"Updating inventory for order {order_id}")
    
    async def _process_payment(self, order_id: str, order_data: Dict[str, Any]) -> None:
        """Process payment for order."""
        # TODO: Integrate with Payment Service
        logger.info(f"Processing payment for order {order_id}")
    
    async def _process_refund(self, order_id: str, amount: Decimal) -> None:
        """Process refund for cancelled order."""
        # TODO: Integrate with Payment Service
        logger.info(f"Processing refund of ${amount} for order {order_id}")
    
    async def _send_order_confirmation(self, order_data: Dict[str, Any]) -> None:
        """Send order confirmation notification."""
        try:
            await self.notification_service.notify_order_status(
                order_id=order_data['order_id'],
                status="confirmado",
                customer_id=str(order_data['user_id'])
            )
            
            # Also notify admin/sales team of new order
            customer_name = order_data.get('customer_name', 'Cliente')
            total_amount = float(order_data.get('total_amount', 0))
            await self.notification_service.notify_new_order(
                order_id=order_data['order_id'],
                customer_name=customer_name,
                total_amount=total_amount
            )
            
            logger.info(f"Order confirmation notifications sent for order {order_data['order_id']}")
        except Exception as e:
            logger.error(f"Failed to send order confirmation notifications: {e}")
    
    async def _send_cancellation_notification(self, order_id: str, reason: str) -> None:
        """Send order cancellation notification."""
        try:
            # Get order details (would be from database in real implementation)
            order_data = await self.get_order_by_id(order_id)
            if order_data:
                await self.notification_service.notify_order_status(
                    order_id=order_id,
                    status="cancelado",
                    customer_id=str(order_data.get('user_id', ''))
                )
            logger.info(f"Order cancellation notification sent for order {order_id}")
        except Exception as e:
            logger.error(f"Failed to send cancellation notification: {e}")
    
    async def _send_shipping_notification(self, order_id: str) -> None:
        """Send shipping notification with tracking info."""
        try:
            # Get order details (would be from database in real implementation)
            order_data = await self.get_order_by_id(order_id)
            if order_data:
                await self.notification_service.notify_order_status(
                    order_id=order_id,
                    status="enviado",
                    customer_id=str(order_data.get('user_id', ''))
                )
            logger.info(f"Shipping notification sent for order {order_id}")
        except Exception as e:
            logger.error(f"Failed to send shipping notification: {e}")
    
    async def _send_delivery_confirmation(self, order_id: str) -> None:
        """Send delivery confirmation notification."""
        try:
            # Get order details (would be from database in real implementation)
            order_data = await self.get_order_by_id(order_id)
            if order_data:
                await self.notification_service.notify_order_status(
                    order_id=order_id,
                    status="entregado",
                    customer_id=str(order_data.get('user_id', ''))
                )
            logger.info(f"Delivery confirmation sent for order {order_id}")
        except Exception as e:
            logger.error(f"Failed to send delivery confirmation: {e}")


# Global order service instance factory
def create_order_service(session: AsyncSession) -> OrderService:
    """Create an OrderService instance with the given session."""
    return OrderService(session)