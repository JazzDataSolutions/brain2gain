from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from sqlmodel import Session, select, func

from app.models import OrderStatus, SalesItem, SalesOrder


class OrderAnalytics:
    """Service for order-related analytics methods."""

    def __init__(self, db: Session):
        self.db = db

    def get_average_order_value(
        self, start_date: datetime | None = None, end_date: datetime | None = None
    ) -> Decimal:
        revenue_query = (
            select(func.sum(SalesItem.qty * SalesItem.unit_price))
            .join(SalesOrder)
            .where(SalesOrder.status == OrderStatus.COMPLETED)
        )
        orders_query = select(func.count(SalesOrder.so_id)).where(
            SalesOrder.status == OrderStatus.COMPLETED
        )
        if start_date:
            revenue_query = revenue_query.where(SalesOrder.order_date >= start_date)
            orders_query = orders_query.where(SalesOrder.order_date >= start_date)
        if end_date:
            revenue_query = revenue_query.where(SalesOrder.order_date <= end_date)
            orders_query = orders_query.where(SalesOrder.order_date <= end_date)
        total_revenue = self.db.exec(revenue_query).first() or Decimal(0)
        total_orders = self.db.exec(orders_query).first() or 0
        if total_orders == 0:
            return Decimal(0)
        return round(total_revenue / total_orders, 2)

    def get_order_metrics(self) -> dict:
        today = datetime.utcnow().date()
        month_start = datetime(today.year, today.month, 1)
        orders_today = (
            self.db.exec(
                select(func.count(SalesOrder.so_id)).where(
                    func.date(SalesOrder.order_date) == today
                )
            ).first()
            or 0
        )
        orders_month = (
            self.db.exec(
                select(func.count(SalesOrder.so_id)).where(
                    SalesOrder.order_date >= month_start
                )
            ).first()
            or 0
        )
        pending_orders = (
            self.db.exec(
                select(func.count(SalesOrder.so_id)).where(
                    SalesOrder.status == OrderStatus.PENDING
                )
            ).first()
            or 0
        )
        return {
            "orders_today": orders_today,
            "orders_month": orders_month,
            "pending_orders": pending_orders,
            "average_order_value": float(self.get_average_order_value()),
        }
