import { createFileRoute } from "@tanstack/react-router"
import ProductCatalog from "../../components/Store/ProductCatalog"

export const Route = createFileRoute("/store/products")({
  component: ProductCatalog,
})