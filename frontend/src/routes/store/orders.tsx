import { createFileRoute } from "@tanstack/react-router"
import UserOrdersPage from "../../components/Store/UserOrdersPage"

export const Route = createFileRoute("/store/orders")({
  component: UserOrdersPage,
})