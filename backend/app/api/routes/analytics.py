# backend/app/api/routes/analytics.py

from datetime import date, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session

from ...api.deps import get_current_active_superuser
from ...core.cache import CacheService
from ...core.db import get_db
from ...models import User
from ...services.alert_service import AlertService, AlertSeverity, AlertType
from ...services.analytics_service import AnalyticsService

router = APIRouter()


@router.get("/financial-summary", response_model=dict)
async def get_financial_summary(
    *,
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_active_superuser),
) -> dict:
    """
    Get comprehensive financial summary for executive dashboard.

    This endpoint provides real-time financial metrics including revenue,
    orders, customer analytics, and inventory status. Data is cached for
    optimal performance while maintaining accuracy for business decisions.

    Args:
        db (Session): Database session dependency
        current_user (User): Must be authenticated superuser

    Returns:
        Dict: Financial summary containing:
            - total_revenue: Current period revenue (Decimal)
            - total_orders: Number of completed orders (int)
            - avg_order_value: Average order value (Decimal)
            - customer_count: Total active customers (int)
            - inventory_value: Total inventory valuation (Decimal)
            - top_products: Best selling products (List[Dict])
            - revenue_trend: Period-over-period comparison (Dict)

    Raises:
        HTTPException: 403 if user lacks superuser privileges
        HTTPException: 500 if database or cache operation fails

    Security:
        - Requires superuser authentication
        - Admin-only endpoint (not exposed in public API mode)
        - Sensitive financial data requires proper authorization

    Caching:
        - Cached for 5 minutes to balance performance and accuracy
        - Cache key: "analytics:financial_summary"
        - Cache invalidated on significant financial events

    Performance:
        - Optimized queries with proper indexing
        - Aggregation performed at database level
        - Redis cache for frequently accessed metrics
    """
    cache_key = "analytics:financial_summary"

    # Try to get from cache first
    cached_data = await CacheService.get(cache_key)
    if cached_data:
        return cached_data

    # Generate fresh data
    analytics_service = AnalyticsService(db)
    data = analytics_service.get_financial_summary()

    # Cache for 5 minutes (300 seconds)
    await CacheService.set(cache_key, data, ttl=300)

    return data


@router.get("/realtime-metrics", response_model=dict)
async def get_realtime_metrics(
    *,
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_active_superuser),
) -> dict:
    """
    Get real-time metrics for dashboard monitoring.
    Requires admin privileges. Cached for 1 minute.
    """
    cache_key = "analytics:realtime_metrics"

    # Try to get from cache first
    cached_data = await CacheService.get(cache_key)
    if cached_data:
        return cached_data

    # Generate fresh data
    analytics_service = AnalyticsService(db)
    data = analytics_service.get_realtime_metrics()

    # Cache for 1 minute (60 seconds) - shorter TTL for real-time data
    await CacheService.set(cache_key, data, ttl=60)

    return data


@router.get("/revenue/total")
def get_total_revenue(
    *,
    db: Session = Depends(get_db),
    start_date: datetime | None = Query(
        None, description="Start date for revenue calculation"
    ),
    end_date: datetime | None = Query(
        None, description="End date for revenue calculation"
    ),
    _current_user: User = Depends(get_current_active_superuser),
) -> dict:
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
        "currency": "USD",
    }


@router.get("/revenue/daily/{target_date}")
def get_daily_revenue(
    *,
    target_date: date,
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_active_superuser),
) -> dict:
    """
    Get revenue for a specific day.
    Requires admin privileges.
    """
    analytics_service = AnalyticsService(db)
    daily_revenue = analytics_service.get_daily_revenue(target_date)

    return {
        "date": target_date.isoformat(),
        "revenue": float(daily_revenue),
        "currency": "USD",
    }


@router.get("/revenue/monthly/{year}/{month}")
def get_monthly_revenue(
    *,
    year: int,
    month: int,
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_active_superuser),
) -> dict:
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
        "currency": "USD",
    }


@router.get("/revenue/growth-rate")
def get_revenue_growth_rate(
    *,
    period_days: int = Query(
        30, description="Number of days for growth rate comparison"
    ),
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_active_superuser),
) -> dict:
    """
    Get revenue growth rate comparing two periods.
    Requires admin privileges.
    """
    analytics_service = AnalyticsService(db)
    growth_rate = analytics_service.get_revenue_growth_rate(period_days)

    return {
        "growth_rate_percentage": growth_rate,
        "period_days": period_days,
        "comparison_periods": f"Last {period_days} days vs previous {period_days} days",
    }


