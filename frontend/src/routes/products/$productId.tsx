import { createFileRoute } from '@tanstack/react-router'
import ProductDetail from '../../components/Products/ProductDetail'

export const Route = createFileRoute('/products/$productId')({
  component: ProductDetail,
})