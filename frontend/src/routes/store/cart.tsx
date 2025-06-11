import { createFileRoute } from "@tanstack/react-router"
import CartPage from "../../components/Store/CartPage"

export const Route = createFileRoute("/store/cart")({
  component: CartPage,
})