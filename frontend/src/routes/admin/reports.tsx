import { createFileRoute } from "@tanstack/react-router"
import ReportsAndAnalytics from "../../components/Admin/ReportsAndAnalytics"

export const Route = createFileRoute("/admin/reports")({
  component: ReportsAndAnalytics,
})
