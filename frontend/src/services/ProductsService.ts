import { ItemsService } from '../client'

// Interfaces unificadas
export interface Product {
  id: number
  name: string
  price: number
  sku: string
  status: 'ACTIVE' | 'DISCONTINUED'
  image?: string
  created_at?: string
  updated_at?: string
}

export interface ProductsResponse {
  data: Product[]
  count: number
}

// Transform functions
const transformItemToProduct = (item: any): Product => {
  return {
    id: item.id || item.product_id,
    name: item.title || item.name,
    price: item.unit_price || item.price || 0,
    sku: item.sku || `SKU-${item.id}`,
    status: item.status || 'ACTIVE',
    image: item.image || '/imagenes/proteina_catalogo.jpg',
    created_at: item.created_at,
    updated_at: item.updated_at,
  }
}

const transformItemsResponse = (itemsResponse: any): ProductsResponse => {
  // Handle both direct array and wrapped response
  const items = Array.isArray(itemsResponse) ? itemsResponse : itemsResponse.data || []
  
  return {
    data: items.map(transformItemToProduct),
    count: items.length
  }
}

// ProductsService wrapper
export class ProductsService {
  /**
   * List products with pagination
   */
  static async readProducts(params?: { skip?: number; limit?: number }): Promise<ProductsResponse> {
    try {
      const response = await ItemsService.readItems({
        skip: params?.skip || 0,
        limit: params?.limit || 50
      })
      
      return transformItemsResponse(response)
    } catch (error) {
      console.error('Error fetching products:', error)
      // Return empty response as fallback
      return { data: [], count: 0 }
    }
  }

  /**
   * Get product by ID
   */
  static async readProduct(productId: string): Promise<Product | null> {
    try {
      const response = await ItemsService.readItem({ id: parseInt(productId) })
      return transformItemToProduct(response)
    } catch (error) {
      console.error('Error fetching product:', error)
      return null
    }
  }

  /**
   * Create mock products for development
   */
  static async getMockProducts(): Promise<ProductsResponse> {
    // Mock data for when backend is not available
    const mockProducts: Product[] = [
      {
        id: 1,
        name: 'Whey Protein Gold Standard',
        price: 65.99,
        sku: 'WPG-001',
        status: 'ACTIVE',
        image: '/imagenes/proteina_catalogo.jpg'
      },
      {
        id: 2,
        name: 'Creatina Monohidrato',
        price: 29.99,
        sku: 'CRE-002',
        status: 'ACTIVE',
        image: '/imagenes/creatina_catalogo.jpg'
      },
      {
        id: 3,
        name: 'Pre-Workout Extreme',
        price: 45.99,
        sku: 'PWO-003',
        status: 'ACTIVE',
        image: '/imagenes/preworkout_catalogo.jpg'
      },
      {
        id: 4,
        name: 'BCAA Aminoácidos',
        price: 35.99,
        sku: 'BCAA-004',
        status: 'ACTIVE',
        image: '/imagenes/proteina_catalogo.jpg'
      },
      {
        id: 5,
        name: 'Quemador de Grasa',
        price: 55.99,
        sku: 'FAT-005',
        status: 'ACTIVE',
        image: '/imagenes/cafeina.jpg'
      },
      {
        id: 6,
        name: 'Proteína Caseína',
        price: 70.99,
        sku: 'CAS-006',
        status: 'ACTIVE',
        image: '/imagenes/proteina_catalogo.jpg'
      },
      {
        id: 7,
        name: 'Vitaminas Multivitamínico',
        price: 25.99,
        sku: 'VIT-007',
        status: 'ACTIVE',
        image: '/imagenes/proteina_catalogo.jpg'
      },
      {
        id: 8,
        name: 'Glutamina Pura',
        price: 32.99,
        sku: 'GLU-008',
        status: 'ACTIVE',
        image: '/imagenes/proteina_catalogo.jpg'
      }
    ]

    return {
      data: mockProducts,
      count: mockProducts.length
    }
  }

  /**
   * Fetch products with fallback to mock data
   */
  static async getProductsWithFallback(params?: { skip?: number; limit?: number }): Promise<ProductsResponse> {
    try {
      // Try to get real data first
      const response = await this.readProducts(params)
      
      // If no data, use mock
      if (response.data.length === 0) {
        console.log('No products from API, using mock data')
        return await this.getMockProducts()
      }
      
      return response
    } catch (error) {
      console.log('API unavailable, using mock data')
      return await this.getMockProducts()
    }
  }
}

export default ProductsService