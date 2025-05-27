import { createFileRoute } from '@tanstack/react-router'
import ProductCatalog from '../components/Products/ProductCatalog'

export const Route = createFileRoute('/products')({
  component: ProductCatalog,
})