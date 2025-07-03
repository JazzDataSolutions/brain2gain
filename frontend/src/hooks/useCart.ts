/**
 * useCart Hook - Complete Cart Integration
 * 
 * Provides full cart functionality with backend integration:
 * - Add/update/remove items
 * - Persistent cart across sessions
 * - Real-time price calculations
 * - Error handling and optimistic updates
 */

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { useState, useCallback } from "react"
import { CartService } from "../client"
import useCustomToast from "./useCustomToast"
import useAuth from "./useAuth"

// Cart types
export interface CartItem {
  id: string
  product_id: string
  product_name: string
  product_image?: string
  price: number
  quantity: number
  subtotal: number
  stock_available: number
}

export interface Cart {
  id?: string
  items: CartItem[]
  total_price: number
  item_count: number
  total_items: number
  last_updated: string
}

interface AddToCartParams {
  product_id: string
  quantity: number
  product_name?: string
  price?: number
}

interface UpdateQuantityParams {
  product_id: string
  quantity: number
}

const useCart = () => {
  const { user, isAdmin } = useAuth()
  const queryClient = useQueryClient()
  const showToast = useCustomToast()
  const [optimisticUpdates, setOptimisticUpdates] = useState<Record<string, number>>({})

  // Query keys
  const cartQueryKey = ['cart', user?.id]

  // Fetch cart data
  const {
    data: cart,
    isLoading,
    error,
    refetch
  } = useQuery({
    queryKey: cartQueryKey,
    queryFn: async (): Promise<Cart> => {
      try {
        const response = await CartService.getCart()
        return response
      } catch (error: any) {
        // Handle cart not found or user not authenticated
        if (error?.status === 404 || error?.status === 401) {
          return {
            items: [],
            total_price: 0,
            item_count: 0,
            total_items: 0,
            last_updated: new Date().toISOString()
          }
        }
        throw error
      }
    },
    enabled: !!user, // Only fetch when user is authenticated
    staleTime: 1000 * 60 * 5, // 5 minutes
    gcTime: 1000 * 60 * 30, // 30 minutes
    retry: (failureCount, error: any) => {
      // Don't retry on authentication errors
      if (error?.status === 401 || error?.status === 403) {
        return false
      }
      return failureCount < 3
    }
  })

  // Add item to cart
  const addToCartMutation = useMutation({
    mutationFn: async (params: AddToCartParams) => {
      const response = await CartService.addToCart({
        requestBody: {
          product_id: params.product_id,
          quantity: params.quantity
        }
      })
      return response
    },
    onMutate: async (params) => {
      // Cancel any outgoing refetches
      await queryClient.cancelQueries({ queryKey: cartQueryKey })

      // Snapshot the previous value
      const previousCart = queryClient.getQueryData<Cart>(cartQueryKey)

      // Optimistically update cart
      queryClient.setQueryData<Cart>(cartQueryKey, (old) => {
        if (!old) {
          return {
            items: [{
              id: `temp-${params.product_id}`,
              product_id: params.product_id,
              product_name: params.product_name || 'Product',
              price: params.price || 0,
              quantity: params.quantity,
              subtotal: (params.price || 0) * params.quantity,
              stock_available: 100
            }],
            total_price: (params.price || 0) * params.quantity,
            item_count: 1,
            total_items: params.quantity,
            last_updated: new Date().toISOString()
          }
        }

        // Check if item already exists
        const existingItemIndex = old.items.findIndex(item => item.product_id === params.product_id)
        
        if (existingItemIndex >= 0) {
          // Update existing item
          const updatedItems = [...old.items]
          const existingItem = updatedItems[existingItemIndex]
          const newQuantity = existingItem.quantity + params.quantity
          
          updatedItems[existingItemIndex] = {
            ...existingItem,
            quantity: newQuantity,
            subtotal: existingItem.price * newQuantity
          }

          return {
            ...old,
            items: updatedItems,
            total_price: updatedItems.reduce((sum, item) => sum + item.subtotal, 0),
            total_items: updatedItems.reduce((sum, item) => sum + item.quantity, 0),
            item_count: updatedItems.length,
            last_updated: new Date().toISOString()
          }
        } else {
          // Add new item
          const newItem: CartItem = {
            id: `temp-${params.product_id}`,
            product_id: params.product_id,
            product_name: params.product_name || 'Product',
            price: params.price || 0,
            quantity: params.quantity,
            subtotal: (params.price || 0) * params.quantity,
            stock_available: 100
          }

          const updatedItems = [...old.items, newItem]

          return {
            ...old,
            items: updatedItems,
            total_price: updatedItems.reduce((sum, item) => sum + item.subtotal, 0),
            total_items: updatedItems.reduce((sum, item) => sum + item.quantity, 0),
            item_count: updatedItems.length,
            last_updated: new Date().toISOString()
          }
        }
      })

      // Store optimistic update
      setOptimisticUpdates(prev => ({
        ...prev,
        [params.product_id]: params.quantity
      }))

      return { previousCart }
    },
    onError: (err: any, params, context) => {
      // Rollback optimistic update
      if (context?.previousCart) {
        queryClient.setQueryData(cartQueryKey, context.previousCart)
      }
      
      setOptimisticUpdates(prev => {
        const updated = { ...prev }
        delete updated[params.product_id]
        return updated
      })

      const errorMessage = err?.body?.detail || err?.message || "Error al agregar producto al carrito"
      showToast("Error", errorMessage, "error")
    },
    onSuccess: (data, params) => {
      // Clear optimistic update
      setOptimisticUpdates(prev => {
        const updated = { ...prev }
        delete updated[params.product_id]
        return updated
      })

      showToast(
        "Producto agregado",
        `${params.product_name || 'Producto'} agregado al carrito`,
        "success"
      )
    },
    onSettled: () => {
      // Refetch to ensure we have the latest data
      queryClient.invalidateQueries({ queryKey: cartQueryKey })
    }
  })

  // Update item quantity
  const updateQuantityMutation = useMutation({
    mutationFn: async (params: UpdateQuantityParams) => {
      if (params.quantity <= 0) {
        // Remove item if quantity is 0 or negative
        return await CartService.removeFromCart({
          productId: params.product_id
        })
      } else {
        // Update quantity
        return await CartService.updateCartItem({
          productId: params.product_id,
          requestBody: {
            quantity: params.quantity
          }
        })
      }
    },
    onMutate: async (params) => {
      await queryClient.cancelQueries({ queryKey: cartQueryKey })
      const previousCart = queryClient.getQueryData<Cart>(cartQueryKey)

      queryClient.setQueryData<Cart>(cartQueryKey, (old) => {
        if (!old) return old

        if (params.quantity <= 0) {
          // Remove item
          const updatedItems = old.items.filter(item => item.product_id !== params.product_id)
          return {
            ...old,
            items: updatedItems,
            total_price: updatedItems.reduce((sum, item) => sum + item.subtotal, 0),
            total_items: updatedItems.reduce((sum, item) => sum + item.quantity, 0),
            item_count: updatedItems.length,
            last_updated: new Date().toISOString()
          }
        } else {
          // Update quantity
          const updatedItems = old.items.map(item => {
            if (item.product_id === params.product_id) {
              return {
                ...item,
                quantity: params.quantity,
                subtotal: item.price * params.quantity
              }
            }
            return item
          })

          return {
            ...old,
            items: updatedItems,
            total_price: updatedItems.reduce((sum, item) => sum + item.subtotal, 0),
            total_items: updatedItems.reduce((sum, item) => sum + item.quantity, 0),
            item_count: updatedItems.length,
            last_updated: new Date().toISOString()
          }
        }
      })

      return { previousCart }
    },
    onError: (err: any, params, context) => {
      if (context?.previousCart) {
        queryClient.setQueryData(cartQueryKey, context.previousCart)
      }

      const errorMessage = err?.body?.detail || err?.message || "Error al actualizar cantidad"
      showToast("Error", errorMessage, "error")
    },
    onSuccess: (data, params) => {
      if (params.quantity <= 0) {
        showToast("Producto eliminado", "Producto eliminado del carrito", "info")
      } else {
        showToast("Cantidad actualizada", "Cantidad actualizada correctamente", "success")
      }
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: cartQueryKey })
    }
  })

  // Remove item from cart
  const removeFromCartMutation = useMutation({
    mutationFn: async (productId: string) => {
      return await CartService.removeFromCart({ productId })
    },
    onMutate: async (productId) => {
      await queryClient.cancelQueries({ queryKey: cartQueryKey })
      const previousCart = queryClient.getQueryData<Cart>(cartQueryKey)

      queryClient.setQueryData<Cart>(cartQueryKey, (old) => {
        if (!old) return old

        const updatedItems = old.items.filter(item => item.product_id !== productId)
        return {
          ...old,
          items: updatedItems,
          total_price: updatedItems.reduce((sum, item) => sum + item.subtotal, 0),
          total_items: updatedItems.reduce((sum, item) => sum + item.quantity, 0),
          item_count: updatedItems.length,
          last_updated: new Date().toISOString()
        }
      })

      return { previousCart }
    },
    onError: (err: any, productId, context) => {
      if (context?.previousCart) {
        queryClient.setQueryData(cartQueryKey, context.previousCart)
      }

      const errorMessage = err?.body?.detail || err?.message || "Error al eliminar producto"
      showToast("Error", errorMessage, "error")
    },
    onSuccess: () => {
      showToast("Producto eliminado", "Producto eliminado del carrito", "info")
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: cartQueryKey })
    }
  })

  // Clear entire cart
  const clearCartMutation = useMutation({
    mutationFn: async () => {
      return await CartService.clearCart()
    },
    onMutate: async () => {
      await queryClient.cancelQueries({ queryKey: cartQueryKey })
      const previousCart = queryClient.getQueryData<Cart>(cartQueryKey)

      queryClient.setQueryData<Cart>(cartQueryKey, () => ({
        items: [],
        total_price: 0,
        item_count: 0,
        total_items: 0,
        last_updated: new Date().toISOString()
      }))

      return { previousCart }
    },
    onError: (err: any, variables, context) => {
      if (context?.previousCart) {
        queryClient.setQueryData(cartQueryKey, context.previousCart)
      }

      const errorMessage = err?.body?.detail || err?.message || "Error al limpiar carrito"
      showToast("Error", errorMessage, "error")
    },
    onSuccess: () => {
      showToast("Carrito limpio", "Se han eliminado todos los productos del carrito", "info")
    }
  })

  // Utility functions
  const addToCart = useCallback((params: AddToCartParams) => {
    if (!user) {
      showToast("Autenticación requerida", "Debes iniciar sesión para agregar productos al carrito", "warning")
      return
    }
    
    addToCartMutation.mutate(params)
  }, [user, addToCartMutation, showToast])

  const updateQuantity = useCallback((productId: string, quantity: number) => {
    if (!user) {
      showToast("Autenticación requerida", "Debes iniciar sesión", "warning")
      return
    }

    updateQuantityMutation.mutate({ product_id: productId, quantity })
  }, [user, updateQuantityMutation, showToast])

  const removeFromCart = useCallback((productId: string) => {
    if (!user) {
      showToast("Autenticación requerida", "Debes iniciar sesión", "warning")
      return
    }

    removeFromCartMutation.mutate(productId)
  }, [user, removeFromCartMutation, showToast])

  const clearCart = useCallback(() => {
    if (!user) {
      showToast("Autenticación requerida", "Debes iniciar sesión", "warning")
      return
    }

    clearCartMutation.mutate()
  }, [user, clearCartMutation, showToast])

  // Helper functions
  const getItemQuantity = useCallback((productId: string): number => {
    const optimisticQuantity = optimisticUpdates[productId]
    if (optimisticQuantity !== undefined) {
      return optimisticQuantity
    }
    
    const item = cart?.items.find(item => item.product_id === productId)
    return item?.quantity || 0
  }, [cart, optimisticUpdates])

  const isInCart = useCallback((productId: string): boolean => {
    return getItemQuantity(productId) > 0
  }, [getItemQuantity])

  const getTotalPrice = useCallback((): number => {
    return cart?.total_price || 0
  }, [cart])

  const getItemCount = useCallback((): number => {
    return cart?.item_count || 0
  }, [cart])

  const getTotalItems = useCallback((): number => {
    return cart?.total_items || 0
  }, [cart])

  return {
    // Data
    cart: cart || {
      items: [],
      total_price: 0,
      item_count: 0,
      total_items: 0,
      last_updated: new Date().toISOString()
    },
    isLoading,
    error,

    // Actions
    addToCart,
    updateQuantity,
    removeFromCart,
    clearCart,
    refetch,

    // Helpers
    getItemQuantity,
    isInCart,
    getTotalPrice,
    getItemCount,
    getTotalItems,

    // Loading states
    isAddingToCart: addToCartMutation.isPending,
    isUpdatingQuantity: updateQuantityMutation.isPending,
    isRemovingFromCart: removeFromCartMutation.isPending,
    isClearingCart: clearCartMutation.isPending,

    // Error states
    addToCartError: addToCartMutation.error,
    updateQuantityError: updateQuantityMutation.error,
    removeFromCartError: removeFromCartMutation.error,
    clearCartError: clearCartMutation.error
  }
}

export default useCart