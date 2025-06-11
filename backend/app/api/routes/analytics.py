# backend/app/api/routes/analytics.py

from datetime import datetime, date
from typing import Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session

from ...core.db import get_db
from ...services.analytics_service import AnalyticsService
from ...services.alert_service import AlertService, AlertType, AlertSeverity
from ...api.deps import get_current_active_superuser
from ...models import User

router = APIRouter()


@router.get("/financial-summary", response_model=Dict)
def get_financial_summary(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_superuser)
) -> Dict:
    """
    Get comprehensive financial summary including revenue, orders, customers, and inventory metrics.
    Requires admin privileges.
    """
    analytics_service = AnalyticsService(db)
    return analytics_service.get_financial_summary()


@router.get("/realtime-metrics", response_model=Dict)
def get_realtime_metrics(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_superuser)
) -> Dict:
    """
    Get real-time metrics for dashboard monitoring.
    Requires admin privileges.
    """
    analytics_service = AnalyticsService(db)
    return analytics_service.get_realtime_metrics()


@router.get("/revenue/total")
def get_total_revenue(
    *,
    db: Session = Depends(get_db),
    start_date: Optional[datetime] = Query(None, description="Start date for revenue calculation"),
    end_date: Optional[datetime] = Query(None, description="End date for revenue calculation"),
    current_user: User = Depends(get_current_active_superuser)
) -> Dict:
    """
    Get total revenue for a specified period.
    Requires admin privileges.
    """
    analytics_service = AnalyticsService(db)
    total_revenue = analytics_service.get_total_revenue(start_date, end_date)
    
    return {
        "total_revenue": float(total_revenue),
        "start_date": start_date.isoformat() if start_date else None,
        "end_date": end_date.isoformat() if end_date else None,
        "currency": "USD"
    }


@router.get("/revenue/daily/{target_date}")
def get_daily_revenue(
    *,
    target_date: date,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_superuser)
) -> Dict:
    """
    Get revenue for a specific day.
    Requires admin privileges.
    """
    analytics_service = AnalyticsService(db)
    daily_revenue = analytics_service.get_daily_revenue(target_date)
    
    return {
        "date": target_date.isoformat(),
        "revenue": float(daily_revenue),
        "currency": "USD"
    }


@router.get("/revenue/monthly/{year}/{month}")
def get_monthly_revenue(
    *,
    year: int,
    month: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_superuser)
) -> Dict:
    """
    Get revenue for a specific month.
    Requires admin privileges.
    """
    if month < 1 or month > 12:
        raise HTTPException(status_code=400, detail="Month must be between 1 and 12")
    
    analytics_service = AnalyticsService(db)
    monthly_revenue = analytics_service.get_monthly_revenue(year, month)
    
    return {
        "year": year,
        "month": month,
        "revenue": float(monthly_revenue),
        "currency": "USD"
    }


@router.get("/revenue/growth-rate")
def get_revenue_growth_rate(
    *,
    period_days: int = Query(30, description="Number of days for growth rate comparison"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_superuser)
) -> Dict:
    """
    Get revenue growth rate comparing two periods.
    Requires admin privileges.
    """
    analytics_service = AnalyticsService(db)
    growth_rate = analytics_service.get_revenue_growth_rate(period_days)
    
    return {
        "growth_rate_percentage": growth_rate,
        "period_days": period_days,
        "comparison_periods": f"Last {period_days} days vs previous {period_days} days"
    }


@router.get("/orders/metrics")
def get_order_metrics(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_superuser)
) -> Dict:
    """
    Get comprehensive order metrics including AOV and order counts.
    Requires admin privileges.
    """
    analytics_service = AnalyticsService(db)
    return analytics_service.get_order_metrics()


@router.get("/orders/average-order-value")
def get_average_order_value(
    *,
    db: Session = Depends(get_db),
    start_date: Optional[datetime] = Query(None, description="Start date for AOV calculation"),
    end_date: Optional[datetime] = Query(None, description="End date for AOV calculation"),
    current_user: User = Depends(get_current_active_superuser)
) -> Dict:
    """
    Get Average Order Value (AOV) for a specified period.
    Requires admin privileges.
    """
    analytics_service = AnalyticsService(db)
    aov = analytics_service.get_average_order_value(start_date, end_date)
    
    return {
        "average_order_value": float(aov),
        "start_date": start_date.isoformat() if start_date else None,
        "end_date": end_date.isoformat() if end_date else None,
        "currency": "USD"
    }


@router.get("/customers/metrics")
def get_customer_metrics(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_superuser)
) -> Dict:
    """
    Get comprehensive customer metrics including conversion rates and activity.
    Requires admin privileges.
    """
    analytics_service = AnalyticsService(db)
    return analytics_service.get_customer_metrics()


