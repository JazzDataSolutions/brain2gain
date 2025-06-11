// frontend/performance_optimizations/optimized_components.tsx
/**
 * Performance-optimized React components with memoization,
 * lazy loading, and efficient rendering patterns.
 */

import React, { 
  memo, 
  useMemo, 
  useCallback, 
  lazy, 
  Suspense,
  startTransition,
  useDeferredValue,
  useState,
  useEffect
} from 'react'
import { ErrorBoundary } from 'react-error-boundary'
import { VirtualItem, useVirtualizer } from '@tanstack/react-virtual'

// ─── VIRTUALIZED PRODUCT LIST ─────────────────────────────────────────────

interface Product {
  id: string
  name: string
  price: number
  image?: string
  category: string
}

interface VirtualizedProductListProps {
  products: Product[]
  onProductClick: (product: Product) => void
  itemHeight?: number
}

export const VirtualizedProductList = memo<VirtualizedProductListProps>(({
  products,
  onProductClick,
  itemHeight = 120
}) => {
  const parentRef = React.useRef<HTMLDivElement>(null)
  
  const virtualizer = useVirtualizer({
    count: products.length,
    getScrollElement: () => parentRef.current,
    estimateSize: () => itemHeight,
    overscan: 5, // Render 5 extra items outside viewport
  })

  const handleProductClick = useCallback((product: Product) => {
    startTransition(() => {
      onProductClick(product)
    })
  }, [onProductClick])

  return (
    <div
      ref={parentRef}
      className="h-96 overflow-auto"
      style={{ contain: 'strict' }} // CSS containment for performance
    >
      <div
        style={{
          height: `${virtualizer.getTotalSize()}px`,
          width: '100%',
          position: 'relative',
        }}
      >
        {virtualizer.getVirtualItems().map((virtualItem) => {
          const product = products[virtualItem.index]
          return (
            <VirtualizedProductItem
              key={product.id}
              virtualItem={virtualItem}
              product={product}
              onClick={handleProductClick}
            />
          )
        })}
      </div>
    </div>
  )
})

// ─── MEMOIZED PRODUCT ITEM ─────────────────────────────────────────────────

interface VirtualizedProductItemProps {
  virtualItem: VirtualItem
  product: Product
  onClick: (product: Product) => void
}

const VirtualizedProductItem = memo<VirtualizedProductItemProps>(({
  virtualItem,
  product,
  onClick
}) => {
  const handleClick = useCallback(() => {
    onClick(product)
  }, [onClick, product])

  return (
    <div
      style={{
        position: 'absolute',
        top: 0,
        left: 0,
        width: '100%',
        height: `${virtualItem.size}px`,
        transform: `translateY(${virtualItem.start}px)`,
      }}
      className="border-b border-gray-200 p-4 flex items-center gap-4 hover:bg-gray-50 cursor-pointer"
      onClick={handleClick}
    >
      {product.image && (
        <OptimizedImage
          src={product.image}
          alt={product.name}
          className="w-16 h-16 object-cover rounded"
          loading="lazy"
        />
      )}
      <div className="flex-1">
        <h3 className="font-medium text-gray-900">{product.name}</h3>
        <p className="text-sm text-gray-500">{product.category}</p>
        <p className="text-lg font-semibold text-green-600">
          ${product.price.toFixed(2)}
        </p>
      </div>
    </div>
  )
}, (prevProps, nextProps) => {
  // Custom comparison for better memoization
  return (
    prevProps.product.id === nextProps.product.id &&
    prevProps.product.name === nextProps.product.name &&
    prevProps.product.price === nextProps.product.price &&
    prevProps.virtualItem.index === nextProps.virtualItem.index
  )
})

// ─── OPTIMIZED IMAGE COMPONENT ─────────────────────────────────────────────

interface OptimizedImageProps extends React.ImgHTMLAttributes<HTMLImageElement> {
  src: string
  alt: string
  fallback?: string
  placeholder?: React.ReactNode
}

