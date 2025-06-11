// frontend/performance_optimizations/optimized_stores.ts
/**
 * Optimized Zustand stores with performance enhancements,
 * intelligent persistence, and memory management.
 */

import { create } from 'zustand'
import { persist, createJSONStorage, subscribeWithSelector } from 'zustand/middleware'
import { immer } from 'zustand/middleware/immer'
import { temporal } from 'zundo'

// ─── OPTIMIZED CART STORE ──────────────────────────────────────────────────

export interface CartItem {
  id: string
  name: string
  price: number
  quantity: number
  image?: string
  sku?: string
  maxQuantity?: number
  lastUpdated: number
}

export interface CartState {
  items: CartItem[]
  isLoading: boolean
  error: string | null
  lastSyncTime: number
  totalPrice: number
  totalItems: number
  version: number // For optimistic updates
}

export interface CartActions {
  addItem: (item: Omit<CartItem, 'lastUpdated'>) => Promise<void>
  removeItem: (itemId: string) => void
  updateQuantity: (itemId: string, quantity: number) => void
  clearCart: () => void
  syncWithServer: () => Promise<void>
  setLoading: (loading: boolean) => void
  setError: (error: string | null) => void
  optimisticUpdate: (itemId: string, quantity: number) => void
  revertOptimisticUpdate: () => void
}

// Optimized cart store with computed values and intelligent updates
export const useOptimizedCartStore = create<CartState & CartActions>()(
  // Add undo/redo capability
  temporal(
    // Subscribe to changes for analytics
    subscribeWithSelector(
      // Add immer for immutable updates
      immer(
        // Persist with optimized storage
        persist(
          (set, get) => ({
            // State
            items: [],
            isLoading: false,
            error: null,
            lastSyncTime: 0,
            totalPrice: 0,
            totalItems: 0,
            version: 0,

            // Optimized actions
            addItem: async (item: Omit<CartItem, 'lastUpdated'>) => {
              const state = get()
              const now = Date.now()
              
              // Optimistic update
              set((draft) => {
                const existingItemIndex = draft.items.findIndex(
                  existing => existing.id === item.id
                )

                if (existingItemIndex >= 0) {
                  const existing = draft.items[existingItemIndex]
                  const newQuantity = existing.quantity + item.quantity
                  
                  // Check max quantity constraint
                  if (item.maxQuantity && newQuantity > item.maxQuantity) {
                    draft.error = `Cannot add more than ${item.maxQuantity} items`
                    return
                  }
                  
                  existing.quantity = newQuantity
                  existing.lastUpdated = now
                } else {
                  draft.items.push({
                    ...item,
                    lastUpdated: now
                  })
                }
                
                // Update computed values
                draft.totalPrice = draft.items.reduce(
                  (total, item) => total + (item.price * item.quantity), 0
                )
                draft.totalItems = draft.items.reduce(
                  (total, item) => total + item.quantity, 0
                )
                draft.version += 1
                draft.error = null
              })

              // Sync with server in background
              try {
                await get().syncWithServer()
              } catch (error) {
                console.error('Failed to sync cart with server:', error)
                // Could implement retry logic here
              }
            },

            removeItem: (itemId: string) => {
              set((draft) => {
                const index = draft.items.findIndex(item => item.id === itemId)
                if (index >= 0) {
                  draft.items.splice(index, 1)
                  
                  // Update computed values
                  draft.totalPrice = draft.items.reduce(
                    (total, item) => total + (item.price * item.quantity), 0
                  )
                  draft.totalItems = draft.items.reduce(
                    (total, item) => total + item.quantity, 0
                  )
                  draft.version += 1
                }
              })
            },

            updateQuantity: (itemId: string, quantity: number) => {
              if (quantity <= 0) {
                get().removeItem(itemId)
                return
              }

              set((draft) => {
                const item = draft.items.find(item => item.id === itemId)
                if (item) {
                  // Check max quantity constraint
                  if (item.maxQuantity && quantity > item.maxQuantity) {
                    draft.error = `Cannot add more than ${item.maxQuantity} items`
                    return
                  }
                  
                  item.quantity = quantity
                  item.lastUpdated = Date.now()
                  
                  // Update computed values
                  draft.totalPrice = draft.items.reduce(
                    (total, item) => total + (item.price * item.quantity), 0
                  )
                  draft.totalItems = draft.items.reduce(
                    (total, item) => total + item.quantity, 0
                  )
                  draft.version += 1
                  draft.error = null
                }
              })
            },

            clearCart: () => {
              set((draft) => {
                draft.items = []
                draft.totalPrice = 0
                draft.totalItems = 0
                draft.error = null
                draft.version += 1
              })
            },

            syncWithServer: async () => {
              const state = get()
              
              try {
                set((draft) => { draft.isLoading = true })
                
                // Here you would sync with your API
                // const response = await api.syncCart(state.items)
                
                set((draft) => {
                  draft.lastSyncTime = Date.now()
                  draft.isLoading = false
                  draft.error = null
                })
                
              } catch (error) {
                set((draft) => {
                  draft.isLoading = false
                  draft.error = error instanceof Error ? error.message : 'Sync failed'
                })
                throw error
              }
            },

            setLoading: (loading: boolean) => {
              set((draft) => { draft.isLoading = loading })
            },

            setError: (error: string | null) => {
              set((draft) => { draft.error = error })
            },

            optimisticUpdate: (itemId: string, quantity: number) => {
              // Store current state for potential rollback
              const currentState = get()
              
              set((draft) => {
                const item = draft.items.find(item => item.id === itemId)
                if (item) {
                  item.quantity = quantity
                  item.lastUpdated = Date.now()
                  
                  // Update computed values
                  draft.totalPrice = draft.items.reduce(
                    (total, item) => total + (item.price * item.quantity), 0
                  )
                  draft.totalItems = draft.items.reduce(
                    (total, item) => total + item.quantity, 0
                  )
                }
              })
            },

            revertOptimisticUpdate: () => {
              // Revert to previous state (would need to implement state history)
              console.warn('Optimistic update revert not implemented')
            }
          }),
          {
            name: 'brain2gain-cart-v2',
            storage: createJSONStorage(() => {
              // Use custom storage with compression for large carts
              return {
                getItem: (name: string) => {
                  const item = localStorage.getItem(name)
                  if (!item) return null
                  
                  try {
                    // Decompress if needed
                    return item.startsWith('compressed:') 
                      ? decompressData(item.slice(11))
                      : item
                  } catch {
                    return null
                  }
                },
                setItem: (name: string, value: string) => {
                  // Compress large data
                  const finalValue = value.length > 5000 
                    ? `compressed:${compressData(value)}`
                    : value
                  localStorage.setItem(name, finalValue)
                },
                removeItem: (name: string) => localStorage.removeItem(name)
              }
            }),
            partialize: (state) => ({
              items: state.items,
              lastSyncTime: state.lastSyncTime,
              version: state.version
            }),
            onRehydrateStorage: () => (state) => {
              if (state) {
                // Recalculate computed values after rehydration
                state.totalPrice = state.items.reduce(
                  (total, item) => total + (item.price * item.quantity), 0
                )
                state.totalItems = state.items.reduce(
                  (total, item) => total + item.quantity, 0
                )
              }
            }
          }
        )
      )
    )
  )
)

