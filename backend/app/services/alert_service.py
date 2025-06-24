# backend/app/services/alert_service.py

from datetime import datetime, timedelta
from enum import Enum

from sqlmodel import Session, func, select

from ..models import (
    OrderStatus,
    Product,
    SalesOrder,
    Stock,
    Transaction,
)
from .analytics_service import AnalyticsService


class AlertSeverity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class AlertType(str, Enum):
    INVENTORY_LOW_STOCK = "inventory_low_stock"
    INVENTORY_OUT_OF_STOCK = "inventory_out_of_stock"
    REVENUE_DROP = "revenue_drop"
    HIGH_PENDING_ORDERS = "high_pending_orders"
    CONVERSION_DROP = "conversion_drop"
    SYSTEM_PERFORMANCE = "system_performance"
    HIGH_CHURN_RISK = "high_churn_risk"
    LOW_CLV = "low_clv"
    MRR_DECLINE = "mrr_decline"
    AOV_DROP = "aov_drop"


class Alert:
    def __init__(
        self,
        alert_type: AlertType,
        severity: AlertSeverity,
        title: str,
        description: str,
        data: dict | None = None,
        timestamp: datetime | None = None,
    ):
        self.alert_type = alert_type
        self.severity = severity
        self.title = title
        self.description = description
        self.data = data or {}
        self.timestamp = timestamp or datetime.utcnow()
        self.id = f"{alert_type.value}_{int(self.timestamp.timestamp())}"

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "type": self.alert_type.value,
            "severity": self.severity.value,
            "title": self.title,
            "description": self.description,
            "data": self.data,
            "timestamp": self.timestamp.isoformat(),
            "created_at": self.timestamp.isoformat(),
        }


def create_alert(
    alert_type: AlertType,
    severity: AlertSeverity,
    title: str,
    description: str,
    data: dict | None = None,
    timestamp: datetime | None = None,
) -> Alert:
    """Factory helper to build an Alert instance."""
    return Alert(
        alert_type=alert_type,
        severity=severity,
        title=title,
        description=description,
        data=data,
        timestamp=timestamp,
    )


