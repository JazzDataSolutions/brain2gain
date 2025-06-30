import { DeleteIcon } from "@chakra-ui/icons"
import {
  Badge,
  Box,
  Button,
  Divider,
  HStack,
  IconButton,
  Image,
  Popover,
  PopoverArrow,
  PopoverBody,
  PopoverCloseButton,
  PopoverContent,
  PopoverFooter,
  PopoverHeader,
  PopoverTrigger,
  Text,
  VStack,
  useColorModeValue,
} from "@chakra-ui/react"
import { Link } from "@tanstack/react-router"
import { FiShoppingCart } from "react-icons/fi"

import { useCartStore } from "../../stores/cartStore"

const MiniCart = () => {
  const { items, removeItem, getTotalPrice, getTotalItems } = useCartStore()

  const formatPrice = (price: number) => {
    return new Intl.NumberFormat("es-CO", {
      style: "currency",
      currency: "COP",
    }).format(price)
  }

  return (
    <Popover placement="bottom-end">
      <PopoverTrigger>
        <Button
          variant="ghost"
          size="sm"
          position="relative"
          leftIcon={<FiShoppingCart />}
        >
          Carrito
          {getTotalItems() > 0 && (
            <Badge
              position="absolute"
              top="-1"
              right="-1"
              colorScheme="red"
              borderRadius="full"
              fontSize="xs"
              minW="20px"
              h="20px"
              display="flex"
              alignItems="center"
              justifyContent="center"
            >
              {getTotalItems() > 99 ? "99+" : getTotalItems()}
            </Badge>
          )}
        </Button>
      </PopoverTrigger>

      <PopoverContent w="400px" maxW="90vw">
        <PopoverArrow />
        <PopoverCloseButton />
        <PopoverHeader>
          <Text fontWeight="semibold">
            Carrito de Compras {getTotalItems() > 0 && `(${getTotalItems()})`}
          </Text>
        </PopoverHeader>

        <PopoverBody p={0}>
          {items.length === 0 ? (
            <Box p={4} textAlign="center">
              <Text color="gray.500" mb={4}>
                Tu carrito está vacío
              </Text>
              <Button as={Link} to="/products" colorScheme="blue" size="sm">
                Ver Productos
              </Button>
            </Box>
          ) : (
            <VStack spacing={0} align="stretch" maxH="300px" overflowY="auto">
              {items.slice(0, 3).map((item, index) => (
                <Box key={item.id}>
                  <HStack p={3} spacing={3} align="start">
                    <Image
                      src={item.image || "/imagenes/proteina_catalogo.jpg"}
                      alt={item.name}
                      boxSize="50px"
                      objectFit="cover"
                      borderRadius="md"
                      fallbackSrc="https://via.placeholder.com/50x50?text=Brain2Gain"
                    />

                    <VStack align="stretch" flex={1} spacing={1}>
                      <Text fontSize="sm" fontWeight="medium" noOfLines={2}>
                        {item.name}
                      </Text>
                      <HStack justify="space-between" align="center">
                        <Text fontSize="xs" color="gray.500">
                          {item.quantity} x {formatPrice(item.price)}
                        </Text>
                        <Text
                          fontSize="sm"
                          fontWeight="semibold"
                          color="blue.600"
                        >
                          {formatPrice(item.price * item.quantity)}
                        </Text>
                      </HStack>
                    </VStack>

                    <IconButton
                      aria-label="Eliminar"
                      icon={<DeleteIcon />}
                      size="xs"
                      variant="ghost"
                      colorScheme="red"
                      onClick={() => removeItem(item.id)}
                    />
                  </HStack>
                  {index < Math.min(items.length, 3) - 1 && <Divider />}
                </Box>
              ))}

              {items.length > 3 && (
                <Box p={3} bg={useColorModeValue("gray.50", "gray.700")}>
                  <Text fontSize="sm" color="gray.600" textAlign="center">
                    y {items.length - 3} producto
                    {items.length - 3 !== 1 ? "s" : ""} más...
                  </Text>
                </Box>
              )}
            </VStack>
          )}
        </PopoverBody>

        {items.length > 0 && (
          <PopoverFooter>
            <VStack spacing={3} align="stretch">
              <HStack justify="space-between">
                <Text fontWeight="semibold">Total:</Text>
                <Text fontWeight="bold" color="blue.600">
                  {formatPrice(getTotalPrice())}
                </Text>
              </HStack>

              <HStack spacing={2}>
                <Button
                  as={Link}
                  to="/cart"
                  variant="outline"
                  size="sm"
                  flex={1}
                >
                  Ver Carrito
                </Button>
                <Button
                  as={Link}
                  to="/checkout"
                  colorScheme="blue"
                  size="sm"
                  flex={1}
                >
                  Checkout
                </Button>
              </HStack>
            </VStack>
          </PopoverFooter>
        )}
      </PopoverContent>
    </Popover>
  )
}

export default MiniCart
