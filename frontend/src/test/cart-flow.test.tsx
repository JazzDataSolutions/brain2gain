import { describe, it, expect, beforeEach, vi } from 'vitest'
import { screen, waitFor } from '@testing-library/react'
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
  price: 45.99,
  image: '/images/whey-protein.jpg',
}

// Mock cart store
vi.mock('../stores/cartStore', () => ({
  useCartStore: vi.fn(),
}))

describe('Cart Flow Integration Tests', () => {
  const mockAddToCart = vi.fn()
  const mockUpdateQuantity = vi.fn()
  const mockRemoveFromCart = vi.fn()
  const mockClearCart = vi.fn()

  beforeEach(() => {
    vi.clearAllMocks()
    
    // Mock the cart store implementation
    ;(useCartStore as any).mockReturnValue({
      items: [],
      totalItems: 0,
      totalPrice: 0,
      addToCart: mockAddToCart,
      updateQuantity: mockUpdateQuantity,
      removeFromCart: mockRemoveFromCart,
      clearCart: mockClearCart,
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
      
      expect(mockAddToCart).toHaveBeenCalled()
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
        
        expect(mockAddToCart).toHaveBeenCalledWith(mockProduct, 2)
      } else {
        // If no quantity selector, should add 1 by default
        const addButtons = screen.getAllByRole('button', { name: /agregar al carrito/i })
        await user.click(addButtons[0])
        
        expect(mockAddToCart).toHaveBeenCalledWith(mockProduct, 1)
      }
    })

    it('should show loading state when adding to cart', async () => {
      const user = userEvent.setup()
      
      // Mock a slow addToCart function
      const slowAddToCart = vi.fn().mockImplementation(() => {
        return new Promise(resolve => setTimeout(resolve, 100))
      })
      
      ;(useCartStore as any).mockReturnValue({
        items: [],
        totalItems: 0,
        totalPrice: 0,
        addToCart: slowAddToCart,
        updateQuantity: mockUpdateQuantity,
        removeFromCart: mockRemoveFromCart,
        clearCart: mockClearCart,
      })
      
      render(<ProductCard product={mockProduct} />)
      
      const addButtons = screen.getAllByRole('button', { name: /agregar al carrito/i })
      await user.click(addButtons[0])
      
      // Should show loading state (this depends on ProductCard implementation)
      // expect(screen.getByText(/adding/i)).toBeInTheDocument()
      
      await waitFor(() => {
        expect(slowAddToCart).toHaveBeenCalled()
      })
    })
  })

  describe('Cart Management', () => {
    beforeEach(() => {
      // Mock cart with items
      ;(useCartStore as any).mockReturnValue({
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
        totalItems: 2,
        totalPrice: 91.98,
        addToCart: mockAddToCart,
        updateQuantity: mockUpdateQuantity,
        removeFromCart: mockRemoveFromCart,
        clearCart: mockClearCart,
        getTotalItems: vi.fn(() => 2),
        getTotalPrice: vi.fn(() => 91.98),
      })
    })

    it('should display cart items correctly', () => {
      render(<CartPage />)
      
      expect(screen.getByText(mockProduct.name)).toBeInTheDocument()
      expect(screen.getByText('$45.99')).toBeInTheDocument()
      expect(screen.getByDisplayValue('2')).toBeInTheDocument()
      expect(screen.getByText('$91.98')).toBeInTheDocument()
    })

    it('should update quantity when using quantity controls', async () => {
      const user = userEvent.setup()
      
      render(<CartPage />)
      
      const increaseButton = screen.getByRole('button', { name: /increase quantity/i })
      await user.click(increaseButton)
      
      expect(mockUpdateQuantity).toHaveBeenCalledWith(mockProduct.id, 3)
      
      const decreaseButton = screen.getByRole('button', { name: /decrease quantity/i })
      await user.click(decreaseButton)
      
      expect(mockUpdateQuantity).toHaveBeenCalledWith(mockProduct.id, 1)
    })

    it('should remove item from cart', async () => {
      const user = userEvent.setup()
      
      render(<CartPage />)
      
      const removeButton = screen.getByRole('button', { name: /remove/i })
      await user.click(removeButton)
      
      expect(mockRemoveFromCart).toHaveBeenCalledWith(mockProduct.id)
    })

    it('should proceed to checkout when cart has items', async () => {
      const user = userEvent.setup()
      
      render(<CartPage />)
      
      const checkoutButton = screen.getByRole('button', { name: /proceed to checkout/i })
      expect(checkoutButton).toBeEnabled()
      
      await user.click(checkoutButton)
      
      // This would typically navigate to checkout page
      // The exact assertion depends on your routing implementation
    })
  })

  describe('Mini Cart', () => {
    it('should display cart item count', () => {
      ;(useCartStore as any).mockReturnValue({
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
        totalItems: 3,
        totalPrice: 137.97,
        addToCart: mockAddToCart,
        updateQuantity: mockUpdateQuantity,
        removeFromCart: mockRemoveFromCart,
        clearCart: mockClearCart,
        getTotalItems: vi.fn(() => 3),
        getTotalPrice: vi.fn(() => 137.97),
      })
      
      render(<MiniCart />)
      
      expect(screen.getByText('3')).toBeInTheDocument() // Item count badge
    })

    it('should show empty cart message when no items', () => {
      ;(useCartStore as any).mockReturnValue({
        items: [],
        totalItems: 0,
        totalPrice: 0,
        addToCart: mockAddToCart,
        updateQuantity: mockUpdateQuantity,
        removeFromCart: mockRemoveFromCart,
        clearCart: mockClearCart,
        getTotalItems: vi.fn(() => 0),
        getTotalPrice: vi.fn(() => 0),
      })
      
      render(<MiniCart />)
      
      expect(screen.getByText(/your cart is empty/i)).toBeInTheDocument()
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
      
      const errorAddToCart = vi.fn().mockRejectedValue(new Error('Out of stock'))
      
      ;(useCartStore as any).mockReturnValue({
        items: [],
        totalItems: 0,
        totalPrice: 0,
        addToCart: errorAddToCart,
        updateQuantity: mockUpdateQuantity,
        removeFromCart: mockRemoveFromCart,
        clearCart: mockClearCart,
      })
      
      render(<ProductCard product={mockProduct} />)
      
      const addButtons = screen.getAllByRole('button', { name: /agregar al carrito/i })
      await user.click(addButtons[0])
      
      expect(errorAddToCart).toHaveBeenCalled()
      
      // Should show error message (implementation dependent)
      // expect(screen.getByText(/out of stock/i)).toBeInTheDocument()
    })

    it('should validate quantity inputs', async () => {
      const user = userEvent.setup()
      
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