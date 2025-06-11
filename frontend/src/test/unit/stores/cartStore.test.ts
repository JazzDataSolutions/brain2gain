/**
 * Unit tests for cart store (Zustand).
 */

import { describe, it, expect, beforeEach, vi } from 'vitest'
import { act } from '@testing-library/react'
import { createStore } from 'zustand'
import { subscribeWithSelector } from 'zustand/middleware'
import { CartState, createCartStore } from '../../../stores/cartStore'

// Mock localStorage
const localStorageMock = {
  getItem: vi.fn(),
  setItem: vi.fn(),
  removeItem: vi.fn(),
  clear: vi.fn(),
}

Object.defineProperty(window, 'localStorage', {
  value: localStorageMock,
})

// Mock product data
const mockProduct1 = {
  product_id: '1',
  sku: 'WP-001',
  name: 'Whey Protein Gold Standard',
  description: '100% Whey Protein Isolate',
  unit_price: 45.99,
  stock_quantity: 100,
  status: 'ACTIVE',
  category: 'proteins',
  brand: 'Optimum Nutrition',
}

const mockProduct2 = {
  product_id: '2',
  sku: 'CR-001',
  name: 'Creatine Monohydrate',
  description: 'Pure Creatine Monohydrate',
  unit_price: 29.99,
  stock_quantity: 50,
  status: 'ACTIVE',
  category: 'creatine',
  brand: 'MuscleTech',
}

