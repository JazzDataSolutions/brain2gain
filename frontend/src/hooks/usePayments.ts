/**
 * usePayments Hook - Complete Payment Processing Integration
 * 
 * Provides full payment functionality with backend integration:
 * - Payment method management
 * - Payment processing (Stripe, PayPal, Bank Transfer)
 * - Payment history and tracking
 * - Refund management (admin)
 * - Real-time payment status updates
 */

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { useState, useCallback } from "react"
import { PaymentsService } from "../client"
import useCustomToast from "./useCustomToast"
import useAuth from "./useAuth"

// Payment types (matching backend schemas)
export interface PaymentMethod {
  id: string
  type: "stripe" | "paypal" | "bank_transfer"
  enabled: boolean
  fee_percentage?: number
  fee_fixed?: number
  min_amount: number
  max_amount: number
  display_name: string
  description: string
  icon?: string
}

export interface PaymentProcess {
  payment_id: string
  stripe_payment_method_id?: string
  stripe_customer_id?: string
  paypal_order_id?: string
  payment_method_data?: any
}

export interface Payment {
  payment_id: string
  order_id: string
  payment_method: string
  amount: number
  currency: string
  status: "PENDING" | "AUTHORIZED" | "CAPTURED" | "FAILED" | "REFUNDED" | "CANCELLED"
  gateway_payment_id?: string
  gateway_customer_id?: string
  gateway_response?: any
  failure_reason?: string
  processed_at?: string
  created_at: string
  updated_at: string
}

export interface PaymentStats {
  total_payments: number
  total_revenue: number
  pending_payments: number
  authorized_payments: number
  captured_payments: number
  failed_payments: number
  refunded_payments: number
  average_payment_amount: number
  payment_methods_breakdown: Record<string, number>
}

export interface Refund {
  refund_id: string
  payment_id: string
  amount: number
  reason: string
  status: "PENDING" | "COMPLETED" | "FAILED"
  gateway_refund_id?: string
  processed_at?: string
  created_at: string
}

export interface PaymentProcessResponse {
  success: boolean
  payment: Payment
  client_secret?: string // For Stripe
  approval_url?: string // For PayPal
  error?: string
}

interface PaymentFilters {
  status?: string[]
  payment_method?: string[]
  order_id?: string
}

