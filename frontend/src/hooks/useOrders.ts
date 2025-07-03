/**
 * useOrders Hook - Complete Order Management Integration
 * 
 * Provides full order functionality with backend integration:
 * - Order creation from cart/checkout
 * - Order history and tracking
 * - Order cancellation
 * - Real-time order status updates
 * - Admin order management
 */

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { useState, useCallback } from "react"
import { OrdersService } from "../client"
import useCustomToast from "./useCustomToast"
import useAuth from "./useAuth"

// Order types (matching backend schemas)
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
  payment_method: "stripe" | "paypal" | "bank_transfer"
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
  status: "PENDING" | "CONFIRMED" | "PROCESSING" | "SHIPPED" | "DELIVERED" | "CANCELLED"
  payment_status: "PENDING" | "AUTHORIZED" | "CAPTURED" | "FAILED" | "REFUNDED"
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

export interface OrderStats {
  total_orders: number
  total_revenue: number
  average_order_value: number
  pending_orders: number
  processing_orders: number
  shipped_orders: number
  delivered_orders: number
  cancelled_orders: number
}

export interface OrderTotals {
  subtotal: number
  tax_amount: number
  shipping_cost: number
  total_amount: number
}

interface OrderFilters {
  status?: string[]
  payment_status?: string[]
  search?: string
}

