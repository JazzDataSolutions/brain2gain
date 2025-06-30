import { DeleteIcon } from "@chakra-ui/icons"
import {
  Box,
  HStack,
  IconButton,
  Image,
  NumberDecrementStepper,
  NumberIncrementStepper,
  NumberInput,
  NumberInputField,
  NumberInputStepper,
  Text,
  VStack,
  useColorModeValue,
  useToast,
} from "@chakra-ui/react"
import { Link } from "@tanstack/react-router"

import {
  type CartItem as CartItemType,
  useCartStore,
} from "../../stores/cartStore"

interface CartItemProps {
  item: CartItemType
}

const CartItem = ({ item }: CartItemProps) => {
  const { updateQuantity, removeItem } = useCartStore()
  const toast = useToast()

  const cardBg = useColorModeValue("white", "gray.800")
  const borderColor = useColorModeValue("gray.200", "gray.600")

  const handleQuantityChange = (quantity: number) => {
    if (quantity < 1) return
    updateQuantity(item.id, quantity)
  }

  const handleRemove = () => {
    removeItem(item.id)
    toast({
      title: "Producto eliminado",
      description: `${item.name} fue eliminado del carrito`,
      status: "info",
      duration: 3000,
      isClosable: true,
    })
  }

  const formatPrice = (price: number) => {
    return new Intl.NumberFormat("es-CO", {
      style: "currency",
      currency: "COP",
    }).format(price)
  }

  return (
    <Box
      bg={cardBg}
      border="1px"
      borderColor={borderColor}
      borderRadius="lg"
      p={4}
      shadow="sm"
    >
      <HStack spacing={4} align="stretch">
        {/* Product Image */}
        <Box flexShrink={0}>
          <Image
            src={`/imagenes/${item.sku?.toLowerCase()}.jpg`}
            alt={item.name}
            boxSize="80px"
            objectFit="cover"
            borderRadius="md"
            fallbackSrc="https://via.placeholder.com/80x80?text=Brain2Gain"
          />
        </Box>

        {/* Product Info */}
        <VStack align="stretch" flex={1} spacing={2}>
          <Box>
            <Text
              as={Link}
              to={`/products/${item.id.toString()}`}
              fontWeight="semibold"
              fontSize="lg"
              _hover={{ color: "blue.600" }}
              noOfLines={2}
            >
              {item.name}
            </Text>
            <Text color="gray.500" fontSize="sm">
              SKU: {item.sku}
            </Text>
          </Box>

          <HStack justify="space-between" align="center">
            {/* Quantity Controls */}
            <HStack spacing={2}>
              <Text fontSize="sm" color="gray.600" minW="60px">
                Cantidad:
              </Text>
              <NumberInput
                size="sm"
                maxW="80px"
                min={1}
                max={10}
                value={item.quantity}
                onChange={(_, value) => handleQuantityChange(value || 1)}
              >
                <NumberInputField />
                <NumberInputStepper>
                  <NumberIncrementStepper />
                  <NumberDecrementStepper />
                </NumberInputStepper>
              </NumberInput>
            </HStack>

            {/* Price */}
            <VStack spacing={1} align="end">
              <Text fontSize="sm" color="gray.600">
                {formatPrice(item.price)} c/u
              </Text>
              <Text fontSize="lg" fontWeight="bold" color="blue.600">
                {formatPrice(item.price * item.quantity)}
              </Text>
            </VStack>

            {/* Remove Button */}
            <IconButton
              aria-label="Eliminar producto"
              icon={<DeleteIcon />}
              size="sm"
              colorScheme="red"
              variant="ghost"
              onClick={handleRemove}
            />
          </HStack>
        </VStack>
      </HStack>
    </Box>
  )
}

export default CartItem