@router.get("/orders/metrics")
def get_order_metrics(
    *,
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_active_superuser),
) -> dict:
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
    start_date: datetime | None = Query(
        None, description="Start date for AOV calculation"
    ),
    end_date: datetime | None = Query(None, description="End date for AOV calculation"),
    _current_user: User = Depends(get_current_active_superuser),
) -> dict:
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
        "currency": "USD",
    }


@router.get("/customers/metrics")
def get_customer_metrics(
    *,
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_active_superuser),
) -> dict:
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
    _current_user: User = Depends(get_current_active_superuser),
) -> dict:
    """
    Get Customer Lifetime Value (CLV) for a specific customer.
    Requires admin privileges.
    """
    analytics_service = AnalyticsService(db)
    clv = analytics_service.calculate_customer_lifetime_value(customer_id)

    return {
        "customer_id": customer_id,
        "customer_lifetime_value": float(clv),
        "currency": "USD",
    }


@router.get("/products/top-selling")
def get_top_selling_products(
    *,
    limit: int = Query(
        10, description="Number of top products to return", ge=1, le=100
    ),
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_active_superuser),
) -> dict:
    """
    Get top selling products by quantity sold.
    Requires admin privileges.
    """
    analytics_service = AnalyticsService(db)
    top_products = analytics_service.get_top_selling_products(limit)

    return {
        "top_products": top_products,
        "limit": limit,
        "total_returned": len(top_products),
    }


@router.get("/inventory/metrics")
def get_inventory_metrics(
    *,
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_active_superuser),
) -> dict:
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
    _current_user: User = Depends(get_current_active_superuser),
) -> dict:
    """
    Get cart abandonment rate for a specified period.
    Requires admin privileges.
    """
    analytics_service = AnalyticsService(db)
    abandonment_rate = analytics_service.get_cart_abandonment_rate(days)

    return {
        "cart_abandonment_rate_percentage": abandonment_rate,
        "analysis_period_days": days,
        "completion_rate_percentage": round(100 - abandonment_rate, 2),
    }


@router.get("/revenue/mrr")
def get_monthly_recurring_revenue(
    *,
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_active_superuser),
) -> dict:
    """
    Get Monthly Recurring Revenue (MRR).
    Requires admin privileges.
    """
    analytics_service = AnalyticsService(db)
    mrr = analytics_service.calculate_mrr()

    return {
        "mrr": float(mrr),
        "currency": "USD",
        "calculation_date": datetime.utcnow().isoformat(),
    }


@router.get("/revenue/arr")
def get_annual_recurring_revenue(
    *,
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_active_superuser),
) -> dict:
    """
    Get Annual Recurring Revenue (ARR).
    Requires admin privileges.
    """
    analytics_service = AnalyticsService(db)
    arr = analytics_service.calculate_arr()

    return {
        "arr": float(arr),
        "currency": "USD",
        "calculation_date": datetime.utcnow().isoformat(),
    }


@router.get("/conversion/rate")
def get_conversion_rate(
    *,
    days: int = Query(30, description="Number of days to analyze", ge=1, le=365),
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_active_superuser),
) -> dict:
    """
    Get overall conversion rate for a specified period.
    Requires admin privileges.
    """
    analytics_service = AnalyticsService(db)
    conversion_rate = analytics_service.calculate_conversion_rate(days)

    return {
        "conversion_rate_percentage": conversion_rate,
        "analysis_period_days": days,
        "calculation_date": datetime.utcnow().isoformat(),
    }


@router.get("/customers/repeat-rate")
def get_repeat_customer_rate(
    *,
    days: int = Query(30, description="Number of days to analyze", ge=1, le=365),
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_active_superuser),
) -> dict:
    """
    Get repeat customer rate for a specified period.
    Requires admin privileges.
    """
    analytics_service = AnalyticsService(db)
    repeat_rate = analytics_service.calculate_repeat_customer_rate(days)

    return {
        "repeat_customer_rate_percentage": repeat_rate,
        "analysis_period_days": days,
        "calculation_date": datetime.utcnow().isoformat(),
    }


@router.get("/customers/churn-rate")
def get_churn_rate(
    *,
    period_days: int = Query(
        90, description="Period to analyze for churn", ge=30, le=365
    ),
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_active_superuser),
) -> dict:
    """
    Get customer churn rate for a specified period.
    Requires admin privileges.
    """
    analytics_service = AnalyticsService(db)
    churn_rate = analytics_service.calculate_churn_rate(period_days)

    return {
        "churn_rate_percentage": churn_rate,
        "retention_rate_percentage": round(100 - churn_rate, 2),
        "analysis_period_days": period_days,
        "calculation_date": datetime.utcnow().isoformat(),
    }


