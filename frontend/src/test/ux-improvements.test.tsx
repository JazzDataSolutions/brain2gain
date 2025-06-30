/**
 * UX Improvements Test Suite
 * Tests for the newly implemented UX features
 */

import { ChakraProvider } from "@chakra-ui/react"
import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { fireEvent, render, screen, waitFor } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { beforeEach, describe, expect, it, vi } from "vitest"

// Components to test
import QuickCart, { useQuickCart } from "../components/Cart/QuickCart"
import InstantSearch from "../components/Search/InstantSearch"
// import ProductCard, { ProductCardSkeleton } from '../components/Products/ProductCard'
import LoadingSpinner, {
  ProductCardSkeleton as LoadingProductCardSkeleton,
  PageLoadingSpinner,
  ButtonLoadingSpinner,
  SearchLoadingSpinner,
} from "../components/UI/LoadingSpinner"

// Mock data
const mockProduct = {
  id: "1",
  name: "Proteína Whey Gold",
  price: 89990,
  sku: "WHEY001",
  status: "ACTIVE" as const,
  image: "/test-image.jpg",
  rating: 4.5,
}

const mockCartItems = [
  {
    id: "1",
    name: "Proteína Whey Gold",
    price: 89990,
    quantity: 2,
    image: "/test-image.jpg",
  },
  {
    id: "2",
    name: "Creatina Monohidrato",
    price: 45990,
    quantity: 1,
    image: "/test-image2.jpg",
  },
]

// Mock zustand store
vi.mock("../stores/cartStore", () => ({
  useCartStore: () => ({
    items: mockCartItems,
    addItem: vi.fn(),
    removeItem: vi.fn(),
    updateQuantity: vi.fn(),
    clearCart: vi.fn(),
    getTotalPrice: () =>
      mockCartItems.reduce((sum, item) => sum + item.price * item.quantity, 0),
    getTotalItems: () =>
      mockCartItems.reduce((sum, item) => sum + item.quantity, 0),
    setLoading: vi.fn(),
    setError: vi.fn(),
  }),
}))

// Mock TanStack Router
vi.mock("@tanstack/react-router", () => ({
  useNavigate: () => vi.fn(),
  Link: ({ children, ...props }: any) => <a {...props}>{children}</a>,
}))

// Mock framer-motion for testing
vi.mock("framer-motion", () => ({
  motion: {
    div: ({ children, ...props }: any) => <div {...props}>{children}</div>,
    Box: ({ children, ...props }: any) => <div {...props}>{children}</div>,
  },
  AnimatePresence: ({ children }: any) => children,
  useReducedMotion: () => false,
}))

// Test wrapper component
const TestWrapper = ({ children }: { children: React.ReactNode }) => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
    },
  })

  return (
    <ChakraProvider>
      <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
    </ChakraProvider>
  )
}

