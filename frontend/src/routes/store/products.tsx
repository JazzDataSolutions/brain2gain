import { createFileRoute } from "@tanstack/react-router"
import ProductCatalog from "../../components/Products/ProductCatalog"

export const Route = createFileRoute("/store/products")({
  component: ProductCatalog,
})
