# backend/app/services/customer_segmentation_service.py

from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Optional, Tuple
from sqlmodel import Session, select, func, and_
from dataclasses import dataclass
import pandas as pd
import numpy as np
from enum import Enum

from ..models import Customer, SalesOrder, SalesItem, Transaction, TransactionType, OrderStatus


class RFMSegment(str, Enum):
    CHAMPIONS = "Champions"
    LOYAL_CUSTOMERS = "Loyal_Customers" 
    POTENTIAL_LOYALISTS = "Potential_Loyalists"
    NEW_CUSTOMERS = "New_Customers"
    PROMISING = "Promising"
    NEED_ATTENTION = "Need_Attention"
    ABOUT_TO_SLEEP = "About_to_Sleep"
    AT_RISK = "At_Risk"
    CANNOT_LOSE = "Cannot_Lose"
    HIBERNATING = "Hibernating"


@dataclass
class RFMScores:
    customer_id: int
    recency_days: int
    frequency: int
    monetary_value: float
    recency_score: int
    frequency_score: int
    monetary_score: int
    rfm_score: str
    segment: RFMSegment


@dataclass
class CustomerSegmentProfile:
    segment: RFMSegment
    description: str
    characteristics: List[str]
    marketing_strategy: List[str]
    expected_percentage: float
    color: str


