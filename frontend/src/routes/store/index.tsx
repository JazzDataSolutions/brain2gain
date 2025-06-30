import { createFileRoute } from "@tanstack/react-router"
import StoreDashboard from "../../components/Store/StoreDashboard"

export const Route = createFileRoute("/store/")({
  component: StoreDashboard,
})