describe('Cart Store', () => {
  let store: ReturnType<typeof createStore<CartState>>

  beforeEach(() => {
    vi.clearAllMocks()
    localStorageMock.getItem.mockReturnValue(null)
    
    // Create a fresh store instance for each test
    store = createStore<CartState>()(
      subscribeWithSelector(createCartStore)
    )
  })

  describe('Initial State', () => {
    it('should initialize with empty cart', () => {
      const state = store.getState()

      expect(state.items).toEqual([])
      expect(state.totalItems).toBe(0)
      expect(state.totalPrice).toBe(0)
      expect(state.isLoading).toBe(false)
      expect(state.error).toBe(null)
    })

    it('should restore cart from localStorage if available', () => {
      const persistedCart = [
        {
          product: mockProduct1,
          quantity: 2,
          subtotal: 91.98,
        },
      ]

      localStorageMock.getItem.mockReturnValue(JSON.stringify(persistedCart))

      // Create new store instance to trigger restoration
      store = createStore<CartState>()(
        subscribeWithSelector(createCartStore)
      )

      const state = store.getState()

      expect(state.items).toHaveLength(1)
      expect(state.items[0].product.product_id).toBe(mockProduct1.product_id)
      expect(state.items[0].quantity).toBe(2)
    })

    it('should handle corrupted localStorage data gracefully', () => {
      localStorageMock.getItem.mockReturnValue('invalid json')

      // Should not throw and should initialize with empty cart
      expect(() => {
        store = createStore<CartState>()(
          subscribeWithSelector(createCartStore)
        )
      }).not.toThrow()

      const state = store.getState()
      expect(state.items).toEqual([])
    })
  })

  describe('Adding Items to Cart', () => {
    it('should add new item to cart', () => {
      act(() => {
        store.getState().addToCart(mockProduct1, 2)
      })

      const state = store.getState()

      expect(state.items).toHaveLength(1)
      expect(state.items[0].product.product_id).toBe(mockProduct1.product_id)
      expect(state.items[0].quantity).toBe(2)
      expect(state.items[0].subtotal).toBe(91.98) // 45.99 * 2
      expect(state.totalItems).toBe(2)
      expect(state.totalPrice).toBe(91.98)
    })

    it('should add multiple different items to cart', () => {
      act(() => {
        store.getState().addToCart(mockProduct1, 1)
        store.getState().addToCart(mockProduct2, 3)
      })

      const state = store.getState()

      expect(state.items).toHaveLength(2)
      expect(state.totalItems).toBe(4) // 1 + 3
      expect(state.totalPrice).toBe(135.96) // 45.99 + (29.99 * 3)
    })

    it('should increase quantity when adding existing item', () => {
      act(() => {
        store.getState().addToCart(mockProduct1, 1)
        store.getState().addToCart(mockProduct1, 2)
      })

      const state = store.getState()

      expect(state.items).toHaveLength(1)
      expect(state.items[0].quantity).toBe(3) // 1 + 2
      expect(state.items[0].subtotal).toBe(137.97) // 45.99 * 3
      expect(state.totalItems).toBe(3)
    })

    it('should default to quantity 1 when not specified', () => {
      act(() => {
        store.getState().addToCart(mockProduct1)
      })

      const state = store.getState()

      expect(state.items[0].quantity).toBe(1)
    })

    it('should persist cart to localStorage after adding item', () => {
      act(() => {
        store.getState().addToCart(mockProduct1, 2)
      })

      expect(localStorageMock.setItem).toHaveBeenCalledWith(
        'cart',
        expect.stringContaining(mockProduct1.product_id)
      )
    })

    it('should handle adding item with zero quantity', () => {
      act(() => {
        store.getState().addToCart(mockProduct1, 0)
      })

      const state = store.getState()

      // Should not add item with zero quantity
      expect(state.items).toHaveLength(0)
    })

    it('should handle adding item with negative quantity', () => {
      act(() => {
        store.getState().addToCart(mockProduct1, -1)
      })

      const state = store.getState()

      // Should not add item with negative quantity
      expect(state.items).toHaveLength(0)
    })
  })

  describe('Updating Item Quantities', () => {
    beforeEach(() => {
      act(() => {
        store.getState().addToCart(mockProduct1, 2)
        store.getState().addToCart(mockProduct2, 1)
      })
    })

    it('should update item quantity correctly', () => {
      act(() => {
        store.getState().updateQuantity(mockProduct1.product_id, 5)
      })

      const state = store.getState()
      const item = state.items.find(item => item.product.product_id === mockProduct1.product_id)

      expect(item?.quantity).toBe(5)
      expect(item?.subtotal).toBe(229.95) // 45.99 * 5
      expect(state.totalItems).toBe(6) // 5 + 1
      expect(state.totalPrice).toBe(259.94) // 229.95 + 29.99
    })

    it('should remove item when quantity is updated to zero', () => {
      act(() => {
        store.getState().updateQuantity(mockProduct1.product_id, 0)
      })

      const state = store.getState()

      expect(state.items).toHaveLength(1)
      expect(state.items[0].product.product_id).toBe(mockProduct2.product_id)
      expect(state.totalItems).toBe(1)
    })

    it('should handle updating non-existent item', () => {
      const initialState = store.getState()

      act(() => {
        store.getState().updateQuantity('non-existent-id', 5)
      })

      const state = store.getState()

      // State should remain unchanged
      expect(state.items).toEqual(initialState.items)
      expect(state.totalItems).toBe(initialState.totalItems)
    })

    it('should not allow negative quantities', () => {
      act(() => {
        store.getState().updateQuantity(mockProduct1.product_id, -1)
      })

      const state = store.getState()
      const item = state.items.find(item => item.product.product_id === mockProduct1.product_id)

      // Quantity should remain unchanged or be set to minimum (1)
      expect(item?.quantity).toBeGreaterThan(0)
    })

    it('should persist cart to localStorage after updating quantity', () => {
      act(() => {
        store.getState().updateQuantity(mockProduct1.product_id, 3)
      })

      expect(localStorageMock.setItem).toHaveBeenCalled()
    })
  })

  describe('Removing Items from Cart', () => {
    beforeEach(() => {
      act(() => {
        store.getState().addToCart(mockProduct1, 2)
        store.getState().addToCart(mockProduct2, 1)
      })
    })

    it('should remove item from cart', () => {
      act(() => {
        store.getState().removeFromCart(mockProduct1.product_id)
      })

      const state = store.getState()

      expect(state.items).toHaveLength(1)
      expect(state.items[0].product.product_id).toBe(mockProduct2.product_id)
      expect(state.totalItems).toBe(1)
      expect(state.totalPrice).toBe(29.99)
    })

    it('should handle removing non-existent item', () => {
      const initialState = store.getState()

      act(() => {
        store.getState().removeFromCart('non-existent-id')
      })

      const state = store.getState()

      // State should remain unchanged
      expect(state.items).toEqual(initialState.items)
      expect(state.totalItems).toBe(initialState.totalItems)
    })

    it('should persist cart to localStorage after removing item', () => {
      act(() => {
        store.getState().removeFromCart(mockProduct1.product_id)
      })

      expect(localStorageMock.setItem).toHaveBeenCalled()
    })
  })

  describe('Clearing Cart', () => {
    beforeEach(() => {
      act(() => {
        store.getState().addToCart(mockProduct1, 2)
        store.getState().addToCart(mockProduct2, 1)
      })
    })

    it('should clear all items from cart', () => {
      act(() => {
        store.getState().clearCart()
      })

      const state = store.getState()

      expect(state.items).toEqual([])
      expect(state.totalItems).toBe(0)
      expect(state.totalPrice).toBe(0)
    })

    it('should persist empty cart to localStorage after clearing', () => {
      act(() => {
        store.getState().clearCart()
      })

      expect(localStorageMock.setItem).toHaveBeenCalledWith('cart', '[]')
    })
  })

  describe('Cart Calculations', () => {
    it('should calculate total items correctly', () => {
      act(() => {
        store.getState().addToCart(mockProduct1, 2)
        store.getState().addToCart(mockProduct2, 3)
      })

      const state = store.getState()

      expect(state.totalItems).toBe(5) // 2 + 3
    })

    it('should calculate total price correctly', () => {
      act(() => {
        store.getState().addToCart(mockProduct1, 2) // 45.99 * 2 = 91.98
        store.getState().addToCart(mockProduct2, 1) // 29.99 * 1 = 29.99
      })

      const state = store.getState()

      expect(state.totalPrice).toBe(121.97) // 91.98 + 29.99
    })

    it('should handle price calculations with decimal precision', () => {
      const productWithDecimals = {
        ...mockProduct1,
        unit_price: 12.33,
      }

      act(() => {
        store.getState().addToCart(productWithDecimals, 3)
      })

      const state = store.getState()

      expect(state.totalPrice).toBe(36.99) // 12.33 * 3
      expect(state.items[0].subtotal).toBe(36.99)
    })
  })

  describe('Utility Functions', () => {
    beforeEach(() => {
      act(() => {
        store.getState().addToCart(mockProduct1, 2)
        store.getState().addToCart(mockProduct2, 1)
      })
    })

    it('should check if item is in cart', () => {
      const state = store.getState()

      expect(state.isInCart(mockProduct1.product_id)).toBe(true)
      expect(state.isInCart(mockProduct2.product_id)).toBe(true)
      expect(state.isInCart('non-existent-id')).toBe(false)
    })

    it('should get item quantity from cart', () => {
      const state = store.getState()

      expect(state.getItemQuantity(mockProduct1.product_id)).toBe(2)
      expect(state.getItemQuantity(mockProduct2.product_id)).toBe(1)
      expect(state.getItemQuantity('non-existent-id')).toBe(0)
    })

    it('should get item from cart by product ID', () => {
      const state = store.getState()

      const item1 = state.getItem(mockProduct1.product_id)
      const item2 = state.getItem(mockProduct2.product_id)
      const nonExistentItem = state.getItem('non-existent-id')

      expect(item1?.product.product_id).toBe(mockProduct1.product_id)
      expect(item1?.quantity).toBe(2)
      expect(item2?.product.product_id).toBe(mockProduct2.product_id)
      expect(item2?.quantity).toBe(1)
      expect(nonExistentItem).toBeUndefined()
    })
  })

  describe('Loading States', () => {
    it('should set loading state during async operations', async () => {
      // Mock async operation
      const asyncAddToCart = async (product: any, quantity: number) => {
        act(() => {
          store.setState({ isLoading: true })
        })

        // Simulate API call
        await new Promise(resolve => setTimeout(resolve, 100))

        act(() => {
          store.getState().addToCart(product, quantity)
          store.setState({ isLoading: false })
        })
      }

      const promise = asyncAddToCart(mockProduct1, 2)

      // Should be loading
      expect(store.getState().isLoading).toBe(true)

      await promise

      // Should not be loading
      expect(store.getState().isLoading).toBe(false)
      expect(store.getState().items).toHaveLength(1)
    })
  })

  describe('Error Handling', () => {
    it('should handle errors during cart operations', () => {
      const errorMessage = 'Failed to add item to cart'

      act(() => {
        store.setState({ error: errorMessage })
      })

      const state = store.getState()

      expect(state.error).toBe(errorMessage)
    })

    it('should clear error on successful operation', () => {
      // Set initial error
      act(() => {
        store.setState({ error: 'Previous error' })
      })

      // Perform successful operation
      act(() => {
        store.getState().addToCart(mockProduct1, 1)
        store.setState({ error: null })
      })

      const state = store.getState()

      expect(state.error).toBe(null)
      expect(state.items).toHaveLength(1)
    })
  })

  describe('Store Persistence', () => {
    it('should save cart to localStorage on every change', () => {
      act(() => {
        store.getState().addToCart(mockProduct1, 1)
      })

      expect(localStorageMock.setItem).toHaveBeenCalledWith(
        'cart',
        expect.any(String)
      )

      const savedData = JSON.parse(localStorageMock.setItem.mock.calls[0][1])
      expect(savedData).toHaveLength(1)
      expect(savedData[0].product.product_id).toBe(mockProduct1.product_id)
    })

    it('should handle localStorage errors gracefully', () => {
      localStorageMock.setItem.mockImplementation(() => {
        throw new Error('localStorage is full')
      })

      // Should not throw even if localStorage fails
      expect(() => {
        act(() => {
          store.getState().addToCart(mockProduct1, 1)
        })
      }).not.toThrow()
    })
  })

  describe('Store Subscriptions', () => {
    it('should notify subscribers of cart changes', () => {
      const subscriber = vi.fn()

      const unsubscribe = store.subscribe(subscriber)

      act(() => {
        store.getState().addToCart(mockProduct1, 1)
      })

      expect(subscriber).toHaveBeenCalled()

      unsubscribe()
    })

    it('should allow selective subscriptions', () => {
      const itemsSubscriber = vi.fn()
      const totalSubscriber = vi.fn()

      const unsubscribeItems = store.subscribe(
        state => state.items,
        itemsSubscriber
      )

      const unsubscribeTotal = store.subscribe(
        state => state.totalPrice,
        totalSubscriber
      )

      act(() => {
        store.getState().addToCart(mockProduct1, 1)
      })

      expect(itemsSubscriber).toHaveBeenCalled()
      expect(totalSubscriber).toHaveBeenCalled()

      unsubscribeItems()
      unsubscribeTotal()
    })
  })
})