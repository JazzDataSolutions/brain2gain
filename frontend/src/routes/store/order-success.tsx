import { createFileRoute, redirect } from "@tanstack/react-router"
import OrderSuccessPage from "../../components/Store/OrderSuccessPage"

export const Route = createFileRoute("/store/order-success")({
  component: OrderSuccessPage,
  beforeLoad: ({ search }) => {
    // If no orderId is provided, redirect to store
    if (!search?.orderId) {
      throw redirect({
        to: "/store",
        replace: true,
      })
    }
  },
  validateSearch: (search) => ({
    orderId: search.orderId as string,
  }),
})
