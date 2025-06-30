import { useNavigate } from "@tanstack/react-router"
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest"
import UserOrdersPage from "../components/Store/UserOrdersPage"
import orderService from "../services/orderService"
import { render, screen, waitFor } from "./test-utils"

const mockOrders = [
  {
    order_id: "order123",
    created_at: "2025-06-20T10:00:00Z",
    total_amount: 150.75,
    status: "CONFIRMED",
    payment_status: "CAPTURED",
    items: [{ product_name: "Product A", quantity: 1 }],
  },
  {
    order_id: "order456",
    created_at: "2025-06-18T12:30:00Z",
    total_amount: 200.0,
    status: "PENDING",
    payment_status: "PENDING",
    items: [{ product_name: "Product B", quantity: 2 }],
  },
]

describe("UserOrdersPage", () => {
  let getMyOrdersSpy: vi.SpyInstance
  let cancelOrderSpy: vi.SpyInstance

  beforeEach(() => {
    // Spy on the actual methods of orderService
    getMyOrdersSpy = vi.spyOn(orderService, "getMyOrders")
    cancelOrderSpy = vi.spyOn(orderService, "cancelOrder")
  })

  afterEach(() => {
    // Restore the original implementations after each test
    getMyOrdersSpy.mockRestore()
    cancelOrderSpy.mockRestore()
  })

  it("should display loading spinner when orders are being fetched", () => {
    getMyOrdersSpy.mockReturnValueOnce(new Promise(() => {})) // Never resolve to keep loading

    render(<UserOrdersPage />)

    expect(screen.getByText("Cargando pedidos...")).toBeInTheDocument()
  })

  it("should display error message if fetching orders fails", async () => {
    getMyOrdersSpy.mockRejectedValueOnce(new Error("Failed to fetch orders"))

    render(<UserOrdersPage />)

    await waitFor(() => {
      expect(
        screen.getByText("No se pudieron cargar los pedidos"),
      ).toBeInTheDocument()
      expect(screen.getByRole("alert")).toBeInTheDocument()
    })
  })

  it('should display "No tienes pedidos" message when there are no orders', async () => {
    getMyOrdersSpy.mockResolvedValueOnce({
      orders: [],
      total: 0,
      total_pages: 0,
    })

    render(<UserOrdersPage />)

    await waitFor(() => {
      expect(screen.getByText("No tienes pedidos")).toBeInTheDocument()
      expect(
        screen.getByText("Cuando realices tu primera compra, aparecerá aquí"),
      ).toBeInTheDocument()
      expect(
        screen.getByRole("button", { name: /explorar productos/i }),
      ).toBeInTheDocument()
    })
  })

  it("should display a list of orders when orders are fetched successfully", async () => {
    getMyOrdersSpy.mockResolvedValueOnce({
      orders: mockOrders,
      total: mockOrders.length,
      total_pages: 1,
    })

    render(<UserOrdersPage />)

    await waitFor(() => {
      // The component shows order_id.slice(-8).toUpperCase(), so "order123" becomes "ORDER123"
      expect(screen.getByText("Pedido #ORDER123")).toBeInTheDocument()
      expect(screen.getByText("Pedido #ORDER456")).toBeInTheDocument()

      // Use getAllByText for status badges since they appear both in dropdown and in badges
      const statusElements = screen.getAllByText("Confirmado")
      expect(statusElements.length).toBeGreaterThan(0)

      const pendingElements = screen.getAllByText("Pendiente")
      expect(pendingElements.length).toBeGreaterThan(0)

      expect(screen.getByText("$150.75")).toBeInTheDocument()
      expect(screen.getByText("$200.00")).toBeInTheDocument()
    })
  })
})