class AlertService:
    """Service for monitoring business metrics and generating alerts"""

    def __init__(self, db: Session):
        self.db = db
        self.analytics_service = AnalyticsService(db)

        # Alert thresholds - can be made configurable
        self.thresholds = {
            "low_stock_quantity": 10,
            "revenue_drop_percentage": 20,  # 20% drop triggers alert
            "high_pending_orders": 15,  # More than 15 pending orders
            "conversion_drop_percentage": 15,  # 15% drop in conversion
            "analysis_period_days": 7,  # Compare with last 7 days
            "high_churn_threshold": 15.0,  # 15% churn rate triggers alert
            "low_clv_threshold": 50.0,  # CLV below $50 triggers alert
            "mrr_decline_percentage": 10.0,  # 10% MRR decline triggers alert
            "aov_drop_percentage": 15.0,  # 15% AOV drop triggers alert
        }

    def check_all_alerts(self) -> list[Alert]:
        """Check all alert conditions and return triggered alerts"""
        alerts = []

        # Check inventory alerts
        alerts.extend(self.check_inventory_alerts())

        # Check revenue alerts
        alerts.extend(self.check_revenue_alerts())

        # Check order alerts
        alerts.extend(self.check_order_alerts())

        # Check conversion alerts
        alerts.extend(self.check_conversion_alerts())

        # Check customer health alerts
        alerts.extend(self.check_customer_health_alerts())

        # Check KPI alerts
        alerts.extend(self.check_kpi_alerts())

        return alerts

    def check_inventory_alerts(self) -> list[Alert]:
        """Check for inventory-related alerts"""
        alerts = []

        # Low stock products
        low_stock_query = (
            select(Product.name, Product.sku, Stock.quantity)
            .join(Stock)
            .where(
                Stock.quantity <= self.thresholds["low_stock_quantity"],
                Stock.quantity > 0,
                Product.status == "ACTIVE",
            )
        )
        low_stock_products = self.db.exec(low_stock_query).all()

        if low_stock_products:
            product_list = [
                f"{product.name} ({product.sku}): {product.quantity} units"
                for product in low_stock_products
            ]

            alerts.append(
                create_alert(
                    alert_type=AlertType.INVENTORY_LOW_STOCK,
                    severity=AlertSeverity.WARNING,
                    title=f"Low Stock Alert - {len(low_stock_products)} Products",
                    description=(
                        f"The following products are running low on stock: {', '.join(product_list[:3])}{'...' if len(product_list) > 3 else ''}"
                    ),
                    data={
                        "affected_products": len(low_stock_products),
                        "products": [
                            {"name": p.name, "sku": p.sku, "quantity": p.quantity}
                            for p in low_stock_products
                        ],
                        "threshold": self.thresholds["low_stock_quantity"],
                    },
                )
            )

        # Out of stock products
        out_of_stock_query = (
            select(Product.name, Product.sku)
            .join(Stock)
            .where(Stock.quantity == 0, Product.status == "ACTIVE")
        )
        out_of_stock_products = self.db.exec(out_of_stock_query).all()

        if out_of_stock_products:
            product_names = [f"{p.name} ({p.sku})" for p in out_of_stock_products]

            alerts.append(
                create_alert(
                    alert_type=AlertType.INVENTORY_OUT_OF_STOCK,
                    severity=AlertSeverity.CRITICAL,
                    title=f"Out of Stock Alert - {len(out_of_stock_products)} Products",
                    description=(
                        f"The following products are out of stock: {', '.join(product_names[:3])}{'...' if len(product_names) > 3 else ''}"
                    ),
                    data={
                        "affected_products": len(out_of_stock_products),
                        "products": [
                            {"name": p.name, "sku": p.sku}
                            for p in out_of_stock_products
                        ],
                    },
                )
            )

        return alerts

    def check_revenue_alerts(self) -> list[Alert]:
        """Check for revenue-related alerts"""
        alerts = []

        try:
            # Compare revenue with previous period
            period_days = self.thresholds["analysis_period_days"]
            end_date = datetime.utcnow()
            start_current = end_date - timedelta(days=period_days)
            start_previous = start_current - timedelta(days=period_days)
            end_previous = start_current

            current_revenue = self.analytics_service.get_total_revenue(
                start_current, end_date
            )
            previous_revenue = self.analytics_service.get_total_revenue(
                start_previous, end_previous
            )

            if previous_revenue > 0:
                change_percentage = float(
                    (current_revenue - previous_revenue) / previous_revenue * 100
                )

                if change_percentage <= -self.thresholds["revenue_drop_percentage"]:
                    alerts.append(
                        create_alert(
                            alert_type=AlertType.REVENUE_DROP,
                            severity=AlertSeverity.CRITICAL,
                            title=f"Revenue Drop Alert - {abs(change_percentage):.1f}% Decrease",
                            description=(
                                f"Revenue has dropped {abs(change_percentage):.1f}% compared to the previous {period_days} days. Current: ${current_revenue:,.2f}, Previous: ${previous_revenue:,.2f}"
                            ),
                            data={
                                "current_revenue": float(current_revenue),
                                "previous_revenue": float(previous_revenue),
                                "change_percentage": change_percentage,
                                "period_days": period_days,
                                "threshold_percentage": self.thresholds[
                                    "revenue_drop_percentage"
                                ],
                            },
                        )
                    )
        except Exception as e:
            # Log error but don't fail the entire alert check
            print(f"Error checking revenue alerts: {e}")

        return alerts

    def check_order_alerts(self) -> list[Alert]:
        """Check for order-related alerts"""
        alerts = []

        # High number of pending orders
        pending_orders_count = (
            self.db.exec(
                select(func.count(SalesOrder.so_id)).where(
                    SalesOrder.status == OrderStatus.PENDING
                )
            ).first()
            or 0
        )

        if pending_orders_count > self.thresholds["high_pending_orders"]:
            alerts.append(
                create_alert(
                    alert_type=AlertType.HIGH_PENDING_ORDERS,
                    severity=AlertSeverity.WARNING,
                    title=f"High Pending Orders - {pending_orders_count} Orders",
                    description=(
                        f"There are {pending_orders_count} pending orders that need attention. Consider reviewing fulfillment processes."
                    ),
                    data={
                        "pending_orders_count": pending_orders_count,
                        "threshold": self.thresholds["high_pending_orders"],
                    },
                )
            )

        return alerts

    def check_conversion_alerts(self) -> list[Alert]:
        """Check for conversion-related alerts"""
        alerts = []

        try:
            # Compare cart abandonment rates
            period_days = self.thresholds["analysis_period_days"]
            current_abandonment = self.analytics_service.get_cart_abandonment_rate(
                period_days
            )
            previous_abandonment = self.analytics_service.get_cart_abandonment_rate(
                period_days * 2
            )  # Previous period

            if previous_abandonment > 0:
                change = current_abandonment - previous_abandonment

                if change >= self.thresholds["conversion_drop_percentage"]:
                    alerts.append(
                        create_alert(
                            alert_type=AlertType.CONVERSION_DROP,
                            severity=AlertSeverity.WARNING,
                            title=f"Conversion Drop Alert - {change:.1f}% Increase in Abandonment",
                            description=(
                                f"Cart abandonment rate has increased by {change:.1f}% to {current_abandonment:.1f}%. Review checkout process for potential issues."
                            ),
                            data={
                                "current_abandonment_rate": current_abandonment,
                                "previous_abandonment_rate": previous_abandonment,
                                "change": change,
                                "threshold": self.thresholds[
                                    "conversion_drop_percentage"
                                ],
                            },
                        )
                    )
        except Exception as e:
            # Log error but don't fail the entire alert check
            print(f"Error checking conversion alerts: {e}")

        return alerts

    def get_alert_summary(self) -> dict:
        """Get a summary of current alerts by severity"""
        alerts = self.check_all_alerts()

        summary = {
            "total_alerts": len(alerts),
            "critical_alerts": len(
                [a for a in alerts if a.severity == AlertSeverity.CRITICAL]
            ),
            "warning_alerts": len(
                [a for a in alerts if a.severity == AlertSeverity.WARNING]
            ),
            "info_alerts": len([a for a in alerts if a.severity == AlertSeverity.INFO]),
            "last_checked": datetime.utcnow().isoformat(),
            "alerts": [alert.to_dict() for alert in alerts],
        }

        return summary

    def get_alerts_by_type(self, alert_type: AlertType) -> list[Alert]:
        """Get alerts filtered by type"""
        all_alerts = self.check_all_alerts()
        return [alert for alert in all_alerts if alert.alert_type == alert_type]

    def get_alerts_by_severity(self, severity: AlertSeverity) -> list[Alert]:
        """Get alerts filtered by severity"""
        all_alerts = self.check_all_alerts()
        return [alert for alert in all_alerts if alert.severity == severity]

    def check_customer_health_alerts(self) -> list[Alert]:
        """Check for customer health-related alerts"""
        alerts = []

        try:
            # Check churn rate
            churn_rate = self.analytics_service.calculate_churn_rate()
            if churn_rate > self.thresholds["high_churn_threshold"]:
                alerts.append(
                    create_alert(
                        alert_type=AlertType.HIGH_CHURN_RISK,
                        severity=AlertSeverity.WARNING,
                        title=f"High Churn Risk - {churn_rate:.1f}% Churn Rate",
                        description=(
                            f"Customer churn rate has reached {churn_rate:.1f}%, exceeding the threshold of {self.thresholds['high_churn_threshold']}%. Consider implementing retention strategies."
                        ),
                        data={
                            "churn_rate": churn_rate,
                            "threshold": self.thresholds["high_churn_threshold"],
                            "retention_rate": round(100 - churn_rate, 2),
                        },
                    )
                )

            # Check average CLV for recent customers
            recent_customers = self.db.exec(
                select(func.distinct(Transaction.customer_id)).where(
                    Transaction.created_at >= datetime.utcnow() - timedelta(days=30)
                )
            ).all()

            if recent_customers:
                low_clv_customers = []
                for customer_id in recent_customers[
                    :10
                ]:  # Check first 10 recent customers
                    clv = self.analytics_service.calculate_customer_lifetime_value(
                        customer_id
                    )
                    if clv < self.thresholds["low_clv_threshold"]:
                        low_clv_customers.append((customer_id, clv))

                if len(low_clv_customers) >= 5:  # If 5 or more have low CLV
                    avg_low_clv = sum(clv for _, clv in low_clv_customers) / len(
                        low_clv_customers
                    )
                    alerts.append(
                        create_alert(
                            alert_type=AlertType.LOW_CLV,
                            severity=AlertSeverity.INFO,
                            title=f"Low CLV Alert - {len(low_clv_customers)} Recent Customers",
                            description=(
                                f"Recent customers showing low CLV averaging ${avg_low_clv:.2f}. Consider improving onboarding and engagement strategies."
                            ),
                            data={
                                "low_clv_customers_count": len(low_clv_customers),
                                "average_low_clv": float(avg_low_clv),
                                "threshold": self.thresholds["low_clv_threshold"],
                            },
                        )
                    )
        except Exception as e:
            print(f"Error checking customer health alerts: {e}")

        return alerts

    def check_kpi_alerts(self) -> list[Alert]:
        """Check for KPI-related alerts"""
        alerts = []

        try:
            # Check MRR decline (compare current vs previous month)
            current_mrr = self.analytics_service.calculate_mrr()
            # For previous MRR, we'll approximate by looking at revenue 30-60 days ago
            start_previous = datetime.utcnow() - timedelta(days=60)
            end_previous = datetime.utcnow() - timedelta(days=30)

            previous_month_revenue = self.analytics_service.get_total_revenue(
                start_previous, end_previous
            )

            if previous_month_revenue > 0 and current_mrr > 0:
                mrr_change = float(
                    (current_mrr - previous_month_revenue)
                    / previous_month_revenue
                    * 100
                )

                if mrr_change <= -self.thresholds["mrr_decline_percentage"]:
                    alerts.append(
                        create_alert(
                            alert_type=AlertType.MRR_DECLINE,
                            severity=AlertSeverity.WARNING,
                            title=f"MRR Decline Alert - {abs(mrr_change):.1f}% Decrease",
                            description=(
                                f"Monthly Recurring Revenue has declined by {abs(mrr_change):.1f}%. Current MRR: ${current_mrr:,.2f}, Previous: ${previous_month_revenue:,.2f}"
                            ),
                            data={
                                "current_mrr": float(current_mrr),
                                "previous_mrr": float(previous_month_revenue),
                                "change_percentage": mrr_change,
                                "threshold": self.thresholds["mrr_decline_percentage"],
                            },
                        )
                    )

            # Check AOV decline
            current_aov = self.analytics_service.get_average_order_value()
            previous_aov = self.analytics_service.get_average_order_value(
                start_previous, end_previous
            )

            if previous_aov > 0 and current_aov > 0:
                aov_change = float((current_aov - previous_aov) / previous_aov * 100)

                if aov_change <= -self.thresholds["aov_drop_percentage"]:
                    alerts.append(
                        create_alert(
                            alert_type=AlertType.AOV_DROP,
                            severity=AlertSeverity.WARNING,
                            title=f"AOV Drop Alert - {abs(aov_change):.1f}% Decrease",
                            description=(
                                f"Average Order Value has dropped by {abs(aov_change):.1f}%. Current AOV: ${current_aov:.2f}, Previous: ${previous_aov:.2f}"
                            ),
                            data={
                                "current_aov": float(current_aov),
                                "previous_aov": float(previous_aov),
                                "change_percentage": aov_change,
                                "threshold": self.thresholds["aov_drop_percentage"],
                            },
                        )
                    )
        except Exception as e:
            print(f"Error checking KPI alerts: {e}")

        return alerts

    def update_thresholds(self, new_thresholds: dict) -> dict:
        """Update alert thresholds"""
        self.thresholds.update(new_thresholds)
        return self.thresholds