const OptimizedImage = memo<OptimizedImageProps>(({
  src,
  alt,
  fallback = '/images/placeholder.webp',
  placeholder,
  className,
  ...props
}) => {
  const [imageSrc, setImageSrc] = useState<string>(src)
  const [isLoading, setIsLoading] = useState(true)
  const [hasError, setHasError] = useState(false)

  const handleLoad = useCallback(() => {
    setIsLoading(false)
  }, [])

  const handleError = useCallback(() => {
    setHasError(true)
    setIsLoading(false)
    if (imageSrc !== fallback) {
      setImageSrc(fallback)
    }
  }, [imageSrc, fallback])

  // Generate optimized image sources
  const optimizedSrc = useMemo(() => {
    if (src.includes('http')) {
      // For external images, you might want to use a service like Cloudinary
      return src
    }
    // For local images, generate WebP versions
    return src.replace(/\.(jpg|jpeg|png)$/i, '.webp')
  }, [src])

  return (
    <div className={`relative ${className}`}>
      {isLoading && placeholder && (
        <div className="absolute inset-0 flex items-center justify-center bg-gray-100">
          {placeholder}
        </div>
      )}
      
      <picture>
        <source srcSet={optimizedSrc} type="image/webp" />
        <img
          src={imageSrc}
          alt={alt}
          className={`${className} ${isLoading ? 'opacity-0' : 'opacity-100'} transition-opacity duration-200`}
          onLoad={handleLoad}
          onError={handleError}
          decoding="async"
          {...props}
        />
      </picture>
      
      {hasError && !isLoading && (
        <div className="absolute inset-0 flex items-center justify-center bg-gray-100 text-gray-500 text-sm">
          Image not available
        </div>
      )}
    </div>
  )
})

// ─── DEBOUNCED SEARCH COMPONENT ────────────────────────────────────────────

interface DebouncedSearchProps {
  onSearch: (query: string) => void
  placeholder?: string
  debounceMs?: number
}

export const DebouncedSearch = memo<DebouncedSearchProps>(({
  onSearch,
  placeholder = "Search products...",
  debounceMs = 300
}) => {
  const [query, setQuery] = useState('')
  const deferredQuery = useDeferredValue(query)

  // Debounced search effect
  useEffect(() => {
    const timeoutId = setTimeout(() => {
      if (deferredQuery !== query) return // Skip if query changed again
      
      startTransition(() => {
        onSearch(deferredQuery)
      })
    }, debounceMs)

    return () => clearTimeout(timeoutId)
  }, [deferredQuery, onSearch, debounceMs, query])

  const handleInputChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    setQuery(e.target.value)
  }, [])

  return (
    <div className="relative">
      <input
        type="text"
        value={query}
        onChange={handleInputChange}
        placeholder={placeholder}
        className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
      />
      {query && (
        <button
          onClick={() => setQuery('')}
          className="absolute right-2 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-gray-600"
        >
          ✕
        </button>
      )}
    </div>
  )
})

// ─── LAZY LOADED COMPONENTS ────────────────────────────────────────────────

// Lazy load heavy components
const LazyProductDetail = lazy(() => 
  import('../components/Products/ProductDetail').then(module => ({
    default: module.ProductDetail
  }))
)

const LazyCartPage = lazy(() => 
  import('../components/Cart/CartPage').then(module => ({
    default: module.CartPage
  }))
)

const LazyUserSettings = lazy(() => 
  import('../components/UserSettings/UserInformation').then(module => ({
    default: module.UserInformation
  }))
)

// ─── SUSPENSE WRAPPER WITH ERROR BOUNDARY ──────────────────────────────────

interface SuspenseWrapperProps {
  children: React.ReactNode
  fallback?: React.ReactNode
  errorFallback?: React.ComponentType<{ error: Error; resetErrorBoundary: () => void }>
}

export const SuspenseWrapper: React.FC<SuspenseWrapperProps> = ({
  children,
  fallback = <LoadingSpinner />,
  errorFallback: ErrorFallback = DefaultErrorFallback
}) => {
  return (
    <ErrorBoundary
      FallbackComponent={ErrorFallback}
      onError={(error, errorInfo) => {
        console.error('Component error:', error, errorInfo)
        // Here you could send error to monitoring service
      }}
    >
      <Suspense fallback={fallback}>
        {children}
      </Suspense>
    </ErrorBoundary>
  )
}

