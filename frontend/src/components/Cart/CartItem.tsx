import {
  Box,
  HStack,
  VStack,
  Image,
  Text,
  Button,
  NumberInput,
  NumberInputField,
  NumberInputStepper,
  NumberIncrementStepper,
  NumberDecrementStepper,
  IconButton,
  useColorModeValue,
  useToast,
} from '@chakra-ui/react'
import { DeleteIcon } from '@chakra-ui/icons'
import { Link } from '@tanstack/react-router'

import { CartItem as CartItemType, useCartStore } from '../../stores/cartStore'

interface CartItemProps {
  item: CartItemType
}

const CartItem = ({ item }: CartItemProps) => {
  const { updateQuantity, removeFromCart } = useCartStore()
  const toast = useToast()

  const cardBg = useColorModeValue('white', 'gray.800')
  const borderColor = useColorModeValue('gray.200', 'gray.600')

  const handleQuantityChange = (quantity: number) => {
    if (quantity < 1) return
    updateQuantity(item.product_id, quantity)
  }

  const handleRemove = () => {
    removeFromCart(item.product_id)
    toast({
      title: 'Producto eliminado',
      description: `${item.product_name} fue eliminado del carrito`,
      status: 'info',
      duration: 3000,
      isClosable: true,
    })
  }

  const formatPrice = (price: number) => {
    return new Intl.NumberFormat('es-CO', {
      style: 'currency',
      currency: 'COP',
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
            src={`/imagenes/${item.product_sku.toLowerCase()}.jpg`}
            alt={item.product_name}
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
              to="/products/$productId"
              params={{ productId: item.product_id.toString() }}
              fontWeight="semibold"
              fontSize="lg"
              _hover={{ color: 'blue.600' }}
              noOfLines={2}
            >
              {item.product_name}
            </Text>
            <Text color="gray.500" fontSize="sm">
              SKU: {item.product_sku}
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
                {formatPrice(item.unit_price)} c/u
              </Text>
              <Text fontSize="lg" fontWeight="bold" color="blue.600">
                {formatPrice(item.total_price)}
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