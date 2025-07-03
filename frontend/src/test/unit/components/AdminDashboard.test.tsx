/**
 * Unit tests for AdminDashboard component.
 * Tests core admin functionality and data display.
 */

import { fireEvent, screen, waitFor } from "@testing-library/react"
import { beforeEach, describe, expect, it, vi } from "vitest"
import { render } from "../../test-utils"
import AdminDashboard from "../../../components/Admin/AdminDashboard"

// Mock analytics service
vi.mock("../../../client", () => ({
  AnalyticsService: {
    getOverview: vi.fn(),
    getRecentOrders: vi.fn(),
    getTopProducts: vi.fn(),
    getSalesMetrics: vi.fn(),
  },
  OrdersService: {
    readOrders: vi.fn(),
  },
  ProductsService: {
    readProducts: vi.fn(),
  },
  UsersService: {
    readUsers: vi.fn(),
  },
}))

// Mock data
const mockOverviewData = {
  total_revenue: 156780,
  total_orders: 1234,
  total_customers: 567,
  total_products: 89,
  revenue_change: 12.5,
  orders_change: 8.3,
  customers_change: 15.2,
  products_change: 5.1,
}

const mockRecentOrders = [
  {
    id: "1",
    user_id: "user1",
    total_amount: 1299,
    status: "completed",
    created_at: "2024-01-10T10:00:00Z",
    customer_name: "Juan Pérez",
    customer_email: "juan@email.com",
  },
  {
    id: "2", 
    user_id: "user2",
    total_amount: 899,
    status: "processing",
    created_at: "2024-01-10T09:30:00Z",
    customer_name: "María García",
    customer_email: "maria@email.com",
  },
]

const mockTopProducts = [
  {
    id: "1",
    name: "Whey Protein Gold",
    sales_count: 156,
    revenue: 45600,
    category: "Proteínas",
  },
  {
    id: "2",
    name: "Creatina Monohidrato",
    sales_count: 134,
    revenue: 32100,
    category: "Creatinas",
  },
]