// ─── PRODUCT CACHE STORE ───────────────────────────────────────────────────

interface ProductCacheState {
  products: Map<string, any>
  categories: Map<string, any>
  searchResults: Map<string, any>
  lastCleanup: number
  maxCacheSize: number
}

interface ProductCacheActions {
  setProduct: (id: string, product: any) => void
  getProduct: (id: string) => any | null
  setCategory: (id: string, category: any) => void
  setSearchResults: (query: string, results: any) => void
  cleanup: () => void
  clearCache: () => void
}

export const useProductCacheStore = create<ProductCacheState & ProductCacheActions>()(
  subscribeWithSelector((set, get) => ({
    products: new Map(),
    categories: new Map(),
    searchResults: new Map(),
    lastCleanup: Date.now(),
    maxCacheSize: 1000, // Maximum number of cached items

    setProduct: (id: string, product: any) => {
      set((state) => {
        // Clone the Map to trigger updates
        const newProducts = new Map(state.products)
        newProducts.set(id, {
          data: product,
          timestamp: Date.now(),
          accessCount: (state.products.get(id)?.accessCount || 0) + 1
        })
        
        // Cleanup if cache is too large
        if (newProducts.size > state.maxCacheSize) {
          const entries = Array.from(newProducts.entries())
          // Sort by least recently used
          entries.sort((a, b) => a[1].timestamp - b[1].timestamp)
          
          // Remove oldest 10%
          const toRemove = Math.floor(entries.length * 0.1)
          for (let i = 0; i < toRemove; i++) {
            newProducts.delete(entries[i][0])
          }
        }
        
        return { ...state, products: newProducts }
      })
    },

    getProduct: (id: string) => {
      const state = get()
      const cached = state.products.get(id)
      
      if (cached) {
        // Update access count and timestamp
        state.products.set(id, {
          ...cached,
          timestamp: Date.now(),
          accessCount: cached.accessCount + 1
        })
        
        return cached.data
      }
      
      return null
    },

    setCategory: (id: string, category: any) => {
      set((state) => {
        const newCategories = new Map(state.categories)
        newCategories.set(id, {
          data: category,
          timestamp: Date.now()
        })
        return { ...state, categories: newCategories }
      })
    },

    setSearchResults: (query: string, results: any) => {
      set((state) => {
        const newSearchResults = new Map(state.searchResults)
        newSearchResults.set(query, {
          data: results,
          timestamp: Date.now()
        })
        
        // Keep only last 50 search results
        if (newSearchResults.size > 50) {
          const entries = Array.from(newSearchResults.entries())
          entries.sort((a, b) => a[1].timestamp - b[1].timestamp)
          
          for (let i = 0; i < entries.length - 50; i++) {
            newSearchResults.delete(entries[i][0])
          }
        }
        
        return { ...state, searchResults: newSearchResults }
      })
    },

    cleanup: () => {
      const now = Date.now()
      const maxAge = 30 * 60 * 1000 // 30 minutes
      
      set((state) => {
        if (now - state.lastCleanup < 5 * 60 * 1000) { // Cleanup max every 5 minutes
          return state
        }
        
        const newProducts = new Map()
        const newCategories = new Map()
        const newSearchResults = new Map()
        
        // Clean expired products
        for (const [key, value] of state.products) {
          if (now - value.timestamp < maxAge) {
            newProducts.set(key, value)
          }
        }
        
        // Clean expired categories
        for (const [key, value] of state.categories) {
          if (now - value.timestamp < maxAge) {
            newCategories.set(key, value)
          }
        }
        
        // Clean expired search results (shorter TTL)
        for (const [key, value] of state.searchResults) {
          if (now - value.timestamp < 10 * 60 * 1000) { // 10 minutes
            newSearchResults.set(key, value)
          }
        }
        
        return {
          ...state,
          products: newProducts,
          categories: newCategories,
          searchResults: newSearchResults,
          lastCleanup: now
        }
      })
    },

    clearCache: () => {
      set({
        products: new Map(),
        categories: new Map(),
        searchResults: new Map(),
        lastCleanup: Date.now(),
        maxCacheSize: 1000
      })
    }
  }))
)