@router.get("/revenue/per-visitor")
def get_revenue_per_visitor(
    *,
    days: int = Query(30, description="Number of days to analyze", ge=1, le=365),
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_active_superuser),
) -> dict:
    """
    Get Revenue Per Visitor (RPV) for a specified period.
    Requires admin privileges.
    """
    analytics_service = AnalyticsService(db)
    rpv = analytics_service.calculate_revenue_per_visitor(days)

    return {
        "revenue_per_visitor": float(rpv),
        "currency": "USD",
        "analysis_period_days": days,
        "calculation_date": datetime.utcnow().isoformat(),
    }


# ─── ALERT ENDPOINTS ─────────────────────────────────────────────────────


@router.get("/alerts/summary")
async def get_alert_summary(
    *,
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_active_superuser),
) -> dict:
    """
    Get summary of all current alerts.
    Requires admin privileges. Cached for 2 minutes.
    """
    cache_key = "analytics:alerts_summary"

    # Try to get from cache first
    cached_data = await CacheService.get(cache_key)
    if cached_data:
        return cached_data

    # Generate fresh data
    alert_service = AlertService(db)
    data = alert_service.get_alert_summary()

    # Cache for 2 minutes (120 seconds)
    await CacheService.set(cache_key, data, ttl=120)

    return data


@router.get("/alerts/all")
def get_all_alerts(
    *,
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_active_superuser),
) -> dict:
    """
    Get all current alerts with full details.
    Requires admin privileges.
    """
    alert_service = AlertService(db)
    alerts = alert_service.check_all_alerts()

    return {
        "alerts": [alert.to_dict() for alert in alerts],
        "total_count": len(alerts),
        "timestamp": datetime.utcnow().isoformat(),
    }


@router.get("/alerts/by-severity/{severity}")
def get_alerts_by_severity(
    *,
    severity: AlertSeverity,
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_active_superuser),
) -> dict:
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
        "timestamp": datetime.utcnow().isoformat(),
    }


@router.get("/alerts/by-type/{alert_type}")
def get_alerts_by_type(
    *,
    alert_type: AlertType,
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_active_superuser),
) -> dict:
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
        "timestamp": datetime.utcnow().isoformat(),
    }


@router.get("/alerts/inventory")
def get_inventory_alerts(
    *,
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_active_superuser),
) -> dict:
    """
    Get inventory-specific alerts (low stock, out of stock).
    Requires admin privileges.
    """
    alert_service = AlertService(db)
    alerts = alert_service.check_inventory_alerts()

    return {
        "alerts": [alert.to_dict() for alert in alerts],
        "count": len(alerts),
        "timestamp": datetime.utcnow().isoformat(),
    }


@router.post("/alerts/thresholds")
def update_alert_thresholds(
    *,
    thresholds: dict,
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_active_superuser),
) -> dict:
    """
    Update alert thresholds configuration.
    Requires admin privileges.
    """
    alert_service = AlertService(db)
    updated_thresholds = alert_service.update_thresholds(thresholds)

    return {
        "message": "Alert thresholds updated successfully",
        "thresholds": updated_thresholds,
        "updated_at": datetime.utcnow().isoformat(),
    }


# ─── CACHE MANAGEMENT ENDPOINTS ──────────────────────────────────────────────


@router.delete("/cache/invalidate")
async def invalidate_analytics_cache(
    *,
    pattern: str = Query("analytics:*", description="Cache pattern to invalidate"),
    _current_user: User = Depends(get_current_active_superuser),
) -> dict:
    """
    Invalidate analytics cache by pattern.
    Requires admin privileges.
    """
    from ...core.cache import invalidate_cache_pattern

    deleted_count = await invalidate_cache_pattern(pattern)

    return {
        "message": "Cache invalidated successfully",
        "pattern": pattern,
        "deleted_keys": deleted_count,
        "timestamp": datetime.utcnow().isoformat(),
    }


@router.get("/cache/stats")
async def get_cache_stats(
    *, _current_user: User = Depends(get_current_active_superuser)
) -> dict:
    """
    Get cache statistics and performance metrics.
    Requires admin privileges.
    """
    from ...core.cache import get_cache_stats

    stats = await get_cache_stats()

    return {"cache_stats": stats, "timestamp": datetime.utcnow().isoformat()}


