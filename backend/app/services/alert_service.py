# backend/app/services/alert_service.py

from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Optional, Literal
from sqlmodel import Session, select, func
from enum import Enum

from ..models import Stock, Product, SalesOrder, OrderStatus, Transaction, TransactionType
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


class Alert:
    def __init__(
        self,
        alert_type: AlertType,
        severity: AlertSeverity,
        title: str,
        description: str,
        data: Optional[Dict] = None,
        timestamp: Optional[datetime] = None
    ):
        self.alert_type = alert_type
        self.severity = severity
        self.title = title
        self.description = description
        self.data = data or {}
        self.timestamp = timestamp or datetime.utcnow()
        self.id = f"{alert_type.value}_{int(self.timestamp.timestamp())}"
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "type": self.alert_type.value,
            "severity": self.severity.value,
            "title": self.title,
            "description": self.description,
            "data": self.data,
            "timestamp": self.timestamp.isoformat(),
            "created_at": self.timestamp.isoformat()
        }


class AlertService:
    """Service for monitoring business metrics and generating alerts"""
    
    def __init__(self, db: Session):
        self.db = db
        self.analytics_service = AnalyticsService(db)
        
        # Alert thresholds - can be made configurable
        self.thresholds = {
            "low_stock_quantity": 10,
            "revenue_drop_percentage": 20,  # 20% drop triggers alert
            "high_pending_orders": 15,      # More than 15 pending orders
            "conversion_drop_percentage": 15,  # 15% drop in conversion
            "analysis_period_days": 7       # Compare with last 7 days
        }
    
    def check_all_alerts(self) -> List[Alert]:
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
        
        return alerts
    
    def check_inventory_alerts(self) -> List[Alert]:
        """Check for inventory-related alerts"""
        alerts = []
        
        # Low stock products
        low_stock_query = (
            select(Product.name, Product.sku, Stock.quantity)
            .join(Stock)
            .where(
                Stock.quantity <= self.thresholds["low_stock_quantity"],
                Stock.quantity > 0,
                Product.status == "ACTIVE"
            )
        )
        low_stock_products = self.db.exec(low_stock_query).all()
        
        if low_stock_products:
            product_list = [
                f"{product.name} ({product.sku}): {product.quantity} units"
                for product in low_stock_products
            ]
            
            alerts.append(Alert(
                alert_type=AlertType.INVENTORY_LOW_STOCK,
                severity=AlertSeverity.WARNING,
                title=f"Low Stock Alert - {len(low_stock_products)} Products",
                description=f"The following products are running low on stock: {', '.join(product_list[:3])}{'...' if len(product_list) > 3 else ''}",
                data={
                    "affected_products": len(low_stock_products),
                    "products": [
                        {
                            "name": p.name,
                            "sku": p.sku,
                            "quantity": p.quantity
                        } for p in low_stock_products
                    ],
                    "threshold": self.thresholds["low_stock_quantity"]
                }
            ))
        
        # Out of stock products
        out_of_stock_query = (
            select(Product.name, Product.sku)
            .join(Stock)
            .where(
                Stock.quantity == 0,
                Product.status == "ACTIVE"
            )
        )
        out_of_stock_products = self.db.exec(out_of_stock_query).all()
        
        if out_of_stock_products:
            product_names = [f"{p.name} ({p.sku})" for p in out_of_stock_products]
            
            alerts.append(Alert(
                alert_type=AlertType.INVENTORY_OUT_OF_STOCK,
                severity=AlertSeverity.CRITICAL,
                title=f"Out of Stock Alert - {len(out_of_stock_products)} Products",
                description=f"The following products are out of stock: {', '.join(product_names[:3])}{'...' if len(product_names) > 3 else ''}",
                data={
                    "affected_products": len(out_of_stock_products),
                    "products": [
                        {
                            "name": p.name,
                            "sku": p.sku
                        } for p in out_of_stock_products
                    ]
                }
            ))
        
        return alerts
    
    def check_revenue_alerts(self) -> List[Alert]:
        """Check for revenue-related alerts"""
        alerts = []
        
        try:
            # Compare revenue with previous period
            period_days = self.thresholds["analysis_period_days"]
            end_date = datetime.utcnow()
            start_current = end_date - timedelta(days=period_days)
            start_previous = start_current - timedelta(days=period_days)
            end_previous = start_current
            
            current_revenue = self.analytics_service.get_total_revenue(start_current, end_date)
            previous_revenue = self.analytics_service.get_total_revenue(start_previous, end_previous)
            
            if previous_revenue > 0:
                change_percentage = float((current_revenue - previous_revenue) / previous_revenue * 100)
                
                if change_percentage <= -self.thresholds["revenue_drop_percentage"]:
                    alerts.append(Alert(
                        alert_type=AlertType.REVENUE_DROP,
                        severity=AlertSeverity.CRITICAL,
                        title=f"Revenue Drop Alert - {abs(change_percentage):.1f}% Decrease",
                        description=f"Revenue has dropped {abs(change_percentage):.1f}% compared to the previous {period_days} days. Current: ${current_revenue:,.2f}, Previous: ${previous_revenue:,.2f}",
                        data={
                            "current_revenue": float(current_revenue),
                            "previous_revenue": float(previous_revenue),
                            "change_percentage": change_percentage,
                            "period_days": period_days,
                            "threshold_percentage": self.thresholds["revenue_drop_percentage"]
                        }
                    ))
        except Exception as e:
            # Log error but don't fail the entire alert check
            print(f"Error checking revenue alerts: {e}")
        
        return alerts
    
    def check_order_alerts(self) -> List[Alert]:
        """Check for order-related alerts"""
        alerts = []
        
        # High number of pending orders
        pending_orders_count = self.db.exec(
            select(func.count(SalesOrder.so_id)).where(
                SalesOrder.status == OrderStatus.PENDING
            )
        ).first() or 0
        
        if pending_orders_count > self.thresholds["high_pending_orders"]:
            alerts.append(Alert(
                alert_type=AlertType.HIGH_PENDING_ORDERS,
                severity=AlertSeverity.WARNING,
                title=f"High Pending Orders - {pending_orders_count} Orders",
                description=f"There are {pending_orders_count} pending orders that need attention. Consider reviewing fulfillment processes.",
                data={
                    "pending_orders_count": pending_orders_count,
                    "threshold": self.thresholds["high_pending_orders"]
                }
            ))
        
        return alerts
    
    def check_conversion_alerts(self) -> List[Alert]:
        """Check for conversion-related alerts"""
        alerts = []
        
        try:
            # Compare cart abandonment rates
            period_days = self.thresholds["analysis_period_days"]
            current_abandonment = self.analytics_service.get_cart_abandonment_rate(period_days)
            previous_abandonment = self.analytics_service.get_cart_abandonment_rate(period_days * 2)  # Previous period
            
            if previous_abandonment > 0:
                change = current_abandonment - previous_abandonment
                
                if change >= self.thresholds["conversion_drop_percentage"]:
                    alerts.append(Alert(
                        alert_type=AlertType.CONVERSION_DROP,
                        severity=AlertSeverity.WARNING,
                        title=f"Conversion Drop Alert - {change:.1f}% Increase in Abandonment",
                        description=f"Cart abandonment rate has increased by {change:.1f}% to {current_abandonment:.1f}%. Review checkout process for potential issues.",
                        data={
                            "current_abandonment_rate": current_abandonment,
                            "previous_abandonment_rate": previous_abandonment,
                            "change": change,
                            "threshold": self.thresholds["conversion_drop_percentage"]
                        }
                    ))
        except Exception as e:
            # Log error but don't fail the entire alert check
            print(f"Error checking conversion alerts: {e}")
        
        return alerts
    
    def get_alert_summary(self) -> Dict:
        """Get a summary of current alerts by severity"""
        alerts = self.check_all_alerts()
        
        summary = {
            "total_alerts": len(alerts),
            "critical_alerts": len([a for a in alerts if a.severity == AlertSeverity.CRITICAL]),
            "warning_alerts": len([a for a in alerts if a.severity == AlertSeverity.WARNING]),
            "info_alerts": len([a for a in alerts if a.severity == AlertSeverity.INFO]),
            "last_checked": datetime.utcnow().isoformat(),
            "alerts": [alert.to_dict() for alert in alerts]
        }
        
        return summary
    
    def get_alerts_by_type(self, alert_type: AlertType) -> List[Alert]:
        """Get alerts filtered by type"""
        all_alerts = self.check_all_alerts()
        return [alert for alert in all_alerts if alert.alert_type == alert_type]
    
    def get_alerts_by_severity(self, severity: AlertSeverity) -> List[Alert]:
        """Get alerts filtered by severity"""
        all_alerts = self.check_all_alerts()
        return [alert for alert in all_alerts if alert.severity == severity]
    
    def update_thresholds(self, new_thresholds: Dict) -> Dict:
        """Update alert thresholds"""
        self.thresholds.update(new_thresholds)
        return self.thresholds