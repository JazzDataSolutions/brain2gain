import { createFileRoute } from "@tanstack/react-router"
import AdminDashboard from "../../components/Admin/AdminDashboard"

export const Route = createFileRoute("/admin/")({
  component: AdminDashboard,
})