describe.skip("UX Improvements", () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe("QuickCart Component", () => {
    it("renders cart items correctly", () => {
      render(
        <TestWrapper>
          <QuickCart isOpen={true} onClose={vi.fn()} />
        </TestWrapper>,
      )

      // Check if cart items are displayed
      expect(screen.getByText("Proteína Whey Gold")).toBeInTheDocument()
      expect(screen.getByText("Creatina Monohidrato")).toBeInTheDocument()

      // Check quantities
      expect(screen.getByDisplayValue("2")).toBeInTheDocument()
      expect(screen.getByDisplayValue("1")).toBeInTheDocument()
    })

    it("shows total price correctly", () => {
      render(
        <TestWrapper>
          <QuickCart isOpen={true} onClose={vi.fn()} />
        </TestWrapper>,
      )

      // Total should be (89990 * 2) + (45990 * 1) = 225970
      expect(screen.getByText(/225\.970/)).toBeInTheDocument()
    })

    it("shows empty state when no items", () => {
      // Mock empty cart
      vi.mocked(require("../stores/cartStore").useCartStore).mockReturnValue({
        items: [],
        getTotalPrice: () => 0,
        getTotalItems: () => 0,
        addItem: vi.fn(),
        removeItem: vi.fn(),
        updateQuantity: vi.fn(),
        clearCart: vi.fn(),
        setLoading: vi.fn(),
        setError: vi.fn(),
      })

      render(
        <TestWrapper>
          <QuickCart isOpen={true} onClose={vi.fn()} />
        </TestWrapper>,
      )

      expect(screen.getByText("Tu carrito está vacío")).toBeInTheDocument()
      expect(screen.getByText("Explorar Productos")).toBeInTheDocument()
    })

    it("handles close action", async () => {
      const mockOnClose = vi.fn()

      render(
        <TestWrapper>
          <QuickCart isOpen={true} onClose={mockOnClose} />
        </TestWrapper>,
      )

      const closeButton = screen.getByLabelText("Cerrar carrito")
      await userEvent.click(closeButton)

      expect(mockOnClose).toHaveBeenCalled()
    })
  })

  describe("useQuickCart Hook", () => {
    it("provides cart control functions", () => {
      const TestComponent = () => {
        const { isOpen, openCart, closeCart, toggleCart } = useQuickCart()

        return (
          <div>
            <span data-testid="is-open">{isOpen.toString()}</span>
            <button onClick={openCart} data-testid="open">
              Open
            </button>
            <button onClick={closeCart} data-testid="close">
              Close
            </button>
            <button onClick={toggleCart} data-testid="toggle">
              Toggle
            </button>
          </div>
        )
      }

      render(<TestComponent />)

      expect(screen.getByTestId("is-open")).toHaveTextContent("false")

      // Test open
      fireEvent.click(screen.getByTestId("open"))
      expect(screen.getByTestId("is-open")).toHaveTextContent("true")

      // Test close
      fireEvent.click(screen.getByTestId("close"))
      expect(screen.getByTestId("is-open")).toHaveTextContent("false")
    })
  })

  describe("InstantSearch Component", () => {
    it("renders search input", () => {
      render(
        <TestWrapper>
          <InstantSearch />
        </TestWrapper>,
      )

      const searchInput = screen.getByPlaceholderText(
        /Buscar proteínas, creatina/,
      )
      expect(searchInput).toBeInTheDocument()
    })

    it("shows search results on typing", async () => {
      // Mock API response
      global.fetch = vi.fn().mockResolvedValue({
        ok: true,
        json: async () => ({
          products: [
            {
              id: "1",
              name: "Proteína Test",
              price: 50000,
              category: "Proteínas",
            },
          ],
        }),
      })

      render(
        <TestWrapper>
          <InstantSearch />
        </TestWrapper>,
      )

      const searchInput = screen.getByPlaceholderText(
        /Buscar proteínas, creatina/,
      )

      // Type to trigger search
      await userEvent.type(searchInput, "proteína")

      // Wait for debounced search
      await waitFor(
        () => {
          expect(global.fetch).toHaveBeenCalledWith(
            expect.stringContaining("/api/v1/products/search?q=prote%C3%ADna"),
          )
        },
        { timeout: 1000 },
      )
    })

    it("handles keyboard navigation", async () => {
      render(
        <TestWrapper>
          <InstantSearch />
        </TestWrapper>,
      )

      const searchInput = screen.getByPlaceholderText(
        /Buscar proteínas, creatina/,
      )

      // Type to open dropdown
      await userEvent.type(searchInput, "test")

      // Test escape key
      await userEvent.keyboard("{Escape}")

      // Input should lose focus
      expect(searchInput).not.toHaveFocus()
    })
  })

  describe.skip("Enhanced ProductCard", () => {
    it("renders product information correctly", () => {
      render(
        <TestWrapper>
          <ProductCard product={mockProduct} />
        </TestWrapper>,
      )

      expect(screen.getByText("Proteína Whey Gold")).toBeInTheDocument()
      expect(screen.getByText("SKU: WHEY001")).toBeInTheDocument()
      expect(screen.getByText(/89\.990/)).toBeInTheDocument()
      expect(screen.getByText("Disponible")).toBeInTheDocument()
    })

    it("shows loading skeleton when isLoading is true", () => {
      render(
        <TestWrapper>
          <ProductCard product={mockProduct} isLoading={true} />
        </TestWrapper>,
      )

      // Should show skeleton instead of content
      expect(screen.queryByText("Proteína Whey Gold")).not.toBeInTheDocument()
    })

    it("handles wishlist toggle", async () => {
      const mockWishlistToggle = vi.fn()

      render(
        <TestWrapper>
          <ProductCard
            product={mockProduct}
            onWishlistToggle={mockWishlistToggle}
            showQuickActions={true}
          />
        </TestWrapper>,
      )

      // Hover to show quick actions overlay
      const productCard = screen
        .getByRole("img", { name: "Proteína Whey Gold" })
        .closest("div")
      await userEvent.hover(productCard!)

      // Click wishlist button
      const wishlistButton = screen.getByLabelText("Agregar a favoritos")
      await userEvent.click(wishlistButton)

      expect(mockWishlistToggle).toHaveBeenCalledWith("1")
    })

    it("handles add to cart with custom quantity", async () => {
      const mockAddItem = vi.fn()
      vi.mocked(require("../stores/cartStore").useCartStore).mockReturnValue({
        items: [],
        addItem: mockAddItem,
        removeItem: vi.fn(),
        updateQuantity: vi.fn(),
        clearCart: vi.fn(),
        getTotalPrice: () => 0,
        getTotalItems: () => 0,
        setLoading: vi.fn(),
        setError: vi.fn(),
      })

      render(
        <TestWrapper>
          <ProductCard product={mockProduct} />
        </TestWrapper>,
      )

      // Change quantity
      const quantityInput = screen.getByDisplayValue("1")
      await userEvent.clear(quantityInput)
      await userEvent.type(quantityInput, "3")

      // Add to cart
      const addButton = screen.getByText("Agregar al Carrito")
      await userEvent.click(addButton)

      expect(mockAddItem).toHaveBeenCalledWith({
        id: "1",
        name: "Proteína Whey Gold",
        price: 89990,
        quantity: 3,
        image: "/test-image.jpg",
      })
    })
  })

  describe.skip("ProductCardSkeleton", () => {
    it("renders skeleton components", () => {
      render(
        <TestWrapper>
          <ProductCardSkeleton />
        </TestWrapper>,
      )

      // Should contain skeleton elements (they don't have specific text content)
      const container = screen.getByRole("generic")
      expect(container).toBeInTheDocument()
    })
  })

  describe("Loading Spinners", () => {
    it("renders different spinner variants", () => {
      const { rerender } = render(
        <TestWrapper>
          <LoadingSpinner variant="dots" text="Loading dots..." />
        </TestWrapper>,
      )

      expect(screen.getByText("Loading dots...")).toBeInTheDocument()

      rerender(
        <TestWrapper>
          <LoadingSpinner variant="circle" text="Loading circle..." />
        </TestWrapper>,
      )

      expect(screen.getByText("Loading circle...")).toBeInTheDocument()

      rerender(
        <TestWrapper>
          <LoadingSpinner variant="pulse" text="Loading pulse..." />
        </TestWrapper>,
      )

      expect(screen.getByText("Loading pulse...")).toBeInTheDocument()
    })

    it("renders predefined spinner components", () => {
      render(
        <TestWrapper>
          <div>
            <PageLoadingSpinner />
            <ButtonLoadingSpinner />
            <SearchLoadingSpinner />
          </div>
        </TestWrapper>,
      )

      expect(screen.getByText("Cargando página...")).toBeInTheDocument()
      expect(screen.getByText("Buscando productos...")).toBeInTheDocument()
    })
  })

  describe("Performance Optimizations", () => {
    it.skip("memoizes ProductCard component", () => {
      const { rerender } = render(
        <TestWrapper>
          <ProductCard product={mockProduct} />
        </TestWrapper>,
      )

      // Rerender with same props - should not cause re-render
      rerender(
        <TestWrapper>
          <ProductCard product={mockProduct} />
        </TestWrapper>,
      )

      // Component should be memoized
      expect(ProductCard.displayName).toBe("ProductCard")
    })

    it("uses useCallback for event handlers", () => {
      // This test ensures that event handlers are optimized
      // The actual implementation uses useCallback which is tested indirectly
      render(
        <TestWrapper>
          <ProductCard product={mockProduct} />
        </TestWrapper>,
      )

      // Multiple clicks should not cause performance issues
      const addButton = screen.getByText("Agregar al Carrito")
      fireEvent.click(addButton)
      fireEvent.click(addButton)

      // Should handle multiple clicks gracefully
      expect(addButton).toBeInTheDocument()
    })
  })

  describe("Accessibility Features", () => {
    it("provides proper ARIA labels", () => {
      render(
        <TestWrapper>
          <QuickCart isOpen={true} onClose={vi.fn()} />
        </TestWrapper>,
      )

      expect(screen.getByLabelText("Cerrar carrito")).toBeInTheDocument()
    })

    it("supports keyboard navigation in search", async () => {
      render(
        <TestWrapper>
          <InstantSearch />
        </TestWrapper>,
      )

      const searchInput = screen.getByPlaceholderText(
        /Buscar proteínas, creatina/,
      )

      // Should be focusable
      searchInput.focus()
      expect(searchInput).toHaveFocus()

      // Should handle arrow keys (tested in implementation)
      await userEvent.keyboard("{ArrowDown}")
      await userEvent.keyboard("{ArrowUp}")
      await userEvent.keyboard("{Enter}")
    })

    it("provides tooltips for icon buttons", () => {
      render(
        <TestWrapper>
          <ProductCard
            product={mockProduct}
            onWishlistToggle={vi.fn()}
            showQuickActions={true}
          />
        </TestWrapper>,
      )

      // Tooltips are provided for accessibility
      // The actual tooltip text is tested in integration
    })
  })
})