# ─── PHASE 2: ADVANCED ANALYTICS ENDPOINTS ───────────────────────────────────


@router.get("/segmentation/rfm")
async def get_rfm_segmentation(
    *,
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_active_superuser),
) -> dict:
    """
    Get RFM customer segmentation analysis.
    Requires admin privileges. Cached for 30 minutes.
    """
    from ...services.customer_segmentation_service import CustomerSegmentationService

    cache_key = "analytics:rfm_segmentation"
    cached_data = await CacheService.get(cache_key)
    if cached_data:
        return cached_data

    segmentation_service = CustomerSegmentationService(db)
    data = segmentation_service.get_segment_analysis()

    await CacheService.set(cache_key, data, ttl=1800)  # 30 minutes
    return data


@router.get("/segmentation/customers/{segment}")
def get_customers_by_segment(
    *,
    segment: str,
    limit: int = Query(100, description="Number of customers to return", ge=1, le=1000),
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_active_superuser),
) -> dict:
    """
    Get customers belonging to a specific RFM segment.
    Requires admin privileges.
    """
    from ...services.customer_segmentation_service import (
        CustomerSegmentationService,
        RFMSegment,
    )

    try:
        segment_enum = RFMSegment(segment)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid segment: {segment}")

    segmentation_service = CustomerSegmentationService(db)
    customers = segmentation_service.get_customers_by_segment(segment_enum, limit)
    recommendations = segmentation_service.get_segment_recommendations(segment_enum)

    return {
        "segment": segment,
        "customers": customers,
        "total_returned": len(customers),
        "recommendations": recommendations,
    }


@router.get("/cohorts/retention")
async def get_cohort_retention_analysis(
    *,
    months_back: int = Query(
        12, description="Number of months to analyze", ge=3, le=24
    ),
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_active_superuser),
) -> dict:
    """
    Get cohort retention analysis.
    Requires admin privileges. Cached for 60 minutes.
    """
    from ...services.cohort_analysis_service import CohortAnalysisService

    cache_key = f"analytics:cohort_retention:{months_back}"
    cached_data = await CacheService.get(cache_key)
    if cached_data:
        return cached_data

    cohort_service = CohortAnalysisService(db)
    data = cohort_service.calculate_retention_cohorts(months_back=months_back)

    await CacheService.set(cache_key, data, ttl=3600)  # 60 minutes
    return data


@router.get("/cohorts/revenue")
async def get_cohort_revenue_analysis(
    *,
    months_back: int = Query(
        12, description="Number of months to analyze", ge=3, le=24
    ),
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_active_superuser),
) -> dict:
    """
    Get cohort revenue analysis.
    Requires admin privileges. Cached for 60 minutes.
    """
    from ...services.cohort_analysis_service import CohortAnalysisService

    cache_key = f"analytics:cohort_revenue:{months_back}"
    cached_data = await CacheService.get(cache_key)
    if cached_data:
        return cached_data

    cohort_service = CohortAnalysisService(db)
    data = cohort_service.calculate_revenue_cohorts(months_back=months_back)

    await CacheService.set(cache_key, data, ttl=3600)  # 60 minutes
    return data


@router.get("/cohorts/product-adoption")
def get_product_adoption_cohorts(
    *,
    product_category: str | None = Query(
        None, description="Filter by product category"
    ),
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_active_superuser),
) -> dict:
    """
    Get product adoption cohort analysis.
    Requires admin privileges.
    """
    from ...services.cohort_analysis_service import CohortAnalysisService

    cohort_service = CohortAnalysisService(db)
    data = cohort_service.calculate_product_adoption_cohorts(product_category)

    return data


@router.get("/funnel/conversion")
async def get_conversion_funnel(
    *,
    days: int = Query(30, description="Number of days to analyze", ge=1, le=90),
    channel: str | None = Query(None, description="Marketing channel filter"),
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_active_superuser),
) -> dict:
    """
    Get detailed conversion funnel analysis.
    Requires admin privileges. Cached for 20 minutes.
    """
    from ...services.conversion_funnel_service import ConversionFunnelService

    cache_key = f"analytics:conversion_funnel:{days}:{channel or 'all'}"
    cached_data = await CacheService.get(cache_key)
    if cached_data:
        return cached_data

    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)

    funnel_service = ConversionFunnelService(db)
    data = funnel_service.calculate_conversion_funnel(start_date, end_date, channel)

    await CacheService.set(cache_key, data, ttl=1200)  # 20 minutes
    return data