describe("AdminDashboard Component", () => {
  beforeEach(() => {
    vi.clearAllMocks()
    
    // Setup mock implementations
    const { AnalyticsService, OrdersService, ProductsService, UsersService } = 
      require("../../../client")
    
    AnalyticsService.getOverview.mockResolvedValue(mockOverviewData)
    AnalyticsService.getRecentOrders.mockResolvedValue(mockRecentOrders)
    AnalyticsService.getTopProducts.mockResolvedValue(mockTopProducts)
    AnalyticsService.getSalesMetrics.mockResolvedValue({
      daily_sales: Array.from({ length: 30 }, (_, i) => ({
        date: new Date(Date.now() - i * 24 * 60 * 60 * 1000).toISOString().split("T")[0],
        revenue: Math.floor(Math.random() * 5000) + 1000,
        orders: Math.floor(Math.random() * 50) + 10,
      })),
    })
    
    OrdersService.readOrders.mockResolvedValue(mockRecentOrders)
    ProductsService.readProducts.mockResolvedValue([])
    UsersService.readUsers.mockResolvedValue([])
  })

  describe("Data Loading", () => {
    it("should display loading state initially", () => {
      render(<AdminDashboard />)
      
      expect(screen.getByRole("status")).toBeInTheDocument() // Spinner
    })

    it("should load and display overview metrics", async () => {
      render(<AdminDashboard />)
      
      await waitFor(() => {
        expect(screen.getByText("$156,780")).toBeInTheDocument()
        expect(screen.getByText("1,234")).toBeInTheDocument()
        expect(screen.getByText("567")).toBeInTheDocument()
        expect(screen.getByText("89")).toBeInTheDocument()
      })
    })

    it("should display percentage changes", async () => {
      render(<AdminDashboard />)
      
      await waitFor(() => {
        expect(screen.getByText("+12.5%")).toBeInTheDocument()
        expect(screen.getByText("+8.3%")).toBeInTheDocument()
        expect(screen.getByText("+15.2%")).toBeInTheDocument()
        expect(screen.getByText("+5.1%")).toBeInTheDocument()
      })
    })

    it("should handle API errors gracefully", async () => {
      const { AnalyticsService } = require("../../../client")
      AnalyticsService.getOverview.mockRejectedValue(new Error("API Error"))
      
      render(<AdminDashboard />)
      
      await waitFor(() => {
        expect(screen.getByText(/error loading data/i)).toBeInTheDocument()
      })
    })
  })

  describe("Recent Orders Section", () => {
    it("should display recent orders", async () => {
      render(<AdminDashboard />)
      
      await waitFor(() => {
        expect(screen.getByText("Juan Pérez")).toBeInTheDocument()
        expect(screen.getByText("María García")).toBeInTheDocument()
        expect(screen.getByText("$12.99")).toBeInTheDocument()
        expect(screen.getByText("$8.99")).toBeInTheDocument()
      })
    })

    it("should display order statuses with correct styling", async () => {
      render(<AdminDashboard />)
      
      await waitFor(() => {
        const completedBadge = screen.getByText("Completado")
        const processingBadge = screen.getByText("Procesando")
        
        expect(completedBadge).toHaveClass("chakra-badge")
        expect(processingBadge).toHaveClass("chakra-badge")
      })
    })

    it("should show view all orders link", async () => {
      render(<AdminDashboard />)
      
      await waitFor(() => {
        const viewAllLink = screen.getByText("Ver todos los pedidos")
        expect(viewAllLink).toBeInTheDocument()
      })
    })
  })

  describe("Top Products Section", () => {
    it("should display top selling products", async () => {
      render(<AdminDashboard />)
      
      await waitFor(() => {
        expect(screen.getByText("Whey Protein Gold")).toBeInTheDocument()
        expect(screen.getByText("Creatina Monohidrato")).toBeInTheDocument()
        expect(screen.getByText("156 ventas")).toBeInTheDocument()
        expect(screen.getByText("134 ventas")).toBeInTheDocument()
      })
    })

    it("should display product revenue", async () => {
      render(<AdminDashboard />)
      
      await waitFor(() => {
        expect(screen.getByText("$456.00")).toBeInTheDocument()
        expect(screen.getByText("$321.00")).toBeInTheDocument()
      })
    })

    it("should display product categories", async () => {
      render(<AdminDashboard />)
      
      await waitFor(() => {
        expect(screen.getByText("Proteínas")).toBeInTheDocument()
        expect(screen.getByText("Creatinas")).toBeInTheDocument()
      })
    })
  })

  describe("Sales Chart", () => {
    it("should render sales chart component", async () => {
      render(<AdminDashboard />)
      
      await waitFor(() => {
        expect(screen.getByText("Ventas de los últimos 30 días")).toBeInTheDocument()
      })
    })

    it("should display chart controls", async () => {
      render(<AdminDashboard />)
      
      await waitFor(() => {
        const timeframeSelect = screen.getByDisplayValue("30 días")
        expect(timeframeSelect).toBeInTheDocument()
      })
    })

    it("should allow changing chart timeframe", async () => {
      render(<AdminDashboard />)
      
      await waitFor(() => {
        const timeframeSelect = screen.getByDisplayValue("30 días")
        fireEvent.change(timeframeSelect, { target: { value: "7" } })
        
        expect(timeframeSelect.value).toBe("7")
      })
    })
  })

  describe("Responsive Design", () => {
    it("should adapt layout for mobile screens", () => {
      // Mock mobile viewport
      Object.defineProperty(window, "innerWidth", {
        writable: true,
        configurable: true,
        value: 375,
      })
      
      render(<AdminDashboard />)
      
      const dashboard = screen.getByTestId("admin-dashboard")
      expect(dashboard).toHaveClass("admin-dashboard")
    })

    it("should display metrics in grid layout", async () => {
      render(<AdminDashboard />)
      
      await waitFor(() => {
        const metricsGrid = screen.getByTestId("metrics-grid")
        expect(metricsGrid).toBeInTheDocument()
      })
    })
  })

  describe("Data Refresh", () => {
    it("should refresh data when refresh button is clicked", async () => {
      const { AnalyticsService } = require("../../../client")
      
      render(<AdminDashboard />)
      
      await waitFor(() => {
        const refreshButton = screen.getByLabelText("Actualizar datos")
        fireEvent.click(refreshButton)
      })
      
      expect(AnalyticsService.getOverview).toHaveBeenCalledTimes(2)
    })

    it("should show loading state during refresh", async () => {
      render(<AdminDashboard />)
      
      await waitFor(() => {
        const refreshButton = screen.getByLabelText("Actualizar datos")
        fireEvent.click(refreshButton)
        
        expect(screen.getByRole("status")).toBeInTheDocument()
      })
    })
  })

  describe("Error Handling", () => {
    it("should display error message for network failures", async () => {
      const { AnalyticsService } = require("../../../client")
      AnalyticsService.getOverview.mockRejectedValue(new Error("Network Error"))
      
      render(<AdminDashboard />)
      
      await waitFor(() => {
        expect(screen.getByText(/error de conexión/i)).toBeInTheDocument()
      })
    })

    it("should show retry button on error", async () => {
      const { AnalyticsService } = require("../../../client")
      AnalyticsService.getOverview.mockRejectedValue(new Error("API Error"))
      
      render(<AdminDashboard />)
      
      await waitFor(() => {
        const retryButton = screen.getByText("Reintentar")
        expect(retryButton).toBeInTheDocument()
      })
    })

    it("should retry data loading when retry button is clicked", async () => {
      const { AnalyticsService } = require("../../../client")
      AnalyticsService.getOverview
        .mockRejectedValueOnce(new Error("API Error"))
        .mockResolvedValue(mockOverviewData)
      
      render(<AdminDashboard />)
      
      await waitFor(() => {
        const retryButton = screen.getByText("Reintentar")
        fireEvent.click(retryButton)
      })
      
      await waitFor(() => {
        expect(screen.getByText("$156,780")).toBeInTheDocument()
      })
    })
  })

  describe("Performance", () => {
    it("should not re-render unnecessarily", async () => {
      const { AnalyticsService } = require("../../../client")
      let renderCount = 0
      
      const TestComponent = () => {
        renderCount++
        return <AdminDashboard />
      }
      
      render(<TestComponent />)
      
      await waitFor(() => {
        expect(screen.getByText("$156,780")).toBeInTheDocument()
      })
      
      // Should render only once after data loads
      expect(renderCount).toBe(2) // Initial render + data loaded render
    })

    it("should cache API responses", async () => {
      const { AnalyticsService } = require("../../../client")
      
      render(<AdminDashboard />)
      
      await waitFor(() => {
        expect(AnalyticsService.getOverview).toHaveBeenCalledTimes(1)
      })
      
      // Re-render should use cached data
      render(<AdminDashboard />)
      
      await waitFor(() => {
        expect(AnalyticsService.getOverview).toHaveBeenCalledTimes(1)
      })
    })
  })
})