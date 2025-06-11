import {
  Box,
  Container,
  VStack,
  Heading,
  Text,
  Card,
  CardBody,
  Image,
  Button,
  HStack,
  IconButton,
  NumberInput,
  NumberInputField,
  NumberInputStepper,
  NumberIncrementStepper,
  NumberDecrementStepper,
  Divider,
  useColorModeValue,
  Flex,
  Badge,
  Alert,
  AlertIcon,
} from '@chakra-ui/react'
import { FiTrash2, FiShoppingCart, FiArrowLeft } from 'react-icons/fi'
import { useNavigate } from '@tanstack/react-router'

import { useCartStore } from '../../stores/cartStore'

const CartPage = () => {
  const navigate = useNavigate()
  const cardBg = useColorModeValue('white', 'gray.800')
  const { items, updateQuantity, removeItem, getTotalPrice, getTotalItems, clearCart } = useCartStore()

  const handleQuantityChange = (itemId: string, newQuantity: number) => {
    if (newQuantity <= 0) {
      removeItem(itemId)
    } else {
      updateQuantity(itemId, newQuantity)
    }
  }

  const CartItem = ({ item }: { item: any }) => (
    <Card bg={cardBg} mb={4}>
      <CardBody>
        <Flex direction={{ base: 'column', md: 'row' }} gap={4}>
          {/* Product Image */}
          <Image
            src={item.image}
            alt={item.name}
            boxSize={{ base: 'full', md: '120px' }}
            objectFit="cover"
            rounded="md"
          />

          {/* Product Info */}
          <Box flex={1}>
            <VStack align="start" spacing={2}>
              <Text fontWeight="semibold" fontSize="lg">
                {item.name}
              </Text>
              <Text color="gray.600" fontSize="sm">
                SKU: {item.id}
              </Text>
              <Badge colorScheme="green" size="sm">
                En Stock
              </Badge>
            </VStack>
          </Box>

          {/* Quantity Controls */}
          <VStack spacing={3}>
            <Text fontSize="sm" color="gray.600">
              Cantidad
            </Text>
            <NumberInput
              value={item.quantity}
              min={1}
              max={99}
              size="sm"
              w="80px"
              onChange={(_, value) => handleQuantityChange(item.id, value)}
            >
              <NumberInputField />
              <NumberInputStepper>
                <NumberIncrementStepper />
                <NumberDecrementStepper />
              </NumberInputStepper>
            </NumberInput>
          </VStack>

          {/* Price and Actions */}
          <VStack spacing={3} align="end">
            <VStack spacing={1} align="end">
              <Text fontSize="sm" color="gray.600">
                Precio Unitario
              </Text>
              <Text fontWeight="semibold">
                ${item.price}
              </Text>
            </VStack>
            
            <VStack spacing={1} align="end">
              <Text fontSize="sm" color="gray.600">
                Subtotal
              </Text>
              <Text fontSize="lg" fontWeight="bold" color="blue.500">
                ${(item.price * item.quantity).toFixed(2)}
              </Text>
            </VStack>

            <IconButton
              icon={<FiTrash2 />}
              variant="ghost"
              colorScheme="red"
              size="sm"
              onClick={() => removeItem(item.id)}
              aria-label="Eliminar producto"
            />
          </VStack>
        </Flex>
      </CardBody>
    </Card>
  )

  return (
    <Container maxW="6xl" py={8}>
      <VStack spacing={8} align="stretch">
        {/* Header */}
        <HStack>
          <IconButton
            icon={<FiArrowLeft />}
            variant="ghost"
            onClick={() => navigate({ to: '/store/products' })}
            aria-label="Volver a productos"
          />
          <Box>
            <Heading size="xl" mb={2}>
              Carrito de Compras
            </Heading>
            <Text color="gray.600">
              {getTotalItems()} artículos en tu carrito
            </Text>
          </Box>
        </HStack>

        {items.length === 0 ? (
          /* Empty Cart */
          <Card bg={cardBg}>
            <CardBody>
              <VStack spacing={6} py={12}>
                <FiShoppingCart size={64} color="gray.300" />
                <VStack spacing={2}>
                  <Text fontSize="xl" fontWeight="semibold" color="gray.500">
                    Tu carrito está vacío
                  </Text>
                  <Text color="gray.400" textAlign="center">
                    Explora nuestro catálogo y agrega productos para comenzar tu compra
                  </Text>
                </VStack>
                <Button
                  colorScheme="blue"
                  size="lg"
                  onClick={() => navigate({ to: '/store/products' })}
                >
                  Explorar Productos
                </Button>
              </VStack>
            </CardBody>
          </Card>
        ) : (
          /* Cart with Items */
          <Flex direction={{ base: 'column', lg: 'row' }} gap={8}>
            {/* Cart Items */}
            <Box flex={2}>
              <VStack spacing={4} align="stretch">
                {items.map((item) => (
                  <CartItem key={item.id} item={item} />
                ))}

                {/* Clear Cart */}
                <HStack justify="space-between">
                  <Button
                    variant="ghost"
                    colorScheme="red"
                    size="sm"
                    onClick={clearCart}
                  >
                    Vaciar Carrito
                  </Button>
                  <Button
                    variant="outline"
                    onClick={() => navigate({ to: '/store/products' })}
                  >
                    Continuar Comprando
                  </Button>
                </HStack>
              </VStack>
            </Box>

            {/* Order Summary */}
            <Box flex={1}>
              <Card bg={cardBg} position="sticky" top="4">
                <CardBody>
                  <VStack spacing={4} align="stretch">
                    <Heading size="md">Resumen del Pedido</Heading>
                    
                    <VStack spacing={3} align="stretch">
                      <HStack justify="space-between">
                        <Text>Subtotal ({getTotalItems()} artículos)</Text>
                        <Text fontWeight="semibold">${getTotalPrice().toFixed(2)}</Text>
                      </HStack>
                      
                      <HStack justify="space-between">
                        <Text>Envío</Text>
                        <Text fontWeight="semibold" color="green.500">
                          {getTotalPrice() >= 50 ? 'GRATIS' : '$5.99'}
                        </Text>
                      </HStack>
                      
                      <HStack justify="space-between">
                        <Text>Impuestos</Text>
                        <Text fontWeight="semibold">
                          ${(getTotalPrice() * 0.16).toFixed(2)}
                        </Text>
                      </HStack>
                    </VStack>

                    <Divider />

                    <HStack justify="space-between">
                      <Text fontSize="lg" fontWeight="bold">Total</Text>
                      <Text fontSize="xl" fontWeight="bold" color="blue.500">
                        ${(getTotalPrice() + (getTotalPrice() >= 50 ? 0 : 5.99) + (getTotalPrice() * 0.16)).toFixed(2)}
                      </Text>
                    </HStack>

                    {getTotalPrice() >= 50 && (
                      <Alert status="success" size="sm" rounded="md">
                        <AlertIcon />
                        <Text fontSize="sm">¡Envío gratis incluido!</Text>
                      </Alert>
                    )}

                    <Button
                      colorScheme="blue"
                      size="lg"
                      w="full"
                      onClick={() => navigate({ to: '/store/checkout' })}
                    >
                      Proceder al Pago
                    </Button>

                    <Text fontSize="xs" color="gray.500" textAlign="center">
                      Compra 100% segura con encriptación SSL
                    </Text>
                  </VStack>
                </CardBody>
              </Card>
            </Box>
          </Flex>
        )}
      </VStack>
    </Container>
  )
}

export default CartPage