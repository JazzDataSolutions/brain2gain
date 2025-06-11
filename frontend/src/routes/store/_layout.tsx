import { Flex } from "@chakra-ui/react"
import { Outlet, createFileRoute } from "@tanstack/react-router"

import StoreNavbar from "../../components/Store/StoreNavbar"
import StoreFooter from "../../components/Store/StoreFooter"

export const Route = createFileRoute("/store/_layout")({
  component: StoreLayout,
})

function StoreLayout() {
  return (
    <Flex direction="column" minH="100vh">
      {/* Navbar de tienda (público) */}
      <StoreNavbar />
      
      {/* Contenido principal */}
      <Flex flex="1" direction="column">
        <Outlet />
      </Flex>
      
      {/* Footer de tienda */}
      <StoreFooter />
    </Flex>
  )
}