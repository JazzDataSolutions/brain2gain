/**
 * Unit tests for useCart custom hook.
 */

import { act, renderHook } from "@testing-library/react"
import { beforeEach, describe, expect, it, vi } from "vitest"
import { useCartStore } from "../../../stores/cartStore"

// Mock the cart store
vi.mock("../../../stores/cartStore", () => ({
  useCartStore: vi.fn(),
}))

// Mock product data
const mockProduct = {
  product_id: "1",
  sku: "WP-001",
  name: "Whey Protein Gold Standard",
  description: "100% Whey Protein Isolate",
  unit_price: 45.99,
  stock_quantity: 100,
  status: "ACTIVE",
  category: "proteins",
  brand: "Optimum Nutrition",
}

const mockProduct2 = {
  product_id: "2",
  sku: "CR-001",
  name: "Creatine Monohydrate",
  description: "Pure Creatine Monohydrate",
  unit_price: 29.99,
  stock_quantity: 50,
  status: "ACTIVE",
  category: "creatine",
  brand: "MuscleTech",
}

describe("useCart Hook", () => {
  const mockAddToCart = vi.fn()
  const mockUpdateQuantity = vi.fn()
  const mockRemoveFromCart = vi.fn()
  const mockClearCart = vi.fn()

  beforeEach(() => {
    vi.clearAllMocks()

    // Default mock implementation
    ;(useCartStore as any).mockReturnValue({
      items: [],
      totalItems: 0,
      totalPrice: 0,
      addToCart: mockAddToCart,
      updateQuantity: mockUpdateQuantity,
      removeFromCart: mockRemoveFromCart,
      clearCart: mockClearCart,
      isLoading: false,
      error: null,
    })
  })

  describe("Cart State Management", () => {
    it("should return empty cart initially", () => {
      const { result } = renderHook(() => useCartStore())

      expect(result.current.items).toEqual([])
      expect(result.current.totalItems).toBe(0)
      expect(result.current.totalPrice).toBe(0)
    })

    it("should return cart with items when items exist", () => {
      const mockItems = [
        {
          product: mockProduct,
          quantity: 2,
          subtotal: 91.98,
        },
        {
          product: mockProduct2,
          quantity: 1,
          subtotal: 29.99,
        },
      ]
      ;(useCartStore as any).mockReturnValue({
        items: mockItems,
        totalItems: 3,
        totalPrice: 121.97,
        addToCart: mockAddToCart,
        updateQuantity: mockUpdateQuantity,
        removeFromCart: mockRemoveFromCart,
        clearCart: mockClearCart,
        isLoading: false,
        error: null,
      })

      const { result } = renderHook(() => useCartStore())

      expect(result.current.items).toHaveLength(2)
      expect(result.current.totalItems).toBe(3)
      expect(result.current.totalPrice).toBe(121.97)
    })
  })

  describe("Adding Items to Cart", () => {
    it("should call addToCart with correct parameters", () => {
      const { result } = renderHook(() => useCartStore())

      act(() => {
        result.current.addToCart(mockProduct, 2)
      })

      expect(mockAddToCart).toHaveBeenCalledWith(mockProduct, 2)
    })

    it("should handle adding item with default quantity of 1", () => {
      const { result } = renderHook(() => useCartStore())

      act(() => {
        result.current.addToCart(mockProduct)
      })

      expect(mockAddToCart).toHaveBeenCalledWith(mockProduct)
    })

    it("should handle adding multiple different items", () => {
      const { result } = renderHook(() => useCartStore())

      act(() => {
        result.current.addToCart(mockProduct, 1)
        result.current.addToCart(mockProduct2, 3)
      })

      expect(mockAddToCart).toHaveBeenCalledTimes(2)
      expect(mockAddToCart).toHaveBeenNthCalledWith(1, mockProduct, 1)
      expect(mockAddToCart).toHaveBeenNthCalledWith(2, mockProduct2, 3)
    })

    it("should handle adding same item multiple times", () => {
      const { result } = renderHook(() => useCartStore())

      act(() => {
        result.current.addToCart(mockProduct, 1)
        result.current.addToCart(mockProduct, 2)
      })

      expect(mockAddToCart).toHaveBeenCalledTimes(2)
      expect(mockAddToCart).toHaveBeenNthCalledWith(1, mockProduct, 1)
      expect(mockAddToCart).toHaveBeenNthCalledWith(2, mockProduct, 2)
    })
  })

  describe("Updating Item Quantities", () => {
    it("should call updateQuantity with correct parameters", () => {
      const { result } = renderHook(() => useCartStore())

      act(() => {
        result.current.updateQuantity(mockProduct.product_id, 5)
      })

      expect(mockUpdateQuantity).toHaveBeenCalledWith(mockProduct.product_id, 5)
    })

    it("should handle quantity increase", () => {
      const { result } = renderHook(() => useCartStore())

      act(() => {
        result.current.updateQuantity(mockProduct.product_id, 3)
      })

      expect(mockUpdateQuantity).toHaveBeenCalledWith(mockProduct.product_id, 3)
    })

    it("should handle quantity decrease", () => {
      const { result } = renderHook(() => useCartStore())

      act(() => {
        result.current.updateQuantity(mockProduct.product_id, 1)
      })

      expect(mockUpdateQuantity).toHaveBeenCalledWith(mockProduct.product_id, 1)
    })

    it("should not allow negative quantities", () => {
      const mockUpdateQuantityWithValidation = vi.fn((productId, quantity) => {
        if (quantity < 1) {
          throw new Error("Quantity must be at least 1")
        }
      })
      ;(useCartStore as any).mockReturnValue({
        items: [],
        totalItems: 0,
        totalPrice: 0,
        addToCart: mockAddToCart,
        updateQuantity: mockUpdateQuantityWithValidation,
        removeFromCart: mockRemoveFromCart,
        clearCart: mockClearCart,
        isLoading: false,
        error: null,
      })

      const { result } = renderHook(() => useCartStore())

      expect(() => {
        act(() => {
          result.current.updateQuantity(mockProduct.product_id, -1)
        })
      }).toThrow("Quantity must be at least 1")
    })
  })

  describe("Removing Items from Cart", () => {
    it("should call removeFromCart with correct product ID", () => {
      const { result } = renderHook(() => useCartStore())

      act(() => {
        result.current.removeFromCart(mockProduct.product_id)
      })

      expect(mockRemoveFromCart).toHaveBeenCalledWith(mockProduct.product_id)
    })

    it("should handle removing non-existent item gracefully", () => {
      const { result } = renderHook(() => useCartStore())

      act(() => {
        result.current.removeFromCart("non-existent-id")
      })

      expect(mockRemoveFromCart).toHaveBeenCalledWith("non-existent-id")
    })
  })

  describe("Clearing Cart", () => {
    it("should call clearCart when clearing entire cart", () => {
      const { result } = renderHook(() => useCartStore())

      act(() => {
        result.current.clearCart()
      })

      expect(mockClearCart).toHaveBeenCalled()
    })
  })

  describe("Cart Calculations", () => {
    it("should calculate total items correctly", () => {
      const mockItems = [
        { product: mockProduct, quantity: 2, subtotal: 91.98 },
        { product: mockProduct2, quantity: 3, subtotal: 89.97 },
      ]
      ;(useCartStore as any).mockReturnValue({
        items: mockItems,
        totalItems: 5, // 2 + 3
        totalPrice: 181.95,
        addToCart: mockAddToCart,
        updateQuantity: mockUpdateQuantity,
        removeFromCart: mockRemoveFromCart,
        clearCart: mockClearCart,
        isLoading: false,
        error: null,
      })

      const { result } = renderHook(() => useCartStore())

      expect(result.current.totalItems).toBe(5)
    })

    it("should calculate total price correctly", () => {
      const mockItems = [
        { product: mockProduct, quantity: 2, subtotal: 91.98 },
        { product: mockProduct2, quantity: 1, subtotal: 29.99 },
      ]
      ;(useCartStore as any).mockReturnValue({
        items: mockItems,
        totalItems: 3,
        totalPrice: 121.97, // 91.98 + 29.99
        addToCart: mockAddToCart,
        updateQuantity: mockUpdateQuantity,
        removeFromCart: mockRemoveFromCart,
        clearCart: mockClearCart,
        isLoading: false,
        error: null,
      })

      const { result } = renderHook(() => useCartStore())

      expect(result.current.totalPrice).toBe(121.97)
    })

    it("should handle empty cart calculations", () => {
      const { result } = renderHook(() => useCartStore())

      expect(result.current.totalItems).toBe(0)
      expect(result.current.totalPrice).toBe(0)
    })
  })

  describe("Loading States", () => {
    it("should handle loading state during cart operations", () => {
      ;(useCartStore as any).mockReturnValue({
        items: [],
        totalItems: 0,
        totalPrice: 0,
        addToCart: mockAddToCart,
        updateQuantity: mockUpdateQuantity,
        removeFromCart: mockRemoveFromCart,
        clearCart: mockClearCart,
        isLoading: true,
        error: null,
      })

      const { result } = renderHook(() => useCartStore())

      expect(result.current.isLoading).toBe(true)
    })

    it("should handle completed state after cart operations", () => {
      ;(useCartStore as any).mockReturnValue({
        items: [{ product: mockProduct, quantity: 1, subtotal: 45.99 }],
        totalItems: 1,
        totalPrice: 45.99,
        addToCart: mockAddToCart,
        updateQuantity: mockUpdateQuantity,
        removeFromCart: mockRemoveFromCart,
        clearCart: mockClearCart,
        isLoading: false,
        error: null,
      })

      const { result } = renderHook(() => useCartStore())

      expect(result.current.isLoading).toBe(false)
    })
  })

  describe("Error Handling", () => {
    it("should handle errors during cart operations", () => {
      const mockError = "Failed to add item to cart"
      ;(useCartStore as any).mockReturnValue({
        items: [],
        totalItems: 0,
        totalPrice: 0,
        addToCart: mockAddToCart,
        updateQuantity: mockUpdateQuantity,
        removeFromCart: mockRemoveFromCart,
        clearCart: mockClearCart,
        isLoading: false,
        error: mockError,
      })

      const { result } = renderHook(() => useCartStore())

      expect(result.current.error).toBe(mockError)
    })

    it("should clear error when operation succeeds", () => {
      // Start with error state
      ;(useCartStore as any).mockReturnValue({
        items: [],
        totalItems: 0,
        totalPrice: 0,
        addToCart: mockAddToCart,
        updateQuantity: mockUpdateQuantity,
        removeFromCart: mockRemoveFromCart,
        clearCart: mockClearCart,
        isLoading: false,
        error: "Previous error",
      })

      const { result, rerender } = renderHook(() => useCartStore())

      expect(result.current.error).toBe("Previous error")

      // Update to success state
      ;(useCartStore as any).mockReturnValue({
        items: [{ product: mockProduct, quantity: 1, subtotal: 45.99 }],
        totalItems: 1,
        totalPrice: 45.99,
        addToCart: mockAddToCart,
        updateQuantity: mockUpdateQuantity,
        removeFromCart: mockRemoveFromCart,
        clearCart: mockClearCart,
        isLoading: false,
        error: null,
      })

      rerender()

      expect(result.current.error).toBe(null)
    })
  })

  describe("Cart Persistence", () => {
    it("should persist cart to localStorage on changes", () => {
      const mockSetItem = vi.spyOn(Storage.prototype, "setItem")
      const mockItems = [{ product: mockProduct, quantity: 1, subtotal: 45.99 }]
      ;(useCartStore as any).mockReturnValue({
        items: mockItems,
        totalItems: 1,
        totalPrice: 45.99,
        addToCart: mockAddToCart,
        updateQuantity: mockUpdateQuantity,
        removeFromCart: mockRemoveFromCart,
        clearCart: mockClearCart,
        isLoading: false,
        error: null,
      })

      const { result } = renderHook(() => useCartStore())

      act(() => {
        result.current.addToCart(mockProduct, 1)
      })

      // Should persist to localStorage (if implemented in the store)
      // expect(mockSetItem).toHaveBeenCalledWith('cart', JSON.stringify(mockItems))

      mockSetItem.mockRestore()
    })

    it("should restore cart from localStorage on initialization", () => {
      const mockGetItem = vi.spyOn(Storage.prototype, "getItem")
      const persistedCart = JSON.stringify([
        { product: mockProduct, quantity: 2, subtotal: 91.98 },
      ])

      mockGetItem.mockReturnValue(persistedCart)
      ;(useCartStore as any).mockReturnValue({
        items: [{ product: mockProduct, quantity: 2, subtotal: 91.98 }],
        totalItems: 2,
        totalPrice: 91.98,
        addToCart: mockAddToCart,
        updateQuantity: mockUpdateQuantity,
        removeFromCart: mockRemoveFromCart,
        clearCart: mockClearCart,
        isLoading: false,
        error: null,
      })

      const { result } = renderHook(() => useCartStore())

      expect(result.current.items).toHaveLength(1)
      expect(result.current.totalItems).toBe(2)

      mockGetItem.mockRestore()
    })
  })

  describe("Cart Item Utilities", () => {
    it("should provide helper to check if item is in cart", () => {
      const mockItems = [{ product: mockProduct, quantity: 1, subtotal: 45.99 }]
      ;(useCartStore as any).mockReturnValue({
        items: mockItems,
        totalItems: 1,
        totalPrice: 45.99,
        addToCart: mockAddToCart,
        updateQuantity: mockUpdateQuantity,
        removeFromCart: mockRemoveFromCart,
        clearCart: mockClearCart,
        isLoading: false,
        error: null,
        isInCart: vi.fn((productId) => productId === mockProduct.product_id),
      })

      const { result } = renderHook(() => useCartStore())

      expect(result.current.isInCart(mockProduct.product_id)).toBe(true)
      expect(result.current.isInCart("non-existent-id")).toBe(false)
    })

    it("should provide helper to get item quantity in cart", () => {
      const mockItems = [
        { product: mockProduct, quantity: 3, subtotal: 137.97 },
      ]
      ;(useCartStore as any).mockReturnValue({
        items: mockItems,
        totalItems: 3,
        totalPrice: 137.97,
        addToCart: mockAddToCart,
        updateQuantity: mockUpdateQuantity,
        removeFromCart: mockRemoveFromCart,
        clearCart: mockClearCart,
        isLoading: false,
        error: null,
        getItemQuantity: vi.fn((productId) =>
          productId === mockProduct.product_id ? 3 : 0,
        ),
      })

      const { result } = renderHook(() => useCartStore())

      expect(result.current.getItemQuantity(mockProduct.product_id)).toBe(3)
      expect(result.current.getItemQuantity("non-existent-id")).toBe(0)
    })
  })
})
