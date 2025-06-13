"""
Inventory Service - Microservice for real-time stock control
Part of Phase 2: Core Microservices Architecture

Handles:
- Stock level management and tracking
- Inventory reservations for orders
- Stock alerts and low inventory warnings
- Multi-warehouse inventory support
- Stock movement history and auditing
- Automated reorder points and purchasing suggestions
"""

import logging
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from typing import List, Optional, Dict, Any
from enum import Enum
import uuid
import asyncio

from sqlalchemy.exc import IntegrityError
from sqlmodel import select, and_, or_, func
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.config import settings
from app.core.cache import cache_key_wrapper, invalidate_cache_pattern, invalidate_cache_key
from app.models import Product
from app.services.notification_service import NotificationService

logger = logging.getLogger(__name__)


class StockMovementType(str, Enum):
    """Stock movement types"""
    PURCHASE = "PURCHASE"          # Incoming stock from suppliers
    SALE = "SALE"                  # Outgoing stock from sales
    ADJUSTMENT = "ADJUSTMENT"      # Manual adjustments
    RESERVATION = "RESERVATION"    # Reserved for pending orders
    RELEASE = "RELEASE"           # Released reservations
    DAMAGE = "DAMAGE"             # Damaged/unusable stock
    TRANSFER = "TRANSFER"         # Warehouse transfers
    RETURN = "RETURN"             # Customer returns


