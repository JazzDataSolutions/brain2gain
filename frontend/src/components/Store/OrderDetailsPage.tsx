import {
  Alert,
  AlertDescription,
  AlertIcon,
  Badge,
  Box,
  Breadcrumb,
  BreadcrumbItem,
  BreadcrumbLink,
  Button,
  Card,
  CardBody,
  CardHeader,
  Container,
  Divider,
  Flex,
  Grid,
  GridItem,
  HStack,
  Heading,
  Icon,
  Image,
  Progress,
  Text,
  Timeline,
  TimelineContent,
  TimelineItem,
  TimelineMarker,
  TimelineTrack,
  VStack,
  useColorModeValue,
} from "@chakra-ui/react"
import { useNavigate, useParams } from "@tanstack/react-router"
import { useEffect, useState } from "react"
import {
  FiArrowLeft,
  FiCreditCard,
  FiDownload,
  FiMapPin,
  FiPackage,
  FiRefreshCcw,
  FiTruck,
} from "react-icons/fi"
import orderService, { type Order } from "../../services/orderService"

const OrderDetailsPage = () => {
  const navigate = useNavigate()
  const { orderId } = useParams({ strict: false })
  const cardBg = useColorModeValue("white", "gray.800")
  const [order, setOrder] = useState<Order | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const fetchOrder = async () => {
      if (!orderId) {
        setError("ID de pedido no válido")
        setLoading(false)
        return
      }

      try {
        const orderData = await orderService.getOrderById(orderId)
        setOrder(orderData)
      } catch (err) {
        console.error("Error fetching order:", err)
        setError("No se pudo cargar la información del pedido")
      } finally {
        setLoading(false)
      }
    }

    fetchOrder()
  }, [orderId])

  const getStatusColor = (status: string) => {
    switch (status.toLowerCase()) {
      case "confirmed":
        return "green"
      case "pending":
        return "yellow"
      case "processing":
        return "blue"
      case "shipped":
        return "purple"
      case "delivered":
        return "green"
      case "cancelled":
        return "red"
      default:
        return "gray"
    }
  }

  const getStatusText = (status: string) => {
    switch (status.toLowerCase()) {
      case "confirmed":
        return "Confirmado"
      case "pending":
        return "Pendiente"
      case "processing":
        return "Procesando"
      case "shipped":
        return "Enviado"
      case "delivered":
        return "Entregado"
      case "cancelled":
        return "Cancelado"
      default:
        return status
    }
  }

  const getOrderProgress = (status: string) => {
    switch (status.toLowerCase()) {
      case "pending":
        return 20
      case "confirmed":
        return 40
      case "processing":
        return 60
      case "shipped":
        return 80
      case "delivered":
        return 100
      case "cancelled":
        return 0
      default:
        return 0
    }
  }

  const getPaymentMethodText = (method: string) => {
    switch (method.toLowerCase()) {
      case "stripe":
        return "Tarjeta de Crédito/Débito"
      case "paypal":
        return "PayPal"
      case "bank_transfer":
        return "Transferencia Bancaria"
      default:
        return method
    }
  }

  if (loading) {
    return (
      <Container maxW="6xl" py={8}>
        <VStack spacing={6} align="center">
          <Heading size="lg">Cargando detalles del pedido...</Heading>
        </VStack>
      </Container>
    )
  }

  if (error || !order) {
    return (
      <Container maxW="6xl" py={8}>
        <VStack spacing={6} align="center" textAlign="center">
          <Heading size="lg" color="red.500">
            Error al cargar el pedido
          </Heading>
          <Text color="gray.600">
            {error || "No se encontró información del pedido"}
          </Text>
          <Button
            leftIcon={<FiArrowLeft />}
            onClick={() => navigate({ to: "/store/orders" })}
          >
            Volver a Mis Pedidos
          </Button>
        </VStack>
      </Container>
    )
  }

  return (
    <Container maxW="6xl" py={8}>
      <VStack spacing={8} align="stretch">
        {/* Breadcrumb */}
        <Breadcrumb>
          <BreadcrumbItem>
            <BreadcrumbLink onClick={() => navigate({ to: "/store" })}>
              Tienda
            </BreadcrumbLink>
          </BreadcrumbItem>
          <BreadcrumbItem>
            <BreadcrumbLink onClick={() => navigate({ to: "/store/orders" })}>
              Mis Pedidos
            </BreadcrumbLink>
          </BreadcrumbItem>
          <BreadcrumbItem isCurrentPage>
            <BreadcrumbLink>
              Pedido #{order.order_id.slice(-8).toUpperCase()}
            </BreadcrumbLink>
          </BreadcrumbItem>
        </Breadcrumb>

        {/* Header */}
        <Flex justify="space-between" align="center" flexWrap="wrap" gap={4}>
          <Box>
            <Heading size="xl" mb={2}>
              Pedido #{order.order_id.slice(-8).toUpperCase()}
            </Heading>
            <HStack spacing={4} flexWrap="wrap">
              <Badge
                colorScheme={getStatusColor(order.status)}
                fontSize="md"
                p={2}
              >
                {getStatusText(order.status)}
              </Badge>
              <Text color="gray.600">
                Realizado el{" "}
                {new Date(order.created_at).toLocaleDateString("es-MX", {
                  year: "numeric",
                  month: "long",
                  day: "numeric",
                  hour: "2-digit",
                  minute: "2-digit",
                })}
              </Text>
            </HStack>
          </Box>
          <HStack spacing={3}>
            <Button
              leftIcon={<FiArrowLeft />}
              variant="outline"
              onClick={() => navigate({ to: "/store/orders" })}
            >
              Volver
            </Button>
            <Button leftIcon={<FiDownload />} variant="outline">
              Descargar Factura
            </Button>
            {(order.status === "PENDING" || order.status === "CONFIRMED") && (
              <Button
                leftIcon={<FiRefreshCcw />}
                colorScheme="red"
                variant="outline"
                onClick={async () => {
                  try {
                    await orderService.cancelOrder(
                      order.order_id,
                      "Cancelado por el usuario",
                    )
                    // Refresh order data
                    window.location.reload()
                  } catch (error) {
                    console.error("Error canceling order:", error)
                  }
                }}
              >
                Cancelar Pedido
              </Button>
            )}
          </HStack>
        </Flex>

        {/* Order Progress */}
        {order.status !== "CANCELLED" && (
          <Card bg={cardBg}>
            <CardHeader>
              <Heading size="md">Estado del Pedido</Heading>
            </CardHeader>
            <CardBody>
              <VStack spacing={4} align="stretch">
                <Box>
                  <Flex justify="space-between" mb={2}>
                    <Text fontWeight="medium">Progreso</Text>
                    <Text fontSize="sm" color="gray.600">
                      {getOrderProgress(order.status)}%
                    </Text>
                  </Flex>
                  <Progress
                    value={getOrderProgress(order.status)}
                    colorScheme={getStatusColor(order.status)}
                    size="lg"
                    rounded="md"
                  />
                </Box>

                {order.tracking_number && (
                  <Alert status="info">
                    <AlertIcon />
                    <AlertDescription>
                      <strong>Número de seguimiento:</strong>{" "}
                      {order.tracking_number}
                    </AlertDescription>
                  </Alert>
                )}

                {order.estimated_delivery && (
                  <Alert status="success">
                    <AlertIcon />
                    <AlertDescription>
                      <strong>Entrega estimada:</strong>{" "}
                      {new Date(order.estimated_delivery).toLocaleDateString(
                        "es-MX",
                      )}
                    </AlertDescription>
                  </Alert>
                )}
              </VStack>
            </CardBody>
          </Card>
        )}

        <Grid templateColumns={{ base: "1fr", lg: "2fr 1fr" }} gap={8}>
          {/* Order Details */}
          <GridItem>
            <VStack spacing={6} align="stretch">
              {/* Products */}
              <Card bg={cardBg}>
                <CardHeader>
                  <Heading size="md">Productos Pedidos</Heading>
                </CardHeader>
                <CardBody>
                  <VStack spacing={4} align="stretch">
                    {order.items.map((item) => (
                      <Box key={item.item_id}>
                        <HStack spacing={4} align="start">
                          <Image
                            src="https://via.placeholder.com/80x80?text=Producto"
                            alt={item.product_name}
                            boxSize="80px"
                            objectFit="cover"
                            rounded="md"
                          />
                          <Box flex={1}>
                            <Text fontWeight="medium" fontSize="lg">
                              {item.product_name}
                            </Text>
                            <Text fontSize="sm" color="gray.500" mb={2}>
                              SKU: {item.product_sku}
                            </Text>
                            <HStack spacing={4}>
                              <Text fontSize="sm">
                                Cantidad: <strong>{item.quantity}</strong>
                              </Text>
                              <Text fontSize="sm">
                                Precio unitario:{" "}
                                <strong>${item.unit_price.toFixed(2)}</strong>
                              </Text>
                            </HStack>
                          </Box>
                          <Box textAlign="right">
                            <Text
                              fontWeight="bold"
                              fontSize="lg"
                              color="blue.500"
                            >
                              ${item.line_total.toFixed(2)}
                            </Text>
                            {item.discount_amount > 0 && (
                              <Text fontSize="sm" color="green.500">
                                Descuento: -${item.discount_amount.toFixed(2)}
                              </Text>
                            )}
                          </Box>
                        </HStack>
                        <Divider mt={4} />
                      </Box>
                    ))}
                  </VStack>
                </CardBody>
              </Card>

              {/* Shipping Address */}
              <Card bg={cardBg}>
                <CardHeader>
                  <HStack>
                    <Icon as={FiMapPin} color="green.500" />
                    <Heading size="md">Dirección de Envío</Heading>
                  </HStack>
                </CardHeader>
                <CardBody>
                  <VStack spacing={2} align="start">
                    <Text fontWeight="medium" fontSize="lg">
                      {order.shipping_address.first_name}{" "}
                      {order.shipping_address.last_name}
                    </Text>
                    {order.shipping_address.company && (
                      <Text color="gray.600">
                        {order.shipping_address.company}
                      </Text>
                    )}
                    <Text>{order.shipping_address.address_line_1}</Text>
                    {order.shipping_address.address_line_2 && (
                      <Text>{order.shipping_address.address_line_2}</Text>
                    )}
                    <Text>
                      {order.shipping_address.city},{" "}
                      {order.shipping_address.state}{" "}
                      {order.shipping_address.postal_code}
                    </Text>
                    <Text>{order.shipping_address.country}</Text>
                    {order.shipping_address.phone && (
                      <Text color="gray.600">
                        Tel: {order.shipping_address.phone}
                      </Text>
                    )}
                  </VStack>
                </CardBody>
              </Card>
            </VStack>
          </GridItem>

          {/* Order Summary */}
          <GridItem>
            <VStack spacing={6} align="stretch">
              {/* Payment & Totals */}
              <Card bg={cardBg}>
                <CardHeader>
                  <Heading size="md">Resumen del Pedido</Heading>
                </CardHeader>
                <CardBody>
                  <VStack spacing={4} align="stretch">
                    {/* Payment Method */}
                    <Box>
                      <HStack mb={2}>
                        <Icon as={FiCreditCard} color="purple.500" />
                        <Text fontWeight="medium">Método de Pago</Text>
                      </HStack>
                      <Text>{getPaymentMethodText(order.payment_method)}</Text>
                      <Badge
                        colorScheme={
                          order.payment_status === "CAPTURED"
                            ? "green"
                            : order.payment_status === "PENDING"
                              ? "yellow"
                              : order.payment_status === "FAILED"
                                ? "red"
                                : "gray"
                        }
                        mt={1}
                      >
                        {order.payment_status}
                      </Badge>
                    </Box>

                    <Divider />

                    {/* Totals */}
                    <VStack spacing={2} align="stretch">
                      <HStack justify="space-between">
                        <Text>Subtotal</Text>
                        <Text>${order.subtotal.toFixed(2)}</Text>
                      </HStack>
                      <HStack justify="space-between">
                        <HStack>
                          <Icon as={FiTruck} size="sm" color="green.500" />
                          <Text>Envío</Text>
                        </HStack>
                        <Text
                          color={
                            order.shipping_cost === 0 ? "green.500" : "inherit"
                          }
                        >
                          {order.shipping_cost === 0
                            ? "GRATIS"
                            : `$${order.shipping_cost.toFixed(2)}`}
                        </Text>
                      </HStack>
                      <HStack justify="space-between">
                        <Text>Impuestos (16%)</Text>
                        <Text>${order.tax_amount.toFixed(2)}</Text>
                      </HStack>
                      <Divider />
                      <HStack
                        justify="space-between"
                        fontSize="lg"
                        fontWeight="bold"
                      >
                        <Text>Total</Text>
                        <Text color="blue.500">
                          ${order.total_amount.toFixed(2)}
                        </Text>
                      </HStack>
                    </VStack>
                  </VStack>
                </CardBody>
              </Card>

              {/* Support */}
              <Card bg={cardBg}>
                <CardHeader>
                  <Heading size="md">¿Necesitas Ayuda?</Heading>
                </CardHeader>
                <CardBody>
                  <VStack spacing={4} align="stretch">
                    <Text fontSize="sm" color="gray.600">
                      Si tienes preguntas sobre tu pedido, no dudes en
                      contactarnos:
                    </Text>
                    <VStack spacing={2} align="start" fontSize="sm">
                      <Text>📧 contacto@brain2gain.com</Text>
                      <Text>📞 +52 55 1234 5678</Text>
                      <Text>💬 WhatsApp: +52 55 1234 5678</Text>
                    </VStack>
                    <Button size="sm" colorScheme="blue" variant="outline">
                      Contactar Soporte
                    </Button>
                  </VStack>
                </CardBody>
              </Card>
            </VStack>
          </GridItem>
        </Grid>
      </VStack>
    </Container>
  )
}

export default OrderDetailsPage
