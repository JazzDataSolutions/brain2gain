import { create } from 'zustand'
import { persist } from 'zustand/middleware'

export interface Product {
  product_id: number
  sku: string
  name: string
  unit_price: number
  status: 'ACTIVE' | 'DISCONTINUED'
  created_at: string
  updated_at: string
}

export interface CartItem {
  product_id: number
  quantity: number
  product_name: string
  product_sku: string
  unit_price: number
  total_price: number
}

export interface CartState {
  cart_id: number | null
  items: CartItem[]
  total_amount: number
  item_count: number
  session_id: string | null
  isLoading: boolean
  error: string | null
}

export interface CartActions {
  addToCart: (product: Product, quantity?: number) => void
  removeFromCart: (productId: number) => void
  updateQuantity: (productId: number, quantity: number) => void
  clearCart: () => void
  setSessionId: (sessionId: string) => void
  setLoading: (loading: boolean) => void
  setError: (error: string | null) => void
  syncWithServer: () => Promise<void>
}

const generateSessionId = () => {
  return `guest_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
}

export const useCartStore = create<CartState & CartActions>()(
  persist(
    (set, get) => ({
      // State
      cart_id: null,
      items: [],
      total_amount: 0,
      item_count: 0,
      session_id: null,
      isLoading: false,
      error: null,

      // Actions
      addToCart: (product: Product, quantity = 1) => {
        set((state) => {
          const existingItem = state.items.find(
            item => item.product_id === product.product_id
          )

          let newItems: CartItem[]
          
          if (existingItem) {
            newItems = state.items.map(item =>
              item.product_id === product.product_id
                ? {
                    ...item,
                    quantity: item.quantity + quantity,
                    total_price: (item.quantity + quantity) * item.unit_price
                  }
                : item
            )
          } else {
            const newItem: CartItem = {
              product_id: product.product_id,
              quantity,
              product_name: product.name,
              product_sku: product.sku,
              unit_price: product.unit_price,
              total_price: product.unit_price * quantity
            }
            newItems = [...state.items, newItem]
          }

          const total_amount = newItems.reduce((sum, item) => sum + item.total_price, 0)
          const item_count = newItems.reduce((sum, item) => sum + item.quantity, 0)

          return {
            ...state,
            items: newItems,
            total_amount,
            item_count,
            session_id: state.session_id || generateSessionId()
          }
        })

        // Sync with server in background
        get().syncWithServer()
      },

      removeFromCart: (productId: number) => {
        set((state) => {
          const newItems = state.items.filter(item => item.product_id !== productId)
          const total_amount = newItems.reduce((sum, item) => sum + item.total_price, 0)
          const item_count = newItems.reduce((sum, item) => sum + item.quantity, 0)

          return {
            ...state,
            items: newItems,
            total_amount,
            item_count
          }
        })

        // Sync with server in background
        get().syncWithServer()
      },

      updateQuantity: (productId: number, quantity: number) => {
        if (quantity <= 0) {
          get().removeFromCart(productId)
          return
        }

        set((state) => {
          const newItems = state.items.map(item =>
            item.product_id === productId
              ? {
                  ...item,
                  quantity,
                  total_price: quantity * item.unit_price
                }
              : item
          )

          const total_amount = newItems.reduce((sum, item) => sum + item.total_price, 0)
          const item_count = newItems.reduce((sum, item) => sum + item.quantity, 0)

          return {
            ...state,
            items: newItems,
            total_amount,
            item_count
          }
        })

        // Sync with server in background
        get().syncWithServer()
      },

      clearCart: () => {
        set({
          cart_id: null,
          items: [],
          total_amount: 0,
          item_count: 0,
          error: null
        })

        // Sync with server in background
        get().syncWithServer()
      },

      setSessionId: (sessionId: string) => {
        set({ session_id: sessionId })
      },

      setLoading: (loading: boolean) => {
        set({ isLoading: loading })
      },

      setError: (error: string | null) => {
        set({ error })
      },

      syncWithServer: async () => {
        // TODO: Implement API sync when backend is ready
        // This would sync the local cart state with the server
        const state = get()
        if (!state.session_id) return

        try {
          set({ isLoading: true, error: null })
          
          // Here we would make API calls to sync cart state
          // For now, we just simulate the sync
          await new Promise(resolve => setTimeout(resolve, 100))
          
          set({ isLoading: false })
        } catch (error) {
          set({ 
            isLoading: false, 
            error: error instanceof Error ? error.message : 'Failed to sync cart'
          })
        }
      }
    }),
    {
      name: 'brain2gain-cart',
      partialize: (state) => ({
        items: state.items,
        total_amount: state.total_amount,
        item_count: state.item_count,
        session_id: state.session_id
      })
    }
  )
)