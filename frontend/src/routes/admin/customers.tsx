import { createFileRoute } from "@tanstack/react-router"
import CustomerManagement from "../../components/Admin/CustomerManagement"

export const Route = createFileRoute("/admin/customers")({
  component: CustomerManagement,
})