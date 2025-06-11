import { create } from 'zustand'
import { persist } from 'zustand/middleware'

export interface CartItem {
  id: string
  name: string
  price: number
  quantity: number
  image?: string
}

export interface CartState {
  items: CartItem[]
  isLoading: boolean
  error: string | null
}

export interface CartActions {
  addItem: (item: CartItem) => void
  removeItem: (itemId: string) => void
  updateQuantity: (itemId: string, quantity: number) => void
  clearCart: () => void
  getTotalPrice: () => number
  getTotalItems: () => number
  setLoading: (loading: boolean) => void
  setError: (error: string | null) => void
}


export const useCartStore = create<CartState & CartActions>()(
  persist(
    (set, get) => ({
      // State
      items: [],
      isLoading: false,
      error: null,

      // Actions
      addItem: (item: CartItem) => {
        set((state) => {
          const existingItemIndex = state.items.findIndex(
            existingItem => existingItem.id === item.id
          )

          let newItems: CartItem[]
          
          if (existingItemIndex >= 0) {
            newItems = state.items.map((existingItem, index) =>
              index === existingItemIndex
                ? {
                    ...existingItem,
                    quantity: existingItem.quantity + item.quantity
                  }
                : existingItem
            )
          } else {
            newItems = [...state.items, item]
          }

          return {
            ...state,
            items: newItems
          }
        })
      },

      removeItem: (itemId: string) => {
        set((state) => ({
          ...state,
          items: state.items.filter(item => item.id !== itemId)
        }))
      },

      updateQuantity: (itemId: string, quantity: number) => {
        if (quantity <= 0) {
          get().removeItem(itemId)
          return
        }

        set((state) => ({
          ...state,
          items: state.items.map(item =>
            item.id === itemId
              ? { ...item, quantity }
              : item
          )
        }))
      },

      clearCart: () => {
        set({
          items: [],
          error: null
        })
      },

      getTotalPrice: () => {
        const state = get()
        return state.items.reduce((total, item) => total + (item.price * item.quantity), 0)
      },

      getTotalItems: () => {
        const state = get()
        return state.items.reduce((total, item) => total + item.quantity, 0)
      },

      setLoading: (loading: boolean) => {
        set({ isLoading: loading })
      },

      setError: (error: string | null) => {
        set({ error })
      }
    }),
    {
      name: 'brain2gain-cart',
      partialize: (state) => ({
        items: state.items
      })
    }
  )
)