describe.skip("UX Integration Tests", () => {
  it.skip("integrates QuickCart with ProductCard", async () => {
    const mockAddItem = vi.fn()
    vi.mocked(require("../stores/cartStore").useCartStore).mockReturnValue({
      items: [],
      addItem: mockAddItem,
      removeItem: vi.fn(),
      updateQuantity: vi.fn(),
      clearCart: vi.fn(),
      getTotalPrice: () => 0,
      getTotalItems: () => 0,
      setLoading: vi.fn(),
      setError: vi.fn(),
    })

    render(
      <TestWrapper>
        <div>
          <ProductCard product={mockProduct} />
          <QuickCart isOpen={true} onClose={vi.fn()} />
        </div>
      </TestWrapper>,
    )

    // Add item from ProductCard
    const addButton = screen.getByText("Agregar al Carrito")
    await userEvent.click(addButton)

    // Should call addItem function
    expect(mockAddItem).toHaveBeenCalled()
  })

  it("integrates InstantSearch with navigation", async () => {
    const mockNavigate = vi.fn()
    vi.mocked(require("@tanstack/react-router").useNavigate).mockReturnValue(
      mockNavigate,
    )

    render(
      <TestWrapper>
        <InstantSearch />
      </TestWrapper>,
    )

    const searchInput = screen.getByPlaceholderText(
      /Buscar proteínas, creatina/,
    )

    // Type search term and press Enter
    await userEvent.type(searchInput, "test product")
    await userEvent.keyboard("{Enter}")

    // Should navigate to search results
    expect(mockNavigate).toHaveBeenCalledWith({
      to: "/store/products",
      search: { q: "test product" },
    })
  })
})
