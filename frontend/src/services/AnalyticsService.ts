// AnalyticsService.ts - Frontend service for analytics API calls

export interface FinancialSummary {
  revenue: {
    today: number
    month: number
    year: number
    growth_rate: number
    mrr: number
    arr: number
    revenue_per_visitor: number
  }
  orders: {
    orders_today: number
    orders_month: number
    pending_orders: number
    average_order_value: number
  }
  customers: {
    total_customers: number
    new_customers_month: number
    customers_with_orders: number
    active_customers_30d: number
    customer_conversion_rate: number
  }
  inventory: {
    total_products: number
    low_stock_products: number
    out_of_stock_products: number
    total_inventory_value: number
  }
  conversion: {
    cart_abandonment_rate: number
    conversion_rate: number
    repeat_customer_rate: number
    churn_rate: number
  }
}

export interface RealtimeMetrics {
  current_revenue_today: number
  orders_today: number
  pending_orders: number
  active_carts: number
  low_stock_alerts: number
  timestamp: string
}

export interface Alert {
  id: string
  type: string
  severity: 'info' | 'warning' | 'critical'
  title: string
  description: string
  data: Record<string, any>
  timestamp: string
  created_at: string
}

export interface AlertSummary {
  total_alerts: number
  critical_alerts: number
  warning_alerts: number
  info_alerts: number
  last_checked: string
  alerts: Alert[]
}

export interface ApiResponse<T> {
  data: T
  success: boolean
  error?: string
}

class AnalyticsService {
  private static readonly BASE_URL = '/api/analytics'

  private static async makeRequest<T>(endpoint: string): Promise<ApiResponse<T>> {
    try {
      const token = localStorage.getItem('access_token')
      if (!token) {
        throw new Error('No authentication token found')
      }

      const response = await fetch(`${this.BASE_URL}${endpoint}`, {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      })

      if (!response.ok) {
        const errorText = await response.text()
        throw new Error(`HTTP ${response.status}: ${errorText}`)
      }

      const data = await response.json()
      return { data, success: true }
    } catch (error) {
      console.error(`Analytics API Error [${endpoint}]:`, error)
      return { 
        data: null as T, 
        success: false, 
        error: error instanceof Error ? error.message : 'Unknown error'
      }
    }
  }

  /**
   * Get comprehensive financial summary
   */
  static async getFinancialSummary(): Promise<ApiResponse<FinancialSummary>> {
    return this.makeRequest<FinancialSummary>('/financial-summary')
  }

  /**
   * Get real-time metrics
   */
  static async getRealtimeMetrics(): Promise<ApiResponse<RealtimeMetrics>> {
    return this.makeRequest<RealtimeMetrics>('/realtime-metrics')
  }

  /**
   * Get alert summary
   */
  static async getAlertSummary(): Promise<ApiResponse<AlertSummary>> {
    return this.makeRequest<AlertSummary>('/alerts/summary')
  }

  /**
   * Get all current alerts
   */
  static async getAllAlerts(): Promise<ApiResponse<{ alerts: Alert[], total_count: number, timestamp: string }>> {
    return this.makeRequest('/alerts/all')
  }

  /**
   * Get Monthly Recurring Revenue
   */
  static async getMRR(): Promise<ApiResponse<{ mrr: number, currency: string, calculation_date: string }>> {
    return this.makeRequest('/revenue/mrr')
  }

  /**
   * Get Annual Recurring Revenue
   */
  static async getARR(): Promise<ApiResponse<{ arr: number, currency: string, calculation_date: string }>> {
    return this.makeRequest('/revenue/arr')
  }

  /**
   * Get conversion rate
   */
  static async getConversionRate(days: number = 30): Promise<ApiResponse<{ 
    conversion_rate_percentage: number
    analysis_period_days: number
    calculation_date: string 
  }>> {
    return this.makeRequest(`/conversion/rate?days=${days}`)
  }

  /**
   * Get repeat customer rate
   */
  static async getRepeatCustomerRate(days: number = 30): Promise<ApiResponse<{ 
    repeat_customer_rate_percentage: number
    analysis_period_days: number
    calculation_date: string 
  }>> {
    return this.makeRequest(`/customers/repeat-rate?days=${days}`)
  }

  /**
   * Get churn rate
   */
  static async getChurnRate(periodDays: number = 90): Promise<ApiResponse<{ 
    churn_rate_percentage: number
    retention_rate_percentage: number
    analysis_period_days: number
    calculation_date: string 
  }>> {
    return this.makeRequest(`/customers/churn-rate?period_days=${periodDays}`)
  }

