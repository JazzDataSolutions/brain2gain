import { Flex, Box } from "@chakra-ui/react"
import { Outlet, createFileRoute, redirect } from "@tanstack/react-router"

import AdminHeader from "../../components/Admin/AdminHeader"
import AdminSidebar from "../../components/Admin/AdminSidebar"
import AdminGuard from "../../components/Auth/AdminGuard"
import useAuth, { isLoggedIn, isAdmin } from "../../hooks/useAuth"

export const Route = createFileRoute("/admin/_layout")({
  component: AdminLayout,
  beforeLoad: async () => {
    // Basic login check - AdminGuard will handle superuser verification
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
  const { user } = useAuth()

  return (
    <AdminGuard redirectTo="/login">
      <Flex maxW="full" h="100vh" bg="gray.50">
        {/* Sidebar del ERP */}
        <AdminSidebar />

        <Flex direction="column" flex="1" overflow="hidden">
          {/* Header del admin */}
          <AdminHeader />

          {/* Contenido principal protegido */}
          <Flex flex="1" p={4} overflow="auto">
            <Box w="full">
              <Outlet />
            </Box>
          </Flex>
        </Flex>
      </Flex>
    </AdminGuard>
  )
}
