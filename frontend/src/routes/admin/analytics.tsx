import { createFileRoute } from "@tanstack/react-router"
import AnalyticsDashboard from "../../components/Admin/AnalyticsDashboard"

export const Route = createFileRoute("/admin/analytics")({
  component: () => <AnalyticsDashboard />,
})