class CustomerSegmentationService:
    """Service for advanced customer segmentation using RFM analysis"""
    
    def __init__(self, db: Session):
        self.db = db
        
        # RFM Segment definitions based on score combinations
        self.rfm_segments = {
            # Champions: R=4-5, F=4-5, M=4-5
            RFMSegment.CHAMPIONS: {
                "R": [4, 5], "F": [4, 5], "M": [4, 5],
                "description": "Best customers who bought recently, buy often and spend the most",
                "characteristics": ["High value", "Recent purchase", "Frequent buyers", "Brand advocates"],
                "marketing_strategy": ["Reward them", "Early access to new products", "VIP treatment", "Referral programs"],
                "expected_percentage": 11.1,
                "color": "#10B981"  # Green
            },
            
            # Loyal Customers: R=2-5, F=3-5, M=3-5
            RFMSegment.LOYAL_CUSTOMERS: {
                "R": [2, 5], "F": [3, 5], "M": [3, 5],
                "description": "Customers who spend good money and respond to promotions",
                "characteristics": ["Regular buyers", "Good monetary value", "Responsive to offers"],
                "marketing_strategy": ["Upsell higher value products", "Cross-sell complementary items", "Loyalty programs"],
                "expected_percentage": 15.6,
                "color": "#059669"  # Dark green
            },
            
            # Potential Loyalists: R=3-5, F=1-3, M=1-3
            RFMSegment.POTENTIAL_LOYALISTS: {
                "R": [3, 5], "F": [1, 3], "M": [1, 3],
                "description": "Recent customers with average spending who can become loyal",
                "characteristics": ["Recent buyers", "Low frequency", "Growth potential"],
                "marketing_strategy": ["Membership programs", "Educational content", "Product recommendations"],
                "expected_percentage": 18.2,
                "color": "#34D399"  # Light green
            },
            
            # New Customers: R=4-5, F=1, M=1
            RFMSegment.NEW_CUSTOMERS: {
                "R": [4, 5], "F": [1, 1], "M": [1, 1],
                "description": "Recently acquired customers with low spending",
                "characteristics": ["Recent first purchase", "Single purchase", "Unknown potential"],
                "marketing_strategy": ["Welcome series", "Onboarding offers", "Product education"],
                "expected_percentage": 13.3,
                "color": "#3B82F6"  # Blue
            },
            
            # Promising: R=3-4, F=1, M=2-3
            RFMSegment.PROMISING: {
                "R": [3, 4], "F": [1, 1], "M": [2, 3],
                "description": "Recent customers who spent a good amount",
                "characteristics": ["Recent buyers", "Higher initial purchase", "Good potential"],
                "marketing_strategy": ["Targeted offers", "Product bundles", "Follow-up campaigns"],
                "expected_percentage": 12.9,
                "color": "#6366F1"  # Indigo
            },
            
            # Need Attention: R=2-3, F=2-3, M=2-3
            RFMSegment.NEED_ATTENTION: {
                "R": [2, 3], "F": [2, 3], "M": [2, 3],
                "description": "Average customers who need re-engagement",
                "characteristics": ["Moderate recency", "Average frequency", "Declining engagement"],
                "marketing_strategy": ["Re-engagement campaigns", "Special discounts", "Win-back offers"],
                "expected_percentage": 8.1,
                "color": "#F59E0B"  # Yellow
            },
            
            # About to Sleep: R=2-3, F=1-2, M=1-2
            RFMSegment.ABOUT_TO_SLEEP: {
                "R": [2, 3], "F": [1, 2], "M": [1, 2],
                "description": "Customers who haven't purchased recently",
                "characteristics": ["Declining activity", "Low engagement", "Risk of churn"],
                "marketing_strategy": ["Reactivation campaigns", "Limited-time offers", "Survey feedback"],
                "expected_percentage": 7.8,
                "color": "#F97316"  # Orange
            },
            
            # At Risk: R=1-2, F=2-4, M=2-4
            RFMSegment.AT_RISK: {
                "R": [1, 2], "F": [2, 4], "M": [2, 4],
                "description": "Previously good customers who haven't purchased recently",
                "characteristics": ["Was valuable", "Long time since purchase", "High churn risk"],
                "marketing_strategy": ["Win-back campaigns", "Personal outreach", "Exclusive offers"],
                "expected_percentage": 7.3,
                "color": "#EF4444"  # Red
            },
            
            # Cannot Lose: R=1-2, F=4-5, M=4-5
            RFMSegment.CANNOT_LOSE: {
                "R": [1, 2], "F": [4, 5], "M": [4, 5],
                "description": "High-value customers who haven't purchased recently",
                "characteristics": ["High historical value", "Frequent past buyers", "Critical to retain"],
                "marketing_strategy": ["VIP treatment", "Personal contact", "Major incentives"],
                "expected_percentage": 2.4,
                "color": "#DC2626"  # Dark red
            },
            
            # Hibernating: R=1-2, F=1-2, M=1-2
            RFMSegment.HIBERNATING: {
                "R": [1, 2], "F": [1, 2], "M": [1, 2],
                "description": "Inactive customers with low value",
                "characteristics": ["Long inactive", "Low value", "Minimal engagement"],
                "marketing_strategy": ["Low-cost reactivation", "Surveys", "Consider removing"],
                "expected_percentage": 3.3,
                "color": "#6B7280"  # Gray
            }
        }
    
    def calculate_rfm_scores(self, analysis_date: datetime = None) -> List[RFMScores]:
        """Calculate RFM scores for all customers"""
        if analysis_date is None:
            analysis_date = datetime.utcnow()
        
        # Get customer RFM data
        rfm_query = '''
        WITH customer_rfm AS (
            SELECT 
                c.customer_id,
                c.first_name,
                c.last_name,
                c.email,
                -- Recency: days since last order
                COALESCE(
                    EXTRACT(DAY FROM (:analysis_date - MAX(so.order_date))), 
                    999
                ) as recency_days,
                -- Frequency: number of completed orders
                COUNT(CASE WHEN so.status = 'COMPLETED' THEN so.so_id END) as frequency,
                -- Monetary: total amount spent on completed orders
                COALESCE(
                    SUM(CASE WHEN so.status = 'COMPLETED' THEN si.qty * si.unit_price END), 
                    0
                ) as monetary_value
            FROM customer c
            LEFT JOIN salesorder so ON c.customer_id = so.customer_id
            LEFT JOIN salesitem si ON so.so_id = si.so_id
            GROUP BY c.customer_id, c.first_name, c.last_name, c.email
            HAVING COUNT(CASE WHEN so.status = 'COMPLETED' THEN so.so_id END) > 0
        )
        SELECT * FROM customer_rfm
        ORDER BY customer_id
        '''
        
        result = self.db.exec(text(rfm_query), {"analysis_date": analysis_date})
        customers_data = result.fetchall()
        
        if not customers_data:
            return []
        
        # Convert to DataFrame for easier analysis
        df = pd.DataFrame(customers_data, columns=[
            'customer_id', 'first_name', 'last_name', 'email', 
            'recency_days', 'frequency', 'monetary_value'
        ])
        
        # Calculate RFM scores using quintile-based scoring
        df['recency_score'] = pd.qcut(df['recency_days'].rank(method='first'), 5, labels=[5,4,3,2,1])
        df['frequency_score'] = pd.qcut(df['frequency'].rank(method='first'), 5, labels=[1,2,3,4,5])
        df['monetary_score'] = pd.qcut(df['monetary_value'].rank(method='first'), 5, labels=[1,2,3,4,5])
        
        # Create RFM score string
        df['rfm_score'] = (
            df['recency_score'].astype(str) + 
            df['frequency_score'].astype(str) + 
            df['monetary_score'].astype(str)
        )
        
        # Assign segments
        df['segment'] = df.apply(self._assign_rfm_segment, axis=1)
        
        # Convert to RFMScores objects
        rfm_scores = []
        for _, row in df.iterrows():
            rfm_scores.append(RFMScores(
                customer_id=int(row['customer_id']),
                recency_days=int(row['recency_days']),
                frequency=int(row['frequency']),
                monetary_value=float(row['monetary_value']),
                recency_score=int(row['recency_score']),
                frequency_score=int(row['frequency_score']),
                monetary_score=int(row['monetary_score']),
                rfm_score=str(row['rfm_score']),
                segment=RFMSegment(row['segment'])
            ))
        
        return rfm_scores
    
    def _assign_rfm_segment(self, row) -> str:
        """Assign RFM segment based on R, F, M scores"""
        r, f, m = int(row['recency_score']), int(row['frequency_score']), int(row['monetary_score'])
        
        for segment, criteria in self.rfm_segments.items():
            if (criteria["R"][0] <= r <= criteria["R"][1] and 
                criteria["F"][0] <= f <= criteria["F"][1] and 
                criteria["M"][0] <= m <= criteria["M"][1]):
                return segment.value
        
        # Default fallback
        return RFMSegment.HIBERNATING.value
    
    def get_segment_analysis(self) -> Dict:
        """Get comprehensive segment analysis"""
        rfm_scores = self.calculate_rfm_scores()
        
        if not rfm_scores:
            return {
                "total_customers": 0,
                "segments": {},
                "segment_distribution": {},
                "insights": []
            }
        
        # Count customers by segment
        segment_counts = {}
        total_customers = len(rfm_scores)
        
        for score in rfm_scores:
            segment = score.segment
            if segment not in segment_counts:
                segment_counts[segment] = {
                    "count": 0,
                    "percentage": 0,
                    "avg_recency": 0,
                    "avg_frequency": 0,
                    "avg_monetary": 0,
                    "total_monetary": 0
                }
            
            segment_counts[segment]["count"] += 1
            segment_counts[segment]["avg_recency"] += score.recency_days
            segment_counts[segment]["avg_frequency"] += score.frequency
            segment_counts[segment]["avg_monetary"] += score.monetary_value
            segment_counts[segment]["total_monetary"] += score.monetary_value
        
        # Calculate averages and percentages
        for segment, data in segment_counts.items():
            count = data["count"]
            data["percentage"] = round((count / total_customers) * 100, 1)
            data["avg_recency"] = round(data["avg_recency"] / count, 1)
            data["avg_frequency"] = round(data["avg_frequency"] / count, 1)
            data["avg_monetary"] = round(data["avg_monetary"] / count, 2)
            data["total_monetary"] = round(data["total_monetary"], 2)
        
        # Get segment profiles
        segment_profiles = {}
        for segment in segment_counts.keys():
            if segment in self.rfm_segments:
                profile_data = self.rfm_segments[segment]
                segment_profiles[segment.value] = CustomerSegmentProfile(
                    segment=segment,
                    description=profile_data["description"],
                    characteristics=profile_data["characteristics"],
                    marketing_strategy=profile_data["marketing_strategy"],
                    expected_percentage=profile_data["expected_percentage"],
                    color=profile_data["color"]
                )
        
        # Generate insights
        insights = self._generate_segment_insights(segment_counts, total_customers)
        
        return {
            "total_customers": total_customers,
            "analysis_date": datetime.utcnow().isoformat(),
            "segments": {
                segment.value: {
                    **data,
                    "profile": segment_profiles.get(segment.value, {}).__dict__ if segment.value in segment_profiles else {}
                }
                for segment, data in segment_counts.items()
            },
            "segment_distribution": [
                {
                    "segment": segment.value,
                    "count": data["count"],
                    "percentage": data["percentage"],
                    "color": segment_profiles.get(segment.value, CustomerSegmentProfile(
                        segment, "", [], [], 0, "#6B7280"
                    )).color
                }
                for segment, data in segment_counts.items()
            ],
            "insights": insights
        }
    
    def _generate_segment_insights(self, segment_counts: Dict, total_customers: int) -> List[str]:
        """Generate actionable insights from segmentation analysis"""
        insights = []
        
        # Check for high-value segments
        champions_pct = segment_counts.get(RFMSegment.CHAMPIONS, {}).get("percentage", 0)
        if champions_pct < 5:
            insights.append("Low Champions percentage suggests need for customer retention programs")
        elif champions_pct > 15:
            insights.append("High Champions percentage indicates strong customer loyalty")
        
        # Check for at-risk customers
        at_risk_pct = (
            segment_counts.get(RFMSegment.AT_RISK, {}).get("percentage", 0) +
            segment_counts.get(RFMSegment.CANNOT_LOSE, {}).get("percentage", 0)
        )
        if at_risk_pct > 15:
            insights.append(f"High percentage ({at_risk_pct:.1f}%) of at-risk customers needs immediate attention")
        
        # Check for new customer conversion
        new_customers_pct = segment_counts.get(RFMSegment.NEW_CUSTOMERS, {}).get("percentage", 0)
        potential_loyalists_pct = segment_counts.get(RFMSegment.POTENTIAL_LOYALISTS, {}).get("percentage", 0)
        
        if new_customers_pct > potential_loyalists_pct:
            insights.append("Focus on converting new customers to repeat buyers")
        
        # Check hibernating customers
        hibernating_pct = segment_counts.get(RFMSegment.HIBERNATING, {}).get("percentage", 0)
        if hibernating_pct > 10:
            insights.append("Consider cleaning hibernating customers from active marketing lists")
        
        # Revenue concentration
        champions_revenue = segment_counts.get(RFMSegment.CHAMPIONS, {}).get("total_monetary", 0)
        loyal_revenue = segment_counts.get(RFMSegment.LOYAL_CUSTOMERS, {}).get("total_monetary", 0)
        total_revenue = sum(data.get("total_monetary", 0) for data in segment_counts.values())
        
        high_value_revenue_pct = ((champions_revenue + loyal_revenue) / total_revenue * 100) if total_revenue > 0 else 0
        
        if high_value_revenue_pct > 60:
            insights.append(f"High revenue concentration ({high_value_revenue_pct:.1f}%) in top segments - ensure retention")
        
        return insights
    
    def get_customers_by_segment(self, segment: RFMSegment, limit: int = 100) -> List[Dict]:
        """Get customers belonging to a specific segment"""
        rfm_scores = self.calculate_rfm_scores()
        
        segment_customers = [
            {
                "customer_id": score.customer_id,
                "recency_days": score.recency_days,
                "frequency": score.frequency,
                "monetary_value": score.monetary_value,
                "rfm_score": score.rfm_score,
                "recency_score": score.recency_score,
                "frequency_score": score.frequency_score,
                "monetary_score": score.monetary_score
            }
            for score in rfm_scores 
            if score.segment == segment
        ][:limit]
        
        return segment_customers
    
    def get_segment_recommendations(self, segment: RFMSegment) -> Dict:
        """Get marketing recommendations for a specific segment"""
        if segment not in self.rfm_segments:
            return {}
        
        profile = self.rfm_segments[segment]
        customers = self.get_customers_by_segment(segment, limit=10)
        
        return {
            "segment": segment.value,
            "profile": profile,
            "customer_count": len(self.get_customers_by_segment(segment, limit=10000)),
            "sample_customers": customers,
            "recommended_actions": profile["marketing_strategy"],
            "characteristics": profile["characteristics"]
        }