import { Flex, Spinner } from "@chakra-ui/react"
import { Outlet, createFileRoute, redirect } from "@tanstack/react-router"

import AdminSidebar from "../../components/Admin/AdminSidebar"
import AdminHeader from "../../components/Admin/AdminHeader"
import useAuth, { isLoggedIn } from "../../hooks/useAuth"

export const Route = createFileRoute("/admin/_layout")({
  component: AdminLayout,
  beforeLoad: async () => {
    if (!isLoggedIn()) {
      throw redirect({
        to: "/login",
        search: {
          redirect: window.location.pathname,
        },
      })
    }
  },
})

function AdminLayout() {
  const { isLoading, user } = useAuth()

  // Solo permitir acceso a usuarios con rol admin/manager
  if (user && !user.is_superuser) {
    throw redirect({
      to: "/store",
    })
  }

  return (
    <Flex maxW="full" h="100vh" bg="gray.50">
      {/* Sidebar del ERP */}
      <AdminSidebar />
      
      <Flex direction="column" flex="1" overflow="hidden">
        {/* Header del admin */}
        <AdminHeader />
        
        {/* Contenido principal */}
        <Flex flex="1" p={4} overflow="auto">
          {isLoading ? (
            <Flex justify="center" align="center" height="100%" width="full">
              <Spinner size="xl" color="blue.500" />
            </Flex>
          ) : (
            <Outlet />
          )}
        </Flex>
      </Flex>
    </Flex>
  )
}