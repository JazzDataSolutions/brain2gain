# backend/app/services/order_service.py
import logging
import uuid
from datetime import datetime
from decimal import Decimal

from fastapi import HTTPException, status
from sqlmodel import Session, String, func, or_, select

from app.models import (
    Cart,
    CartItem,
    Order,
    OrderItem,
    OrderStatus,
    PaymentStatus,
    Product,
    Stock,
    User,
)
from app.schemas.order import (
    CheckoutCalculation,
    CheckoutInitiate,
    CheckoutValidation,
    OrderFilters,
    OrderUpdate,
)
from app.services.inventory_service import InventoryService
from app.services.notification_service import NotificationService

logger = logging.getLogger(__name__)


class OrderService:
    """Service for order business logic and data operations."""

    def __init__(self, session: Session):
        self.session = session
        self.inventory_service = InventoryService(session)
        self.notification_service = NotificationService(session)

    # ─── ORDER CREATION ──────────────────────────────────────────────────
    async def create_order_from_cart(
        self,
        user_id: uuid.UUID,
        cart: Cart,
        checkout_data: CheckoutInitiate
    ) -> Order:
        """
        Create order from user's cart
        """
        try:
            # Calculate order totals
            calculation = await self.calculate_order_totals(
                cart_items=cart.items,
                shipping_address=checkout_data.shipping_address,
                payment_method=checkout_data.payment_method
            )

            # Create order
            order = Order(
                user_id=user_id,
                status=OrderStatus.PENDING,
                payment_status=PaymentStatus.PENDING,
                payment_method=checkout_data.payment_method,
                subtotal=calculation.subtotal,
                tax_amount=calculation.tax_amount,
                shipping_cost=calculation.shipping_cost,
                total_amount=calculation.total_amount,
                shipping_address=checkout_data.shipping_address.dict(),
                billing_address=(checkout_data.billing_address.dict()
                                if checkout_data.billing_address
                                else checkout_data.shipping_address.dict()),
                notes=getattr(checkout_data, 'notes', None)
            )

            self.session.add(order)
            self.session.flush()  # Get order_id

            # Create order items
            for cart_item in cart.items:
                product = await self._get_product(cart_item.product_id)
                if not product:
                    raise ValueError(f"Product {cart_item.product_id} not found")

                # Reserve inventory
                await self.inventory_service.reserve_stock(
                    product_id=cart_item.product_id,
                    quantity=cart_item.quantity,
                    reservation_id=str(order.order_id)
                )

                # Calculate line total
                line_total = cart_item.quantity * product.unit_price

                order_item = OrderItem(
                    order_id=order.order_id,
                    product_id=cart_item.product_id,
                    product_name=product.name,
                    product_sku=product.sku,
                    quantity=cart_item.quantity,
                    unit_price=product.unit_price,
                    line_total=line_total,
                    discount_amount=Decimal(0)  # TODO: Implement discounts
                )

                self.session.add(order_item)

            self.session.commit()

            # Send notifications
            await self._send_order_notifications(order, "created")

            logger.info(f"Order {order.order_id} created for user {user_id}")
            return order

        except Exception as e:
            self.session.rollback()
            logger.error(f"Failed to create order: {str(e)}")
            raise

    async def calculate_order_totals(
        self,
        cart_items: list[CartItem],
        shipping_address: dict,
        payment_method: str
    ) -> CheckoutCalculation:
        """
        Calculate order totals including tax and shipping
        """
        subtotal = Decimal(0)
        order_items = []

        for cart_item in cart_items:
            product = await self._get_product(cart_item.product_id)
            if not product:
                raise ValueError(f"Product {cart_item.product_id} not found")

            # Check stock availability
            stock = await self._get_product_stock(cart_item.product_id)
            if not stock or stock.quantity < cart_item.quantity:
                raise ValueError(f"Insufficient stock for product {product.name}")

            line_total = cart_item.quantity * product.unit_price
            subtotal += line_total

            order_items.append({
                "product_id": cart_item.product_id,
                "product_name": product.name,
                "product_sku": product.sku,
                "quantity": cart_item.quantity,
                "unit_price": product.unit_price,
                "line_total": line_total
            })

        # Calculate tax (16% IVA in Mexico)
        tax_rate = Decimal("0.16")
        tax_amount = subtotal * tax_rate

        # Calculate shipping cost
        shipping_cost = await self._calculate_shipping_cost(
            subtotal=subtotal,
            shipping_address=shipping_address,
            payment_method=payment_method
        )

        total_amount = subtotal + tax_amount + shipping_cost

        return CheckoutCalculation(
            subtotal=subtotal,
            tax_amount=tax_amount,
            shipping_cost=shipping_cost,
            total_amount=total_amount,
            items=order_items
        )

    async def validate_checkout(
        self,
        cart: Cart,
        checkout_data: CheckoutInitiate
    ) -> CheckoutValidation:
        """
        Validate checkout data before processing
        """
        errors = []
        warnings = []

        # Validate cart items
        if not cart.items:
            errors.append("Cart is empty")
            return CheckoutValidation(valid=False, errors=errors)

        # Validate stock availability
        for cart_item in cart.items:
            product = await self._get_product(cart_item.product_id)
            if not product:
                errors.append(f"Product {cart_item.product_id} not found")
                continue

            stock = await self._get_product_stock(cart_item.product_id)
            if not stock:
                errors.append(f"Stock information not available for {product.name}")
                continue

            if stock.quantity < cart_item.quantity:
                if stock.quantity == 0:
                    errors.append(f"Product '{product.name}' is out of stock")
                else:
                    errors.append(
                        f"Only {stock.quantity} units available for '{product.name}', "
                        f"but {cart_item.quantity} requested"
                    )
            elif stock.quantity < cart_item.quantity + 5:  # Low stock warning
                warnings.append(
                    f"Low stock warning: Only {stock.quantity} units left for '{product.name}'"
                )

        # Validate payment method
        valid_payment_methods = ["stripe", "paypal", "bank_transfer"]
        if checkout_data.payment_method not in valid_payment_methods:
            errors.append(f"Invalid payment method: {checkout_data.payment_method}")

        # Validate shipping address
        address = checkout_data.shipping_address
        required_fields = ["first_name", "last_name", "address_line_1", "city", "state", "postal_code", "country"]
        for field in required_fields:
            if not getattr(address, field, None):
                errors.append(f"Missing required shipping address field: {field}")

        # Calculate totals if validation passes
        calculation = None
        if not errors:
            try:
                calculation = await self.calculate_order_totals(
                    cart_items=cart.items,
                    shipping_address=checkout_data.shipping_address.dict(),
                    payment_method=checkout_data.payment_method
                )
            except Exception as e:
                errors.append(f"Failed to calculate totals: {str(e)}")

        return CheckoutValidation(
            valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            calculation=calculation
        )

    # ─── ORDER RETRIEVAL ─────────────────────────────────────────────────
    async def get_order_by_id(self, order_id: uuid.UUID) -> Order | None:
        """Get order by ID with items"""
        statement = (
            select(Order)
            .where(Order.order_id == order_id)
        )
        result = self.session.exec(statement)
        order = result.first()

        if order:
            # Load order items
            items_statement = select(OrderItem).where(OrderItem.order_id == order_id)
            items_result = self.session.exec(items_statement)
            order.items = list(items_result)

        return order

    async def get_user_orders(
        self,
        user_id: uuid.UUID,
        page: int = 1,
        page_size: int = 10,
        filters: OrderFilters | None = None
    ) -> tuple[list[Order], int]:
        """Get user's orders with pagination"""
        # Build query
        statement = select(Order).where(Order.user_id == user_id)

        # Apply filters
        if filters:
            if filters.status:
                statement = statement.where(Order.status.in_(filters.status))
            if filters.payment_status:
                statement = statement.where(Order.payment_status.in_(filters.payment_status))
            if filters.date_from:
                statement = statement.where(Order.created_at >= filters.date_from)
            if filters.date_to:
                statement = statement.where(Order.created_at <= filters.date_to)
            if filters.min_amount:
                statement = statement.where(Order.total_amount >= filters.min_amount)
            if filters.max_amount:
                statement = statement.where(Order.total_amount <= filters.max_amount)

        # Count total
        count_statement = select(func.count(Order.order_id)).where(Order.user_id == user_id)
        if filters:
            if filters.status:
                count_statement = count_statement.where(Order.status.in_(filters.status))
            if filters.payment_status:
                count_statement = count_statement.where(Order.payment_status.in_(filters.payment_status))

        total = self.session.exec(count_statement).first()

        # Apply pagination
        statement = statement.order_by(Order.created_at.desc())
        statement = statement.offset((page - 1) * page_size).limit(page_size)

        result = self.session.exec(statement)
        orders = list(result)

        # Load order items for each order
        for order in orders:
            items_statement = select(OrderItem).where(OrderItem.order_id == order.order_id)
            items_result = self.session.exec(items_statement)
            order.items = list(items_result)

        return orders, total

    async def get_all_orders(
        self,
        page: int = 1,
        page_size: int = 20,
        filters: OrderFilters | None = None
    ) -> tuple[list[Order], int]:
        """Get all orders (admin) with pagination"""
        # Build query
        statement = select(Order)

        # Apply filters
        if filters:
            if filters.status:
                statement = statement.where(Order.status.in_(filters.status))
            if filters.payment_status:
                statement = statement.where(Order.payment_status.in_(filters.payment_status))
            if filters.date_from:
                statement = statement.where(Order.created_at >= filters.date_from)
            if filters.date_to:
                statement = statement.where(Order.created_at <= filters.date_to)
            if filters.min_amount:
                statement = statement.where(Order.total_amount >= filters.min_amount)
            if filters.max_amount:
                statement = statement.where(Order.total_amount <= filters.max_amount)
            if filters.search:
                # Search in order ID or customer name
                search_term = f"%{filters.search}%"
                statement = statement.join(User).where(
                    or_(
                        Order.order_id.cast(String).like(search_term),
                        User.full_name.like(search_term),
                        User.email.like(search_term)
                    )
                )

        # Count total
        count_statement = select(func.count(Order.order_id))
        if filters and filters.search:
            count_statement = count_statement.join(User).where(
                or_(
                    Order.order_id.cast(String).like(f"%{filters.search}%"),
                    User.full_name.like(f"%{filters.search}%"),
                    User.email.like(f"%{filters.search}%")
                )
            )

        total = self.session.exec(count_statement).first()

        # Apply pagination
        statement = statement.order_by(Order.created_at.desc())
        statement = statement.offset((page - 1) * page_size).limit(page_size)

        result = self.session.exec(statement)
        orders = list(result)

        # Load order items for each order
        for order in orders:
            items_statement = select(OrderItem).where(OrderItem.order_id == order.order_id)
            items_result = self.session.exec(items_statement)
            order.items = list(items_result)

        return orders, total

    # ─── ORDER MANAGEMENT ────────────────────────────────────────────────
    async def update_order(self, order_id: uuid.UUID, order_update: OrderUpdate) -> Order:
        """Update order (admin only)"""
        order = await self.get_order_by_id(order_id)
        if not order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Order not found"
            )

        # Update fields
        update_data = order_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(order, field, value)

        order.updated_at = datetime.utcnow()

        self.session.add(order)
        self.session.commit()
        self.session.refresh(order)

        # Send notifications for status changes
        if 'status' in update_data:
            await self._send_order_notifications(order, "status_updated")

        logger.info(f"Order {order_id} updated")
        return order

    async def cancel_order(self, order_id: uuid.UUID, reason: str) -> Order:
        """Cancel order and release inventory"""
        order = await self.get_order_by_id(order_id)
        if not order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Order not found"
            )

        # Update order status
        order.status = OrderStatus.CANCELLED
        order.cancelled_at = datetime.utcnow()
        order.notes = f"{order.notes or ''}\nCancellation reason: {reason}".strip()
        order.updated_at = datetime.utcnow()

        # Release inventory reservations
        for item in order.items:
            await self.inventory_service.release_stock_reservation(
                product_id=item.product_id,
                quantity=item.quantity,
                reservation_id=str(order_id)
            )

        self.session.add(order)
        self.session.commit()

        # Send notifications
        await self._send_order_notifications(order, "cancelled")

        logger.info(f"Order {order_id} cancelled: {reason}")
        return order

    async def get_order_statistics(self) -> dict:
        """Get order statistics for admin dashboard"""
        # Order counts by status
        status_counts = {}
        for status in OrderStatus:
            count_stmt = select(func.count(Order.order_id)).where(Order.status == status)
            count = self.session.exec(count_stmt).first()
            status_counts[status.value] = count

        # Revenue calculations
        revenue_stmt = select(func.sum(Order.total_amount)).where(
            Order.status.in_([OrderStatus.DELIVERED, OrderStatus.SHIPPED])
        )
        total_revenue = self.session.exec(revenue_stmt).first() or Decimal(0)

        # Average order value
        avg_stmt = select(func.avg(Order.total_amount)).where(
            Order.status.in_([OrderStatus.DELIVERED, OrderStatus.SHIPPED])
        )
        avg_order_value = self.session.exec(avg_stmt).first() or Decimal(0)

        # Orders today
        today = datetime.now().date()
        today_stmt = select(func.count(Order.order_id)).where(
            func.date(Order.created_at) == today
        )
        orders_today = self.session.exec(today_stmt).first()

        return {
            "total_orders": sum(status_counts.values()),
            "pending_orders": status_counts.get("PENDING", 0),
            "processing_orders": status_counts.get("PROCESSING", 0),
            "shipped_orders": status_counts.get("SHIPPED", 0),
            "delivered_orders": status_counts.get("DELIVERED", 0),
            "cancelled_orders": status_counts.get("CANCELLED", 0),
            "total_revenue": total_revenue,
            "average_order_value": avg_order_value,
            "orders_today": orders_today,
            "orders_this_week": 0,  # TODO: Implement
            "orders_this_month": 0,  # TODO: Implement
        }

    # ─── PRIVATE HELPER METHODS ──────────────────────────────────────────
    async def _get_product(self, product_id: int) -> Product | None:
        """Get product by ID"""
        statement = select(Product).where(Product.product_id == product_id)
        result = self.session.exec(statement)
        return result.first()

    async def _get_product_stock(self, product_id: int) -> Stock | None:
        """Get product stock information"""
        statement = select(Stock).where(Stock.product_id == product_id)
        result = self.session.exec(statement)
        return result.first()

    async def _calculate_shipping_cost(
        self,
        subtotal: Decimal,
        shipping_address: dict,
        payment_method: str
    ) -> Decimal:
        """Calculate shipping cost based on location and order value"""
        # Free shipping for orders over $1000 MXN
        if subtotal >= Decimal("1000"):
            return Decimal(0)

        # Basic shipping cost calculation
        # TODO: Implement proper shipping calculator with zones
        base_shipping = Decimal("150")  # 150 MXN base shipping

        # Adjust based on location (example logic)
        state = shipping_address.get("state", "").upper()
        if state in ["CDMX", "MEXICO", "GUADALAJARA"]:
            # Major cities - standard rate
            return base_shipping
        else:
            # Other states - higher rate
            return base_shipping * Decimal("1.5")

    async def _send_order_notifications(self, order: Order, event_type: str):
        """Send order-related notifications"""
        try:
            await self.notification_service.send_order_notification(
                order_id=order.order_id,
                user_id=order.user_id,
                event_type=event_type,
                order_data={
                    "status": order.status,
                    "total_amount": float(order.total_amount),
                    "items_count": len(order.items)
                }
            )
        except Exception as e:
            logger.error(f"Failed to send order notification: {str(e)}")
            # Don't fail the order operation if notification fails
