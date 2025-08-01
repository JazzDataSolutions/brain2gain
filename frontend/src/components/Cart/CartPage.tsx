import { ChevronRightIcon } from "@chakra-ui/icons"
import {
  Box,
  Breadcrumb,
  BreadcrumbItem,
  BreadcrumbLink,
  Button,
  Container,
  Divider,
  HStack,
  Heading,
  Text,
  VStack,
} from "@chakra-ui/react"
import { Link } from "@tanstack/react-router"

import { useCartStore } from "../../stores/cartStore"
import CartItem from "./CartItem"
import CartSummary from "./CartSummary"

const CartPage = () => {
  const { items, getTotalItems, getTotalPrice } = useCartStore()

  const formatPrice = (price: number) => {
    return new Intl.NumberFormat("es-CO", {
      style: "currency",
      currency: "COP",
    }).format(price)
  }

  if (items.length === 0) {
    return (
      <Container maxW="7xl" py={8}>
        <VStack spacing={8} align="stretch">
          {/* Breadcrumb */}
          <Breadcrumb
            spacing="8px"
            separator={<ChevronRightIcon color="gray.500" />}
          >
            <BreadcrumbItem>
              <BreadcrumbLink as={Link} to="/">
                Inicio
              </BreadcrumbLink>
            </BreadcrumbItem>
            <BreadcrumbItem isCurrentPage>
              <BreadcrumbLink>Carrito</BreadcrumbLink>
            </BreadcrumbItem>
          </Breadcrumb>

          {/* Empty Cart */}
          <Box textAlign="center" py={12}>
            <Heading size="lg" mb={4}>
              Tu carrito está vacío
            </Heading>
            <Text color="gray.600" mb={6}>
              Agrega algunos productos para comenzar tu compra
            </Text>
            <Button as={Link} to="/products" colorScheme="blue" size="lg">
              Ver Productos
            </Button>
          </Box>
        </VStack>
      </Container>
    )
  }

  return (
    <Container maxW="7xl" py={8}>
      <VStack spacing={8} align="stretch">
        {/* Breadcrumb */}
        <Breadcrumb
          spacing="8px"
          separator={<ChevronRightIcon color="gray.500" />}
        >
          <BreadcrumbItem>
            <BreadcrumbLink as={Link} to="/">
              Inicio
            </BreadcrumbLink>
          </BreadcrumbItem>
          <BreadcrumbItem isCurrentPage>
            <BreadcrumbLink>
              Carrito ({getTotalItems()} productos)
            </BreadcrumbLink>
          </BreadcrumbItem>
        </Breadcrumb>

        {/* Header */}
        <HStack justify="space-between" align="center">
          <Heading size="xl">Mi Carrito</Heading>
          <Text color="gray.600">
            {getTotalItems()} producto{getTotalItems() !== 1 ? "s" : ""}
          </Text>
        </HStack>

        {/* Cart Content */}
        <Box
          display={{ base: "block", lg: "grid" }}
          gridTemplateColumns="2fr 1fr"
          gap={8}
        >
          {/* Cart Items */}
          <VStack spacing={4} align="stretch">
            {items.map((item) => (
              <CartItem key={item.id} item={item} />
            ))}
          </VStack>

          {/* Cart Summary */}
          <Box>
            <CartSummary />
          </Box>
        </Box>

        {/* Continue Shopping */}
        <Divider />

        <HStack justify="space-between" align="center">
          <Button as={Link} to="/products" variant="outline" colorScheme="blue">
            Continuar Comprando
          </Button>

          <Text fontSize="lg" fontWeight="semibold">
            Total: {formatPrice(getTotalPrice())}
          </Text>
        </HStack>
      </VStack>
    </Container>
  )
}

export default CartPage
