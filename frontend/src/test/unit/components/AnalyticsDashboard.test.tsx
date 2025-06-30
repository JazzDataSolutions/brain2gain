/**
 * Component tests for AnalyticsDashboard
 */

import { ChakraProvider } from "@chakra-ui/react"
import { act, fireEvent, render, screen, waitFor } from "@testing-library/react"
import type React from "react"
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest"
import AnalyticsDashboard from "../../../components/Admin/AnalyticsDashboard"
import AnalyticsService from "../../../services/AnalyticsService"

// Mock the AnalyticsService completely to avoid fetch calls
vi.mock("../../../services/AnalyticsService", () => ({
  default: {
    getFinancialSummaryWithFallback: vi.fn(),
    getRealtimeMetricsWithFallback: vi.fn(),
    getAlertSummaryWithFallback: vi.fn(),
    getRFMData: vi.fn(),
    getCohortData: vi.fn(),
    getCustomerSegmentData: vi.fn(),
    getAdvancedMetrics: vi.fn(),
  },
}))

// Mock fetch globally to prevent network calls
const mockFetch = vi.fn()
global.fetch = mockFetch

// Mock localStorage
const mockLocalStorage = {
  getItem: vi.fn(() => "mock-token"),
  setItem: vi.fn(),
  removeItem: vi.fn(),
  clear: vi.fn(),
}
Object.defineProperty(window, "localStorage", { value: mockLocalStorage })

// Mock useToast hook
const mockToast = vi.fn()
vi.mock("@chakra-ui/react", async () => {
  const actual = await vi.importActual("@chakra-ui/react")
  return {
    ...actual,
    useToast: () => mockToast,
  }
})

// Wrapper component for Chakra UI
const TestWrapper: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <ChakraProvider>{children}</ChakraProvider>
)

