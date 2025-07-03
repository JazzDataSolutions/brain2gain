/**
 * CartComponent - Complete Cart Integration
 * 
 * Displays cart contents with full CRUD operations
 * - Real-time updates
 * - Optimistic UI
 * - Error handling
 * - Responsive design
 */

import {
  Box,
  Button,
  Card,
  CardBody,
  CardHeader,
  Divider,
  Flex,
  HStack,
  IconButton,
  Image,
  Text,
  VStack,
  Badge,
  NumberInput,
  NumberInputField,
  NumberInputStepper,
  NumberIncrementStepper,
  NumberDecrementStepper,
  Alert,
  AlertIcon,
  Spinner,
  useColorModeValue,
  Heading,
  Link,
  Skeleton,
} from "@chakra-ui/react"
import { 
  FiTrash2, 
  FiPlus, 
  FiMinus, 
  FiShoppingCart, 
  FiRefreshCw,
  FiArrowRight,
  FiSave
} from "react-icons/fi"
import { Link as RouterLink } from "@tanstack/react-router"
import useCart from "../../hooks/useCart"
import useAuth from "../../hooks/useAuth"

interface CartComponentProps {
  showHeader?: boolean
  showCheckoutButton?: boolean
  maxHeight?: string
  variant?: 'full' | 'compact' | 'mini'
}