@router.get("/customers/{customer_id}/lifetime-value")
def get_customer_lifetime_value(
    *,
    customer_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_superuser)
) -> Dict:
    """
    Get Customer Lifetime Value (CLV) for a specific customer.
    Requires admin privileges.
    """
    analytics_service = AnalyticsService(db)
    clv = analytics_service.calculate_customer_lifetime_value(customer_id)
    
    return {
        "customer_id": customer_id,
        "customer_lifetime_value": float(clv),
        "currency": "USD"
    }


@router.get("/products/top-selling")
def get_top_selling_products(
    *,
    limit: int = Query(10, description="Number of top products to return", ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_superuser)
) -> Dict:
    """
    Get top selling products by quantity sold.
    Requires admin privileges.
    """
    analytics_service = AnalyticsService(db)
    top_products = analytics_service.get_top_selling_products(limit)
    
    return {
        "top_products": top_products,
        "limit": limit,
        "total_returned": len(top_products)
    }


@router.get("/inventory/metrics")
def get_inventory_metrics(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_superuser)
) -> Dict:
    """
    Get inventory-related metrics including stock levels and values.
    Requires admin privileges.
    """
    analytics_service = AnalyticsService(db)
    return analytics_service.get_inventory_metrics()


@router.get("/conversion/cart-abandonment-rate")
def get_cart_abandonment_rate(
    *,
    days: int = Query(30, description="Number of days to analyze", ge=1, le=365),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_superuser)
) -> Dict:
    """
    Get cart abandonment rate for a specified period.
    Requires admin privileges.
    """
    analytics_service = AnalyticsService(db)
    abandonment_rate = analytics_service.get_cart_abandonment_rate(days)
    
    return {
        "cart_abandonment_rate_percentage": abandonment_rate,
        "analysis_period_days": days,
        "completion_rate_percentage": round(100 - abandonment_rate, 2)
    }


# ─── ALERT ENDPOINTS ─────────────────────────────────────────────────────

@router.get("/alerts/summary")
def get_alert_summary(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_superuser)
) -> Dict:
    """
    Get summary of all current alerts.
    Requires admin privileges.
    """
    alert_service = AlertService(db)
    return alert_service.get_alert_summary()


@router.get("/alerts/all")
def get_all_alerts(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_superuser)
) -> Dict:
    """
    Get all current alerts with full details.
    Requires admin privileges.
    """
    alert_service = AlertService(db)
    alerts = alert_service.check_all_alerts()
    
    return {
        "alerts": [alert.to_dict() for alert in alerts],
        "total_count": len(alerts),
        "timestamp": datetime.utcnow().isoformat()
    }


@router.get("/alerts/by-severity/{severity}")
def get_alerts_by_severity(
    *,
    severity: AlertSeverity,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_superuser)
) -> Dict:
    """
    Get alerts filtered by severity level.
    Requires admin privileges.
    """
    alert_service = AlertService(db)
    alerts = alert_service.get_alerts_by_severity(severity)
    
    return {
        "alerts": [alert.to_dict() for alert in alerts],
        "severity": severity.value,
        "count": len(alerts),
        "timestamp": datetime.utcnow().isoformat()
    }


@router.get("/alerts/by-type/{alert_type}")
def get_alerts_by_type(
    *,
    alert_type: AlertType,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_superuser)
) -> Dict:
    """
    Get alerts filtered by type.
    Requires admin privileges.
    """
    alert_service = AlertService(db)
    alerts = alert_service.get_alerts_by_type(alert_type)
    
    return {
        "alerts": [alert.to_dict() for alert in alerts],
        "alert_type": alert_type.value,
        "count": len(alerts),
        "timestamp": datetime.utcnow().isoformat()
    }


@router.get("/alerts/inventory")
def get_inventory_alerts(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_superuser)
) -> Dict:
    """
    Get inventory-specific alerts (low stock, out of stock).
    Requires admin privileges.
    """
    alert_service = AlertService(db)
    alerts = alert_service.check_inventory_alerts()
    
    return {
        "alerts": [alert.to_dict() for alert in alerts],
        "count": len(alerts),
        "timestamp": datetime.utcnow().isoformat()
    }


@router.post("/alerts/thresholds")
def update_alert_thresholds(
    *,
    thresholds: Dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_superuser)
) -> Dict:
    """
    Update alert thresholds configuration.
    Requires admin privileges.
    """
    alert_service = AlertService(db)
    updated_thresholds = alert_service.update_thresholds(thresholds)
    
    return {
        "message": "Alert thresholds updated successfully",
        "thresholds": updated_thresholds,
        "updated_at": datetime.utcnow().isoformat()
    }