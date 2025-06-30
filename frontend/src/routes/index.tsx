import { createFileRoute, redirect } from "@tanstack/react-router"

export const Route = createFileRoute("/")({
  beforeLoad: () => {
    // Redirigir a la tienda por defecto
    throw redirect({
      to: "/store",
    })
  },
})