class InventoryService:
    """Service for inventory management and stock control."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.notification_service = NotificationService(session)
    
    async def get_stock_level(self, product_id: int) -> Dict[str, Any]:
        """
        Get current stock level for a product.
        
        Args:
            product_id: Product ID
            
        Returns:
            Stock information including available, reserved, and total quantities
        """
        product = await self._get_product_by_id(product_id)
        if not product:
            raise ValueError("Product not found")
        
        # TODO: Implement proper inventory tracking table
        # For now, use product.stock_quantity as total stock
        total_stock = product.stock_quantity
        reserved_stock = await self._get_reserved_stock(product_id)
        available_stock = max(0, total_stock - reserved_stock)
        
        return {
            "product_id": product_id,
            "product_name": product.name,
            "product_sku": product.sku,
            "total_stock": total_stock,
            "reserved_stock": reserved_stock,
            "available_stock": available_stock,
            "reorder_point": await self._get_reorder_point(product_id),
            "is_low_stock": available_stock < await self._get_reorder_point(product_id),
            "last_updated": datetime.now(timezone.utc).isoformat()
        }
    
    async def update_stock(
        self,
        product_id: int,
        quantity_change: int,
        movement_type: StockMovementType,
        reference_id: Optional[str] = None,
        notes: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Update stock levels with proper auditing.
        
        Args:
            product_id: Product ID
            quantity_change: Change in quantity (positive for increase, negative for decrease)
            movement_type: Type of stock movement
            reference_id: Reference to order, purchase, etc.
            notes: Optional notes for the movement
            
        Returns:
            Updated stock information
            
        Raises:
            ValueError: If update would result in negative stock
        """
        product = await self._get_product_by_id(product_id)
        if not product:
            raise ValueError("Product not found")
        
        current_stock = product.stock_quantity
        new_stock = current_stock + quantity_change
        
        # Prevent negative stock unless it's a reservation
        if new_stock < 0 and movement_type != StockMovementType.RESERVATION:
            raise ValueError(f"Insufficient stock. Current: {current_stock}, Requested: {abs(quantity_change)}")
        
        try:
            # Update product stock
            product.stock_quantity = new_stock
            self.session.add(product)
            await self.session.commit()
            
            # Create stock movement record
            movement_record = await self._create_stock_movement(
                product_id=product_id,
                quantity_change=quantity_change,
                movement_type=movement_type,
                reference_id=reference_id,
                notes=notes,
                old_quantity=current_stock,
                new_quantity=new_stock
            )
            
            # Invalidate cache
            await self._invalidate_stock_cache(product_id)
            
            # Check for low stock alerts
            await self._check_low_stock_alert(product_id, new_stock)
            
            logger.info(f"Stock updated for product {product_id}: {current_stock} -> {new_stock} ({movement_type})")
            
            return await self.get_stock_level(product_id)
            
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Error updating stock for product {product_id}: {e}")
            raise ValueError(f"Failed to update stock: {str(e)}")
    
    async def reserve_stock(
        self,
        reservations: List[Dict[str, Any]],
        order_id: str
    ) -> Dict[str, Any]:
        """
        Reserve stock for an order.
        
        Args:
            reservations: List of {product_id, quantity} to reserve
            order_id: Order ID for reference
            
        Returns:
            Reservation results
            
        Raises:
            ValueError: If insufficient stock for any item
        """
        successful_reservations = []
        failed_reservations = []
        
        # First, check if all items can be reserved
        for reservation in reservations:
            product_id = reservation.get("product_id")
            quantity = reservation.get("quantity", 0)
            
            if quantity <= 0:
                failed_reservations.append({
                    "product_id": product_id,
                    "error": "Quantity must be positive"
                })
                continue
            
            stock_info = await self.get_stock_level(product_id)
            if stock_info["available_stock"] < quantity:
                failed_reservations.append({
                    "product_id": product_id,
                    "requested": quantity,
                    "available": stock_info["available_stock"],
                    "error": "Insufficient stock"
                })
        
        # If any reservations would fail, don't process any
        if failed_reservations:
            return {
                "success": False,
                "order_id": order_id,
                "successful_reservations": [],
                "failed_reservations": failed_reservations,
                "message": "Reservation failed due to insufficient stock"
            }
        
        # Process all reservations
        for reservation in reservations:
            try:
                product_id = reservation.get("product_id")
                quantity = reservation.get("quantity")
                
                # Create reservation record
                await self._create_stock_reservation(product_id, quantity, order_id)
                
                successful_reservations.append({
                    "product_id": product_id,
                    "quantity": quantity,
                    "reserved_at": datetime.now(timezone.utc).isoformat()
                })
                
            except Exception as e:
                failed_reservations.append({
                    "product_id": reservation.get("product_id"),
                    "error": str(e)
                })
        
        return {
            "success": len(failed_reservations) == 0,
            "order_id": order_id,
            "successful_reservations": successful_reservations,
            "failed_reservations": failed_reservations,
            "total_items": len(reservations),
            "reserved_items": len(successful_reservations)
        }
    
    async def release_reservation(
        self,
        order_id: str,
        release_type: str = "cancelled"
    ) -> Dict[str, Any]:
        """
        Release stock reservations for an order.
        
        Args:
            order_id: Order ID
            release_type: Reason for release (cancelled, fulfilled, expired)
            
        Returns:
            Release results
        """
        # TODO: Get reservations from database
        # For now, simulate reservation release
        logger.info(f"Releasing stock reservations for order {order_id} ({release_type})")
        
        return {
            "success": True,
            "order_id": order_id,
            "release_type": release_type,
            "released_at": datetime.now(timezone.utc).isoformat(),
            "message": "Reservations released successfully"
        }
    
    async def fulfill_order_stock(
        self,
        order_id: str,
        items: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Fulfill an order by converting reservations to actual stock deductions.
        
        Args:
            order_id: Order ID
            items: List of {product_id, quantity} being fulfilled
            
        Returns:
            Fulfillment results
        """
        successful_fulfillments = []
        failed_fulfillments = []
        
        for item in items:
            try:
                product_id = item.get("product_id")
                quantity = item.get("quantity")
                
                # Deduct stock (convert reservation to actual sale)
                await self.update_stock(
                    product_id=product_id,
                    quantity_change=-quantity,
                    movement_type=StockMovementType.SALE,
                    reference_id=order_id,
                    notes=f"Order fulfillment for order {order_id}"
                )
                
                successful_fulfillments.append({
                    "product_id": product_id,
                    "quantity": quantity,
                    "fulfilled_at": datetime.now(timezone.utc).isoformat()
                })
                
            except Exception as e:
                failed_fulfillments.append({
                    "product_id": item.get("product_id"),
                    "error": str(e)
                })
        
        # Release any remaining reservations
        await self.release_reservation(order_id, "fulfilled")
        
        return {
            "success": len(failed_fulfillments) == 0,
            "order_id": order_id,
            "successful_fulfillments": successful_fulfillments,
            "failed_fulfillments": failed_fulfillments,
            "fulfilled_at": datetime.now(timezone.utc).isoformat()
        }
    
    async def get_low_stock_alerts(
        self,
        threshold_override: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Get products that are low in stock.
        
        Args:
            threshold_override: Override default threshold
            
        Returns:
            List of low stock products with details
        """
        low_stock_products = []
        
        # Get all active products
        statement = select(Product).where(Product.status == "ACTIVE")
        result = await self.session.exec(statement)
        products = result.all()
        
        for product in products:
            reorder_point = threshold_override or await self._get_reorder_point(product.product_id)
            stock_info = await self.get_stock_level(product.product_id)
            
            if stock_info["available_stock"] < reorder_point:
                low_stock_products.append({
                    **stock_info,
                    "reorder_point": reorder_point,
                    "stock_deficit": reorder_point - stock_info["available_stock"],
                    "suggested_order_quantity": await self._calculate_suggested_order_quantity(product.product_id)
                })
        
        return sorted(low_stock_products, key=lambda x: x["stock_deficit"], reverse=True)
    
    async def get_stock_movement_history(
        self,
        product_id: int,
        days: int = 30,
        movement_types: Optional[List[StockMovementType]] = None
    ) -> List[Dict[str, Any]]:
        """
        Get stock movement history for a product.
        
        Args:
            product_id: Product ID
            days: Number of days to look back
            movement_types: Filter by specific movement types
            
        Returns:
            List of stock movements
        """
        # TODO: Implement when stock_movements table is created
        # For now, return placeholder data
        return [
            {
                "movement_id": str(uuid.uuid4()),
                "product_id": product_id,
                "movement_type": "PURCHASE",
                "quantity_change": 50,
                "old_quantity": 10,
                "new_quantity": 60,
                "reference_id": "PO-2024-001",
                "notes": "Initial stock purchase",
                "created_at": (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()
            }
        ]
    
    async def bulk_stock_update(
        self,
        updates: List[Dict[str, Any]],
        movement_type: StockMovementType = StockMovementType.ADJUSTMENT,
        notes: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Perform bulk stock updates.
        
        Args:
            updates: List of {product_id, new_quantity} or {product_id, quantity_change}
            movement_type: Type of movement for all updates
            notes: Notes for all movements
            
        Returns:
            Bulk update results
        """
        successful_updates = []
        failed_updates = []
        
        for update in updates:
            try:
                product_id = update.get("product_id")
                
                if "new_quantity" in update:
                    # Set absolute quantity
                    current_stock = (await self.get_stock_level(product_id))["total_stock"]
                    quantity_change = update["new_quantity"] - current_stock
                else:
                    # Relative change
                    quantity_change = update.get("quantity_change", 0)
                
                result = await self.update_stock(
                    product_id=product_id,
                    quantity_change=quantity_change,
                    movement_type=movement_type,
                    notes=notes
                )
                
                successful_updates.append(result)
                
            except Exception as e:
                failed_updates.append({
                    "product_id": update.get("product_id"),
                    "error": str(e)
                })
        
        return {
            "successful_updates": successful_updates,
            "failed_updates": failed_updates,
            "total_processed": len(updates),
            "successful_count": len(successful_updates),
            "failed_count": len(failed_updates),
            "processed_at": datetime.now(timezone.utc).isoformat()
        }
    
    # Private helper methods
    
    async def _get_product_by_id(self, product_id: int) -> Optional[Product]:
        """Get product by ID."""
        statement = select(Product).where(Product.product_id == product_id)
        result = await self.session.exec(statement)
        return result.first()
    
    async def _get_reserved_stock(self, product_id: int) -> int:
        """
        Get currently reserved stock for a product.
        TODO: Implement with proper reservations table.
        """
        # Placeholder - in real implementation, sum from reservations table
        return 0
    
    async def _get_reorder_point(self, product_id: int) -> int:
        """
        Get reorder point for a product.
        TODO: Implement with product settings or calculate based on sales velocity.
        """
        # Placeholder - configurable per product
        return getattr(settings, 'DEFAULT_REORDER_POINT', 10)
    
    async def _create_stock_movement(
        self,
        product_id: int,
        quantity_change: int,
        movement_type: StockMovementType,
        reference_id: Optional[str],
        notes: Optional[str],
        old_quantity: int,
        new_quantity: int
    ) -> Dict[str, Any]:
        """
        Create a stock movement record.
        TODO: Implement with proper stock_movements table.
        """
        movement_record = {
            "movement_id": str(uuid.uuid4()),
            "product_id": product_id,
            "quantity_change": quantity_change,
            "movement_type": movement_type,
            "reference_id": reference_id,
            "notes": notes,
            "old_quantity": old_quantity,
            "new_quantity": new_quantity,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "created_by": "system"  # TODO: Get from auth context
        }
        
        # TODO: Save to database
        logger.info(f"Stock movement recorded: {movement_record}")
        return movement_record
    
    async def _create_stock_reservation(
        self,
        product_id: int,
        quantity: int,
        order_id: str
    ) -> Dict[str, Any]:
        """
        Create a stock reservation record.
        TODO: Implement with proper reservations table.
        """
        reservation = {
            "reservation_id": str(uuid.uuid4()),
            "product_id": product_id,
            "quantity": quantity,
            "order_id": order_id,
            "reserved_at": datetime.now(timezone.utc).isoformat(),
            "expires_at": (datetime.now(timezone.utc) + timedelta(hours=24)).isoformat(),
            "status": "ACTIVE"
        }
        
        # TODO: Save to database
        logger.info(f"Stock reservation created: {reservation}")
        return reservation
    
    async def _check_low_stock_alert(self, product_id: int, current_stock: int) -> None:
        """
        Check if product stock is low and trigger alerts.
        
        Args:
            product_id: Product ID
            current_stock: Current stock level
        """
        reorder_point = await self._get_reorder_point(product_id)
        
        if current_stock <= reorder_point:
            # Get product details for notification
            product = await self._get_product_by_id(product_id)
            if product:
                # Send real-time notification
                try:
                    await self.notification_service.notify_low_stock(
                        product_id=str(product_id),
                        product_name=product.name,
                        stock_quantity=current_stock,
                        min_stock=reorder_point
                    )
                    logger.info(f"Low stock notification sent for product {product_id}: {current_stock} <= {reorder_point}")
                except Exception as e:
                    logger.error(f"Failed to send low stock notification for product {product_id}: {e}")
            
            logger.warning(f"Low stock alert: Product {product_id} has {current_stock} items (reorder point: {reorder_point})")
    
    async def _calculate_suggested_order_quantity(self, product_id: int) -> int:
        """
        Calculate suggested order quantity based on sales velocity and lead time.
        TODO: Implement with proper sales data analysis.
        """
        # Placeholder calculation
        reorder_point = await self._get_reorder_point(product_id)
        return reorder_point * 2  # Simple 2x reorder point
    
    async def _invalidate_stock_cache(self, product_id: int) -> None:
        """Invalidate stock-related cache entries."""
        try:
            await invalidate_cache_pattern(f"inventory:stock:{product_id}:*")
            await invalidate_cache_pattern("inventory:low_stock:*")
            logger.debug(f"Cache invalidated for product {product_id}")
        except Exception as e:
            logger.warning(f"Failed to invalidate inventory cache: {e}")


# Global inventory service instance factory
def create_inventory_service(session: AsyncSession) -> InventoryService:
    """Create an InventoryService instance with the given session."""
    return InventoryService(session)