@router.get("/funnel/product/{product_id}")
def get_product_conversion_funnel(
    *,
    product_id: int,
    days: int = Query(30, description="Number of days to analyze", ge=1, le=90),
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_active_superuser),
) -> dict:
    """
    Get conversion funnel for a specific product.
    Requires admin privileges.
    """
    from ...services.conversion_funnel_service import ConversionFunnelService

    funnel_service = ConversionFunnelService(db)
    data = funnel_service.calculate_product_funnel(product_id, days)

    if not data:
        raise HTTPException(status_code=404, detail="Product not found")

    return data


@router.get("/funnel/channels")
async def get_channel_conversion_funnels(
    *,
    days: int = Query(30, description="Number of days to analyze", ge=1, le=90),
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_active_superuser),
) -> dict:
    """
    Get conversion funnels by marketing channel.
    Requires admin privileges. Cached for 30 minutes.
    """
    from ...services.conversion_funnel_service import ConversionFunnelService

    cache_key = f"analytics:channel_funnels:{days}"
    cached_data = await CacheService.get(cache_key)
    if cached_data:
        return cached_data

    funnel_service = ConversionFunnelService(db)
    data = funnel_service.calculate_channel_funnels(days)

    await CacheService.set(cache_key, data, ttl=1800)  # 30 minutes
    return data


@router.get("/funnel/devices")
async def get_device_conversion_comparison(
    *,
    days: int = Query(30, description="Number of days to analyze", ge=1, le=90),
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_active_superuser),
) -> dict:
    """
    Get mobile vs desktop conversion funnel comparison.
    Requires admin privileges. Cached for 30 minutes.
    """
    from ...services.conversion_funnel_service import ConversionFunnelService

    cache_key = f"analytics:device_funnels:{days}"
    cached_data = await CacheService.get(cache_key)
    if cached_data:
        return cached_data

    funnel_service = ConversionFunnelService(db)
    data = funnel_service.calculate_mobile_vs_desktop_funnel(days)

    await CacheService.set(cache_key, data, ttl=1800)  # 30 minutes
    return data


@router.get("/reports/executive")
async def get_executive_report(
    *,
    period: str = Query(
        "monthly", description="Report period: daily, weekly, monthly, quarterly"
    ),
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_active_superuser),
) -> dict:
    """
    Generate comprehensive executive report.
    Requires admin privileges. Cached for 60 minutes.
    """
    from ...services.report_service import ReportGenerationService, ReportPeriod

    try:
        period_enum = ReportPeriod(period)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid period: {period}")

    cache_key = f"analytics:executive_report:{period}"
    cached_data = await CacheService.get(cache_key)
    if cached_data:
        return cached_data

    report_service = ReportGenerationService(db)
    data = report_service.generate_executive_report(period_enum)

    await CacheService.set(cache_key, data, ttl=3600)  # 60 minutes
    return data


@router.get("/reports/operational")
async def get_operational_report(
    *,
    days: int = Query(7, description="Number of days to analyze", ge=1, le=30),
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_active_superuser),
) -> dict:
    """
    Generate detailed operational report.
    Requires admin privileges. Cached for 30 minutes.
    """
    from ...services.report_service import ReportGenerationService

    cache_key = f"analytics:operational_report:{days}"
    cached_data = await CacheService.get(cache_key)
    if cached_data:
        return cached_data

    report_service = ReportGenerationService(db)
    data = report_service.generate_operational_report(days)

    await CacheService.set(cache_key, data, ttl=1800)  # 30 minutes
    return data


@router.get("/reports/customer")
async def get_customer_analytics_report(
    *,
    months_back: int = Query(6, description="Number of months to analyze", ge=3, le=12),
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_active_superuser),
) -> dict:
    """
    Generate comprehensive customer analytics report.
    Requires admin privileges. Cached for 60 minutes.
    """
    from ...services.report_service import ReportGenerationService

    cache_key = f"analytics:customer_report:{months_back}"
    cached_data = await CacheService.get(cache_key)
    if cached_data:
        return cached_data

    report_service = ReportGenerationService(db)
    data = report_service.generate_customer_analytics_report(months_back)

    await CacheService.set(cache_key, data, ttl=3600)  # 60 minutes
    return data