  /**
   * Get revenue per visitor
   */
  static async getRevenuePerVisitor(days: number = 30): Promise<ApiResponse<{ 
    revenue_per_visitor: number
    currency: string
    analysis_period_days: number
    calculation_date: string 
  }>> {
    return this.makeRequest(`/revenue/per-visitor?days=${days}`)
  }

  /**
   * Get revenue growth rate
   */
  static async getRevenueGrowthRate(periodDays: number = 30): Promise<ApiResponse<{ 
    growth_rate_percentage: number
    period_days: number
    comparison_periods: string 
  }>> {
    return this.makeRequest(`/revenue/growth-rate?period_days=${periodDays}`)
  }

  /**
   * Get top selling products
   */
  static async getTopSellingProducts(limit: number = 10): Promise<ApiResponse<{ 
    top_products: Array<{
      product_id: number
      name: string
      sku: string
      total_sold: number
      total_revenue: number
    }>
    limit: number
    total_returned: number 
  }>> {
    return this.makeRequest(`/products/top-selling?limit=${limit}`)
  }

  /**
   * Mock data for development/fallback
   */
  static getMockFinancialSummary(): FinancialSummary {
    return {
      revenue: {
        today: 2500.00,
        month: 45000.00,
        year: 350000.00,
        growth_rate: 15.2,
        mrr: 38000.00,
        arr: 456000.00,
        revenue_per_visitor: 12.50
      },
      orders: {
        orders_today: 12,
        orders_month: 180,
        pending_orders: 8,
        average_order_value: 85.50
      },
      customers: {
        total_customers: 1250,
        new_customers_month: 95,
        customers_with_orders: 780,
        active_customers_30d: 320,
        customer_conversion_rate: 62.4
      },
      inventory: {
        total_products: 45,
        low_stock_products: 3,
        out_of_stock_products: 1,
        total_inventory_value: 125000.00
      },
      conversion: {
        cart_abandonment_rate: 28.5,
        conversion_rate: 3.2,
        repeat_customer_rate: 42.1,
        churn_rate: 8.7
      }
    }
  }

  static getMockRealtimeMetrics(): RealtimeMetrics {
    return {
      current_revenue_today: 2847.50,
      orders_today: 14,
      pending_orders: 6,
      active_carts: 23,
      low_stock_alerts: 3,
      timestamp: new Date().toISOString()
    }
  }

  static getMockAlertSummary(): AlertSummary {
    return {
      total_alerts: 3,
      critical_alerts: 1,
      warning_alerts: 2,
      info_alerts: 0,
      last_checked: new Date().toISOString(),
      alerts: [
        {
          id: 'inventory_out_of_stock_1',
          type: 'inventory_out_of_stock',
          severity: 'critical',
          title: 'Out of Stock Alert - 1 Product',
          description: 'Whey Protein Gold Standard is out of stock',
          data: { affected_products: 1 },
          timestamp: new Date().toISOString(),
          created_at: new Date().toISOString()
        },
        {
          id: 'inventory_low_stock_2',
          type: 'inventory_low_stock',
          severity: 'warning',
          title: 'Low Stock Alert - 3 Products',
          description: 'Multiple products are running low on stock',
          data: { affected_products: 3 },
          timestamp: new Date().toISOString(),
          created_at: new Date().toISOString()
        }
      ]
    }
  }

  /**
   * Get financial summary with fallback
   */
  static async getFinancialSummaryWithFallback(): Promise<FinancialSummary> {
    const response = await this.getFinancialSummary()
    
    if (response.success && response.data) {
      return response.data
    }
    
    console.warn('Failed to fetch financial summary, using mock data:', response.error)
    return this.getMockFinancialSummary()
  }

  /**
   * Get realtime metrics with fallback
   */
  static async getRealtimeMetricsWithFallback(): Promise<RealtimeMetrics> {
    const response = await this.getRealtimeMetrics()
    
    if (response.success && response.data) {
      return response.data
    }
    
    console.warn('Failed to fetch realtime metrics, using mock data:', response.error)
    return this.getMockRealtimeMetrics()
  }

  /**
   * Get alert summary with fallback
   */
  static async getAlertSummaryWithFallback(): Promise<AlertSummary> {
    const response = await this.getAlertSummary()
    
    if (response.success && response.data) {
      return response.data
    }
    
    console.warn('Failed to fetch alerts, using mock data:', response.error)
    return this.getMockAlertSummary()
  }
}

export default AnalyticsService