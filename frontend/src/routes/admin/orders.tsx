import { createFileRoute } from "@tanstack/react-router"
import OrderManagement from "../../components/Admin/OrderManagement"

export const Route = createFileRoute("/admin/orders")({
  component: OrderManagement,
})