const CartComponent = ({ 
  showHeader = true, 
  showCheckoutButton = true,
  maxHeight = "400px",
  variant = 'full'
}: CartComponentProps) => {
  const { user } = useAuth()
  const {
    cart,
    isLoading,
    error,
    updateQuantity,
    removeFromCart,
    clearCart,
    getTotalPrice,
    getItemCount,
    getTotalItems,
    isUpdatingQuantity,
    isRemovingFromCart,
    isClearingCart,
    refetch
  } = useCart()

  const bgColor = useColorModeValue("white", "gray.800")
  const borderColor = useColorModeValue("gray.200", "gray.700")
  const textSecondary = useColorModeValue("gray.600", "gray.400")

  const formatPrice = (price: number) => {
    return new Intl.NumberFormat("es-MX", {
      style: "currency",
      currency: "MXN"
    }).format(price / 100) // Assuming prices are in cents
  }

  // Loading state
  if (isLoading) {
    return (
      <Card bg={bgColor} border="1px" borderColor={borderColor}>
        {showHeader && (
          <CardHeader>
            <Skeleton height="24px" width="150px" />
          </CardHeader>
        )}
        <CardBody>
          <VStack spacing={4}>
            {[1, 2, 3].map(i => (
              <HStack key={i} w="full" spacing={4}>
                <Skeleton height="60px" width="60px" />
                <VStack flex={1} align="start" spacing={2}>
                  <Skeleton height="16px" width="100%" />
                  <Skeleton height="14px" width="60%" />
                </VStack>
                <Skeleton height="32px" width="80px" />
              </HStack>
            ))}
          </VStack>
        </CardBody>
      </Card>
    )
  }

  // Error state
  if (error) {
    return (
      <Card bg={bgColor} border="1px" borderColor={borderColor}>
        <CardBody>
          <Alert status="error">
            <AlertIcon />
            <VStack align="start" spacing={2}>
              <Text>Error al cargar el carrito</Text>
              <Button 
                size="sm" 
                leftIcon={<FiRefreshCw />}
                onClick={() => refetch()}
              >
                Reintentar
              </Button>
            </VStack>
          </Alert>
        </CardBody>
      </Card>
    )
  }

  // Authentication required
  if (!user) {
    return (
      <Card bg={bgColor} border="1px" borderColor={borderColor}>
        <CardBody>
          <VStack spacing={4} py={8}>
            <FiShoppingCart size={48} color="gray" />
            <Text color={textSecondary}>
              Inicia sesión para ver tu carrito
            </Text>
            <Button 
              as={RouterLink} 
              to="/login" 
              colorScheme="blue"
            >
              Iniciar Sesión
            </Button>
          </VStack>
        </CardBody>
      </Card>
    )
  }

  // Empty cart
  if (!cart?.items?.length) {
    return (
      <Card bg={bgColor} border="1px" borderColor={borderColor}>
        {showHeader && (
          <CardHeader>
            <Heading size="md">
              <HStack>
                <FiShoppingCart />
                <Text>Mi Carrito</Text>
                <Badge colorScheme="gray">0</Badge>
              </HStack>
            </Heading>
          </CardHeader>
        )}
        <CardBody>
          <VStack spacing={4} py={8}>
            <FiShoppingCart size={48} color="gray" />
            <Text color={textSecondary}>
              Tu carrito está vacío
            </Text>
            <Button 
              as={RouterLink} 
              to="/store" 
              colorScheme="blue"
              leftIcon={<FiArrowRight />}
            >
              Ir a la Tienda
            </Button>
          </VStack>
        </CardBody>
      </Card>
    )
  }

  // Cart with items
  return (
    <Card bg={bgColor} border="1px" borderColor={borderColor}>
      {showHeader && (
        <CardHeader>
          <HStack justify="space-between">
            <Heading size="md">
              <HStack>
                <FiShoppingCart />
                <Text>Mi Carrito</Text>
                <Badge colorScheme="blue">{getItemCount()}</Badge>
              </HStack>
            </Heading>
            
            {cart.items.length > 0 && (
              <Button
                size="sm"
                variant="ghost"
                colorScheme="red"
                leftIcon={<FiTrash2 />}
                onClick={clearCart}
                isLoading={isClearingCart}
              >
                Limpiar
              </Button>
            )}
          </HStack>
        </CardHeader>
      )}

      <CardBody>
        <VStack spacing={4} maxHeight={maxHeight} overflowY="auto">
          {cart.items.map((item) => (
            <Box key={item.id} w="full">
              <HStack spacing={4} align="start">
                {/* Product Image */}
                <Image
                  src={item.product_image || "/api/placeholder/60/60"}
                  alt={item.product_name}
                  boxSize="60px"
                  objectFit="cover"
                  borderRadius="md"
                  fallbackSrc="/api/placeholder/60/60"
                />

                {/* Product Info */}
                <VStack flex={1} align="start" spacing={1}>
                  <Text fontWeight="medium" noOfLines={2}>
                    {item.product_name}
                  </Text>
                  <Text fontSize="sm" color={textSecondary}>
                    {formatPrice(item.price)} c/u
                  </Text>
                  {item.stock_available < 5 && (
                    <Badge colorScheme="orange" size="sm">
                      Solo {item.stock_available} disponibles
                    </Badge>
                  )}
                </VStack>

                {/* Quantity Controls */}
                <VStack spacing={2}>
                  <HStack>
                    <IconButton
                      aria-label="Disminuir cantidad"
                      icon={<FiMinus />}
                      size="sm"
                      variant="outline"
                      onClick={() => updateQuantity(item.product_id, item.quantity - 1)}
                      isDisabled={isUpdatingQuantity || item.quantity <= 1}
                    />
                    
                    <NumberInput
                      value={item.quantity}
                      min={1}
                      max={item.stock_available}
                      w="70px"
                      size="sm"
                      onChange={(valueString, valueNumber) => {
                        const newQuantity = valueNumber || 1
                        if (newQuantity !== item.quantity) {
                          updateQuantity(item.product_id, newQuantity)
                        }
                      }}
                    >
                      <NumberInputField textAlign="center" />
                      <NumberInputStepper>
                        <NumberIncrementStepper />
                        <NumberDecrementStepper />
                      </NumberInputStepper>
                    </NumberInput>

                    <IconButton
                      aria-label="Aumentar cantidad"
                      icon={<FiPlus />}
                      size="sm"
                      variant="outline"
                      onClick={() => updateQuantity(item.product_id, item.quantity + 1)}
                      isDisabled={isUpdatingQuantity || item.quantity >= item.stock_available}
                    />
                  </HStack>

                  {/* Subtotal */}
                  <Text fontWeight="bold" color="green.500">
                    {formatPrice(item.subtotal)}
                  </Text>
                </VStack>

                {/* Remove Button */}
                <IconButton
                  aria-label="Eliminar producto"
                  icon={<FiTrash2 />}
                  size="sm"
                  variant="ghost"
                  colorScheme="red"
                  onClick={() => removeFromCart(item.product_id)}
                  isLoading={isRemovingFromCart}
                />
              </HStack>

              {variant === 'full' && (
                <HStack justify="space-between" mt={2} fontSize="sm">
                  <Text color={textSecondary}>
                    Total: {item.quantity} × {formatPrice(item.price)}
                  </Text>
                  <Button
                    size="xs"
                    variant="ghost"
                    leftIcon={<FiSave />}
                    onClick={() => {
                      // TODO: Implement save for later
                      console.log('Save for later:', item.product_id)
                    }}
                  >
                    Guardar para después
                  </Button>
                </HStack>
              )}
            </Box>
          ))}
        </VStack>

        <Divider my={4} />

        {/* Cart Summary */}
        <VStack spacing={3}>
          <HStack justify="space-between" w="full">
            <Text color={textSecondary}>
              {getTotalItems()} productos
            </Text>
            <Text fontSize="sm" color={textSecondary}>
              Subtotal
            </Text>
          </HStack>

          <HStack justify="space-between" w="full">
            <Text fontSize="lg" fontWeight="bold">
              Total
            </Text>
            <Text fontSize="xl" fontWeight="bold" color="green.500">
              {formatPrice(getTotalPrice())}
            </Text>
          </HStack>

          {showCheckoutButton && (
            <Button
              as={RouterLink}
              to="/checkout"
              colorScheme="blue"
              size="lg"
              w="full"
              rightIcon={<FiArrowRight />}
            >
              Proceder al Pago
            </Button>
          )}

          <Text fontSize="xs" color={textSecondary} textAlign="center">
            Los precios incluyen IVA. Envío calculado en checkout.
          </Text>
        </VStack>
      </CardBody>
    </Card>
  )
}

export default CartComponent