const usePayments = () => {
  const { user, isAdmin } = useAuth()
  const queryClient = useQueryClient()
  const showToast = useCustomToast()
  const [filters, setFilters] = useState<PaymentFilters>({})

  // Query keys
  const paymentsQueryKey = ['payments', user?.id, filters]
  const paymentStatsQueryKey = ['payment-stats']
  const paymentMethodsQueryKey = ['payment-methods']

  // Get available payment methods
  const {
    data: paymentMethods,
    isLoading: isLoadingMethods,
    error: methodsError,
    refetch: refetchMethods
  } = useQuery({
    queryKey: paymentMethodsQueryKey,
    queryFn: async (): Promise<PaymentMethod[]> => {
      const response = await PaymentsService.getPaymentMethods()
      
      // Transform backend response to frontend format
      const methods: PaymentMethod[] = []
      
      if (response.stripe?.enabled) {
        methods.push({
          id: 'stripe',
          type: 'stripe',
          enabled: true,
          fee_percentage: response.stripe.fee_percentage,
          min_amount: response.stripe.min_amount,
          max_amount: response.stripe.max_amount,
          display_name: 'Tarjeta de Crédito/Débito',
          description: 'Pago seguro con Stripe',
          icon: 'credit-card'
        })
      }
      
      if (response.paypal?.enabled) {
        methods.push({
          id: 'paypal',
          type: 'paypal',
          enabled: true,
          fee_percentage: response.paypal.fee_percentage,
          min_amount: response.paypal.min_amount,
          max_amount: response.paypal.max_amount,
          display_name: 'PayPal',
          description: 'Pago con PayPal',
          icon: 'paypal'
        })
      }
      
      if (response.bank_transfer?.enabled) {
        methods.push({
          id: 'bank_transfer',
          type: 'bank_transfer',
          enabled: true,
          fee_fixed: response.bank_transfer.fee_fixed,
          min_amount: response.bank_transfer.min_amount,
          max_amount: response.bank_transfer.max_amount,
          display_name: 'Transferencia Bancaria',
          description: 'Transferencia bancaria directa',
          icon: 'bank'
        })
      }
      
      return methods
    },
    staleTime: 1000 * 60 * 15, // 15 minutes
    gcTime: 1000 * 60 * 60, // 1 hour
  })

  // Get user's payments
  const {
    data: userPayments,
    isLoading: isLoadingPayments,
    error: paymentsError,
    refetch: refetchPayments
  } = useQuery({
    queryKey: paymentsQueryKey,
    queryFn: async (): Promise<Payment[]> => {
      const response = await PaymentsService.getMyPayments({
        page: 1,
        pageSize: 50,
        status: filters.status
      })
      return response
    },
    enabled: !!user && !isAdmin(), // Only for regular users
    staleTime: 1000 * 60 * 2, // 2 minutes
    gcTime: 1000 * 60 * 15, // 15 minutes
  })

  // Get all payments (admin only)
  const {
    data: allPayments,
    isLoading: isLoadingAllPayments,
    error: allPaymentsError,
    refetch: refetchAllPayments
  } = useQuery({
    queryKey: ['all-payments', filters],
    queryFn: async (): Promise<Payment[]> => {
      const response = await PaymentsService.getAllPayments({
        page: 1,
        pageSize: 100,
        status: filters.status,
        paymentMethod: filters.payment_method,
        orderId: filters.order_id
      })
      return response
    },
    enabled: !!user && isAdmin(), // Only for admin users
    staleTime: 1000 * 60 * 2, // 2 minutes
    gcTime: 1000 * 60 * 15, // 15 minutes
  })

  // Get payment statistics (admin only)
  const {
    data: paymentStats,
    isLoading: isLoadingStats,
    error: statsError,
    refetch: refetchStats
  } = useQuery({
    queryKey: paymentStatsQueryKey,
    queryFn: async (): Promise<PaymentStats> => {
      const response = await PaymentsService.getPaymentStats()
      return response
    },
    enabled: !!user && isAdmin(), // Only for admin users
    staleTime: 1000 * 60 * 5, // 5 minutes
    gcTime: 1000 * 60 * 30, // 30 minutes
  })

  // Process payment
  const processPaymentMutation = useMutation({
    mutationFn: async (paymentData: PaymentProcess): Promise<PaymentProcessResponse> => {
      const response = await PaymentsService.processPayment({
        requestBody: paymentData
      })
      return response
    },
    onSuccess: (data) => {
      // Invalidate payment and order queries
      queryClient.invalidateQueries({ queryKey: ['payments'] })
      queryClient.invalidateQueries({ queryKey: ['orders'] })
      queryClient.invalidateQueries({ queryKey: paymentStatsQueryKey })
      
      if (data.success) {
        showToast(
          "Pago procesado",
          "Tu pago ha sido procesado exitosamente",
          "success"
        )
      } else {
        showToast(
          "Error en el pago",
          data.error || "Hubo un problema procesando el pago",
          "error"
        )
      }
    },
    onError: (err: any) => {
      const errorMessage = err?.body?.detail || err?.message || "Error al procesar pago"
      showToast("Error", errorMessage, "error")
    }
  })

  // Create refund (admin only)
  const createRefundMutation = useMutation({
    mutationFn: async ({ paymentId, amount, reason }: {
      paymentId: string
      amount?: number
      reason: string
    }): Promise<Refund> => {
      const response = await PaymentsService.createRefund({
        requestBody: {
          payment_id: paymentId,
          amount,
          reason
        }
      })
      return response
    },
    onSuccess: (data) => {
      // Invalidate payment queries
      queryClient.invalidateQueries({ queryKey: ['payments'] })
      queryClient.invalidateQueries({ queryKey: paymentStatsQueryKey })
      
      showToast(
        "Reembolso creado",
        "El reembolso ha sido procesado exitosamente",
        "success"
      )
    },
    onError: (err: any) => {
      const errorMessage = err?.body?.detail || err?.message || "Error al crear reembolso"
      showToast("Error", errorMessage, "error")
    }
  })

  // Get specific payment
  const getPayment = useCallback(async (paymentId: string): Promise<Payment | null> => {
    try {
      if (isAdmin()) {
        const response = await PaymentsService.getPaymentAdmin({ paymentId })
        return response
      } else {
        const response = await PaymentsService.getMyPayment({ paymentId })
        return response
      }
    } catch (error: any) {
      const errorMessage = error?.body?.detail || error?.message || "Error al obtener pago"
      showToast("Error", errorMessage, "error")
      return null
    }
  }, [isAdmin, showToast])

  // Utility functions
  const processPayment = useCallback((paymentData: PaymentProcess) => {
    if (!user) {
      showToast("Autenticación requerida", "Debes iniciar sesión", "warning")
      return
    }
    
    processPaymentMutation.mutate(paymentData)
  }, [user, processPaymentMutation, showToast])

  const createRefund = useCallback((paymentId: string, amount: number | undefined, reason: string) => {
    if (!user || !isAdmin()) {
      showToast("Permisos insuficientes", "Solo administradores pueden crear reembolsos", "warning")
      return
    }

    createRefundMutation.mutate({ paymentId, amount, reason })
  }, [user, isAdmin, createRefundMutation, showToast])

  // Helper functions
  const getPaymentsByStatus = useCallback((status: string) => {
    const payments = isAdmin() ? allPayments : userPayments
    return payments?.filter(payment => payment.status === status) || []
  }, [userPayments, allPayments, isAdmin])

  const getPaymentsByMethod = useCallback((method: string) => {
    const payments = isAdmin() ? allPayments : userPayments
    return payments?.filter(payment => payment.payment_method === method) || []
  }, [userPayments, allPayments, isAdmin])

  const getTotalRevenue = useCallback(() => {
    return paymentStats?.total_revenue || 0
  }, [paymentStats])

  const getAveragePaymentAmount = useCallback(() => {
    return paymentStats?.average_payment_amount || 0
  }, [paymentStats])

  const getPaymentMethodFee = useCallback((methodId: string, amount: number): number => {
    const method = paymentMethods?.find(m => m.id === methodId)
    if (!method) return 0
    
    if (method.fee_percentage) {
      return (amount * method.fee_percentage) / 100
    }
    
    if (method.fee_fixed) {
      return method.fee_fixed
    }
    
    return 0
  }, [paymentMethods])

  const updateFilters = useCallback((newFilters: Partial<PaymentFilters>) => {
    setFilters(prev => ({ ...prev, ...newFilters }))
  }, [])

  return {
    // Data
    payments: isAdmin() ? allPayments || [] : userPayments || [],
    paymentMethods: paymentMethods || [],
    paymentStats: paymentStats || {
      total_payments: 0,
      total_revenue: 0,
      pending_payments: 0,
      authorized_payments: 0,
      captured_payments: 0,
      failed_payments: 0,
      refunded_payments: 0,
      average_payment_amount: 0,
      payment_methods_breakdown: {}
    },
    filters,

    // Loading states
    isLoadingPayments: isAdmin() ? isLoadingAllPayments : isLoadingPayments,
    isLoadingMethods,
    isLoadingStats,
    isProcessingPayment: processPaymentMutation.isPending,
    isCreatingRefund: createRefundMutation.isPending,

    // Error states
    paymentsError: isAdmin() ? allPaymentsError : paymentsError,
    methodsError,
    statsError,
    processPaymentError: processPaymentMutation.error,
    createRefundError: createRefundMutation.error,

    // Actions
    processPayment,
    createRefund,
    getPayment,
    refetchPayments: isAdmin() ? refetchAllPayments : refetchPayments,
    refetchMethods,
    refetchStats,
    updateFilters,

    // Results
    paymentResult: processPaymentMutation.data,
    refundResult: createRefundMutation.data,

    // Helpers
    getPaymentsByStatus,
    getPaymentsByMethod,
    getTotalRevenue,
    getAveragePaymentAmount,
    getPaymentMethodFee,

    // Payment method utilities
    isMethodAvailable: (methodId: string) => {
      const method = paymentMethods?.find(m => m.id === methodId)
      return method?.enabled || false
    },
    
    getMethodLimits: (methodId: string) => {
      const method = paymentMethods?.find(m => m.id === methodId)
      return {
        min: method?.min_amount || 0,
        max: method?.max_amount || Infinity
      }
    },

    // Payment status helpers
    isPending: (payment: Payment) => payment.status === "PENDING",
    isAuthorized: (payment: Payment) => payment.status === "AUTHORIZED",
    isCaptured: (payment: Payment) => payment.status === "CAPTURED",
    isFailed: (payment: Payment) => payment.status === "FAILED",
    isRefunded: (payment: Payment) => payment.status === "REFUNDED",
    isCancelled: (payment: Payment) => payment.status === "CANCELLED"
  }
}

export default usePayments