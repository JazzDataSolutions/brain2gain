import { createFileRoute } from "@tanstack/react-router"
import OrderDetailsPage from "../../../components/Store/OrderDetailsPage"

export const Route = createFileRoute("/store/orders/$orderId")({
  component: OrderDetailsPage,
})
