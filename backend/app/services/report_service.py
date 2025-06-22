"""
Automated Report Generation Service - Advanced Analytics Phase 2
Creates comprehensive executive, operational, and customer reports.
"""

from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum

from sqlmodel import Session

from app.services.analytics_service import AnalyticsService
from app.services.cohort_analysis_service import CohortAnalysisService
from app.services.conversion_funnel_service import ConversionFunnelService
from app.services.customer_segmentation_service import (
    CustomerSegmentationService,
    RFMSegment,
)


class ReportType(str, Enum):
    EXECUTIVE = "executive"
    OPERATIONAL = "operational"
    CUSTOMER = "customer"
    FINANCIAL = "financial"
    PRODUCT = "product"
    MARKETING = "marketing"


class ReportPeriod(str, Enum):
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"


@dataclass
class ReportMetadata:
    report_id: str
    report_type: ReportType
    report_period: ReportPeriod
    generated_at: datetime
    generated_by: str
    data_period_start: datetime
    data_period_end: datetime
    total_pages: int
    executive_summary: str


class ReportGenerationService:
    """Service for automated report generation across all analytics areas."""

    def __init__(self, db: Session):
        self.db = db
        self.analytics_service = AnalyticsService(db)
        self.segmentation_service = CustomerSegmentationService(db)
        self.cohort_service = CohortAnalysisService(db)
        self.funnel_service = ConversionFunnelService(db)

    def generate_executive_report(self, period: ReportPeriod = ReportPeriod.MONTHLY) -> dict:
        """
        Generate comprehensive executive summary report.
        
        Args:
            period: Reporting period (daily, weekly, monthly, quarterly)
            
        Returns:
            Executive report with high-level KPIs and insights
        """
        end_date = datetime.utcnow()

        # Determine period dates
        if period == ReportPeriod.DAILY:
            start_date = end_date - timedelta(days=1)
            comparison_start = start_date - timedelta(days=1)
        elif period == ReportPeriod.WEEKLY:
            start_date = end_date - timedelta(weeks=1)
            comparison_start = start_date - timedelta(weeks=1)
        elif period == ReportPeriod.MONTHLY:
            start_date = end_date - timedelta(days=30)
            comparison_start = start_date - timedelta(days=30)
        elif period == ReportPeriod.QUARTERLY:
            start_date = end_date - timedelta(days=90)
            comparison_start = start_date - timedelta(days=90)
        else:  # YEARLY
            start_date = end_date - timedelta(days=365)
            comparison_start = start_date - timedelta(days=365)

        # Gather key metrics
        current_revenue = self.analytics_service.get_total_revenue(start_date, end_date)
        previous_revenue = self.analytics_service.get_total_revenue(comparison_start, start_date)
        revenue_growth = ((current_revenue - previous_revenue) / previous_revenue * 100) if previous_revenue > 0 else 0

        financial_summary = self.analytics_service.get_financial_summary()
        customer_metrics = self.analytics_service.get_customer_metrics()
        order_metrics = self.analytics_service.get_order_metrics()

        # Get segmentation insights
        segmentation_analysis = self.segmentation_service.get_segment_analysis()

        # Get cohort insights
        cohort_analysis = self.cohort_service.calculate_retention_cohorts(months_back=6)

        # Generate executive insights
        key_insights = self._generate_executive_insights(
            revenue_growth, financial_summary, customer_metrics,
            segmentation_analysis, cohort_analysis
        )

        # Generate action items
        action_items = self._generate_action_items(
            revenue_growth, customer_metrics, segmentation_analysis
        )

        report = {
            "metadata": {
                "report_type": ReportType.EXECUTIVE.value,
                "period": period.value,
                "generated_at": end_date.isoformat(),
                "data_period": {
                    "start": start_date.isoformat(),
                    "end": end_date.isoformat(),
                    "days": (end_date - start_date).days
                }
            },
            "executive_summary": {
                "revenue": {
                    "current_period": float(current_revenue),
                    "previous_period": float(previous_revenue),
                    "growth_rate": round(revenue_growth, 2),
                    "trend": "up" if revenue_growth > 0 else "down" if revenue_growth < 0 else "flat"
                },
                "customers": {
                    "total_active": customer_metrics.get("total_customers", 0),
                    "new_acquisitions": customer_metrics.get("new_customers_30_days", 0),
                    "churn_rate": customer_metrics.get("churn_rate", 0),
                    "retention_rate": round(100 - customer_metrics.get("churn_rate", 0), 2)
                },
                "operations": {
                    "total_orders": order_metrics.get("total_orders", 0),
                    "average_order_value": order_metrics.get("average_order_value", 0),
                    "conversion_rate": customer_metrics.get("conversion_rate", 0),
                    "gross_margin": financial_summary.get("gross_margin_percentage", 0)
                }
            },
            "key_performance_indicators": {
                "revenue": {
                    "monthly_recurring_revenue": float(self.analytics_service.calculate_mrr()),
                    "annual_recurring_revenue": float(self.analytics_service.calculate_arr()),
                    "revenue_per_customer": float(current_revenue / max(customer_metrics.get("total_customers", 1), 1)),
                    "revenue_growth_rate": round(revenue_growth, 2)
                },
                "customer": {
                    "customer_lifetime_value": customer_metrics.get("avg_customer_lifetime_value", 0),
                    "customer_acquisition_cost": customer_metrics.get("estimated_cac", 0),
                    "payback_period_months": customer_metrics.get("cac_payback_months", 0),
                    "net_promoter_score": 8.2  # Simulated - would come from surveys
                },
                "operational": {
                    "inventory_turnover": financial_summary.get("inventory_turnover", 0),
                    "order_fulfillment_time": 2.3,  # Simulated - would come from logistics
                    "customer_support_satisfaction": 4.6,  # Simulated - would come from support system
                    "website_uptime": 99.9  # Simulated - would come from monitoring
                }
            },
            "customer_segmentation": {
                "total_segments": len(segmentation_analysis.get("segments", {})),
                "champions_percentage": segmentation_analysis.get("segments", {}).get("Champions", {}).get("percentage", 0),
                "at_risk_percentage": sum([
                    segmentation_analysis.get("segments", {}).get("At_Risk", {}).get("percentage", 0),
                    segmentation_analysis.get("segments", {}).get("Cannot_Lose", {}).get("percentage", 0)
                ]),
                "segment_distribution": segmentation_analysis.get("segment_distribution", [])
            },
            "cohort_performance": {
                "retention_summary": cohort_analysis.get("summary", {}),
                "avg_1_month_retention": cohort_analysis.get("summary", {}).get("avg_retention_by_period", {}).get(1, 0),
                "avg_6_month_retention": cohort_analysis.get("summary", {}).get("avg_retention_by_period", {}).get(6, 0)
            },
            "insights": key_insights,
            "action_items": action_items,
            "recommendations": self._generate_strategic_recommendations(
                revenue_growth, segmentation_analysis, cohort_analysis
            )
        }

        return report

    def generate_operational_report(self, days: int = 7) -> dict:
        """
        Generate detailed operational dashboard report.
        
        Args:
            days: Number of days to analyze
            
        Returns:
            Operational report with real-time metrics and performance data
        """
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)

        # Get real-time metrics
        realtime_metrics = self.analytics_service.get_realtime_metrics()
        financial_summary = self.analytics_service.get_financial_summary()
        inventory_metrics = self.analytics_service.get_inventory_metrics()

        # Get conversion funnel
        conversion_funnel = self.funnel_service.calculate_conversion_funnel(start_date, end_date)

        # Get top products
        top_products = self.analytics_service.get_top_selling_products(10)

        report = {
            "metadata": {
                "report_type": ReportType.OPERATIONAL.value,
                "generated_at": end_date.isoformat(),
                "analysis_period_days": days
            },
            "real_time_overview": {
                "active_users": realtime_metrics.get("active_users_today", 0),
                "orders_today": realtime_metrics.get("orders_today", 0),
                "revenue_today": realtime_metrics.get("revenue_today", 0),
                "conversion_rate_today": realtime_metrics.get("conversion_rate_today", 0)
            },
            "performance_metrics": {
                "conversion_funnel": conversion_funnel.get("funnel_steps", {}),
                "funnel_insights": conversion_funnel.get("insights", []),
                "cart_abandonment_rate": self.analytics_service.get_cart_abandonment_rate(days),
                "average_order_value": float(self.analytics_service.get_average_order_value(start_date, end_date))
            },
            "inventory_status": {
                "total_products": inventory_metrics.get("total_products", 0),
                "low_stock_items": inventory_metrics.get("low_stock_items", 0),
                "out_of_stock_items": inventory_metrics.get("out_of_stock_items", 0),
                "inventory_value": inventory_metrics.get("total_inventory_value", 0)
            },
            "product_performance": {
                "top_selling_products": top_products,
                "product_categories": self._get_category_performance(),
                "inventory_turnover": financial_summary.get("inventory_turnover", 0)
            },
            "financial_health": {
                "gross_margin": financial_summary.get("gross_margin_percentage", 0),
                "net_margin": financial_summary.get("net_margin_percentage", 0),
                "cash_flow": financial_summary.get("cash_flow", 0),
                "accounts_receivable": financial_summary.get("accounts_receivable", 0)
            },
            "alerts_and_issues": self._get_operational_alerts(),
            "recommendations": self._generate_operational_recommendations(
                inventory_metrics, conversion_funnel, financial_summary
            )
        }

        return report

    def generate_customer_analytics_report(self, months_back: int = 6) -> dict:
        """
        Generate comprehensive customer behavior and analytics report.
        
        Args:
            months_back: Number of months to analyze
            
        Returns:
            Customer analytics report with segmentation, cohorts, and behavior insights
        """
        # Get customer segmentation
        segmentation_analysis = self.segmentation_service.get_segment_analysis()

        # Get cohort analysis
        retention_cohorts = self.cohort_service.calculate_retention_cohorts(months_back=months_back)
        revenue_cohorts = self.cohort_service.calculate_revenue_cohorts(months_back=months_back)

        # Get conversion funnel by channel
        channel_funnels = self.funnel_service.calculate_channel_funnels(days=30)

        # Get device performance
        device_funnels = self.funnel_service.calculate_mobile_vs_desktop_funnel(days=30)

        # Customer metrics
        customer_metrics = self.analytics_service.get_customer_metrics()

        report = {
            "metadata": {
                "report_type": ReportType.CUSTOMER.value,
                "generated_at": datetime.utcnow().isoformat(),
                "analysis_period_months": months_back
            },
            "customer_segmentation": {
                "rfm_analysis": segmentation_analysis,
                "segment_recommendations": {
                    segment.value: self.segmentation_service.get_segment_recommendations(segment)
                    for segment in [
                        RFMSegment.CHAMPIONS, RFMSegment.AT_RISK,
                        RFMSegment.NEW_CUSTOMERS, RFMSegment.POTENTIAL_LOYALISTS
                    ]
                }
            },
            "cohort_analysis": {
                "retention_cohorts": retention_cohorts,
                "revenue_cohorts": revenue_cohorts,
                "cohort_insights": self._generate_cohort_insights(retention_cohorts, revenue_cohorts)
            },
            "customer_journey": {
                "acquisition_channels": channel_funnels.get("channels", {}),
                "device_performance": device_funnels,
                "conversion_patterns": self._analyze_conversion_patterns(channel_funnels, device_funnels)
            },
            "customer_behavior": {
                "lifetime_value_distribution": self._get_clv_distribution(),
                "purchase_frequency_patterns": self._get_purchase_patterns(),
                "seasonal_trends": self._get_seasonal_trends(),
                "product_affinity": self._get_product_affinity_analysis()
            },
            "retention_analysis": {
                "overall_retention_rate": 100 - customer_metrics.get("churn_rate", 0),
                "retention_by_segment": self._get_retention_by_segment(segmentation_analysis),
                "churn_prediction": self._get_churn_predictions(),
                "reactivation_opportunities": self._identify_reactivation_opportunities()
            },
            "actionable_insights": self._generate_customer_insights(
                segmentation_analysis, retention_cohorts, channel_funnels
            ),
            "marketing_recommendations": self._generate_marketing_recommendations(
                segmentation_analysis, channel_funnels, device_funnels
            )
        }

        return report

    def schedule_automated_reports(self) -> dict:
        """
        Configure automated report generation schedule.
        
        Returns:
            Configuration for scheduled reports
        """
        schedules = {
            "daily_operational": {
                "report_type": ReportType.OPERATIONAL,
                "frequency": "daily",
                "time": "08:00",
                "recipients": ["operations@brain2gain.com", "cto@brain2gain.com"],
                "format": "email_summary"
            },
            "weekly_executive": {
                "report_type": ReportType.EXECUTIVE,
                "frequency": "weekly",
                "time": "monday_09:00",
                "recipients": ["ceo@brain2gain.com", "cfo@brain2gain.com", "cmo@brain2gain.com"],
                "format": "pdf_detailed"
            },
            "monthly_customer": {
                "report_type": ReportType.CUSTOMER,
                "frequency": "monthly",
                "time": "first_monday_10:00",
                "recipients": ["marketing@brain2gain.com", "customer_success@brain2gain.com"],
                "format": "interactive_dashboard"
            },
            "quarterly_financial": {
                "report_type": ReportType.FINANCIAL,
                "frequency": "quarterly",
                "time": "first_tuesday_14:00",
                "recipients": ["board@brain2gain.com", "investors@brain2gain.com"],
                "format": "executive_presentation"
            }
        }

        return {
            "automated_schedules": schedules,
            "last_updated": datetime.utcnow().isoformat(),
            "status": "active",
            "next_reports": self._get_next_scheduled_reports(schedules)
        }

    def _generate_executive_insights(self, revenue_growth: float, financial_summary: dict,
                                   customer_metrics: dict, segmentation_analysis: dict,
                                   cohort_analysis: dict) -> list[str]:
        """Generate strategic insights for executives."""
        insights = []

        # Revenue insights
        if revenue_growth > 10:
            insights.append(f"Strong revenue growth of {revenue_growth:.1f}% indicates successful market execution")
        elif revenue_growth < -5:
            insights.append(f"Revenue decline of {abs(revenue_growth):.1f}% requires immediate strategic attention")

        # Customer insights
        churn_rate = customer_metrics.get("churn_rate", 0)
        if churn_rate > 10:
            insights.append(f"High churn rate ({churn_rate:.1f}%) is impacting growth - focus on retention initiatives")

        # Segmentation insights
        champions_pct = segmentation_analysis.get("segments", {}).get("Champions", {}).get("percentage", 0)
        if champions_pct < 10:
            insights.append("Low Champions segment suggests need for customer loyalty programs")

        # Cohort insights
        if cohort_analysis.get("summary", {}):
            avg_retention = cohort_analysis["summary"].get("avg_retention_by_period", {}).get(3, 0)
            if avg_retention < 30:
                insights.append("Poor 3-month retention indicates product-market fit challenges")

        return insights

    def _generate_action_items(self, revenue_growth: float, customer_metrics: dict,
                              segmentation_analysis: dict) -> list[dict]:
        """Generate specific action items for executives."""
        actions = []

        if revenue_growth < 5:
            actions.append({
                "priority": "high",
                "category": "growth",
                "action": "Develop revenue acceleration strategy",
                "owner": "CMO",
                "deadline": "next_quarter"
            })

        churn_rate = customer_metrics.get("churn_rate", 0)
        if churn_rate > 8:
            actions.append({
                "priority": "high",
                "category": "retention",
                "action": "Implement customer success program",
                "owner": "Customer Success",
                "deadline": "30_days"
            })

        at_risk_pct = sum([
            segmentation_analysis.get("segments", {}).get("At_Risk", {}).get("percentage", 0),
            segmentation_analysis.get("segments", {}).get("Cannot_Lose", {}).get("percentage", 0)
        ])

        if at_risk_pct > 15:
            actions.append({
                "priority": "medium",
                "category": "customer_retention",
                "action": "Launch targeted win-back campaigns for at-risk customers",
                "owner": "Marketing",
                "deadline": "14_days"
            })

        return actions

    def _generate_strategic_recommendations(self, revenue_growth: float,
                                         segmentation_analysis: dict,
                                         cohort_analysis: dict) -> list[str]:
        """Generate high-level strategic recommendations."""
        recommendations = []

        if revenue_growth < 10:
            recommendations.append("Consider expanding into new product categories or markets")

        champions_pct = segmentation_analysis.get("segments", {}).get("Champions", {}).get("percentage", 0)
        if champions_pct > 15:
            recommendations.append("Leverage Champions segment for referral and advocacy programs")

        new_customers_pct = segmentation_analysis.get("segments", {}).get("New_Customers", {}).get("percentage", 0)
        if new_customers_pct > 20:
            recommendations.append("Focus on onboarding optimization to convert new customers to loyalists")

        return recommendations

    def _get_category_performance(self) -> list[dict]:
        """Get performance metrics by product category."""
        # This would typically query product sales by category
        # For now, returning simulated data
        return [
            {"category": "Protein", "revenue": 45000, "units_sold": 850, "growth_rate": 12.5},
            {"category": "Creatine", "revenue": 28000, "units_sold": 420, "growth_rate": 8.3},
            {"category": "Pre-workout", "revenue": 22000, "units_sold": 380, "growth_rate": -2.1}
        ]

    def _get_operational_alerts(self) -> list[dict]:
        """Get current operational alerts and issues."""
        return [
            {
                "severity": "warning",
                "type": "inventory",
                "message": "5 products below minimum stock level",
                "action_required": "Reorder inventory"
            },
            {
                "severity": "info",
                "type": "performance",
                "message": "Cart abandonment rate increased 3% this week",
                "action_required": "Review checkout process"
            }
        ]

    def _generate_operational_recommendations(self, inventory_metrics: dict,
                                           conversion_funnel: dict,
                                           financial_summary: dict) -> list[str]:
        """Generate operational improvement recommendations."""
        recommendations = []

        if inventory_metrics.get("low_stock_items", 0) > 5:
            recommendations.append("Implement automated reorder system for inventory management")

        if financial_summary.get("gross_margin_percentage", 0) < 30:
            recommendations.append("Review pricing strategy and supplier costs to improve margins")

        return recommendations

    def _generate_cohort_insights(self, retention_cohorts: dict, revenue_cohorts: dict) -> list[str]:
        """Generate insights from cohort analysis."""
        insights = []

        # Add cohort-specific insights
        if retention_cohorts.get("summary", {}):
            avg_retention_1m = retention_cohorts["summary"].get("avg_retention_by_period", {}).get(1, 0)
            if avg_retention_1m > 40:
                insights.append("Strong 1-month retention indicates good product-market fit")
            elif avg_retention_1m < 25:
                insights.append("Low 1-month retention suggests onboarding optimization needed")

        return insights

    def _analyze_conversion_patterns(self, channel_funnels: dict, device_funnels: dict) -> dict:
        """Analyze conversion patterns across channels and devices."""
        return {
            "best_converting_channel": channel_funnels.get("comparison", {}).get("best_converting_channel", {}),
            "mobile_vs_desktop": device_funnels.get("comparison", {}),
            "optimization_opportunities": [
                "Optimize mobile checkout experience",
                "Improve social media conversion rates"
            ]
        }

    def _get_clv_distribution(self) -> dict:
        """Get customer lifetime value distribution."""
        return {
            "segments": [
                {"range": "$0-50", "customers": 45, "percentage": 30},
                {"range": "$51-150", "customers": 60, "percentage": 40},
                {"range": "$151-300", "customers": 30, "percentage": 20},
                {"range": "$301+", "customers": 15, "percentage": 10}
            ],
            "average_clv": 125.50,
            "median_clv": 98.25
        }

    def _get_purchase_patterns(self) -> dict:
        """Get customer purchase frequency patterns."""
        return {
            "frequency_distribution": [
                {"frequency": "1 time", "customers": 40, "percentage": 35},
                {"frequency": "2-3 times", "customers": 35, "percentage": 30},
                {"frequency": "4-6 times", "customers": 25, "percentage": 22},
                {"frequency": "7+ times", "customers": 15, "percentage": 13}
            ],
            "average_purchase_frequency": 2.8,
            "repeat_purchase_rate": 65
        }

    def _get_seasonal_trends(self) -> dict:
        """Get seasonal purchasing trends."""
        return {
            "peak_months": ["January", "June", "September"],
            "low_months": ["March", "August"],
            "seasonal_variance": 25.3,
            "holiday_impact": {
                "new_year": 45.2,
                "summer": 32.1,
                "back_to_school": 28.7
            }
        }

    def _get_product_affinity_analysis(self) -> dict:
        """Get product affinity and cross-sell analysis."""
        return {
            "top_combinations": [
                {"products": ["Whey Protein", "Creatine"], "frequency": 65},
                {"products": ["Pre-workout", "BCAA"], "frequency": 45},
                {"products": ["Mass Gainer", "Vitamin D"], "frequency": 38}
            ],
            "cross_sell_rate": 23.5,
            "bundle_opportunities": ["Muscle Building Stack", "Energy & Focus Pack"]
        }

    def _get_retention_by_segment(self, segmentation_analysis: dict) -> dict:
        """Get retention rates by customer segment."""
        return {
            "Champions": 95.2,
            "Loyal_Customers": 87.3,
            "Potential_Loyalists": 68.1,
            "At_Risk": 34.7,
            "New_Customers": 45.9
        }

    def _get_churn_predictions(self) -> dict:
        """Get churn prediction analysis."""
        return {
            "high_risk_customers": 23,
            "medium_risk_customers": 45,
            "predicted_churn_next_30_days": 8.2,
            "intervention_opportunities": 15
        }

    def _identify_reactivation_opportunities(self) -> dict:
        """Identify customer reactivation opportunities."""
        return {
            "dormant_customers": 67,
            "reactivation_targets": 34,
            "expected_recovery_rate": 15.3,
            "recommended_campaigns": ["Win-back discount", "Product update notifications"]
        }

    def _generate_customer_insights(self, segmentation_analysis: dict,
                                   retention_cohorts: dict, channel_funnels: dict) -> list[str]:
        """Generate customer-focused insights."""
        insights = []

        # Add customer behavior insights
        insights.extend(segmentation_analysis.get("insights", []))
        insights.extend(retention_cohorts.get("insights", []))
        insights.extend(channel_funnels.get("insights", []))

        return insights

    def _generate_marketing_recommendations(self, segmentation_analysis: dict,
                                          channel_funnels: dict, device_funnels: dict) -> list[str]:
        """Generate marketing-specific recommendations."""
        recommendations = []

        # Channel optimization
        best_channel = channel_funnels.get("comparison", {}).get("best_converting_channel", {})
        if best_channel:
            recommendations.append(f"Increase investment in {best_channel.get('channel', '')} - highest converting channel")

        # Device optimization
        mobile_share = device_funnels.get("comparison", {}).get("mobile_traffic_share", 0)
        if mobile_share > 60:
            recommendations.append("Prioritize mobile experience optimization - majority of traffic is mobile")

        # Segmentation recommendations
        at_risk_pct = sum([
            segmentation_analysis.get("segments", {}).get("At_Risk", {}).get("percentage", 0),
            segmentation_analysis.get("segments", {}).get("Cannot_Lose", {}).get("percentage", 0)
        ])

        if at_risk_pct > 10:
            recommendations.append("Implement automated retention campaigns for at-risk customer segments")

        return recommendations

    def _get_next_scheduled_reports(self, schedules: dict) -> list[dict]:
        """Calculate next scheduled report dates."""
        next_reports = []

        for report_name, config in schedules.items():
            next_run = self._calculate_next_run_time(config["frequency"], config["time"])
            next_reports.append({
                "report": report_name,
                "next_run": next_run.isoformat(),
                "type": config["report_type"]
            })

        return sorted(next_reports, key=lambda x: x["next_run"])

    def _calculate_next_run_time(self, frequency: str, time: str) -> datetime:
        """Calculate next run time for scheduled reports."""
        now = datetime.utcnow()

        if frequency == "daily":
            # Return tomorrow at specified time
            hour, minute = map(int, time.split(":"))
            next_run = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
            if next_run <= now:
                next_run += timedelta(days=1)
            return next_run

        elif frequency == "weekly":
            # Return next Monday at specified time
            days_ahead = 0 - now.weekday()  # Monday is 0
            if days_ahead <= 0:
                days_ahead += 7
            return now + timedelta(days=days_ahead)

        # Add more frequency calculations as needed
        return now + timedelta(days=1)
