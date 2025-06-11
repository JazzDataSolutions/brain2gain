import { createFileRoute } from "@tanstack/react-router"
import InventoryManagement from "../../components/Admin/InventoryManagement"

export const Route = createFileRoute("/admin/inventory")({
  component: InventoryManagement,
})