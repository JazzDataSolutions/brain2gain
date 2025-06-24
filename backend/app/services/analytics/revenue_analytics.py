from __future__ import annotations

from datetime import date, datetime, timedelta
from decimal import Decimal
from sqlmodel import Session, and_, select, func

from app.models import SalesOrder, Transaction, TransactionType


class RevenueAnalytics:
    """Service for revenue-related analytics methods."""

    def __init__(self, db: Session):
        self.db = db

    def get_total_revenue(
        self, start_date: datetime | None = None, end_date: datetime | None = None
    ) -> Decimal:
        query = select(func.sum(Transaction.amount)).where(
            Transaction.tx_type == TransactionType.SALE, Transaction.paid
        )
        if start_date:
            query = query.where(Transaction.created_at >= start_date)
        if end_date:
            query = query.where(Transaction.created_at <= end_date)
        result = self.db.exec(query).first()
        return result or Decimal(0)

    def get_daily_revenue(self, target_date: date) -> Decimal:
        start_datetime = datetime.combine(target_date, datetime.min.time())
        end_datetime = datetime.combine(target_date, datetime.max.time())
        return self.get_total_revenue(start_datetime, end_datetime)

    def get_monthly_revenue(self, year: int, month: int) -> Decimal:
        start_date = datetime(year, month, 1)
        if month == 12:
            end_date = datetime(year + 1, 1, 1) - timedelta(seconds=1)
        else:
            end_date = datetime(year, month + 1, 1) - timedelta(seconds=1)
        return self.get_total_revenue(start_date, end_date)

    def get_revenue_growth_rate(self, period_days: int = 30) -> float:
        end_date = datetime.utcnow()
        start_current = end_date - timedelta(days=period_days)
        start_previous = start_current - timedelta(days=period_days)
        end_previous = start_current
        current_revenue = self.get_total_revenue(start_current, end_date)
        previous_revenue = self.get_total_revenue(start_previous, end_previous)
        if previous_revenue == 0:
            return 0.0
        growth_rate = float((current_revenue - previous_revenue) / previous_revenue * 100)
        return round(growth_rate, 2)

    def calculate_mrr(self) -> Decimal:
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        recurring_customers_revenue = self.db.exec(
            select(func.sum(Transaction.amount)).where(
                and_(
                    Transaction.tx_type == TransactionType.SALE,
                    Transaction.paid,
                    Transaction.created_at >= thirty_days_ago,
                    Transaction.customer_id.in_(
                        select(SalesOrder.customer_id)
                        .group_by(SalesOrder.customer_id)
                        .having(func.count(SalesOrder.so_id) > 1)
                    ),
                )
            )
        ).first() or Decimal(0)
        return recurring_customers_revenue

    def calculate_arr(self) -> Decimal:
        return self.calculate_mrr() * 12

    def calculate_cac(self, channel: str | None = None) -> Decimal:
        # Placeholder for marketing spend data
        return Decimal(0)

    def calculate_revenue_per_visitor(self, days: int = 30) -> Decimal:
        start_date = datetime.utcnow() - timedelta(days=days)
        revenue = self.get_total_revenue(start_date)
        active_customers = (
            self.db.exec(
                select(func.count(func.distinct(SalesOrder.customer_id))).where(
                    SalesOrder.order_date >= start_date
                )
            ).first()
            or 1
        )
        return revenue / active_customers if active_customers > 0 else Decimal(0)
