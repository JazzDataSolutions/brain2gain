import {
  Box,
  Container,
  VStack,
  HStack,
  Heading,
  Text,
  Card,
  CardBody,
  Button,
  useColorModeValue,
  Badge,
  Divider,
  Icon,
  Alert,
  AlertIcon,
  AlertDescription,
  Flex,
} from '@chakra-ui/react'
import { FiCheck, FiMail, FiTruck, FiHome } from 'react-icons/fi'
import { FaWhatsapp, FaPhone, FaEnvelope } from 'react-icons/fa'
import { useNavigate, useSearch } from '@tanstack/react-router'
import { useEffect, useState } from 'react'
import orderService, { type Order } from '../../services/orderService'

const OrderSuccessPage = () => {
  const navigate = useNavigate()
  const { orderId } = useSearch({ from: '/store/order-success' })
  const cardBg = useColorModeValue('white', 'gray.800')
  const [order, setOrder] = useState<Order | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const fetchOrder = async () => {
      if (!orderId) {
        setError('ID de pedido no encontrado')
        setLoading(false)
        return
      }

      try {
        const orderData = await orderService.getOrderById(orderId)
        setOrder(orderData)
      } catch (err) {
        console.error('Error fetching order:', err)
        setError('No se pudo cargar la información del pedido')
      } finally {
        setLoading(false)
      }
    }

    fetchOrder()
  }, [orderId])

  const getStatusColor = (status: string) => {
    switch (status.toLowerCase()) {
      case 'confirmed':
        return 'green'
      case 'pending':
        return 'yellow'
      case 'processing':
        return 'blue'
      case 'shipped':
        return 'purple'
      case 'delivered':
        return 'green'
      case 'cancelled':
        return 'red'
      default:
        return 'gray'
    }
  }

  const getPaymentStatusColor = (status: string) => {
    switch (status.toLowerCase()) {
      case 'captured':
        return 'green'
      case 'authorized':
        return 'blue'
      case 'pending':
        return 'yellow'
      case 'failed':
        return 'red'
      case 'refunded':
        return 'orange'
      default:
        return 'gray'
    }
  }

  if (loading) {
    return (
      <Container maxW="4xl" py={8}>
        <VStack spacing={6} align="center">
          <Heading size="lg">Cargando información del pedido...</Heading>
        </VStack>
      </Container>
    )
  }

  if (error || !order) {
    return (
      <Container maxW="4xl" py={8}>
        <VStack spacing={6} align="center" textAlign="center">
          <Heading size="lg" color="red.500">
            Error al cargar el pedido
          </Heading>
          <Text color="gray.600">
            {error || 'No se encontró información del pedido'}
          </Text>
          <Button
            colorScheme="blue"
            onClick={() => navigate({ to: '/store' })}
          >
            Volver a la tienda
          </Button>
        </VStack>
      </Container>
    )
  }

  return (
    <Container maxW="6xl" py={8}>
      <VStack spacing={8} align="stretch">
        {/* Success Header */}
        <Box textAlign="center">
          <VStack spacing={4}>
            <Box
              w={16}
              h={16}
              bg="green.100"
              rounded="full"
              display="flex"
              alignItems="center"
              justifyContent="center"
              mx="auto"
            >
              <Icon as={FiCheck} boxSize={8} color="green.500" />
            </Box>
            <Heading size="xl" color="green.600">
              ¡Pedido Confirmado!
            </Heading>
            <Text fontSize="lg" color="gray.600">
              Gracias por tu compra. Tu pedido ha sido procesado exitosamente.
            </Text>
          </VStack>
        </Box>

        {/* Order Summary */}
        <Card bg={cardBg}>
          <CardBody>
            <VStack spacing={6} align="stretch">
              {/* Order Header */}
              <Flex justify="space-between" align="center" flexWrap="wrap" gap={4}>
                <Box>
                  <Heading size="md" mb={1}>
                    Pedido #{order.order_id.slice(-8).toUpperCase()}
                  </Heading>
                  <Text fontSize="sm" color="gray.500">
                    Realizado el {new Date(order.created_at).toLocaleDateString('es-MX', {
                      year: 'numeric',
                      month: 'long',
                      day: 'numeric',
                      hour: '2-digit',
                      minute: '2-digit'
                    })}
                  </Text>
                </Box>
                <VStack spacing={2} align="end">
                  <Badge colorScheme={getStatusColor(order.status)} fontSize="sm">
                    {order.status}
                  </Badge>
                  <Badge colorScheme={getPaymentStatusColor(order.payment_status)} fontSize="sm">
                    Pago: {order.payment_status}
                  </Badge>
                </VStack>
              </Flex>

              <Divider />

              {/* Order Details */}
              <Box>
                <Heading size="sm" mb={3}>Detalles del Pedido</Heading>
                <VStack spacing={3} align="stretch">
                  {order.items.map((item) => (
                    <HStack key={item.item_id} justify="space-between">
                      <Box>
                        <Text fontWeight="medium">{item.product_name}</Text>
                        <Text fontSize="sm" color="gray.500">
                          Cantidad: {item.quantity} x ${item.unit_price.toFixed(2)}
                        </Text>
                      </Box>
                      <Text fontWeight="semibold">
                        ${item.line_total.toFixed(2)}
                      </Text>
                    </HStack>
                  ))}
                </VStack>
              </Box>

              <Divider />

              {/* Totals */}
              <VStack spacing={2} align="stretch">
                <HStack justify="space-between">
                  <Text>Subtotal</Text>
                  <Text>${order.subtotal.toFixed(2)}</Text>
                </HStack>
                <HStack justify="space-between">
                  <Text>Envío</Text>
                  <Text color={order.shipping_cost === 0 ? "green.500" : "inherit"}>
                    {order.shipping_cost === 0 ? 'GRATIS' : `$${order.shipping_cost.toFixed(2)}`}
                  </Text>
                </HStack>
                <HStack justify="space-between">
                  <Text>Impuestos</Text>
                  <Text>${order.tax_amount.toFixed(2)}</Text>
                </HStack>
                <Divider />
                <HStack justify="space-between" fontSize="lg" fontWeight="bold">
                  <Text>Total</Text>
                  <Text color="blue.500">${order.total_amount.toFixed(2)}</Text>
                </HStack>
              </VStack>

              <Divider />

              {/* Shipping Address */}
              <Box>
                <Heading size="sm" mb={2}>Dirección de Envío</Heading>
                <VStack spacing={1} align="start">
                  <Text fontWeight="medium">
                    {order.shipping_address.first_name} {order.shipping_address.last_name}
                  </Text>
                  <Text>{order.shipping_address.address_line_1}</Text>
                  {order.shipping_address.address_line_2 && (
                    <Text>{order.shipping_address.address_line_2}</Text>
                  )}
                  <Text>
                    {order.shipping_address.city}, {order.shipping_address.state} {order.shipping_address.postal_code}
                  </Text>
                  <Text>{order.shipping_address.country}</Text>
                </VStack>
              </Box>
            </VStack>
          </CardBody>
        </Card>

        {/* Next Steps */}
        <Card bg={cardBg}>
          <CardBody>
            <VStack spacing={4} align="stretch">
              <Heading size="md">¿Qué sigue?</Heading>
              
              <Alert status="info">
                <AlertIcon />
                <AlertDescription>
                  <VStack spacing={2} align="start">
                    <HStack>
                      <Icon as={FiMail} />
                      <Text fontSize="sm">
                        Recibirás un email de confirmación con todos los detalles
                      </Text>
                    </HStack>
                    <HStack>
                      <Icon as={FiTruck} />
                      <Text fontSize="sm">
                        Tu pedido será procesado en las próximas 24-48 horas
                      </Text>
                    </HStack>
                    {order.tracking_number && (
                      <HStack>
                        <Icon as={FiTruck} />
                        <Text fontSize="sm">
                          Número de seguimiento: {order.tracking_number}
                        </Text>
                      </HStack>
                    )}
                  </VStack>
                </AlertDescription>
              </Alert>

              {/* Contact Support */}
              <Box bg="blue.50" p={4} rounded="md">
                <Text fontSize="sm" color="blue.700" mb={3} fontWeight="medium">
                  ¿Necesitas ayuda? Contáctanos:
                </Text>
                <HStack spacing={4} wrap="wrap">
                  <HStack>
                    <Icon as={FaEnvelope} color="blue.500" />
                    <Text fontSize="sm">contacto@brain2gain.com</Text>
                  </HStack>
                  <HStack>
                    <Icon as={FaWhatsapp} color="green.500" />
                    <Text fontSize="sm">+52 55 1234 5678</Text>
                  </HStack>
                </HStack>
              </Box>
            </VStack>
          </CardBody>
        </Card>

        {/* Action Buttons */}
        <HStack justify="center" spacing={4}>
          <Button
            leftIcon={<FiHome />}
            colorScheme="blue"
            onClick={() => navigate({ to: '/store' })}
          >
            Volver a la Tienda
          </Button>
          <Button
            variant="outline"
            onClick={() => navigate({ to: '/store/orders' })}
          >
            Ver Mis Pedidos
          </Button>
        </HStack>
      </VStack>
    </Container>
  )
}

export default OrderSuccessPage