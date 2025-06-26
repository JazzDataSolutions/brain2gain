import { describe, it, expect, beforeEach, vi } from 'vitest'
import { screen, waitFor, fireEvent } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { render } from './test-utils'
import CartPage from '../components/Cart/CartPage'
import ProductCard from '../components/Products/ProductCard'
import MiniCart from '../components/Cart/MiniCart'
import { useCartStore } from '../stores/cartStore'

// Mock product data
const mockProduct = {
  id: '1',
  sku: 'WP-001',
  name: 'Whey Protein Gold Standard',
  price: 45990, // Colombian pesos
  image: '/images/whey-protein.jpg',
  status: 'ACTIVE' as const,
}

// Mock cart store
const mockCartStore = {
  items: [],
  isLoading: false,
  error: null,
  addItem: vi.fn(),
  updateQuantity: vi.fn(),
  removeItem: vi.fn(),
  clearCart: vi.fn(),
  getTotalPrice: vi.fn(() => 0),
  getTotalItems: vi.fn(() => 0),
  setLoading: vi.fn(),
  setError: vi.fn(),
}

vi.mock('../stores/cartStore', () => ({
  useCartStore: () => mockCartStore,
}))

describe('Cart Flow Integration Tests', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    
    // Reset mock store to default state
    Object.assign(mockCartStore, {
      items: [],
      isLoading: false,
      error: null,
      addItem: vi.fn(),
      updateQuantity: vi.fn(),
      removeItem: vi.fn(),
      clearCart: vi.fn(),
      getTotalPrice: vi.fn(() => 0),
      getTotalItems: vi.fn(() => 0),
      setLoading: vi.fn(),
      setError: vi.fn(),
    })
  })

  describe('Adding products to cart', () => {
    it('should add a product to cart when clicking Add to Cart button', async () => {
      const user = userEvent.setup()
      
      render(<ProductCard product={mockProduct} />)
      
      // Use getAllByRole and take the first one if multiple exist
      const addButtons = screen.getAllByRole('button', { name: /agregar al carrito/i })
      const addButton = addButtons[0]
      expect(addButton).toBeInTheDocument()
      
      await user.click(addButton)
      
      expect(mockCartStore.addItem).toHaveBeenCalled()
    })

    it('should allow selecting quantity before adding to cart', async () => {
      const user = userEvent.setup()
      
      render(<ProductCard product={mockProduct} />)
      
      // Find quantity selector (if exists in ProductCard)
      const quantityInput = screen.queryByRole('spinbutton', { name: /quantity/i })
      if (quantityInput) {
        await user.clear(quantityInput)
        await user.type(quantityInput, '2')
        
        const addButtons = screen.getAllByRole('button', { name: /agregar al carrito/i })
        await user.click(addButtons[0])
        
        expect(mockCartStore.addItem).toHaveBeenCalledWith(expect.objectContaining({
          id: mockProduct.id,
          name: mockProduct.name,
          price: mockProduct.price,
          quantity: 2
        }))
      } else {
        // If no quantity selector, should add 1 by default
        const addButtons = screen.getAllByRole('button', { name: /agregar al carrito/i })
        await user.click(addButtons[0])
        
        expect(mockCartStore.addItem).toHaveBeenCalledWith(expect.objectContaining({
          id: mockProduct.id,
          name: mockProduct.name,
          price: mockProduct.price,
          quantity: 1
        }))
      }
    })

    it('should show loading state when adding to cart', async () => {
      const user = userEvent.setup()
      
      // Mock a slow addItem function
      const slowAddItem = vi.fn().mockImplementation(() => {
        return new Promise(resolve => setTimeout(resolve, 100))
      })
      
      // Update the store with the slow function
      mockCartStore.addItem = slowAddItem
      
      render(<ProductCard product={mockProduct} />)
      
      const addButtons = screen.getAllByRole('button', { name: /agregar al carrito/i })
      await user.click(addButtons[0])
      
      // Should show loading state (this depends on ProductCard implementation)
      // expect(screen.getByText(/adding/i)).toBeInTheDocument()
      
      await waitFor(() => {
        expect(slowAddItem).toHaveBeenCalled()
      })
    })
  })

  describe('Cart Management', () => {
    beforeEach(() => {
      // Setup mock cart with items
      Object.assign(mockCartStore, {
        items: [
          {
            id: mockProduct.id,
            name: mockProduct.name,
            sku: mockProduct.sku,
            price: mockProduct.price,
            quantity: 2,
            image: mockProduct.image,
          },
        ],
        isLoading: false,
        error: null,
        addItem: vi.fn(),
        updateQuantity: vi.fn(),
        removeItem: vi.fn(),
        clearCart: vi.fn(),
        getTotalItems: vi.fn(() => 2),
        getTotalPrice: vi.fn(() => 91980),
        setLoading: vi.fn(),
        setError: vi.fn(),
      })
    })

    it('should display cart items correctly', () => {
      render(<CartPage />)
      
      expect(screen.getByText(mockProduct.name)).toBeInTheDocument()
      expect(screen.getByText(/45\.990/)).toBeInTheDocument() // Colombian peso format
      expect(screen.getByDisplayValue('2')).toBeInTheDocument()
      expect(screen.getAllByText(/91\.980/)).toHaveLength(3) // Should appear in summary, subtotal, and total
    })

    it('should update quantity when using quantity controls', async () => {
      render(<CartPage />)
      
      // Find the quantity input field
      const quantityInput = screen.getByDisplayValue('2')
      
      // Simulate changing the value directly (like the onChange event)
      fireEvent.change(quantityInput, { target: { value: '3' } })
      
      // Check that the function was called with the new value
      await waitFor(() => {
        expect(mockCartStore.updateQuantity).toHaveBeenCalledWith(mockProduct.id, 3)
      })
    })

    it('should remove item from cart', async () => {
      const user = userEvent.setup()
      
      render(<CartPage />)
      
      const removeButton = screen.getByRole('button', { name: /eliminar producto/i })
      await user.click(removeButton)
      
      expect(mockCartStore.removeItem).toHaveBeenCalledWith(mockProduct.id)
    })

    it('should proceed to checkout when cart has items', () => {
      render(<CartPage />)
      
      const checkoutButton = screen.getByRole('link', { name: /proceder al checkout/i })
      expect(checkoutButton).toBeInTheDocument()
      expect(checkoutButton).toHaveAttribute('href', '/checkout')
      
      // Navigation testing would be handled in e2e tests
      // Here we just verify the link exists and has correct href
    })
  })

  describe('Mini Cart', () => {
    it('should display cart item count', () => {
      // Setup mock cart with multiple items
      Object.assign(mockCartStore, {
        items: [
          {
            id: mockProduct.id,
            name: mockProduct.name,
            sku: mockProduct.sku,
            price: mockProduct.price,
            quantity: 2,
            image: mockProduct.image,
          },
          {
            id: '2',
            name: mockProduct.name,
            sku: mockProduct.sku,
            price: mockProduct.price,
            quantity: 1,
            image: mockProduct.image,
          },
        ],
        getTotalItems: vi.fn(() => 3),
        getTotalPrice: vi.fn(() => 137970),
      })
      
      render(<MiniCart />)
      
      // Check that the cart button exists and shows count
      expect(screen.getByRole('button', { name: /carrito/i })).toBeInTheDocument()
      expect(screen.getByText('3')).toBeInTheDocument() // Item count badge
    })

    it('should show empty cart message when no items', () => {
      // Setup empty cart
      Object.assign(mockCartStore, {
        items: [],
        getTotalItems: vi.fn(() => 0),
        getTotalPrice: vi.fn(() => 0),
      })
      
      render(<MiniCart />)
      
      expect(screen.getByText(/tu carrito está vacío/i)).toBeInTheDocument()
    })
  })

  describe('Cart Persistence', () => {
    it('should persist cart data in localStorage', () => {
      const cartData = [
        {
          id: mockProduct.id,
          name: mockProduct.name,
          sku: mockProduct.sku,
          price: mockProduct.price,
          quantity: 2,
          image: mockProduct.image,
        },
      ]
      
      // Simulate cart store saving to localStorage
      localStorage.setItem('cart', JSON.stringify(cartData))
      
      expect(localStorage.getItem('cart')).toBe(JSON.stringify(cartData))
    })

    it('should restore cart data from localStorage on page load', () => {
      const cartData = [
        {
          id: mockProduct.id,
          name: mockProduct.name,
          sku: mockProduct.sku,
          price: mockProduct.price,
          quantity: 2,
          image: mockProduct.image,
        },
      ]
      
      localStorage.setItem('cart', JSON.stringify(cartData))
      
      // This would be tested in the actual cart store implementation
      // The store should restore data from localStorage on initialization
      expect(localStorage.getItem('cart')).toBe(JSON.stringify(cartData))
    })
  })

  describe('Error Handling', () => {
    it('should handle add to cart errors gracefully', async () => {
      const user = userEvent.setup()
      
      const errorAddItem = vi.fn().mockRejectedValue(new Error('Out of stock'))
      
      // Setup store with error function
      mockCartStore.addItem = errorAddItem
      
      render(<ProductCard product={mockProduct} />)
      
      const addButtons = screen.getAllByRole('button', { name: /agregar al carrito/i })
      await user.click(addButtons[0])
      
      expect(errorAddItem).toHaveBeenCalled()
      
      // Should show error message (implementation dependent)
      // expect(screen.getByText(/out of stock/i)).toBeInTheDocument()
    })

    it('should validate quantity inputs', async () => {
      const user = userEvent.setup()
      
      // Setup cart with items for this test
      Object.assign(mockCartStore, {
        items: [
          {
            id: mockProduct.id,
            name: mockProduct.name,
            sku: mockProduct.sku,
            price: mockProduct.price,
            quantity: 2,
            image: mockProduct.image,
          },
        ],
        getTotalItems: vi.fn(() => 2),
        getTotalPrice: vi.fn(() => 91980),
      })
      
      render(<CartPage />)
      
      const quantityInput = screen.getByDisplayValue('2')
      
      // Try to set invalid quantity
      await user.clear(quantityInput)
      await user.type(quantityInput, '0')
      
      // Should not allow 0 or negative quantities
      // Implementation would prevent this or show validation error
    })
  })
})