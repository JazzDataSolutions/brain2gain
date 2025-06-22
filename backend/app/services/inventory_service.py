# backend/app/services/inventory_service.py
import logging
from datetime import datetime

from sqlmodel import Session, select

from app.models import Stock

logger = logging.getLogger(__name__)


class InventoryService:
    """Service for inventory management and stock control."""

    def __init__(self, session: Session):
        self.session = session

    async def reserve_stock(
        self,
        product_id: int,
        quantity: int,
        reservation_id: str
    ) -> bool:
        """
        Reserve stock for an order (simplified implementation)
        """
        try:
            # Get current stock
            stock = self.session.exec(
                select(Stock).where(Stock.product_id == product_id)
            ).first()

            if not stock:
                raise ValueError(f"No stock record found for product {product_id}")

            if stock.quantity < quantity:
                raise ValueError(f"Insufficient stock: {stock.quantity} available, {quantity} requested")

            # For now, just reduce the stock immediately
            # TODO: Implement proper reservation system with expiration
            stock.quantity -= quantity
            stock.updated_at = datetime.utcnow()

            self.session.add(stock)
            self.session.commit()

            logger.info(f"Reserved {quantity} units of product {product_id} for reservation {reservation_id}")
            return True

        except Exception as e:
            self.session.rollback()
            logger.error(f"Failed to reserve stock: {str(e)}")
            raise

    async def release_stock_reservation(
        self,
        product_id: int,
        quantity: int,
        reservation_id: str
    ) -> bool:
        """
        Release stock reservation (simplified implementation)
        """
        try:
            # Get current stock
            stock = self.session.exec(
                select(Stock).where(Stock.product_id == product_id)
            ).first()

            if not stock:
                logger.warning(f"No stock record found for product {product_id}")
                return False

            # Return stock to available inventory
            stock.quantity += quantity
            stock.updated_at = datetime.utcnow()

            self.session.add(stock)
            self.session.commit()

            logger.info(f"Released {quantity} units of product {product_id} from reservation {reservation_id}")
            return True

        except Exception as e:
            self.session.rollback()
            logger.error(f"Failed to release stock reservation: {str(e)}")
            raise

    async def get_stock_level(self, product_id: int) -> int | None:
        """Get current stock level for a product"""
        stock = self.session.exec(
            select(Stock).where(Stock.product_id == product_id)
        ).first()

        return stock.quantity if stock else None

    async def update_stock_level(
        self,
        product_id: int,
        new_quantity: int,
        reason: str = "Manual adjustment"
    ) -> bool:
        """Update stock level"""
        try:
            stock = self.session.exec(
                select(Stock).where(Stock.product_id == product_id)
            ).first()

            if not stock:
                # Create new stock record
                stock = Stock(
                    product_id=product_id,
                    quantity=new_quantity
                )
            else:
                stock.quantity = new_quantity
                stock.updated_at = datetime.utcnow()

            self.session.add(stock)
            self.session.commit()

            logger.info(f"Updated stock for product {product_id} to {new_quantity}: {reason}")
            return True

        except Exception as e:
            self.session.rollback()
            logger.error(f"Failed to update stock level: {str(e)}")
            raise
