import { afterEach, beforeEach, describe, expect, it, vi } from "vitest"
import OrderDetailsPage from "../components/Store/OrderDetailsPage"
import orderService from "../services/orderService"
import { render, screen, waitFor } from "./test-utils"

// Mock useParams to return a test order ID
vi.mock("@tanstack/react-router", async (importOriginal) => {
  const actual = await importOriginal()
  return {
    ...actual,
    useParams: vi.fn(() => ({ orderId: "test-order-123" })),
    useNavigate: vi.fn(() => vi.fn()),
  }
})

const mockOrder = {
  order_id: "test-order-123",
  created_at: "2025-06-20T10:00:00Z",
  total_amount: 150.75,
  subtotal: 130.0,
  shipping_cost: 0,
  tax_amount: 20.75,
  status: "CONFIRMED",
  payment_status: "CAPTURED",
  payment_method: "stripe",
  items: [
    {
      product_name: "Test Product",
      quantity: 2,
      unit_price: 65.0,
      line_total: 130.0,
      discount_amount: 0,
    },
  ],
  shipping_address: {
    first_name: "Juan",
    last_name: "Pérez",
    address_line_1: "Test Address 123",
    city: "Test City",
    state: "Test State",
    postal_code: "12345",
    country: "MX",
  },
}

describe("OrderDetailsPage", () => {
  let getOrderByIdSpy: vi.SpyInstance

  beforeEach(() => {
    getOrderByIdSpy = vi.spyOn(orderService, "getOrderById")
  })

  afterEach(() => {
    getOrderByIdSpy.mockRestore()
  })

  it("should display loading state when fetching order", () => {
    getOrderByIdSpy.mockReturnValueOnce(new Promise(() => {})) // Never resolve to keep loading

    render(<OrderDetailsPage />)

    expect(
      screen.getByText("Cargando detalles del pedido..."),
    ).toBeInTheDocument()
  })

  it("should display error message if fetching order fails", async () => {
    getOrderByIdSpy.mockRejectedValueOnce(new Error("Failed to fetch order"))

    render(<OrderDetailsPage />)

    await waitFor(() => {
      expect(screen.getByText("Error al cargar el pedido")).toBeInTheDocument()
      expect(screen.getByText("Volver a Mis Pedidos")).toBeInTheDocument()
    })
  })

  it("should display order details when order is fetched successfully", async () => {
    getOrderByIdSpy.mockResolvedValueOnce(mockOrder)

    render(<OrderDetailsPage />)

    await waitFor(() => {
      // Check if order ID is displayed (appears in multiple places: breadcrumb and heading)
      const orderIdElements = screen.getAllByText("Pedido #RDER-123")
      expect(orderIdElements.length).toBeGreaterThan(0)

      // Check if order status is displayed
      expect(screen.getByText("Confirmado")).toBeInTheDocument()

      // Check if product information is displayed
      expect(screen.getByText("Test Product")).toBeInTheDocument()

      // Check if total amount and other financial details are displayed
      expect(screen.getAllByText("$150.75").length).toBeGreaterThan(0) // total_amount
      expect(screen.getAllByText("$130.00").length).toBeGreaterThan(0) // subtotal (appears in item list and summary)
      expect(screen.getAllByText("$20.75").length).toBeGreaterThan(0) // tax_amount
      expect(screen.getByText("GRATIS")).toBeInTheDocument() // free shipping

      // Check if shipping address is displayed (use partial matching for flexibility)
      expect(screen.getByText(/Test Address 123/)).toBeInTheDocument()
      expect(screen.getByText(/Test City/)).toBeInTheDocument()
    })
  })

  it("should display breadcrumb navigation", async () => {
    getOrderByIdSpy.mockResolvedValueOnce(mockOrder)

    render(<OrderDetailsPage />)

    await waitFor(() => {
      expect(screen.getByText("Tienda")).toBeInTheDocument()
      expect(screen.getByText("Mis Pedidos")).toBeInTheDocument()
      // The breadcrumb shows the order ID (RDER-123 from test-order-123)
      expect(screen.getAllByText("Pedido #RDER-123").length).toBeGreaterThan(0)
    })
  })
})
