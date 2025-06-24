const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

// Interfaces matching backend schemas
export interface OrderAddress {
  first_name: string
  last_name: string
  company?: string
  address_line_1: string
  address_line_2?: string
  city: string
  state: string
  postal_code: string
  country: string
  phone?: string
}

export interface CheckoutData {
  payment_method: 'stripe' | 'paypal' | 'bank_transfer'
  shipping_address: OrderAddress
  billing_address?: OrderAddress
}

export interface OrderItem {
  item_id: string
  product_id: number
  product_name: string
  product_sku: string
  quantity: number
  unit_price: number
  line_total: number
  discount_amount: number
}

export interface Order {
  order_id: string
  user_id: string
  status: 'PENDING' | 'CONFIRMED' | 'PROCESSING' | 'SHIPPED' | 'DELIVERED' | 'CANCELLED'
  payment_status: 'PENDING' | 'AUTHORIZED' | 'CAPTURED' | 'FAILED' | 'REFUNDED'
  subtotal: number
  tax_amount: number
  shipping_cost: number
  total_amount: number
  payment_method: string
  shipping_address: OrderAddress
  billing_address: OrderAddress
  tracking_number?: string
  estimated_delivery?: string
  created_at: string
  updated_at: string
  items: OrderItem[]
}

export interface OrderTotals {
  subtotal: number
  tax_amount: number
  shipping_cost: number
  total_amount: number
}

class OrderService {
  private async fetchWithAuth(url: string, options: RequestInit = {}) {
    const token = localStorage.getItem('authToken')
    
    const response = await fetch(`${API_BASE_URL}${url}`, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...(token && { Authorization: `Bearer ${token}` }),
        ...options.headers,
      },
    })

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Network error' }))
      throw new Error(error.detail || `HTTP error! status: ${response.status}`)
    }

    return response.json()
  }

  // Calculate order totals before checkout
  async calculateOrderTotals(checkoutData: CheckoutData): Promise<OrderTotals> {
    return this.fetchWithAuth('/orders/checkout/calculate', {
      method: 'POST',
      body: JSON.stringify(checkoutData),
    })
  }

  // Validate checkout data
  async validateCheckout(checkoutData: CheckoutData): Promise<{ valid: boolean; errors?: string[] }> {
    return this.fetchWithAuth('/orders/checkout/validate', {
      method: 'POST',
      body: JSON.stringify(checkoutData),
    })
  }

  // Create order and initiate payment
  async confirmCheckout(checkoutData: CheckoutData): Promise<{
    order: Order
    payment_url?: string // For PayPal redirects
    client_secret?: string // For Stripe
  }> {
    return this.fetchWithAuth('/orders/checkout/confirm', {
      method: 'POST',
      body: JSON.stringify(checkoutData),
    })
  }

  // Get user's orders
  async getMyOrders(page: number = 1, pageSize: number = 10, status?: string[]): Promise<{
    orders: Order[]
    total: number
    page: number
    page_size: number
    total_pages: number
  }> {
    const params = new URLSearchParams({
      page: page.toString(),
      page_size: pageSize.toString(),
    })

    if (status && status.length > 0) {
      status.forEach(s => params.append('status', s))
    }

    return this.fetchWithAuth(`/orders/my-orders?${params}`)
  }

  // Get specific order
  async getOrderById(orderId: string): Promise<Order> {
    return this.fetchWithAuth(`/orders/my-orders/${orderId}`)
  }

  // Cancel order
  async cancelOrder(orderId: string, reason: string): Promise<Order> {
    return this.fetchWithAuth(`/orders/${orderId}/cancel?reason=${encodeURIComponent(reason)}`, {
      method: 'POST',
    })
  }

  // Get available payment methods
  async getPaymentMethods(): Promise<{
    stripe: { enabled: boolean; fee_percentage: number; min_amount: number; max_amount: number }
    paypal: { enabled: boolean; fee_percentage: number; min_amount: number; max_amount: number }
    bank_transfer: { enabled: boolean; fee_fixed: number; min_amount: number; max_amount: number }
  }> {
    return this.fetchWithAuth('/payments/methods')
  }

  // Process payment (for Stripe confirmations)
  async processPayment(paymentData: {
    payment_id: string
    payment_method_data?: any
    stripe_payment_method_id?: string
    stripe_customer_id?: string
    paypal_order_id?: string
  }): Promise<{
    success: boolean
    order: Order
    error?: string
  }> {
    return this.fetchWithAuth('/payments/process', {
      method: 'POST',
      body: JSON.stringify(paymentData),
    })
  }
}

export const orderService = new OrderService()
export default orderService