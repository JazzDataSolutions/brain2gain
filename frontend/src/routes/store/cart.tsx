import { createFileRoute } from "@tanstack/react-router"
import CartPage from "../../components/Cart/CartPage"

export const Route = createFileRoute("/store/cart")({
  component: CartPage,
})