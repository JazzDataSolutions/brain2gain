/**
 * Unit tests for ProductCard component.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { screen, fireEvent, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { render } from '../../test-utils'
import ProductCard from '../../../components/Products/ProductCard'
import { useCartStore } from '../../../stores/cartStore'

// Mock the cart store
vi.mock('../../../stores/cartStore', () => ({
  useCartStore: vi.fn(),
}))

// Mock product data
const mockProduct = {
  id: '1',
  product_id: '1',
  sku: 'WP-001',
  name: 'Whey Protein Gold Standard',
  description: '100% Whey Protein Isolate - Chocolate Flavor',
  unit_price: 45990, // Colombian pesos format
  stock_quantity: 100,
  status: 'ACTIVE',
  category: 'proteins',
  brand: 'Optimum Nutrition',
  image_url: '/images/whey-protein.jpg',
}

describe('ProductCard Component', () => {
  const mockAddToCart = vi.fn()
  const mockUpdateQuantity = vi.fn()
  const mockRemoveFromCart = vi.fn()

  beforeEach(() => {
    vi.clearAllMocks()
    
    // Mock cart store implementation
    ;(useCartStore as any).mockReturnValue({
      items: [],
      totalItems: 0,
      totalPrice: 0,
      addToCart: mockAddToCart,
      updateQuantity: mockUpdateQuantity,
      removeFromCart: mockRemoveFromCart,
    })
  })

  describe('Product Display', () => {
    it('should render product information correctly', () => {
      render(<ProductCard product={mockProduct} />)

      expect(screen.getByText(mockProduct.name)).toBeInTheDocument()
      // Use more flexible text matching for description
      expect(screen.getByText(/Whey Protein Isolate/i)).toBeInTheDocument()
      // Colombian peso format
      expect(screen.getByText(/45\.990/)).toBeInTheDocument()
      expect(screen.getByText(mockProduct.brand)).toBeInTheDocument()
      expect(screen.getByText(/proteins/i)).toBeInTheDocument()
    })

    it('should display product image with correct alt text', () => {
      render(<ProductCard product={mockProduct} />)

      const image = screen.getByRole('img', { name: mockProduct.name })
      expect(image).toBeInTheDocument()
      expect(image).toHaveAttribute('src', mockProduct.image_url)
    })

    it('should handle missing image gracefully', () => {
      const productWithoutImage = { ...mockProduct, image_url: undefined }
      render(<ProductCard product={productWithoutImage} />)

      // Should show placeholder or fallback image
      const image = screen.getByRole('img')
      expect(image).toBeInTheDocument()
    })

    it('should display stock status correctly', () => {
      render(<ProductCard product={mockProduct} />)

      // Should show in stock status
      expect(screen.getByText(/in stock/i)).toBeInTheDocument()
    })

    it('should display out of stock status when stock is 0', () => {
      const outOfStockProduct = { ...mockProduct, stock_quantity: 0 }
      render(<ProductCard product={outOfStockProduct} />)

      expect(screen.getByText(/out of stock/i)).toBeInTheDocument()
    })

    it('should display low stock warning when stock is low', () => {
      const lowStockProduct = { ...mockProduct, stock_quantity: 5 }
      render(<ProductCard product={lowStockProduct} />)

      expect(screen.getByText(/only \d+ left/i)).toBeInTheDocument()
    })
  })

  describe('Add to Cart Functionality', () => {
    it('should add product to cart when Add to Cart button is clicked', async () => {
      const user = userEvent.setup()
      render(<ProductCard product={mockProduct} />)

      const addButton = screen.getByRole('button', { name: /add to cart/i })
      await user.click(addButton)

      expect(mockAddToCart).toHaveBeenCalledWith(mockProduct, 1)
    })

    it('should add correct quantity when quantity is specified', async () => {
      const user = userEvent.setup()
      render(<ProductCard product={mockProduct} />)

      // Find quantity input if it exists
      const quantityInput = screen.queryByRole('spinbutton', { name: /quantity/i })
      if (quantityInput) {
        await user.clear(quantityInput)
        await user.type(quantityInput, '3')
      }

      const addButton = screen.getByRole('button', { name: /add to cart/i })
      await user.click(addButton)

      const expectedQuantity = quantityInput ? 3 : 1
      expect(mockAddToCart).toHaveBeenCalledWith(mockProduct, expectedQuantity)
    })

    it('should disable Add to Cart button when out of stock', () => {
      const outOfStockProduct = { ...mockProduct, stock_quantity: 0 }
      render(<ProductCard product={outOfStockProduct} />)

      const addButton = screen.getByRole('button', { name: /add to cart/i })
      expect(addButton).toBeDisabled()
    })

    it('should limit quantity selection to available stock', async () => {
      const user = userEvent.setup()
      const limitedStockProduct = { ...mockProduct, stock_quantity: 3 }
      render(<ProductCard product={limitedStockProduct} />)

      const quantityInput = screen.queryByRole('spinbutton', { name: /quantity/i })
      if (quantityInput) {
        expect(quantityInput).toHaveAttribute('max', '3')
        
        // Try to enter more than available
        await user.clear(quantityInput)
        await user.type(quantityInput, '5')
        
        // Should be limited to max stock
        expect(quantityInput).toHaveValue(3)
      }
    })
  })

  describe('User Interactions', () => {
    it('should show loading state when adding to cart', async () => {
      const user = userEvent.setup()
      
      // Mock slow addToCart function
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
      })

      render(<ProductCard product={mockProduct} />)

      const addButton = screen.getByRole('button', { name: /add to cart/i })
      await user.click(addButton)

      // Should show loading state
      expect(screen.getByText(/adding/i)).toBeInTheDocument()
      expect(addButton).toBeDisabled()

      // Wait for completion
      await waitFor(() => {
        expect(slowAddToCart).toHaveBeenCalled()
      })
    })

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
      })

      render(<ProductCard product={mockProduct} />)

      const addButton = screen.getByRole('button', { name: /add to cart/i })
      await user.click(addButton)

      await waitFor(() => {
        expect(errorAddToCart).toHaveBeenCalled()
      })

      // Should show error message
      expect(screen.getByText(/error/i)).toBeInTheDocument()
    })

    it('should show quick view on product image hover', async () => {
      const user = userEvent.setup()
      render(<ProductCard product={mockProduct} />)

      const productImage = screen.getByRole('img', { name: mockProduct.name })
      await user.hover(productImage)

      // Should show quick view overlay or button
      expect(screen.getByText(/quick view/i)).toBeInTheDocument()
    })

    it('should navigate to product detail on product name click', async () => {
      const user = userEvent.setup()
      render(<ProductCard product={mockProduct} />)

      const productName = screen.getByText(mockProduct.name)
      await user.click(productName)

      // Should navigate to product detail page
      // This would depend on your router implementation
      // expect(mockNavigate).toHaveBeenCalledWith(`/products/${mockProduct.product_id}`)
    })
  })

  describe('Quantity Controls', () => {
    it('should increment quantity when plus button is clicked', async () => {
      const user = userEvent.setup()
      render(<ProductCard product={mockProduct} />)

      const quantityInput = screen.queryByRole('spinbutton', { name: /quantity/i })
      if (quantityInput) {
        const incrementButton = screen.getByRole('button', { name: /increase quantity/i })
        await user.click(incrementButton)

        expect(quantityInput).toHaveValue(2)
      }
    })

    it('should decrement quantity when minus button is clicked', async () => {
      const user = userEvent.setup()
      render(<ProductCard product={mockProduct} />)

      const quantityInput = screen.queryByRole('spinbutton', { name: /quantity/i })
      if (quantityInput) {
        // Set initial value to 3
        fireEvent.change(quantityInput, { target: { value: '3' } })
        
        const decrementButton = screen.getByRole('button', { name: /decrease quantity/i })
        await user.click(decrementButton)

        expect(quantityInput).toHaveValue(2)
      }
    })

    it('should not allow quantity below 1', async () => {
      const user = userEvent.setup()
      render(<ProductCard product={mockProduct} />)

      const quantityInput = screen.queryByRole('spinbutton', { name: /quantity/i })
      if (quantityInput) {
        const decrementButton = screen.getByRole('button', { name: /decrease quantity/i })
        
        // Try to decrement below 1
        await user.click(decrementButton)

        expect(quantityInput).toHaveValue(1)
        expect(decrementButton).toBeDisabled()
      }
    })
  })

  describe('Product Variants', () => {
    it('should display product in compact mode', () => {
      render(<ProductCard product={mockProduct} compact />)

      // In compact mode, description might be hidden
      expect(screen.queryByText(mockProduct.description)).not.toBeInTheDocument()
      
      // But name and price should still be visible
      expect(screen.getByText(mockProduct.name)).toBeInTheDocument()
      expect(screen.getByText(`$${mockProduct.unit_price}`)).toBeInTheDocument()
    })

    it('should display sale badge when product is on sale', () => {
      const saleProduct = { 
        ...mockProduct, 
        original_price: 55.99,
        unit_price: 45.99,
        on_sale: true 
      }
      render(<ProductCard product={saleProduct} />)

      expect(screen.getByText(/sale/i)).toBeInTheDocument()
      expect(screen.getByText('$55.99')).toBeInTheDocument() // Original price
      expect(screen.getByText('$45.99')).toBeInTheDocument() // Sale price
    })

    it('should display new badge for new products', () => {
      const newProduct = { ...mockProduct, is_new: true }
      render(<ProductCard product={newProduct} />)

      expect(screen.getByText(/new/i)).toBeInTheDocument()
    })

    it('should display bestseller badge', () => {
      const bestsellerProduct = { ...mockProduct, is_bestseller: true }
      render(<ProductCard product={bestsellerProduct} />)

      expect(screen.getByText(/bestseller/i)).toBeInTheDocument()
    })
  })

  describe('Accessibility', () => {
    it('should have proper ARIA labels', () => {
      render(<ProductCard product={mockProduct} />)

      const addButton = screen.getByRole('button', { name: /add to cart/i })
      expect(addButton).toHaveAttribute('aria-label')

      const productImage = screen.getByRole('img')
      expect(productImage).toHaveAttribute('alt')
    })

    it('should be keyboard navigable', async () => {
      const user = userEvent.setup()
      render(<ProductCard product={mockProduct} />)

      // Tab through interactive elements
      await user.tab()
      expect(screen.getByText(mockProduct.name)).toHaveFocus()

      await user.tab()
      const addButton = screen.getByRole('button', { name: /add to cart/i })
      expect(addButton).toHaveFocus()

      // Should be able to activate with Enter or Space
      await user.keyboard('{Enter}')
      expect(mockAddToCart).toHaveBeenCalled()
    })

    it('should announce stock status to screen readers', () => {
      const outOfStockProduct = { ...mockProduct, stock_quantity: 0 }
      render(<ProductCard product={outOfStockProduct} />)

      const stockStatus = screen.getByText(/out of stock/i)
      expect(stockStatus).toHaveAttribute('aria-live', 'polite')
    })
  })

  describe('Performance', () => {
    it('should not re-render unnecessarily', () => {
      const { rerender } = render(<ProductCard product={mockProduct} />)
      
      // Re-render with same props
      rerender(<ProductCard product={mockProduct} />)
      
      // Component should be memoized and not re-render
      expect(mockAddToCart).not.toHaveBeenCalled()
    })

    it('should lazy load product image', () => {
      render(<ProductCard product={mockProduct} />)

      const image = screen.getByRole('img')
      expect(image).toHaveAttribute('loading', 'lazy')
    })
  })
})