@router.get("/reports/scheduled")
def get_scheduled_reports(
    *,
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_active_superuser),
) -> dict:
    """
    Get configuration for automated report schedules.
    Requires admin privileges.
    """
    from ...services.report_service import ReportGenerationService

    report_service = ReportGenerationService(db)
    data = report_service.schedule_automated_reports()

    return data


# ─── DATE RANGE ANALYTICS ─────────────────────────────────────────────────────


@router.get("/metrics/date-range")
async def get_metrics_by_date_range(
    *,
    start_date: datetime = Query(..., description="Start date for analysis"),
    end_date: datetime = Query(..., description="End date for analysis"),
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_active_superuser),
) -> dict:
    """
    Get comprehensive metrics for a specific date range.
    Requires admin privileges. Cached for 10 minutes.
    """
    # Create cache key based on date range
    cache_key = f"analytics:date_range:{start_date.date()}:{end_date.date()}"

    # Try to get from cache first
    cached_data = await CacheService.get(cache_key)
    if cached_data:
        return cached_data

    analytics_service = AnalyticsService(db)

    # Calculate metrics for the date range
    data = {
        "date_range": {
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "days": (end_date - start_date).days + 1,
        },
        "revenue": {
            "total": float(analytics_service.get_total_revenue(start_date, end_date)),
            "average_daily": float(
                analytics_service.get_total_revenue(start_date, end_date)
            )
            / ((end_date - start_date).days + 1),
        },
        "orders": {
            "average_order_value": float(
                analytics_service.get_average_order_value(start_date, end_date)
            )
        },
        "conversion": {
            "cart_abandonment_rate": analytics_service.get_cart_abandonment_rate(
                (end_date - start_date).days
            ),
            "conversion_rate": analytics_service.calculate_conversion_rate(
                (end_date - start_date).days
            ),
            "repeat_customer_rate": analytics_service.calculate_repeat_customer_rate(
                (end_date - start_date).days
            ),
        },
        "calculated_at": datetime.utcnow().isoformat(),
    }

    # Cache for 10 minutes (600 seconds) - longer TTL for historical data
    await CacheService.set(cache_key, data, ttl=600)

    return data


@router.get("/trends/revenue")
async def get_revenue_trends(
    *,
    days: int = Query(
        30, description="Number of days for trend analysis", ge=7, le=365
    ),
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_active_superuser),
) -> dict:
    """
    Get revenue trends over time.
    Requires admin privileges. Cached for 15 minutes.
    """
    cache_key = f"analytics:revenue_trends:{days}"

    # Try to get from cache first
    cached_data = await CacheService.get(cache_key)
    if cached_data:
        return cached_data

    analytics_service = AnalyticsService(db)

    # Generate daily revenue data for the trend
    end_date = datetime.utcnow().date()
    trends = []

    for i in range(days):
        target_date = end_date - timedelta(days=i)
        daily_revenue = analytics_service.get_daily_revenue(target_date)
        trends.append(
            {
                "date": target_date.isoformat(),
                "revenue": float(daily_revenue),
                "day_of_week": target_date.strftime("%A"),
            }
        )

    # Calculate trend statistics
    revenues = [t["revenue"] for t in trends]
    avg_revenue = sum(revenues) / len(revenues) if revenues else 0
    max_revenue = max(revenues) if revenues else 0
    min_revenue = min(revenues) if revenues else 0

    # Calculate growth rate (comparing first half vs second half)
    mid_point = len(revenues) // 2
    if mid_point > 0:
        first_half_avg = sum(revenues[:mid_point]) / mid_point
        second_half_avg = sum(revenues[mid_point:]) / (len(revenues) - mid_point)
        growth_rate = (
            ((second_half_avg - first_half_avg) / first_half_avg * 100)
            if first_half_avg > 0
            else 0
        )
    else:
        growth_rate = 0

    data = {
        "period": {
            "days": days,
            "start_date": (end_date - timedelta(days=days - 1)).isoformat(),
            "end_date": end_date.isoformat(),
        },
        "trends": trends[::-1],  # Reverse to show chronological order
        "statistics": {
            "average_daily_revenue": round(avg_revenue, 2),
            "highest_day_revenue": round(max_revenue, 2),
            "lowest_day_revenue": round(min_revenue, 2),
            "growth_rate_percentage": round(growth_rate, 2),
            "total_revenue": round(sum(revenues), 2),
        },
        "calculated_at": datetime.utcnow().isoformat(),
    }

    # Cache for 15 minutes (900 seconds)
    await CacheService.set(cache_key, data, ttl=900)

    return data
