/**
 * Unit tests for AnalyticsService
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import AnalyticsService from '../../../services/AnalyticsService'

// Mock fetch globally
const mockFetch = vi.fn()
global.fetch = mockFetch

// Mock localStorage
const mockLocalStorage = {
  getItem: vi.fn(),
  setItem: vi.fn(),
  removeItem: vi.fn(),
}
Object.defineProperty(window, 'localStorage', {
  value: mockLocalStorage,
})

describe('AnalyticsService', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockLocalStorage.getItem.mockReturnValue('mock-token')
  })

  afterEach(() => {
    vi.resetAllMocks()
  })

  describe('getFinancialSummary', () => {
    it('should return financial summary on successful API call', async () => {
      // Arrange
      const mockData = {
        revenue: {
          today: 1500.50,
          month: 45000.00,
          year: 540000.00,
          growth_rate: 12.5,
          mrr: 38000.00,
          arr: 456000.00,
          revenue_per_visitor: 15.25
        },
        orders: {
          orders_today: 8,
          orders_month: 150,
          pending_orders: 5,
          average_order_value: 95.50
        },
        customers: {
          total_customers: 1200,
          new_customers_month: 85,
          customers_with_orders: 720,
          active_customers_30d: 340,
          customer_conversion_rate: 60.0
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

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockData,
      })

      // Act
      const result = await AnalyticsService.getFinancialSummary()

      // Assert
      expect(result.success).toBe(true)
      expect(result.data).toEqual(mockData)
      expect(mockFetch).toHaveBeenCalledWith(
        '/api/analytics/financial-summary',
        expect.objectContaining({
          method: 'GET',
          headers: expect.objectContaining({
            'Authorization': 'Bearer mock-token',
            'Content-Type': 'application/json',
          }),
        })
      )
    })

    it('should handle API error gracefully', async () => {
      // Arrange
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 500,
        text: async () => 'Internal Server Error',
      })

      // Act
      const result = await AnalyticsService.getFinancialSummary()

      // Assert
      expect(result.success).toBe(false)
      expect(result.error).toContain('HTTP 500')
      expect(result.data).toBeNull()
    })

    it('should handle network error', async () => {
      // Arrange
      mockFetch.mockRejectedValueOnce(new Error('Network error'))

      // Act
      const result = await AnalyticsService.getFinancialSummary()

      // Assert
      expect(result.success).toBe(false)
      expect(result.error).toBe('Network error')
      expect(result.data).toBeNull()
    })

    it('should handle missing auth token', async () => {
      // Arrange
      mockLocalStorage.getItem.mockReturnValue(null)

      // Act
      const result = await AnalyticsService.getFinancialSummary()

      // Assert
      expect(result.success).toBe(false)
      expect(result.error).toBe('No authentication token found')
      expect(mockFetch).not.toHaveBeenCalled()
    })
  })

  describe('getRealtimeMetrics', () => {
    it('should return realtime metrics successfully', async () => {
      // Arrange
      const mockData = {
        current_revenue_today: 2847.50,
        orders_today: 14,
        pending_orders: 6,
        active_carts: 23,
        low_stock_alerts: 3,
        timestamp: new Date().toISOString()
      }

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockData,
      })

      // Act
      const result = await AnalyticsService.getRealtimeMetrics()

      // Assert
      expect(result.success).toBe(true)
      expect(result.data).toEqual(mockData)
      expect(mockFetch).toHaveBeenCalledWith('/api/analytics/realtime-metrics', expect.any(Object))
    })
  })

  describe('getMRR', () => {
    it('should return MRR data successfully', async () => {
      // Arrange
      const mockData = {
        mrr: 38000.00,
        currency: 'USD',
        calculation_date: new Date().toISOString()
      }

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockData,
      })

      // Act
      const result = await AnalyticsService.getMRR()

      // Assert
      expect(result.success).toBe(true)
      expect(result.data).toEqual(mockData)
      expect(mockFetch).toHaveBeenCalledWith('/api/analytics/revenue/mrr', expect.any(Object))
    })
  })

  describe('getARR', () => {
    it('should return ARR data successfully', async () => {
      // Arrange
      const mockData = {
        arr: 456000.00,
        currency: 'USD',
        calculation_date: new Date().toISOString()
      }

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockData,
      })

      // Act
      const result = await AnalyticsService.getARR()

      // Assert
      expect(result.success).toBe(true)
      expect(result.data).toEqual(mockData)
    })
  })

  describe('getConversionRate', () => {
    it('should return conversion rate with default days parameter', async () => {
      // Arrange
      const mockData = {
        conversion_rate_percentage: 3.2,
        analysis_period_days: 30,
        calculation_date: new Date().toISOString()
      }

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockData,
      })

      // Act
      const result = await AnalyticsService.getConversionRate()

      // Assert
      expect(result.success).toBe(true)
      expect(result.data).toEqual(mockData)
      expect(mockFetch).toHaveBeenCalledWith('/api/analytics/conversion/rate?days=30', expect.any(Object))
    })

    it('should return conversion rate with custom days parameter', async () => {
      // Arrange
      const mockData = {
        conversion_rate_percentage: 2.8,
        analysis_period_days: 7,
        calculation_date: new Date().toISOString()
      }

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockData,
      })

      // Act
      const result = await AnalyticsService.getConversionRate(7)

      // Assert
      expect(result.success).toBe(true)
      expect(result.data).toEqual(mockData)
      expect(mockFetch).toHaveBeenCalledWith('/api/analytics/conversion/rate?days=7', expect.any(Object))
    })
  })

  describe('getChurnRate', () => {
    it('should return churn rate with default period', async () => {
      // Arrange
      const mockData = {
        churn_rate_percentage: 8.7,
        retention_rate_percentage: 91.3,
        analysis_period_days: 90,
        calculation_date: new Date().toISOString()
      }

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockData,
      })

      // Act
      const result = await AnalyticsService.getChurnRate()

      // Assert
      expect(result.success).toBe(true)
      expect(result.data).toEqual(mockData)
      expect(mockFetch).toHaveBeenCalledWith('/api/analytics/customers/churn-rate?period_days=90', expect.any(Object))
    })

    it('should return churn rate with custom period', async () => {
      // Arrange
      const mockData = {
        churn_rate_percentage: 12.5,
        retention_rate_percentage: 87.5,
        analysis_period_days: 60,
        calculation_date: new Date().toISOString()
      }

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockData,
      })

      // Act
      const result = await AnalyticsService.getChurnRate(60)

      // Assert
      expect(result.success).toBe(true)
      expect(result.data).toEqual(mockData)
      expect(mockFetch).toHaveBeenCalledWith('/api/analytics/customers/churn-rate?period_days=60', expect.any(Object))
    })
  })

  describe('getAlertSummary', () => {
    it('should return alert summary successfully', async () => {
      // Arrange
      const mockData = {
        total_alerts: 3,
        critical_alerts: 1,
        warning_alerts: 2,
        info_alerts: 0,
        last_checked: new Date().toISOString(),
        alerts: [
          {
            id: 'test-alert-1',
            type: 'inventory_out_of_stock',
            severity: 'critical',
            title: 'Out of Stock Alert',
            description: 'Product XYZ is out of stock',
            data: { affected_products: 1 },
            timestamp: new Date().toISOString(),
            created_at: new Date().toISOString()
          }
        ]
      }

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockData,
      })

      // Act
      const result = await AnalyticsService.getAlertSummary()

      // Assert
      expect(result.success).toBe(true)
      expect(result.data).toEqual(mockData)
      expect(mockFetch).toHaveBeenCalledWith('/api/analytics/alerts/summary', expect.any(Object))
    })
  })

  describe('Fallback methods', () => {
    describe('getFinancialSummaryWithFallback', () => {
      it('should return API data when successful', async () => {
        // Arrange
        const mockData = {
          revenue: { today: 1000, mrr: 5000 },
          orders: { orders_today: 10 },
          customers: { total_customers: 100 },
          inventory: { total_products: 50 },
          conversion: { churn_rate: 5.0 }
        }

        mockFetch.mockResolvedValueOnce({
          ok: true,
          json: async () => mockData,
        })

        // Act
        const result = await AnalyticsService.getFinancialSummaryWithFallback()

        // Assert
        expect(result).toEqual(mockData)
      })

      it('should return mock data when API fails', async () => {
        // Arrange
        mockFetch.mockRejectedValueOnce(new Error('Network error'))
        
        // Mock console.warn to verify it's called
        const consoleSpy = vi.spyOn(console, 'warn').mockImplementation(() => {})

        // Act
        const result = await AnalyticsService.getFinancialSummaryWithFallback()

        // Assert
        expect(result).toEqual(AnalyticsService.getMockFinancialSummary())
        expect(consoleSpy).toHaveBeenCalledWith(
          expect.stringContaining('Failed to fetch financial summary'),
          'Network error'
        )

        consoleSpy.mockRestore()
      })
    })

    describe('getRealtimeMetricsWithFallback', () => {
      it('should return mock data when API fails', async () => {
        // Arrange
        mockFetch.mockResolvedValueOnce({
          ok: false,
          status: 500,
          text: async () => 'Server Error',
        })

        const consoleSpy = vi.spyOn(console, 'warn').mockImplementation(() => {})

        // Act
        const result = await AnalyticsService.getRealtimeMetricsWithFallback()

        // Assert
        const expectedMockData = AnalyticsService.getMockRealtimeMetrics()
        expect(result.current_revenue_today).toBe(expectedMockData.current_revenue_today)
        expect(result.orders_today).toBe(expectedMockData.orders_today)
        expect(result.pending_orders).toBe(expectedMockData.pending_orders)
        expect(result.active_carts).toBe(expectedMockData.active_carts)
        expect(result.low_stock_alerts).toBe(expectedMockData.low_stock_alerts)
        expect(result.timestamp).toBeDefined()
        expect(consoleSpy).toHaveBeenCalled()

        consoleSpy.mockRestore()
      })
    })

    describe('getAlertSummaryWithFallback', () => {
      it('should return mock data when API fails', async () => {
        // Arrange
        mockLocalStorage.getItem.mockReturnValue(null) // No token

        const consoleSpy = vi.spyOn(console, 'warn').mockImplementation(() => {})

        // Act
        const result = await AnalyticsService.getAlertSummaryWithFallback()

        // Assert
        const expectedMockData = AnalyticsService.getMockAlertSummary()
        expect(result.total_alerts).toBe(expectedMockData.total_alerts)
        expect(result.critical_alerts).toBe(expectedMockData.critical_alerts)
        expect(result.warning_alerts).toBe(expectedMockData.warning_alerts)
        expect(result.info_alerts).toBe(expectedMockData.info_alerts)
        expect(result.alerts).toEqual(expectedMockData.alerts)
        expect(result.last_checked).toBeDefined()
        expect(consoleSpy).toHaveBeenCalled()

        consoleSpy.mockRestore()
      })
    })
  })

  describe('Mock data methods', () => {
    it('should return consistent mock financial summary', () => {
      // Act
      const mockData1 = AnalyticsService.getMockFinancialSummary()
      const mockData2 = AnalyticsService.getMockFinancialSummary()

      // Assert
      expect(mockData1).toEqual(mockData2)
      expect(mockData1.revenue.mrr).toBe(38000.00)
      expect(mockData1.revenue.arr).toBe(456000.00)
      expect(mockData1.conversion.churn_rate).toBe(8.7)
    })

    it('should return dynamic mock realtime metrics', () => {
      // Act
      const mockData = AnalyticsService.getMockRealtimeMetrics()

      // Assert
      expect(mockData.current_revenue_today).toBe(2847.50)
      expect(mockData.orders_today).toBe(14)
      expect(mockData.timestamp).toBeDefined()
      expect(new Date(mockData.timestamp)).toBeInstanceOf(Date)
    })

    it('should return mock alert summary with structure', () => {
      // Act
      const mockData = AnalyticsService.getMockAlertSummary()

      // Assert
      expect(mockData.total_alerts).toBe(3)
      expect(mockData.critical_alerts).toBe(1)
      expect(mockData.warning_alerts).toBe(2)
      expect(mockData.alerts).toHaveLength(2)
      expect(mockData.alerts[0]).toHaveProperty('id')
      expect(mockData.alerts[0]).toHaveProperty('severity')
      expect(mockData.alerts[0]).toHaveProperty('title')
    })
  })

  describe('Error handling', () => {
    it('should handle JSON parsing errors', async () => {
      // Arrange
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => {
          throw new Error('Invalid JSON')
        },
      })

      // Act
      const result = await AnalyticsService.getFinancialSummary()

      // Assert
      expect(result.success).toBe(false)
      expect(result.error).toBe('Invalid JSON')
    })

    it('should handle timeout errors gracefully', async () => {
      // Arrange
      const timeoutError = new Error('Request timeout')
      timeoutError.name = 'AbortError'
      mockFetch.mockRejectedValueOnce(timeoutError)

      // Act
      const result = await AnalyticsService.getFinancialSummary()

      // Assert
      expect(result.success).toBe(false)
      expect(result.error).toBe('Request timeout')
    })

    it('should handle malformed API responses', async () => {
      // Arrange
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => null, // Malformed response
      })

      // Act
      const result = await AnalyticsService.getFinancialSummary()

      // Assert
      expect(result.success).toBe(true)
      expect(result.data).toBeNull()
    })
  })

  describe('Request headers', () => {
    it('should include correct authorization header', async () => {
      // Arrange
      mockLocalStorage.getItem.mockReturnValue('test-token-123')
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({}),
      })

      // Act
      await AnalyticsService.getFinancialSummary()

      // Assert
      expect(mockFetch).toHaveBeenCalledWith(
        '/api/analytics/financial-summary',
        expect.objectContaining({
          headers: expect.objectContaining({
            'Authorization': 'Bearer test-token-123',
          }),
        })
      )
    })

    it('should include content-type header', async () => {
      // Arrange
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({}),
      })

      // Act
      await AnalyticsService.getFinancialSummary()

      // Assert
      expect(mockFetch).toHaveBeenCalledWith(
        expect.any(String),
        expect.objectContaining({
          headers: expect.objectContaining({
            'Content-Type': 'application/json',
          }),
        })
      )
    })
  })
})