const useOrders = () => {
  const { user, isAdmin } = useAuth()
  const queryClient = useQueryClient()
  const showToast = useCustomToast()
  const [filters, setFilters] = useState<OrderFilters>({})

  // Query keys
  const ordersQueryKey = ['orders', user?.id, filters]
  const orderStatsQueryKey = ['order-stats']

  // Calculate order totals
  const calculateTotalsMutation = useMutation({
    mutationFn: async (checkoutData: CheckoutData): Promise<OrderTotals> => {
      const response = await OrdersService.calculateCheckout({
        requestBody: checkoutData
      })
      return response
    },
    onError: (err: any) => {
      const errorMessage = err?.body?.detail || err?.message || "Error al calcular totales"
      showToast("Error", errorMessage, "error")
    }
  })

  // Validate checkout data
  const validateCheckoutMutation = useMutation({
    mutationFn: async (checkoutData: CheckoutData): Promise<{ valid: boolean; errors?: string[] }> => {
      const response = await OrdersService.validateCheckout({
        requestBody: checkoutData
      })
      return response
    },
    onError: (err: any) => {
      const errorMessage = err?.body?.detail || err?.message || "Error al validar checkout"
      showToast("Error", errorMessage, "error")
    }
  })

  // Create order and confirm checkout
  const confirmCheckoutMutation = useMutation({
    mutationFn: async (checkoutData: CheckoutData): Promise<{
      order_id: string
      payment_required: boolean
      payment_intent_id?: string
      payment_url?: string
    }> => {
      const response = await OrdersService.confirmCheckout({
        requestBody: checkoutData
      })
      return response
    },
    onSuccess: (data) => {
      // Invalidate orders and cart queries
      queryClient.invalidateQueries({ queryKey: ['orders'] })
      queryClient.invalidateQueries({ queryKey: ['cart'] })
      
      showToast(
        "Orden creada",
        "Tu orden ha sido creada exitosamente",
        "success"
      )
    },
    onError: (err: any) => {
      const errorMessage = err?.body?.detail || err?.message || "Error al confirmar checkout"
      showToast("Error", errorMessage, "error")
    }
  })

  // Get user's orders
  const {
    data: ordersData,
    isLoading: isLoadingOrders,
    error: ordersError,
    refetch: refetchOrders
  } = useQuery({
    queryKey: ordersQueryKey,
    queryFn: async () => {
      const response = await OrdersService.getMyOrders({
        page: 1,
        pageSize: 20,
        status: filters.status
      })
      return response
    },
    enabled: !!user && !isAdmin(), // Only for regular users
    staleTime: 1000 * 60 * 5, // 5 minutes
    gcTime: 1000 * 60 * 30, // 30 minutes
  })

  // Get all orders (admin only)
  const {
    data: allOrdersData,
    isLoading: isLoadingAllOrders,
    error: allOrdersError,
    refetch: refetchAllOrders
  } = useQuery({
    queryKey: ['all-orders', filters],
    queryFn: async () => {
      const response = await OrdersService.getAllOrders({
        page: 1,
        pageSize: 50,
        status: filters.status,
        paymentStatus: filters.payment_status,
        search: filters.search
      })
      return response
    },
    enabled: !!user && isAdmin(), // Only for admin users
    staleTime: 1000 * 60 * 2, // 2 minutes
    gcTime: 1000 * 60 * 15, // 15 minutes
  })

  // Get order statistics (admin only)
  const {
    data: orderStats,
    isLoading: isLoadingStats,
    error: statsError,
    refetch: refetchStats
  } = useQuery({
    queryKey: orderStatsQueryKey,
    queryFn: async (): Promise<OrderStats> => {
      const response = await OrdersService.getOrderStats()
      return response
    },
    enabled: !!user && isAdmin(), // Only for admin users
    staleTime: 1000 * 60 * 5, // 5 minutes
    gcTime: 1000 * 60 * 30, // 30 minutes
  })

  // Get specific order
  const getOrder = useCallback(async (orderId: string): Promise<Order | null> => {
    try {
      if (isAdmin()) {
        const response = await OrdersService.getOrderAdmin({ orderId })
        return response
      } else {
        const response = await OrdersService.getMyOrder({ orderId })
        return response
      }
    } catch (error: any) {
      const errorMessage = error?.body?.detail || error?.message || "Error al obtener orden"
      showToast("Error", errorMessage, "error")
      return null
    }
  }, [isAdmin, showToast])

  // Cancel order
  const cancelOrderMutation = useMutation({
    mutationFn: async ({ orderId, reason }: { orderId: string; reason: string }): Promise<Order> => {
      const response = await OrdersService.cancelOrder({
        orderId,
        reason
      })
      return response
    },
    onSuccess: (data) => {
      // Invalidate orders queries
      queryClient.invalidateQueries({ queryKey: ['orders'] })
      queryClient.invalidateQueries({ queryKey: ['all-orders'] })
      queryClient.invalidateQueries({ queryKey: orderStatsQueryKey })
      
      showToast(
        "Orden cancelada",
        "La orden ha sido cancelada exitosamente",
        "info"
      )
    },
    onError: (err: any) => {
      const errorMessage = err?.body?.detail || err?.message || "Error al cancelar orden"
      showToast("Error", errorMessage, "error")
    }
  })

  // Update order (admin only)
  const updateOrderMutation = useMutation({
    mutationFn: async ({ orderId, updateData }: { 
      orderId: string
      updateData: {
        status?: string
        payment_status?: string
        tracking_number?: string
        notes?: string
      }
    }): Promise<Order> => {
      const response = await OrdersService.updateOrder({
        orderId,
        requestBody: updateData
      })
      return response
    },
    onSuccess: (data) => {
      // Invalidate orders queries
      queryClient.invalidateQueries({ queryKey: ['all-orders'] })
      queryClient.invalidateQueries({ queryKey: orderStatsQueryKey })
      
      showToast(
        "Orden actualizada",
        "La orden ha sido actualizada exitosamente",
        "success"
      )
    },
    onError: (err: any) => {
      const errorMessage = err?.body?.detail || err?.message || "Error al actualizar orden"
      showToast("Error", errorMessage, "error")
    }
  })

  // Utility functions
  const calculateTotals = useCallback((checkoutData: CheckoutData) => {
    if (!user) {
      showToast("Autenticación requerida", "Debes iniciar sesión", "warning")
      return
    }
    
    calculateTotalsMutation.mutate(checkoutData)
  }, [user, calculateTotalsMutation, showToast])

  const validateCheckout = useCallback((checkoutData: CheckoutData) => {
    if (!user) {
      showToast("Autenticación requerida", "Debes iniciar sesión", "warning")
      return
    }
    
    validateCheckoutMutation.mutate(checkoutData)
  }, [user, validateCheckoutMutation, showToast])

  const confirmCheckout = useCallback((checkoutData: CheckoutData) => {
    if (!user) {
      showToast("Autenticación requerida", "Debes iniciar sesión", "warning")
      return
    }
    
    confirmCheckoutMutation.mutate(checkoutData)
  }, [user, confirmCheckoutMutation, showToast])

  const cancelOrder = useCallback((orderId: string, reason: string) => {
    if (!user) {
      showToast("Autenticación requerida", "Debes iniciar sesión", "warning")
      return
    }

    cancelOrderMutation.mutate({ orderId, reason })
  }, [user, cancelOrderMutation, showToast])

  const updateOrder = useCallback((orderId: string, updateData: any) => {
    if (!user || !isAdmin()) {
      showToast("Permisos insuficientes", "Solo administradores pueden actualizar órdenes", "warning")
      return
    }

    updateOrderMutation.mutate({ orderId, updateData })
  }, [user, isAdmin, updateOrderMutation, showToast])

  // Helper functions
  const getOrdersByStatus = useCallback((status: string) => {
    const orders = isAdmin() ? allOrdersData?.orders : ordersData?.orders
    return orders?.filter(order => order.status === status) || []
  }, [ordersData, allOrdersData, isAdmin])

  const getTotalRevenue = useCallback(() => {
    return orderStats?.total_revenue || 0
  }, [orderStats])

  const getAverageOrderValue = useCallback(() => {
    return orderStats?.average_order_value || 0
  }, [orderStats])

  const updateFilters = useCallback((newFilters: Partial<OrderFilters>) => {
    setFilters(prev => ({ ...prev, ...newFilters }))
  }, [])

  return {
    // Data
    orders: isAdmin() ? allOrdersData?.orders || [] : ordersData?.orders || [],
    orderStats: orderStats || {
      total_orders: 0,
      total_revenue: 0,
      average_order_value: 0,
      pending_orders: 0,
      processing_orders: 0,
      shipped_orders: 0,
      delivered_orders: 0,
      cancelled_orders: 0
    },
    filters,

    // Loading states
    isLoadingOrders: isAdmin() ? isLoadingAllOrders : isLoadingOrders,
    isLoadingStats,
    isCalculatingTotals: calculateTotalsMutation.isPending,
    isValidatingCheckout: validateCheckoutMutation.isPending,
    isConfirmingCheckout: confirmCheckoutMutation.isPending,
    isCancellingOrder: cancelOrderMutation.isPending,
    isUpdatingOrder: updateOrderMutation.isPending,

    // Error states
    ordersError: isAdmin() ? allOrdersError : ordersError,
    statsError,
    calculateTotalsError: calculateTotalsMutation.error,
    validateCheckoutError: validateCheckoutMutation.error,
    confirmCheckoutError: confirmCheckoutMutation.error,
    cancelOrderError: cancelOrderMutation.error,
    updateOrderError: updateOrderMutation.error,

    // Actions
    calculateTotals,
    validateCheckout,
    confirmCheckout,
    getOrder,
    cancelOrder,
    updateOrder,
    refetchOrders: isAdmin() ? refetchAllOrders : refetchOrders,
    refetchStats,
    updateFilters,

    // Results
    calculatedTotals: calculateTotalsMutation.data,
    validationResult: validateCheckoutMutation.data,
    checkoutResult: confirmCheckoutMutation.data,

    // Helpers
    getOrdersByStatus,
    getTotalRevenue,
    getAverageOrderValue,

    // Pagination info
    totalOrders: isAdmin() ? allOrdersData?.total || 0 : ordersData?.total || 0,
    currentPage: isAdmin() ? allOrdersData?.page || 1 : ordersData?.page || 1,
    totalPages: isAdmin() ? allOrdersData?.total_pages || 1 : ordersData?.total_pages || 1
  }
}

export default useOrders