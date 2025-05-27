import {
  Box,
  VStack,
  HStack,
  Text,
  Button,
  Divider,
  useColorModeValue,
} from '@chakra-ui/react'
import { Link } from '@tanstack/react-router'

import { useCartStore } from '../../stores/cartStore'

const CartSummary = () => {
  const { items, item_count, total_amount, clearCart } = useCartStore()
  
  const cardBg = useColorModeValue('white', 'gray.800')
  const borderColor = useColorModeValue('gray.200', 'gray.600')

  const formatPrice = (price: number) => {
    return new Intl.NumberFormat('es-CO', {
      style: 'currency',
      currency: 'COP',
    }).format(price)
  }

  // Calculate summary details
  const subtotal = total_amount
  const shipping = subtotal > 100000 ? 0 : 15000 // Free shipping over $100,000
  const tax = Math.round(subtotal * 0.19) // 19% IVA
  const finalTotal = subtotal + shipping + tax

  return (
    <Box
      bg={cardBg}
      border="1px"
      borderColor={borderColor}
      borderRadius="lg"
      p={6}
      shadow="sm"
      position="sticky"
      top={4}
    >
      <VStack spacing={4} align="stretch">
        <Text fontSize="lg" fontWeight="semibold">
          Resumen del Pedido
        </Text>

        <Divider />

        {/* Order Details */}
        <VStack spacing={3} align="stretch">
          <HStack justify="space-between">
            <Text>Subtotal ({item_count} productos)</Text>
            <Text>{formatPrice(subtotal)}</Text>
          </HStack>

          <HStack justify="space-between">
            <Text>Envío</Text>
            <Text color={shipping === 0 ? 'green.500' : 'gray.600'}>
              {shipping === 0 ? 'GRATIS' : formatPrice(shipping)}
            </Text>
          </HStack>

          <HStack justify="space-between">
            <Text>IVA (19%)</Text>
            <Text>{formatPrice(tax)}</Text>
          </HStack>

          {shipping === 0 && (
            <Text fontSize="sm" color="green.500">
              ¡Envío gratis por compras mayores a $100,000!
            </Text>
          )}
        </VStack>

        <Divider />

        {/* Total */}
        <HStack justify="space-between">
          <Text fontSize="lg" fontWeight="bold">
            Total
          </Text>
          <Text fontSize="lg" fontWeight="bold" color="blue.600">
            {formatPrice(finalTotal)}
          </Text>
        </HStack>

        {/* Action Buttons */}
        <VStack spacing={3} align="stretch">
          <Button
            colorScheme="blue"
            size="lg"
            w="100%"
            as={Link}
            to="/checkout"
          >
            Proceder al Checkout
          </Button>

          <Button
            variant="outline"
            size="sm"
            w="100%"
            onClick={clearCart}
          >
            Vaciar Carrito
          </Button>
        </VStack>

        {/* Security Info */}
        <Box>
          <Text fontSize="xs" color="gray.500" textAlign="center">
            🔒 Compra 100% segura
          </Text>
          <Text fontSize="xs" color="gray.500" textAlign="center">
            Aceptamos todas las tarjetas de crédito
          </Text>
        </Box>
      </VStack>
    </Box>
  )
}

export default CartSummary