describe("AnalyticsDashboard", () => {
  const mockFinancialData = {
    revenue: {
      today: 2500.0,
      month: 45000.0,
      year: 350000.0,
      growth_rate: 15.2,
      mrr: 38000.0,
      arr: 456000.0,
      revenue_per_visitor: 12.5,
    },
    orders: {
      orders_today: 12,
      orders_month: 180,
      pending_orders: 8,
      average_order_value: 85.5,
    },
    customers: {
      total_customers: 1250,
      new_customers_month: 95,
      customers_with_orders: 780,
      active_customers_30d: 320,
      customer_conversion_rate: 62.4,
    },
    inventory: {
      total_products: 45,
      low_stock_products: 3,
      out_of_stock_products: 1,
      total_inventory_value: 125000.0,
    },
    conversion: {
      cart_abandonment_rate: 28.5,
      conversion_rate: 3.2,
      repeat_customer_rate: 42.1,
      churn_rate: 8.7,
    },
  }

  const mockRealtimeData = {
    current_revenue_today: 2847.5,
    orders_today: 14,
    pending_orders: 6,
    active_carts: 23,
    low_stock_alerts: 3,
    timestamp: new Date().toISOString(),
  }

  const mockAlertsData = {
    total_alerts: 3,
    critical_alerts: 1,
    warning_alerts: 2,
    info_alerts: 0,
    last_checked: new Date().toISOString(),
    alerts: [
      {
        id: "test-alert-1",
        type: "inventory_out_of_stock",
        severity: "critical",
        title: "Out of Stock Alert - 1 Product",
        description: "Whey Protein Gold Standard is out of stock",
        data: { affected_products: 1 },
        timestamp: new Date().toISOString(),
        created_at: new Date().toISOString(),
      },
      {
        id: "test-alert-2",
        type: "inventory_low_stock",
        severity: "warning",
        title: "Low Stock Alert - 3 Products",
        description: "Multiple products are running low on stock",
        data: { affected_products: 3 },
        timestamp: new Date().toISOString(),
        created_at: new Date().toISOString(),
      },
    ],
  }

  beforeEach(() => {
    vi.clearAllMocks()

    // Setup default mocks for AnalyticsService
    vi.mocked(
      AnalyticsService.getFinancialSummaryWithFallback,
    ).mockResolvedValue(mockFinancialData)
    vi.mocked(
      AnalyticsService.getRealtimeMetricsWithFallback,
    ).mockResolvedValue(mockRealtimeData)
    vi.mocked(AnalyticsService.getAlertSummaryWithFallback).mockResolvedValue(
      mockAlertsData,
    )

    // Setup default fetch mocks for direct API calls in component
    mockFetch.mockImplementation((url: string) => {
      if (url.includes("/analytics/segmentation/rfm")) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({ rfm_segments: [] }),
        })
      }
      if (url.includes("/analytics/cohorts/retention")) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({ cohort_data: [] }),
        })
      }
      if (url.includes("/analytics/funnel/conversion")) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({ funnel_data: [] }),
        })
      }
      return Promise.reject(new Error(`Unhandled fetch call to ${url}`))
    })
  })

  afterEach(() => {
    vi.resetAllMocks()
  })

  describe("Initial render and loading", () => {
    it("should show loading spinner initially", async () => {
      // Arrange - make promises never resolve to keep loading state
      vi.mocked(
        AnalyticsService.getFinancialSummaryWithFallback,
      ).mockImplementation(
        () => new Promise(() => {}), // Never resolves
      )
      vi.mocked(
        AnalyticsService.getRealtimeMetricsWithFallback,
      ).mockImplementation(
        () => new Promise(() => {}), // Never resolves
      )
      vi.mocked(
        AnalyticsService.getAlertSummaryWithFallback,
      ).mockImplementation(
        () => new Promise(() => {}), // Never resolves
      )

      // Act
      await act(async () => {
        render(
          <TestWrapper>
            <AnalyticsDashboard />
          </TestWrapper>,
        )
      })

      // Assert
      expect(
        screen.getByText("Loading analytics dashboard..."),
      ).toBeInTheDocument()
      expect(screen.getByTestId("loading-spinner")).toBeInTheDocument()
    })

    it("should load and display dashboard data", async () => {
      // Act
      await act(async () => {
        render(
          <TestWrapper>
            <AnalyticsDashboard />
          </TestWrapper>,
        )
      })

      // Assert
      await waitFor(() => {
        expect(screen.getByText("Analytics Dashboard")).toBeInTheDocument()
      })

      // Check that financial data is displayed
      await waitFor(() => {
        expect(screen.getByText("$2,500")).toBeInTheDocument() // Today's revenue
        expect(screen.getByText("$45,000")).toBeInTheDocument() // Monthly revenue
        expect(screen.getAllByText("$38,000")[0]).toBeInTheDocument() // MRR
        expect(screen.getByText("$456,000")).toBeInTheDocument() // ARR
      })
    })

    it("should call all data fetching methods on mount", async () => {
      // Act
      render(
        <TestWrapper>
          <AnalyticsDashboard />
        </TestWrapper>,
      )

      // Assert
      await waitFor(() => {
        expect(
          AnalyticsService.getFinancialSummaryWithFallback,
        ).toHaveBeenCalledTimes(1)
        expect(
          AnalyticsService.getRealtimeMetricsWithFallback,
        ).toHaveBeenCalledTimes(1)
        expect(
          AnalyticsService.getAlertSummaryWithFallback,
        ).toHaveBeenCalledTimes(1)
      })
    })
  })

  describe("Revenue Overview section", () => {
    it("should display all revenue metrics correctly", async () => {
      // Act
      render(
        <TestWrapper>
          <AnalyticsDashboard />
        </TestWrapper>,
      )

      // Assert
      await waitFor(() => {
        // Check basic revenue metrics
        expect(screen.getByText("Today's Revenue")).toBeInTheDocument()
        expect(screen.getByText("Monthly Revenue")).toBeInTheDocument()
        expect(screen.getByText("MRR")).toBeInTheDocument()
        expect(screen.getByText("ARR")).toBeInTheDocument()
        expect(screen.getByText("Average Order Value")).toBeInTheDocument()
        expect(screen.getByText("Revenue Per Visitor")).toBeInTheDocument()

        // Check values - use getAllByText for values that might appear multiple times
        expect(screen.getByText("$2,500")).toBeInTheDocument()
        expect(screen.getByText("$45,000")).toBeInTheDocument()
        expect(screen.getAllByText("$38,000")[0]).toBeInTheDocument()
        expect(screen.getByText("$456,000")).toBeInTheDocument()
        expect(screen.getByText("$86")).toBeInTheDocument() // AOV
        expect(screen.getByText("$13")).toBeInTheDocument() // RPV
      })
    })

    it("should show growth indicators correctly", async () => {
      // Act
      render(
        <TestWrapper>
          <AnalyticsDashboard />
        </TestWrapper>,
      )

      // Assert
      await waitFor(() => {
        expect(screen.getByText("15.2% growth")).toBeInTheDocument()
      })
    })
  })

  describe("KPI Summary Cards section", () => {
    it("should display MRR Growth card with correct data", async () => {
      // Act
      render(
        <TestWrapper>
          <AnalyticsDashboard />
        </TestWrapper>,
      )

      // Assert
      await waitFor(() => {
        expect(screen.getByText("MRR Growth")).toBeInTheDocument()
        expect(screen.getByText("Projected ARR: $456,000")).toBeInTheDocument()
      })
    })

    it("should display Customer Health card with churn indicators", async () => {
      // Act
      render(
        <TestWrapper>
          <AnalyticsDashboard />
        </TestWrapper>,
      )

      // Assert
      await waitFor(() => {
        expect(screen.getByText("Customer Health")).toBeInTheDocument()
        expect(screen.getAllByText("Churn Rate")[0]).toBeInTheDocument()
        expect(screen.getByText("Repeat Rate")).toBeInTheDocument()
        expect(screen.getAllByText("8.7%")[0]).toBeInTheDocument() // Churn rate
        expect(screen.getAllByText("42.1%")[0]).toBeInTheDocument() // Repeat rate
      })
    })

    it("should display Conversion Funnel with correct percentages", async () => {
      // Act
      render(
        <TestWrapper>
          <AnalyticsDashboard />
        </TestWrapper>,
      )

      // Assert
      await waitFor(() => {
        expect(screen.getByText("Conversion Funnel")).toBeInTheDocument()
        expect(screen.getByText("Visitors")).toBeInTheDocument()
        expect(screen.getByText("Add to Cart")).toBeInTheDocument()
        expect(screen.getByText("Purchase")).toBeInTheDocument()
        expect(screen.getAllByText("3.2%")[0]).toBeInTheDocument() // Conversion rate
      })
    })
  })

  describe("Alerts section", () => {
    it("should display alerts from API", async () => {
      // Act
      render(
        <TestWrapper>
          <AnalyticsDashboard />
        </TestWrapper>,
      )

      // Assert
      await waitFor(() => {
        expect(
          screen.getByText("Out of Stock Alert - 1 Product"),
        ).toBeInTheDocument()
        expect(
          screen.getByText("Low Stock Alert - 3 Products"),
        ).toBeInTheDocument()
        expect(screen.getByText("CRITICAL")).toBeInTheDocument()
        expect(screen.getByText("WARNING")).toBeInTheDocument()
      })
    })

    it("should show alert badge in header when alerts exist", async () => {
      // Act
      render(
        <TestWrapper>
          <AnalyticsDashboard />
        </TestWrapper>,
      )

      // Assert
      await waitFor(() => {
        expect(screen.getByText("3 Alerts")).toBeInTheDocument()
      })
    })

    it("should not show alert badge when no alerts", async () => {
      // Arrange
      const noAlertsData = { ...mockAlertsData, total_alerts: 0, alerts: [] }
      vi.mocked(AnalyticsService.getAlertSummaryWithFallback).mockResolvedValue(
        noAlertsData,
      )

      // Act
      render(
        <TestWrapper>
          <AnalyticsDashboard />
        </TestWrapper>,
      )

      // Assert
      await waitFor(() => {
        expect(screen.queryByText(/Alerts?$/)).not.toBeInTheDocument()
      })
    })
  })

  describe("Refresh functionality", () => {
    it("should have a refresh button", async () => {
      // Act
      render(
        <TestWrapper>
          <AnalyticsDashboard />
        </TestWrapper>,
      )

      // Assert
      await waitFor(() => {
        expect(
          screen.getByRole("button", { name: /refresh/i }),
        ).toBeInTheDocument()
      })
    })

    it("should call refresh methods when refresh button is clicked", async () => {
      // Act
      await act(async () => {
        render(
          <TestWrapper>
            <AnalyticsDashboard />
          </TestWrapper>,
        )
      })

      await waitFor(() => {
        expect(
          screen.getByRole("button", { name: /refresh/i }),
        ).toBeInTheDocument()
      })

      // Clear the initial calls
      vi.clearAllMocks()

      // Click refresh button
      const refreshButton = screen.getByRole("button", { name: /refresh/i })

      await act(async () => {
        fireEvent.click(refreshButton)
      })

      // Assert
      await waitFor(() => {
        expect(
          AnalyticsService.getFinancialSummaryWithFallback,
        ).toHaveBeenCalledTimes(1)
        expect(
          AnalyticsService.getRealtimeMetricsWithFallback,
        ).toHaveBeenCalledTimes(1)
        expect(
          AnalyticsService.getAlertSummaryWithFallback,
        ).toHaveBeenCalledTimes(1)
      })
    })

    it("should show loading state during refresh", async () => {
      // Arrange - make refresh take some time
      vi.mocked(
        AnalyticsService.getFinancialSummaryWithFallback,
      ).mockImplementation(
        () =>
          new Promise((resolve) =>
            setTimeout(() => resolve(mockFinancialData), 100),
          ),
      )

      // Act
      await act(async () => {
        render(
          <TestWrapper>
            <AnalyticsDashboard />
          </TestWrapper>,
        )
      })

      await waitFor(() => {
        expect(
          screen.getByRole("button", { name: /refresh/i }),
        ).toBeInTheDocument()
      })

      const refreshButton = screen.getByRole("button", { name: /refresh/i })

      await act(async () => {
        fireEvent.click(refreshButton)
      })

      // Assert
      await waitFor(() => {
        expect(screen.getByText("Refreshing")).toBeInTheDocument()
      })
    })

    it("should show success toast after successful refresh", async () => {
      // Act
      await act(async () => {
        render(
          <TestWrapper>
            <AnalyticsDashboard />
          </TestWrapper>,
        )
      })

      await waitFor(() => {
        expect(
          screen.getByRole("button", { name: /refresh/i }),
        ).toBeInTheDocument()
      })

      const refreshButton = screen.getByRole("button", { name: /refresh/i })

      await act(async () => {
        fireEvent.click(refreshButton)
      })

      // Assert
      await waitFor(() => {
        expect(mockToast).toHaveBeenCalledWith({
          title: "Success",
          description: "Dashboard data refreshed successfully",
          status: "success",
          duration: 3000,
          isClosable: true,
        })
      })
    })
  })

  describe("Real-time updates", () => {
    it("should display last updated timestamp", async () => {
      // Act
      render(
        <TestWrapper>
          <AnalyticsDashboard />
        </TestWrapper>,
      )

      // Assert
      await waitFor(() => {
        expect(screen.getByText(/Last updated:/)).toBeInTheDocument()
      })
    })

    it("should show real-time revenue value", async () => {
      // Act
      render(
        <TestWrapper>
          <AnalyticsDashboard />
        </TestWrapper>,
      )

      // Assert
      await waitFor(() => {
        expect(screen.getByText("Real-time: $2,848")).toBeInTheDocument()
      })
    })
  })

  describe("Error handling", () => {
    it("should show error alert when data loading fails", async () => {
      // Arrange
      vi.mocked(
        AnalyticsService.getFinancialSummaryWithFallback,
      ).mockRejectedValue(new Error("Failed to load data"))

      // Act
      render(
        <TestWrapper>
          <AnalyticsDashboard />
        </TestWrapper>,
      )

      // Assert
      await waitFor(() => {
        expect(mockToast).toHaveBeenCalledWith({
          title: "Error",
          description: "Failed to load financial data",
          status: "error",
          duration: 5000,
          isClosable: true,
        })
      })
    })

    it("should handle missing data gracefully", async () => {
      // Arrange
      vi.mocked(
        AnalyticsService.getFinancialSummaryWithFallback,
      ).mockResolvedValue(null as any)

      // Act
      render(
        <TestWrapper>
          <AnalyticsDashboard />
        </TestWrapper>,
      )

      // Assert - should not crash and show some default values
      await waitFor(() => {
        expect(screen.getByText("Analytics Dashboard")).toBeInTheDocument()
      })
    })
  })

  describe("Responsive design", () => {
    it("should render all main sections", async () => {
      // Act
      render(
        <TestWrapper>
          <AnalyticsDashboard />
        </TestWrapper>,
      )

      // Assert
      await waitFor(() => {
        expect(screen.getByText("Revenue Overview")).toBeInTheDocument()
        expect(
          screen.getByText("Key Performance Indicators"),
        ).toBeInTheDocument()
        expect(screen.getByText("Orders")).toBeInTheDocument()
        expect(screen.getByText("Customers")).toBeInTheDocument()
        expect(screen.getByText("Inventory")).toBeInTheDocument()
        expect(screen.getByText("Conversion Metrics")).toBeInTheDocument()
      })
    })
  })

  describe("Data formatting", () => {
    it("should format currency values correctly", async () => {
      // Act
      render(
        <TestWrapper>
          <AnalyticsDashboard />
        </TestWrapper>,
      )

      // Assert
      await waitFor(() => {
        // Should format without decimals for whole numbers
        expect(screen.getByText("$2,500")).toBeInTheDocument()
        expect(screen.getByText("$45,000")).toBeInTheDocument()

        // Should handle decimal values
        expect(screen.getByText("$86")).toBeInTheDocument() // AOV rounded
      })
    })

    it("should format percentage values correctly", async () => {
      // Act
      render(
        <TestWrapper>
          <AnalyticsDashboard />
        </TestWrapper>,
      )

      // Assert
      await waitFor(() => {
        expect(screen.getByText("15.2% growth")).toBeInTheDocument() // Growth rate with "growth" suffix
        expect(screen.getAllByText("28.5%")[0]).toBeInTheDocument() // Cart abandonment
        expect(screen.getAllByText("3.2%")[0]).toBeInTheDocument() // Conversion rate
        expect(screen.getAllByText("42.1%")[0]).toBeInTheDocument() // Repeat rate
        expect(screen.getAllByText("8.7%")[0]).toBeInTheDocument() // Churn rate
      })
    })
  })
})