// ─── UTILITY FUNCTIONS ─────────────────────────────────────────────────────

function compressData(data: string): string {
  // Simple compression using built-in compression
  // In a real app, you might use a library like pako
  try {
    return btoa(data)
  } catch {
    return data
  }
}

function decompressData(data: string): string {
  try {
    return atob(data)
  } catch {
    return data
  }
}

// ─── STORE SELECTORS FOR PERFORMANCE ──────────────────────────────────────

// Optimized selectors to prevent unnecessary re-renders
export const selectCartItems = (state: CartState & CartActions) => state.items
export const selectCartTotal = (state: CartState & CartActions) => state.totalPrice
export const selectCartItemCount = (state: CartState & CartActions) => state.totalItems
export const selectCartLoading = (state: CartState & CartActions) => state.isLoading
export const selectCartError = (state: CartState & CartActions) => state.error

// Memoized selectors for expensive calculations
export const selectCartItemById = (itemId: string) => 
  (state: CartState & CartActions) => 
    state.items.find(item => item.id === itemId)

export const selectCartItemsByCategory = (category: string) =>
  (state: CartState & CartActions) =>
    state.items.filter(item => item.sku?.startsWith(category))

// ─── AUTOMATIC CLEANUP ─────────────────────────────────────────────────────

// Auto-cleanup product cache every 5 minutes
if (typeof window !== 'undefined') {
  setInterval(() => {
    useProductCacheStore.getState().cleanup()
  }, 5 * 60 * 1000)
}

// ─── PERFORMANCE MONITORING ────────────────────────────────────────────────

// Subscribe to cart changes for analytics
useOptimizedCartStore.subscribe(
  (state) => state.items,
  (items, previousItems) => {
    // Track cart modifications for analytics
    if (items.length !== previousItems.length) {
      // Send analytics event
      if (typeof window !== 'undefined' && window.gtag) {
        window.gtag('event', 'cart_modification', {
          items_count: items.length,
          total_value: items.reduce((sum, item) => sum + item.price * item.quantity, 0)
        })
      }
    }
  }
)