/**
 * CartService - Frontend Cart API Integration
 * 
 * Provides cart operations with backend integration
 * Handles cart persistence, validation, and real-time updates
 */

import { request } from "../client/core/request"
import type { ApiRequestOptions } from "../client/core/ApiRequestOptions"

// Cart types
export interface CartItemRequest {
  product_id: string
  quantity: number
}

export interface CartItemResponse {
  id: string
  product_id: string
  product_name: string
  product_image?: string
  price: number
  quantity: number
  subtotal: number
  stock_available: number
}

export interface CartResponse {
  id?: string
  items: CartItemResponse[]
  total_price: number
  item_count: number
  total_items: number
  last_updated: string
}

export interface UpdateCartItemRequest {
  quantity: number
}

export class CartService {
  /**
   * Get current user's cart
   */
  public static async getCart(options?: ApiRequestOptions): Promise<CartResponse> {
    return await request({
      method: "GET",
      url: "/api/v1/cart",
      ...options,
    })
  }

  /**
   * Add item to cart
   */
  public static async addToCart({
    requestBody,
    ...options
  }: {
    requestBody: CartItemRequest
  } & ApiRequestOptions): Promise<CartResponse> {
    return await request({
      method: "POST",
      url: "/api/v1/cart/items",
      body: requestBody,
      mediaType: "application/json",
      ...options,
    })
  }

  /**
   * Update cart item quantity
   */
  public static async updateCartItem({
    productId,
    requestBody,
    ...options
  }: {
    productId: string
    requestBody: UpdateCartItemRequest
  } & ApiRequestOptions): Promise<CartResponse> {
    return await request({
      method: "PUT",
      url: `/api/v1/cart/items/${encodeURIComponent(productId)}`,
      body: requestBody,
      mediaType: "application/json",
      ...options,
    })
  }

  /**
   * Remove item from cart
   */
  public static async removeFromCart({
    productId,
    ...options
  }: {
    productId: string
  } & ApiRequestOptions): Promise<CartResponse> {
    return await request({
      method: "DELETE",
      url: `/api/v1/cart/items/${encodeURIComponent(productId)}`,
      ...options,
    })
  }

  /**
   * Clear entire cart
   */
  public static async clearCart(options?: ApiRequestOptions): Promise<CartResponse> {
    return await request({
      method: "DELETE",
      url: "/api/v1/cart",
      ...options,
    })
  }

  /**
   * Get cart summary (lightweight endpoint)
   */
  public static async getCartSummary(options?: ApiRequestOptions): Promise<{
    item_count: number
    total_price: number
    total_items: number
  }> {
    return await request({
      method: "GET",
      url: "/api/v1/cart/summary",
      ...options,
    })
  }

  /**
   * Validate cart items (check availability, prices)
   */
  public static async validateCart(options?: ApiRequestOptions): Promise<{
    is_valid: boolean
    issues: Array<{
      product_id: string
      issue_type: 'out_of_stock' | 'price_changed' | 'unavailable'
      message: string
      current_stock?: number
      current_price?: number
    }>
  }> {
    return await request({
      method: "POST",
      url: "/api/v1/cart/validate",
      ...options,
    })
  }

  /**
   * Apply coupon to cart
   */
  public static async applyCoupon({
    couponCode,
    ...options
  }: {
    couponCode: string
  } & ApiRequestOptions): Promise<CartResponse> {
    return await request({
      method: "POST",
      url: "/api/v1/cart/coupon",
      body: { coupon_code: couponCode },
      mediaType: "application/json",
      ...options,
    })
  }

  /**
   * Remove coupon from cart
   */
  public static async removeCoupon(options?: ApiRequestOptions): Promise<CartResponse> {
    return await request({
      method: "DELETE",
      url: "/api/v1/cart/coupon",
      ...options,
    })
  }

  /**
   * Get estimated shipping for cart
   */
  public static async getShippingEstimate({
    address,
    ...options
  }: {
    address: {
      postal_code: string
      country: string
      state?: string
    }
  } & ApiRequestOptions): Promise<{
    shipping_options: Array<{
      id: string
      name: string
      price: number
      estimated_days: number
      description: string
    }>
  }> {
    return await request({
      method: "POST",
      url: "/api/v1/cart/shipping-estimate",
      body: address,
      mediaType: "application/json",
      ...options,
    })
  }

  /**
   * Save cart for later (wishlist functionality)
   */
  public static async saveForLater({
    productId,
    ...options
  }: {
    productId: string
  } & ApiRequestOptions): Promise<{ success: boolean }> {
    return await request({
      method: "POST",
      url: `/api/v1/cart/items/${encodeURIComponent(productId)}/save-later`,
      ...options,
    })
  }

  /**
   * Move item from saved to cart
   */
  public static async moveToCart({
    productId,
    quantity = 1,
    ...options
  }: {
    productId: string
    quantity?: number
  } & ApiRequestOptions): Promise<CartResponse> {
    return await request({
      method: "POST",
      url: `/api/v1/cart/items/${encodeURIComponent(productId)}/move-to-cart`,
      body: { quantity },
      mediaType: "application/json",
      ...options,
    })
  }
}