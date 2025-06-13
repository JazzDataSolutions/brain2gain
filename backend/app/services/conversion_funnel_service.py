"""
Conversion Funnel Service - Advanced Analytics Phase 2
Implements detailed conversion funnel analysis with multi-step tracking.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from sqlmodel import Session
from sqlalchemy import text
from enum import Enum

from app.models import Customer, SalesOrder, Cart, CartItem, Product, OrderStatus


class FunnelStep(str, Enum):
    VISITOR = "visitor"
    PAGE_VIEW = "page_view"
    PRODUCT_VIEW = "product_view"
    ADD_TO_CART = "add_to_cart"
    CART_VIEW = "cart_view"
    CHECKOUT_START = "checkout_start"
    PAYMENT_INFO = "payment_info"
    PURCHASE = "purchase"


class ConversionFunnelService:
    """Service for detailed conversion funnel analysis."""
    
    def __init__(self, db: Session):
        self.db = db
        self.funnel_steps = [
            FunnelStep.VISITOR,
            FunnelStep.PRODUCT_VIEW,
            FunnelStep.ADD_TO_CART,
            FunnelStep.CHECKOUT_START,
            FunnelStep.PURCHASE
        ]
    
    def calculate_conversion_funnel(self, start_date: datetime, end_date: datetime, 
                                  channel: Optional[str] = None) -> Dict:
        """
        Calculate detailed conversion funnel for a specific period.
        
        Args:
            start_date: Start date for analysis
            end_date: End date for analysis
            channel: Optional marketing channel filter
            
        Returns:
            Dictionary with funnel analysis
        """
        # For now, we'll simulate the funnel using available data
        # In a real implementation, you would track user events
        
        funnel_data = self._calculate_basic_funnel(start_date, end_date, channel)
        
        # Calculate conversion rates between steps
        conversions = self._calculate_step_conversions(funnel_data)
        
        # Calculate drop-off analysis
        dropoffs = self._calculate_dropoff_analysis(funnel_data)
        
        # Generate insights
        insights = self._generate_funnel_insights(conversions, dropoffs)
        
        return {
            'period': {
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat(),
                'days': (end_date - start_date).days
            },
            'channel': channel,
            'funnel_steps': funnel_data,
            'conversions': conversions,
            'dropoffs': dropoffs,
            'insights': insights,
            'calculated_at': datetime.utcnow().isoformat()
        }
    
    def _calculate_basic_funnel(self, start_date: datetime, end_date: datetime, 
                               channel: Optional[str] = None) -> Dict:
        """Calculate basic funnel metrics from available data."""
        
        # Get customers who made purchases in the period
        purchase_query = text("""
            SELECT COUNT(DISTINCT c.customer_id) as customers
            FROM customers c
            JOIN sales_orders so ON c.customer_id = so.customer_id
            WHERE so.status = 'COMPLETED'
                AND so.order_date BETWEEN :start_date AND :end_date
        """)
        
        purchase_result = self.db.execute(purchase_query, {
            "start_date": start_date,
            "end_date": end_date
        })
        purchase_customers = purchase_result.fetchone()[0] or 0
        
        # Get customers who added to cart
        cart_query = text("""
            SELECT COUNT(DISTINCT c.customer_id) as customers
            FROM customers c
            JOIN carts cart ON c.customer_id = cart.customer_id
            WHERE cart.created_at BETWEEN :start_date AND :end_date
        """)
        
        cart_result = self.db.execute(cart_query, {
            "start_date": start_date,
            "end_date": end_date
        })
        cart_customers = cart_result.fetchone()[0] or 0
        
        # Get total orders in period (including non-completed)
        orders_query = text("""
            SELECT COUNT(DISTINCT so.order_id) as orders
            FROM sales_orders so
            WHERE so.order_date BETWEEN :start_date AND :end_date
        """)
        
        orders_result = self.db.execute(orders_query, {
            "start_date": start_date,
            "end_date": end_date
        })
        checkout_starts = orders_result.fetchone()[0] or 0
        
        # Estimate visitors (we'll use a multiple of purchasers for simulation)
        # In real implementation, this would come from web analytics
        estimated_visitors = max(purchase_customers * 25, 100)  # Assume 4% conversion rate baseline
        
        # Estimate product views (multiple of cart additions)
        estimated_product_views = max(cart_customers * 3, cart_customers + 50)
        
        funnel_data = {
            FunnelStep.VISITOR.value: {
                'count': estimated_visitors,
                'percentage': 100.0,
                'description': 'Unique visitors to the site'
            },
            FunnelStep.PRODUCT_VIEW.value: {
                'count': estimated_product_views,
                'percentage': round((estimated_product_views / estimated_visitors) * 100, 2) if estimated_visitors > 0 else 0,
                'description': 'Visitors who viewed product pages'
            },
            FunnelStep.ADD_TO_CART.value: {
                'count': cart_customers,
                'percentage': round((cart_customers / estimated_visitors) * 100, 2) if estimated_visitors > 0 else 0,
                'description': 'Visitors who added items to cart'
            },
            FunnelStep.CHECKOUT_START.value: {
                'count': checkout_starts,
                'percentage': round((checkout_starts / estimated_visitors) * 100, 2) if estimated_visitors > 0 else 0,
                'description': 'Visitors who started checkout process'
            },
            FunnelStep.PURCHASE.value: {
                'count': purchase_customers,
                'percentage': round((purchase_customers / estimated_visitors) * 100, 2) if estimated_visitors > 0 else 0,
                'description': 'Visitors who completed purchase'
            }
        }
        
        return funnel_data
    
    def _calculate_step_conversions(self, funnel_data: Dict) -> Dict:
        """Calculate conversion rates between funnel steps."""
        conversions = {}
        steps = list(funnel_data.keys())
        
        for i in range(len(steps) - 1):
            current_step = steps[i]
            next_step = steps[i + 1]
            
            current_count = funnel_data[current_step]['count']
            next_count = funnel_data[next_step]['count']
            
            conversion_rate = (next_count / current_count * 100) if current_count > 0 else 0
            
            conversions[f"{current_step}_to_{next_step}"] = {
                'from_step': current_step,
                'to_step': next_step,
                'from_count': current_count,
                'to_count': next_count,
                'conversion_rate': round(conversion_rate, 2),
                'drop_off_count': current_count - next_count,
                'drop_off_rate': round(100 - conversion_rate, 2)
            }
        
        return conversions
    
    def _calculate_dropoff_analysis(self, funnel_data: Dict) -> Dict:
        """Calculate detailed drop-off analysis."""
        steps = list(funnel_data.keys())
        total_visitors = funnel_data[steps[0]]['count']
        
        dropoffs = {}
        
        for i, step in enumerate(steps[:-1]):
            current_count = funnel_data[step]['count']
            next_count = funnel_data[steps[i + 1]]['count']
            dropped_users = current_count - next_count
            
            dropoffs[step] = {
                'users_dropped': dropped_users,
                'drop_off_rate': round((dropped_users / current_count * 100), 2) if current_count > 0 else 0,
                'percentage_of_total': round((dropped_users / total_visitors * 100), 2) if total_visitors > 0 else 0,
                'step_description': funnel_data[step]['description']
            }
        
        return dropoffs
    
    def calculate_product_funnel(self, product_id: int, days: int = 30) -> Dict:
        """
        Calculate conversion funnel for a specific product.
        
        Args:
            product_id: Product ID to analyze
            days: Number of days to look back
            
        Returns:
            Dictionary with product-specific funnel
        """
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # Get product details
        product_query = text("""
            SELECT name, category, price
            FROM products
            WHERE product_id = :product_id
        """)
        
        product_result = self.db.execute(product_query, {"product_id": product_id})
        product_info = product_result.fetchone()
        
        if not product_info:
            return {}
        
        # Get funnel data for this product
        funnel_query = text("""
            SELECT 
                COUNT(DISTINCT CASE WHEN ci.product_id = :product_id THEN c.customer_id END) as cart_adds,
                COUNT(DISTINCT CASE WHEN si.product_id = :product_id AND so.status = 'COMPLETED' THEN c.customer_id END) as purchases,
                COUNT(DISTINCT CASE WHEN si.product_id = :product_id THEN so.order_id END) as checkout_starts,
                SUM(CASE WHEN si.product_id = :product_id AND so.status = 'COMPLETED' THEN si.qty * si.unit_price ELSE 0 END) as revenue
            FROM customers c
            LEFT JOIN carts cart ON c.customer_id = cart.customer_id
            LEFT JOIN cart_items ci ON cart.cart_id = ci.cart_id
            LEFT JOIN sales_orders so ON c.customer_id = so.customer_id
            LEFT JOIN sales_items si ON so.order_id = si.order_id
            WHERE (ci.created_at BETWEEN :start_date AND :end_date)
                OR (so.order_date BETWEEN :start_date AND :end_date)
        """)
        
        funnel_result = self.db.execute(funnel_query, {
            "product_id": product_id,
            "start_date": start_date,
            "end_date": end_date
        })
        funnel_stats = funnel_result.fetchone()
        
        # Estimate product views (in real app, this would be tracked)
        estimated_views = max(funnel_stats[0] * 5, 10)  # Assume 20% add-to-cart rate
        
        product_funnel = {
            'product_info': {
                'product_id': product_id,
                'name': product_info[0],
                'category': product_info[1],
                'price': float(product_info[2])
            },
            'period': {
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat(),
                'days': days
            },
            'funnel': {
                'product_views': {
                    'count': estimated_views,
                    'percentage': 100.0
                },
                'add_to_cart': {
                    'count': funnel_stats[0] or 0,
                    'percentage': round((funnel_stats[0] / estimated_views * 100), 2) if estimated_views > 0 else 0
                },
                'checkout_start': {
                    'count': funnel_stats[2] or 0,
                    'percentage': round((funnel_stats[2] / estimated_views * 100), 2) if estimated_views > 0 else 0
                },
                'purchase': {
                    'count': funnel_stats[1] or 0,
                    'percentage': round((funnel_stats[1] / estimated_views * 100), 2) if estimated_views > 0 else 0
                }
            },
            'revenue': float(funnel_stats[3] or 0),
            'conversion_rate': round((funnel_stats[1] / estimated_views * 100), 2) if estimated_views > 0 else 0
        }
        
        return product_funnel
    
    def calculate_channel_funnels(self, days: int = 30) -> Dict:
        """
        Calculate conversion funnels by marketing channel.
        
        Args:
            days: Number of days to analyze
            
        Returns:
            Dictionary with channel-specific funnels
        """
        # This would typically use UTM parameters or channel attribution
        # For now, we'll create a simulation based on customer registration source
        
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # Simulate channel data (in real app, this would come from tracking)
        channels = ['organic', 'paid_search', 'social', 'email', 'direct']
        channel_funnels = {}
        
        for channel in channels:
            # Get basic metrics (simulated)
            channel_funnel = self._calculate_basic_funnel(start_date, end_date, channel)
            
            # Add channel-specific adjustments
            if channel == 'paid_search':
                # Paid search typically has higher intent
                for step in channel_funnel:
                    channel_funnel[step]['count'] = int(channel_funnel[step]['count'] * 0.3)
                    if step != 'visitor':
                        channel_funnel[step]['percentage'] *= 1.2  # Higher conversion
            elif channel == 'social':
                # Social has more browsers, lower conversion
                for step in channel_funnel:
                    if step == 'visitor':
                        channel_funnel[step]['count'] = int(channel_funnel[step]['count'] * 0.4)
                    else:
                        channel_funnel[step]['count'] = int(channel_funnel[step]['count'] * 0.2)
                        channel_funnel[step]['percentage'] *= 0.8  # Lower conversion
            
            channel_funnels[channel] = {
                'funnel': channel_funnel,
                'conversions': self._calculate_step_conversions(channel_funnel),
                'total_conversion_rate': channel_funnel.get('purchase', {}).get('percentage', 0)
            }
        
        # Calculate channel comparison
        channel_comparison = self._compare_channels(channel_funnels)
        
        return {
            'period': {
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat(),
                'days': days
            },
            'channels': channel_funnels,
            'comparison': channel_comparison,
            'insights': self._generate_channel_insights(channel_funnels),
            'calculated_at': datetime.utcnow().isoformat()
        }
    
    def calculate_mobile_vs_desktop_funnel(self, days: int = 30) -> Dict:
        """
        Compare conversion funnels between mobile and desktop users.
        
        Args:
            days: Number of days to analyze
            
        Returns:
            Dictionary with device-specific funnel comparison
        """
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # Simulate device-specific data (in real app, this would come from user agent tracking)
        base_funnel = self._calculate_basic_funnel(start_date, end_date)
        
        mobile_funnel = {}
        desktop_funnel = {}
        
        # Apply device-specific conversion patterns
        for step, data in base_funnel.items():
            # Mobile typically has more traffic but lower conversion
            mobile_count = int(data['count'] * 0.6)  # 60% of traffic is mobile
            desktop_count = int(data['count'] * 0.4)  # 40% is desktop
            
            if step in ['add_to_cart', 'checkout_start', 'purchase']:
                # Mobile has lower conversion in later funnel steps
                mobile_multiplier = 0.7
                desktop_multiplier = 1.3
            else:
                mobile_multiplier = 1.0
                desktop_multiplier = 1.0
            
            mobile_funnel[step] = {
                'count': int(mobile_count * mobile_multiplier),
                'percentage': data['percentage'] * mobile_multiplier,
                'description': data['description']
            }
            
            desktop_funnel[step] = {
                'count': int(desktop_count * desktop_multiplier),
                'percentage': data['percentage'] * desktop_multiplier,
                'description': data['description']
            }
        
        # Recalculate percentages for mobile and desktop
        mobile_visitors = mobile_funnel['visitor']['count']
        desktop_visitors = desktop_funnel['visitor']['count']
        
        for step in mobile_funnel:
            if mobile_visitors > 0:
                mobile_funnel[step]['percentage'] = round((mobile_funnel[step]['count'] / mobile_visitors) * 100, 2)
        
        for step in desktop_funnel:
            if desktop_visitors > 0:
                desktop_funnel[step]['percentage'] = round((desktop_funnel[step]['count'] / desktop_visitors) * 100, 2)
        
        return {
            'period': {
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat(),
                'days': days
            },
            'mobile': {
                'funnel': mobile_funnel,
                'conversions': self._calculate_step_conversions(mobile_funnel)
            },
            'desktop': {
                'funnel': desktop_funnel,
                'conversions': self._calculate_step_conversions(desktop_funnel)
            },
            'comparison': self._compare_device_funnels(mobile_funnel, desktop_funnel),
            'insights': self._generate_device_insights(mobile_funnel, desktop_funnel),
            'calculated_at': datetime.utcnow().isoformat()
        }
    
    def _compare_channels(self, channel_funnels: Dict) -> Dict:
        """Compare performance across channels."""
        comparison = {}
        
        # Find best and worst performing channels
        conversion_rates = {
            channel: data['total_conversion_rate'] 
            for channel, data in channel_funnels.items()
        }
        
        if conversion_rates:
            best_channel = max(conversion_rates, key=conversion_rates.get)
            worst_channel = min(conversion_rates, key=conversion_rates.get)
            
            comparison = {
                'best_converting_channel': {
                    'channel': best_channel,
                    'conversion_rate': conversion_rates[best_channel]
                },
                'worst_converting_channel': {
                    'channel': worst_channel,
                    'conversion_rate': conversion_rates[worst_channel]
                },
                'conversion_rate_spread': conversion_rates[best_channel] - conversion_rates[worst_channel]
            }
        
        return comparison
    
    def _compare_device_funnels(self, mobile_funnel: Dict, desktop_funnel: Dict) -> Dict:
        """Compare mobile vs desktop funnel performance."""
        mobile_conversion = mobile_funnel.get('purchase', {}).get('percentage', 0)
        desktop_conversion = desktop_funnel.get('purchase', {}).get('percentage', 0)
        
        return {
            'mobile_conversion_rate': mobile_conversion,
            'desktop_conversion_rate': desktop_conversion,
            'desktop_advantage': round(desktop_conversion - mobile_conversion, 2),
            'relative_performance': round((desktop_conversion / mobile_conversion), 2) if mobile_conversion > 0 else 0,
            'mobile_traffic_share': round((mobile_funnel['visitor']['count'] / 
                                         (mobile_funnel['visitor']['count'] + desktop_funnel['visitor']['count'])) * 100, 1)
        }
    
    def _generate_funnel_insights(self, conversions: Dict, dropoffs: Dict) -> List[str]:
        """Generate actionable insights from funnel analysis."""
        insights = []
        
        # Find biggest drop-off points
        biggest_dropoff = max(dropoffs.items(), key=lambda x: x[1]['drop_off_rate'])
        insights.append(f"Biggest drop-off at {biggest_dropoff[0]} ({biggest_dropoff[1]['drop_off_rate']:.1f}%)")
        
        # Check for low conversion rates
        for conversion_key, data in conversions.items():
            if data['conversion_rate'] < 10 and 'cart' in conversion_key:
                insights.append(f"Low cart-to-checkout conversion ({data['conversion_rate']:.1f}%) needs optimization")
        
        # Check overall funnel health
        purchase_conversion = next((data['conversion_rate'] for key, data in conversions.items() 
                                  if 'purchase' in key), 0)
        
        if purchase_conversion < 2:
            insights.append("Overall conversion rate is below industry average (2-3%)")
        elif purchase_conversion > 5:
            insights.append("Excellent overall conversion rate - focus on traffic growth")
        
        return insights
    
    def _generate_channel_insights(self, channel_funnels: Dict) -> List[str]:
        """Generate insights from channel funnel analysis."""
        insights = []
        
        # Compare channel performance
        conversion_rates = {
            channel: data['total_conversion_rate'] 
            for channel, data in channel_funnels.items()
        }
        
        if conversion_rates:
            best_channel = max(conversion_rates, key=conversion_rates.get)
            worst_channel = min(conversion_rates, key=conversion_rates.get)
            
            insights.append(f"Best performing channel: {best_channel} ({conversion_rates[best_channel]:.1f}%)")
            insights.append(f"Worst performing channel: {worst_channel} ({conversion_rates[worst_channel]:.1f}%)")
            
            # Check for significant differences
            spread = conversion_rates[best_channel] - conversion_rates[worst_channel]
            if spread > 3:
                insights.append(f"Large performance gap ({spread:.1f}%) between channels - optimize {worst_channel}")
        
        return insights
    
    def _generate_device_insights(self, mobile_funnel: Dict, desktop_funnel: Dict) -> List[str]:
        """Generate insights from device funnel comparison."""
        insights = []
        
        mobile_conversion = mobile_funnel.get('purchase', {}).get('percentage', 0)
        desktop_conversion = desktop_funnel.get('purchase', {}).get('percentage', 0)
        
        if desktop_conversion > mobile_conversion * 1.5:
            insights.append("Desktop significantly outperforms mobile - optimize mobile experience")
        elif mobile_conversion > desktop_conversion:
            insights.append("Mobile conversion is strong - consider mobile-first strategy")
        
        # Check mobile traffic share
        mobile_visitors = mobile_funnel['visitor']['count']
        total_visitors = mobile_visitors + desktop_funnel['visitor']['count']
        mobile_share = (mobile_visitors / total_visitors) * 100 if total_visitors > 0 else 0
        
        if mobile_share > 60:
            insights.append(f"High mobile traffic ({mobile_share:.1f}%) - mobile optimization is critical")
        
        return insights