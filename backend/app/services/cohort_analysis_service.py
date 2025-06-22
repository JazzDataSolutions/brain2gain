"""
Cohort Analysis Service - Advanced Analytics Phase 2
Implements cohort retention analysis and revenue cohorts.
"""

from datetime import datetime, timedelta

import pandas as pd
from sqlalchemy import text
from sqlmodel import Session


class CohortAnalysisService:
    """Service for advanced cohort analysis."""

    def __init__(self, db: Session):
        self.db = db

    def calculate_retention_cohorts(self, period: str = 'monthly', months_back: int = 12) -> dict:
        """
        Calculate customer retention cohorts.
        
        Args:
            period: 'monthly' or 'weekly' cohort periods
            months_back: Number of months to analyze
            
        Returns:
            Dictionary with cohort retention analysis
        """
        # Get customer first purchase data
        query = text("""
            WITH first_purchases AS (
                SELECT 
                    c.customer_id,
                    MIN(so.order_date) as first_purchase_date,
                    DATE_TRUNC('month', MIN(so.order_date)) as cohort_month
                FROM customers c
                JOIN sales_orders so ON c.customer_id = so.customer_id
                WHERE so.status = 'COMPLETED'
                    AND so.order_date >= :start_date
                GROUP BY c.customer_id
            ),
            customer_orders AS (
                SELECT 
                    fp.customer_id,
                    fp.cohort_month,
                    so.order_date,
                    DATE_TRUNC('month', so.order_date) as order_month
                FROM first_purchases fp
                JOIN sales_orders so ON fp.customer_id = so.customer_id
                WHERE so.status = 'COMPLETED'
            )
            SELECT 
                cohort_month,
                order_month,
                COUNT(DISTINCT customer_id) as customers
            FROM customer_orders
            GROUP BY cohort_month, order_month
            ORDER BY cohort_month, order_month
        """)

        start_date = datetime.utcnow() - timedelta(days=months_back * 30)
        result = self.db.execute(query, {"start_date": start_date})
        data = result.fetchall()

        if not data:
            return {}

        # Convert to DataFrame
        df = pd.DataFrame(data, columns=['cohort_month', 'order_month', 'customers'])
        df['cohort_month'] = pd.to_datetime(df['cohort_month'])
        df['order_month'] = pd.to_datetime(df['order_month'])

        # Calculate period number (months since cohort start)
        df['period_number'] = ((df['order_month'] - df['cohort_month']).dt.days / 30.44).round().astype(int)

        # Create cohort table
        cohort_data = df.pivot_table(
            index='cohort_month',
            columns='period_number',
            values='customers',
            fill_value=0
        )

        # Calculate cohort sizes (period 0)
        cohort_sizes = cohort_data.iloc[:, 0]

        # Calculate retention rates
        retention_table = cohort_data.divide(cohort_sizes, axis=0)

        # Convert to percentage
        retention_percentage = retention_table * 100

        # Calculate average retention by period
        avg_retention = retention_percentage.mean(axis=0)

        return {
            'cohort_data': {
                'raw_data': cohort_data.fillna(0).to_dict(),
                'retention_rates': retention_percentage.fillna(0).round(1).to_dict(),
                'cohort_sizes': cohort_sizes.to_dict()
            },
            'summary': {
                'total_cohorts': len(cohort_data),
                'avg_retention_by_period': avg_retention.fillna(0).round(1).to_dict(),
                'total_customers_analyzed': int(cohort_sizes.sum()),
                'analysis_period_months': months_back
            },
            'insights': self._generate_retention_insights(retention_percentage, avg_retention),
            'calculated_at': datetime.utcnow().isoformat()
        }

    def calculate_revenue_cohorts(self, months_back: int = 12) -> dict:
        """
        Calculate revenue cohorts to analyze revenue generation by customer acquisition period.
        
        Args:
            months_back: Number of months to analyze
            
        Returns:
            Dictionary with revenue cohort analysis
        """
        query = text("""
            WITH first_purchases AS (
                SELECT 
                    c.customer_id,
                    MIN(so.order_date) as first_purchase_date,
                    DATE_TRUNC('month', MIN(so.order_date)) as cohort_month
                FROM customers c
                JOIN sales_orders so ON c.customer_id = so.customer_id
                WHERE so.status = 'COMPLETED'
                    AND so.order_date >= :start_date
                GROUP BY c.customer_id
            ),
            customer_revenue AS (
                SELECT 
                    fp.customer_id,
                    fp.cohort_month,
                    DATE_TRUNC('month', t.transaction_date) as revenue_month,
                    SUM(t.amount) as revenue
                FROM first_purchases fp
                JOIN transactions t ON fp.customer_id = t.customer_id
                WHERE t.transaction_type = 'SALE'
                    AND t.status = 'COMPLETED'
                    AND t.paid = true
                GROUP BY fp.customer_id, fp.cohort_month, DATE_TRUNC('month', t.transaction_date)
            )
            SELECT 
                cohort_month,
                revenue_month,
                COUNT(DISTINCT customer_id) as customers,
                SUM(revenue) as total_revenue,
                AVG(revenue) as avg_revenue_per_customer
            FROM customer_revenue
            GROUP BY cohort_month, revenue_month
            ORDER BY cohort_month, revenue_month
        """)

        start_date = datetime.utcnow() - timedelta(days=months_back * 30)
        result = self.db.execute(query, {"start_date": start_date})
        data = result.fetchall()

        if not data:
            return {}

        # Convert to DataFrame
        df = pd.DataFrame(data, columns=[
            'cohort_month', 'revenue_month', 'customers', 'total_revenue', 'avg_revenue_per_customer'
        ])
        df['cohort_month'] = pd.to_datetime(df['cohort_month'])
        df['revenue_month'] = pd.to_datetime(df['revenue_month'])

        # Calculate period number
        df['period_number'] = ((df['revenue_month'] - df['cohort_month']).dt.days / 30.44).round().astype(int)

        # Create revenue cohort tables
        revenue_table = df.pivot_table(
            index='cohort_month',
            columns='period_number',
            values='total_revenue',
            fill_value=0
        )

        avg_revenue_table = df.pivot_table(
            index='cohort_month',
            columns='period_number',
            values='avg_revenue_per_customer',
            fill_value=0
        )

        # Calculate cumulative revenue
        cumulative_revenue = revenue_table.cumsum(axis=1)

        # Calculate LTV by cohort
        ltv_table = cumulative_revenue.copy()

        return {
            'revenue_cohorts': {
                'monthly_revenue': revenue_table.fillna(0).round(2).to_dict(),
                'cumulative_revenue': cumulative_revenue.fillna(0).round(2).to_dict(),
                'avg_revenue_per_customer': avg_revenue_table.fillna(0).round(2).to_dict(),
                'customer_ltv': ltv_table.fillna(0).round(2).to_dict()
            },
            'summary': {
                'total_cohorts': len(revenue_table),
                'avg_monthly_revenue_by_period': revenue_table.mean(axis=0).fillna(0).round(2).to_dict(),
                'avg_ltv_by_period': ltv_table.mean(axis=0).fillna(0).round(2).to_dict(),
                'total_revenue_analyzed': float(revenue_table.sum().sum()),
                'analysis_period_months': months_back
            },
            'insights': self._generate_revenue_cohort_insights(revenue_table, ltv_table),
            'calculated_at': datetime.utcnow().isoformat()
        }

    def calculate_product_adoption_cohorts(self, product_category: str | None = None) -> dict:
        """
        Calculate product adoption cohorts to analyze how customers adopt different products.
        
        Args:
            product_category: Optional category to filter by
            
        Returns:
            Dictionary with product adoption analysis
        """
        category_filter = ""
        if product_category:
            category_filter = "AND p.category = :category"

        query = text(f"""
            WITH first_purchases AS (
                SELECT 
                    c.customer_id,
                    MIN(so.order_date) as first_purchase_date,
                    DATE_TRUNC('month', MIN(so.order_date)) as cohort_month
                FROM customers c
                JOIN sales_orders so ON c.customer_id = so.customer_id
                WHERE so.status = 'COMPLETED'
                GROUP BY c.customer_id
            ),
            product_purchases AS (
                SELECT 
                    fp.customer_id,
                    fp.cohort_month,
                    p.name as product_name,
                    p.category,
                    DATE_TRUNC('month', so.order_date) as purchase_month,
                    COUNT(*) as purchase_count
                FROM first_purchases fp
                JOIN sales_orders so ON fp.customer_id = so.customer_id
                JOIN sales_items si ON so.order_id = si.order_id
                JOIN products p ON si.product_id = p.product_id
                WHERE so.status = 'COMPLETED'
                    {category_filter}
                GROUP BY fp.customer_id, fp.cohort_month, p.name, p.category, DATE_TRUNC('month', so.order_date)
            )
            SELECT 
                cohort_month,
                product_name,
                category,
                purchase_month,
                COUNT(DISTINCT customer_id) as customers,
                SUM(purchase_count) as total_purchases
            FROM product_purchases
            GROUP BY cohort_month, product_name, category, purchase_month
            ORDER BY cohort_month, product_name, purchase_month
        """)

        params = {}
        if product_category:
            params['category'] = product_category

        result = self.db.execute(query, params)
        data = result.fetchall()

        if not data:
            return {}

        # Convert to DataFrame
        df = pd.DataFrame(data, columns=[
            'cohort_month', 'product_name', 'category', 'purchase_month', 'customers', 'total_purchases'
        ])

        # Calculate period number
        df['cohort_month'] = pd.to_datetime(df['cohort_month'])
        df['purchase_month'] = pd.to_datetime(df['purchase_month'])
        df['period_number'] = ((df['purchase_month'] - df['cohort_month']).dt.days / 30.44).round().astype(int)

        # Group by product and create adoption tables
        product_adoption = {}

        for product in df['product_name'].unique():
            product_data = df[df['product_name'] == product]

            adoption_table = product_data.pivot_table(
                index='cohort_month',
                columns='period_number',
                values='customers',
                fill_value=0
            )

            product_adoption[product] = {
                'adoption_table': adoption_table.fillna(0).to_dict(),
                'category': product_data['category'].iloc[0],
                'total_customers': int(adoption_table.sum().sum()),
                'peak_adoption_period': int(adoption_table.mean(axis=0).idxmax()) if not adoption_table.empty else 0
            }

        return {
            'product_adoption': product_adoption,
            'summary': {
                'products_analyzed': len(product_adoption),
                'category_filter': product_category,
                'total_customers': int(df['customers'].sum()),
                'analysis_period': '12 months'
            },
            'insights': self._generate_product_adoption_insights(product_adoption),
            'calculated_at': datetime.utcnow().isoformat()
        }

    def get_cohort_comparison(self, cohort1_start: datetime, cohort2_start: datetime,
                             comparison_periods: int = 6) -> dict:
        """
        Compare two specific cohorts side by side.
        
        Args:
            cohort1_start: Start date of first cohort
            cohort2_start: Start date of second cohort
            comparison_periods: Number of periods to compare
            
        Returns:
            Dictionary with cohort comparison
        """
        query = text("""
            WITH cohort_data AS (
                SELECT 
                    c.customer_id,
                    DATE_TRUNC('month', MIN(so.order_date)) as cohort_month,
                    so.order_date,
                    t.amount
                FROM customers c
                JOIN sales_orders so ON c.customer_id = so.customer_id
                JOIN transactions t ON so.order_id = t.order_id
                WHERE so.status = 'COMPLETED'
                    AND t.transaction_type = 'SALE'
                    AND t.status = 'COMPLETED'
                    AND t.paid = true
                    AND (DATE_TRUNC('month', so.order_date) = :cohort1 
                         OR DATE_TRUNC('month', so.order_date) = :cohort2)
                GROUP BY c.customer_id, DATE_TRUNC('month', MIN(so.order_date)), so.order_date, t.amount
            )
            SELECT 
                cohort_month,
                DATE_TRUNC('month', order_date) as order_month,
                COUNT(DISTINCT customer_id) as customers,
                SUM(amount) as revenue
            FROM cohort_data
            GROUP BY cohort_month, DATE_TRUNC('month', order_date)
            ORDER BY cohort_month, order_month
        """)

        result = self.db.execute(query, {
            "cohort1": cohort1_start.replace(day=1),
            "cohort2": cohort2_start.replace(day=1)
        })
        data = result.fetchall()

        if not data:
            return {}

        df = pd.DataFrame(data, columns=['cohort_month', 'order_month', 'customers', 'revenue'])
        df['cohort_month'] = pd.to_datetime(df['cohort_month'])
        df['order_month'] = pd.to_datetime(df['order_month'])
        df['period_number'] = ((df['order_month'] - df['cohort_month']).dt.days / 30.44).round().astype(int)

        # Separate cohorts
        cohort1_data = df[df['cohort_month'] == cohort1_start.replace(day=1)]
        cohort2_data = df[df['cohort_month'] == cohort2_start.replace(day=1)]

        comparison = {
            'cohort1': {
                'start_date': cohort1_start.isoformat(),
                'retention': cohort1_data.set_index('period_number')['customers'].to_dict(),
                'revenue': cohort1_data.set_index('period_number')['revenue'].to_dict(),
                'total_customers': int(cohort1_data[cohort1_data['period_number'] == 0]['customers'].sum()),
                'total_revenue': float(cohort1_data['revenue'].sum())
            },
            'cohort2': {
                'start_date': cohort2_start.isoformat(),
                'retention': cohort2_data.set_index('period_number')['customers'].to_dict(),
                'revenue': cohort2_data.set_index('period_number')['revenue'].to_dict(),
                'total_customers': int(cohort2_data[cohort2_data['period_number'] == 0]['customers'].sum()),
                'total_revenue': float(cohort2_data['revenue'].sum())
            }
        }

        # Calculate comparison metrics
        if comparison['cohort1']['total_customers'] > 0 and comparison['cohort2']['total_customers'] > 0:
            retention_improvement = {}
            revenue_improvement = {}

            for period in range(comparison_periods):
                c1_retention = comparison['cohort1']['retention'].get(period, 0)
                c2_retention = comparison['cohort2']['retention'].get(period, 0)
                c1_revenue = comparison['cohort1']['revenue'].get(period, 0)
                c2_revenue = comparison['cohort2']['revenue'].get(period, 0)

                if c1_retention > 0:
                    retention_improvement[period] = ((c2_retention - c1_retention) / c1_retention) * 100

                if c1_revenue > 0:
                    revenue_improvement[period] = ((c2_revenue - c1_revenue) / c1_revenue) * 100

            comparison['improvements'] = {
                'retention_improvement_percentage': retention_improvement,
                'revenue_improvement_percentage': revenue_improvement
            }

        return {
            'comparison': comparison,
            'insights': self._generate_comparison_insights(comparison),
            'calculated_at': datetime.utcnow().isoformat()
        }

    def _generate_retention_insights(self, retention_table: pd.DataFrame, avg_retention: pd.Series) -> list[str]:
        """Generate insights from retention analysis."""
        insights = []

        # Check retention at key periods
        if 1 in avg_retention.index:
            month1_retention = avg_retention[1]
            if month1_retention < 20:
                insights.append(f"Low 1-month retention ({month1_retention:.1f}%) indicates onboarding issues")
            elif month1_retention > 40:
                insights.append(f"Strong 1-month retention ({month1_retention:.1f}%) shows good product-market fit")

        if 3 in avg_retention.index:
            month3_retention = avg_retention[3]
            if month3_retention < 15:
                insights.append(f"Poor 3-month retention ({month3_retention:.1f}%) suggests engagement problems")

        if 6 in avg_retention.index:
            month6_retention = avg_retention[6]
            if month6_retention > 25:
                insights.append(f"Excellent 6-month retention ({month6_retention:.1f}%) indicates strong customer loyalty")

        # Check for improving/declining trends
        if len(avg_retention) >= 3:
            recent_trend = avg_retention.tail(3).diff().mean()
            if recent_trend > 2:
                insights.append("Retention rates are improving over recent cohorts")
            elif recent_trend < -2:
                insights.append("Retention rates are declining - investigate recent changes")

        return insights

    def _generate_revenue_cohort_insights(self, revenue_table: pd.DataFrame, ltv_table: pd.DataFrame) -> list[str]:
        """Generate insights from revenue cohort analysis."""
        insights = []

        # Check LTV progression
        if not ltv_table.empty:
            avg_ltv_6m = ltv_table.iloc[:, :7].iloc[:, -1].mean() if ltv_table.shape[1] >= 7 else 0
            avg_ltv_12m = ltv_table.iloc[:, :13].iloc[:, -1].mean() if ltv_table.shape[1] >= 13 else avg_ltv_6m

            if avg_ltv_12m > avg_ltv_6m * 1.5:
                insights.append(f"Strong LTV growth from 6m (${avg_ltv_6m:.0f}) to 12m (${avg_ltv_12m:.0f})")

        # Check revenue consistency
        if not revenue_table.empty:
            cv = revenue_table.std(axis=0) / revenue_table.mean(axis=0)
            high_variability_periods = cv[cv > 0.5].index.tolist()

            if high_variability_periods:
                insights.append(f"High revenue variability in periods {high_variability_periods}")

        return insights

    def _generate_product_adoption_insights(self, product_adoption: dict) -> list[str]:
        """Generate insights from product adoption analysis."""
        insights = []

        # Find fastest adopting products
        peak_periods = [(product, data['peak_adoption_period'])
                       for product, data in product_adoption.items()]

        if peak_periods:
            fastest_adoption = min(peak_periods, key=lambda x: x[1])
            insights.append(f"Fastest product adoption: {fastest_adoption[0]} (peak at period {fastest_adoption[1]})")

        # Find products with sustained adoption
        sustained_products = [product for product, data in product_adoption.items()
                            if data['peak_adoption_period'] > 3]

        if sustained_products:
            insights.append(f"Products with sustained adoption: {', '.join(sustained_products)}")

        return insights

    def _generate_comparison_insights(self, comparison: dict) -> list[str]:
        """Generate insights from cohort comparison."""
        insights = []

        c1 = comparison['cohort1']
        c2 = comparison['cohort2']

        # Compare overall performance
        if c2['total_revenue'] > c1['total_revenue'] * 1.1:
            insights.append("Newer cohort shows significantly better revenue performance")
        elif c2['total_revenue'] < c1['total_revenue'] * 0.9:
            insights.append("Newer cohort underperforming compared to previous cohort")

        # Check retention improvements
        if 'improvements' in comparison:
            retention_improvements = comparison['improvements']['retention_improvement_percentage']
            positive_periods = [p for p, improvement in retention_improvements.items() if improvement > 10]

            if positive_periods:
                insights.append(f"Strong retention improvements in periods {positive_periods}")

        return insights