// ─── OPTIMIZED LOADING COMPONENTS ──────────────────────────────────────────

const LoadingSpinner = memo(() => (
  <div className="flex items-center justify-center p-8">
    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
    <span className="ml-2 text-gray-600">Loading...</span>
  </div>
))

const DefaultErrorFallback = memo<{ error: Error; resetErrorBoundary: () => void }>(
  ({ error, resetErrorBoundary }) => (
    <div className="text-center p-8 border border-red-200 rounded-lg bg-red-50">
      <h2 className="text-lg font-semibold text-red-800 mb-2">Something went wrong</h2>
      <p className="text-red-600 mb-4">{error.message}</p>
      <button
        onClick={resetErrorBoundary}
        className="px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700 transition-colors"
      >
        Try again
      </button>
    </div>
  )
)

// ─── OPTIMIZED PAGINATION COMPONENT ────────────────────────────────────────

interface OptimizedPaginationProps {
  currentPage: number
  totalPages: number
  onPageChange: (page: number) => void
  maxVisiblePages?: number
}

export const OptimizedPagination = memo<OptimizedPaginationProps>(({
  currentPage,
  totalPages,
  onPageChange,
  maxVisiblePages = 5
}) => {
  const visiblePages = useMemo(() => {
    const halfVisible = Math.floor(maxVisiblePages / 2)
    let startPage = Math.max(1, currentPage - halfVisible)
    let endPage = Math.min(totalPages, startPage + maxVisiblePages - 1)
    
    // Adjust start if we're near the end
    if (endPage - startPage + 1 < maxVisiblePages) {
      startPage = Math.max(1, endPage - maxVisiblePages + 1)
    }
    
    return Array.from(
      { length: endPage - startPage + 1 },
      (_, i) => startPage + i
    )
  }, [currentPage, totalPages, maxVisiblePages])

  const handlePageChange = useCallback((page: number) => {
    if (page >= 1 && page <= totalPages && page !== currentPage) {
      startTransition(() => {
        onPageChange(page)
      })
    }
  }, [currentPage, totalPages, onPageChange])

  if (totalPages <= 1) return null

  return (
    <nav className="flex items-center justify-center space-x-1">
      {/* Previous button */}
      <button
        onClick={() => handlePageChange(currentPage - 1)}
        disabled={currentPage === 1}
        className="px-3 py-2 text-sm font-medium text-gray-500 bg-white border border-gray-300 rounded-l-md hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
      >
        Previous
      </button>

      {/* Page numbers */}
      {visiblePages.map(page => (
        <button
          key={page}
          onClick={() => handlePageChange(page)}
          className={`px-3 py-2 text-sm font-medium border-t border-b ${
            page === currentPage
              ? 'text-blue-600 bg-blue-50 border-blue-300'
              : 'text-gray-500 bg-white border-gray-300 hover:bg-gray-50'
          }`}
        >
          {page}
        </button>
      ))}

      {/* Next button */}
      <button
        onClick={() => handlePageChange(currentPage + 1)}
        disabled={currentPage === totalPages}
        className="px-3 py-2 text-sm font-medium text-gray-500 bg-white border border-gray-300 rounded-r-md hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
      >
        Next
      </button>
    </nav>
  )
})

// ─── PERFORMANCE MONITORING HOOK ───────────────────────────────────────────

export const usePerformanceMonitor = (componentName: string) => {
  useEffect(() => {
    const startTime = performance.now()
    
    return () => {
      const endTime = performance.now()
      const renderTime = endTime - startTime
      
      if (renderTime > 100) { // Log slow renders
        console.warn(`Slow render detected in ${componentName}: ${renderTime.toFixed(2)}ms`)
      }
      
      // Send to analytics service
      if (window.gtag) {
        window.gtag('event', 'component_render_time', {
          component_name: componentName,
          render_time: Math.round(renderTime)
        })
      }
    }
  })
}

// ─── EXPORT LAZY COMPONENTS ────────────────────────────────────────────────

export {
  LazyProductDetail,
  LazyCartPage,
  LazyUserSettings
}