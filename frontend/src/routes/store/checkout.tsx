import { createFileRoute } from "@tanstack/react-router"
import CheckoutPage from "../../components/Store/CheckoutPage"

export const Route = createFileRoute("/store/checkout")({
  component: CheckoutPage,
})