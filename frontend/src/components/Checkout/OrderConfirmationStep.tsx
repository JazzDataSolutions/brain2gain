import {
  Alert,
  AlertDescription,
  AlertIcon,
  Badge,
  Box,
  Button,
  Card,
  CardBody,
  CardHeader,
  Checkbox,
  Divider,
  Grid,
  GridItem,
  HStack,
  Heading,
  Icon,
  Image,
  Link,
  Skeleton,
  Spinner,
  Text,
  VStack,
  useColorModeValue,
} from "@chakra-ui/react"
import {
  FaCreditCard,
  FaMapMarkerAlt,
  FaPaypal,
  FaTruck,
  FaUniversity,
  FaUser,
} from "react-icons/fa"
import { useCartStore } from "../../stores/cartStore"
import type { ContactInformation } from "./ContactInformationStep"
import type { PaymentInformation } from "./PaymentInformationStep"
import type { ShippingInformation } from "./ShippingInformationStep"

interface OrderConfirmationStepProps {
  contactInfo: ContactInformation
  shippingInfo: ShippingInformation
  paymentInfo: PaymentInformation
  onPlaceOrder: () => void
  isLoading?: boolean
  onEditStep: (step: number) => void
  calculatedTotals?: {
    subtotal: number
    tax_amount: number
    shipping_cost: number
    total_amount: number
  } | null
  isCalculatingTotals?: boolean
}

const OrderConfirmationStep = ({
  contactInfo,
  shippingInfo,
  paymentInfo,
  onPlaceOrder,
  isLoading = false,
  onEditStep,
  calculatedTotals,
  isCalculatingTotals = false,
}: OrderConfirmationStepProps) => {
  const { items, getTotalPrice, getTotalItems } = useCartStore()
  const cardBg = useColorModeValue("white", "gray.800")

  // Use calculated totals from backend if available, otherwise fall back to local calculation
  const subtotal = calculatedTotals?.subtotal ?? getTotalPrice()
  const shippingCost =
    calculatedTotals?.shipping_cost ?? (getTotalPrice() >= 50 ? 0 : 5.99)
  const taxAmount = calculatedTotals?.tax_amount ?? getTotalPrice() * 0.16
  const total =
    calculatedTotals?.total_amount ?? subtotal + shippingCost + taxAmount

  const getPaymentMethodIcon = () => {
    switch (paymentInfo.paymentMethod) {
      case "stripe":
        return FaCreditCard
      case "paypal":
        return FaPaypal
      case "bank_transfer":
        return FaUniversity
      default:
        return FaCreditCard
    }
  }

  const getPaymentMethodText = () => {
    switch (paymentInfo.paymentMethod) {
      case "stripe":
        return `Tarjeta terminada en ${
          paymentInfo.cardNumber?.slice(-4) || "****"
        }`
      case "paypal":
        return "PayPal"
      case "bank_transfer":
        return "Transferencia Bancaria"
      default:
        return "Método de pago"
    }
  }

  return (
    <VStack spacing={6} align="stretch">
      <Text fontSize="lg" fontWeight="semibold" color="gray.700">
        Confirmar Pedido
      </Text>

      <Alert status="info">
        <AlertIcon />
        <AlertDescription>
          Revisa cuidadosamente la información antes de confirmar tu pedido. Una
          vez confirmado, recibirás un email de confirmación.
        </AlertDescription>
      </Alert>

      <Grid templateColumns={{ base: "1fr", lg: "2fr 1fr" }} gap={6}>
        {/* Order Details */}
        <GridItem>
          <VStack spacing={6} align="stretch">
            {/* Products Summary */}
            <Card bg={cardBg}>
              <CardHeader>
                <HStack justify="space-between">
                  <Heading size="md">
                    Productos ({getTotalItems()} artículos)
                  </Heading>
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => onEditStep(0)}
                  >
                    Editar Carrito
                  </Button>
                </HStack>
              </CardHeader>
              <CardBody pt={0}>
                <VStack spacing={4} align="stretch">
                  {items.map((item) => (
                    <HStack key={item.id} spacing={4} align="start">
                      <Image
                        src={
                          item.image ||
                          "https://via.placeholder.com/80x80?text=Producto"
                        }
                        alt={item.name}
                        boxSize="60px"
                        objectFit="cover"
                        rounded="md"
                      />
                      <Box flex={1}>
                        <Text fontWeight="medium" fontSize="sm" noOfLines={2}>
                          {item.name}
                        </Text>
                        <Text fontSize="sm" color="gray.500">
                          Cantidad: {item.quantity} x ${item.price.toFixed(2)}
                        </Text>
                      </Box>
                      <Text fontWeight="semibold" color="blue.500">
                        ${(item.price * item.quantity).toFixed(2)}
                      </Text>
                    </HStack>
                  ))}
                </VStack>
              </CardBody>
            </Card>

            {/* Contact Information */}
            <Card bg={cardBg}>
              <CardHeader>
                <HStack justify="space-between">
                  <HStack>
                    <Icon as={FaUser} color="blue.500" />
                    <Heading size="md">Información de Contacto</Heading>
                  </HStack>
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => onEditStep(0)}
                  >
                    Editar
                  </Button>
                </HStack>
              </CardHeader>
              <CardBody pt={0}>
                <VStack spacing={2} align="start">
                  <Text>
                    <strong>Nombre:</strong> {contactInfo.customerName}
                  </Text>
                  <Text>
                    <strong>Email:</strong> {contactInfo.email}
                  </Text>
                  <Text>
                    <strong>Teléfono:</strong> {contactInfo.customerPhone}
                  </Text>
                  {contactInfo.createAccount && (
                    <Badge colorScheme="green">Se creará cuenta</Badge>
                  )}
                </VStack>
              </CardBody>
            </Card>

            {/* Shipping Information */}
            <Card bg={cardBg}>
              <CardHeader>
                <HStack justify="space-between">
                  <HStack>
                    <Icon as={FaMapMarkerAlt} color="green.500" />
                    <Heading size="md">Dirección de Envío</Heading>
                  </HStack>
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => onEditStep(1)}
                  >
                    Editar
                  </Button>
                </HStack>
              </CardHeader>
              <CardBody pt={0}>
                <VStack spacing={1} align="start">
                  <Text fontWeight="medium">
                    {shippingInfo.firstName} {shippingInfo.lastName}
                  </Text>
                  {shippingInfo.company && (
                    <Text fontSize="sm" color="gray.600">
                      {shippingInfo.company}
                    </Text>
                  )}
                  <Text>{shippingInfo.addressLine1}</Text>
                  {shippingInfo.addressLine2 && (
                    <Text>{shippingInfo.addressLine2}</Text>
                  )}
                  <Text>
                    {shippingInfo.city}, {shippingInfo.state}{" "}
                    {shippingInfo.postalCode}
                  </Text>
                  <Text>{shippingInfo.country}</Text>
                  {shippingInfo.phone && (
                    <Text fontSize="sm" color="gray.600">
                      Tel: {shippingInfo.phone}
                    </Text>
                  )}
                </VStack>
              </CardBody>
            </Card>

            {/* Payment Method */}
            <Card bg={cardBg}>
              <CardHeader>
                <HStack justify="space-between">
                  <HStack>
                    <Icon as={getPaymentMethodIcon()} color="purple.500" />
                    <Heading size="md">Método de Pago</Heading>
                  </HStack>
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => onEditStep(2)}
                  >
                    Editar
                  </Button>
                </HStack>
              </CardHeader>
              <CardBody pt={0}>
                <Text>{getPaymentMethodText()}</Text>
                {paymentInfo.paymentMethod === "bank_transfer" && (
                  <Text fontSize="sm" color="orange.600" mt={2}>
                    Se enviará información bancaria por email
                  </Text>
                )}
              </CardBody>
            </Card>
          </VStack>
        </GridItem>

        {/* Order Summary */}
        <GridItem>
          <Card bg={cardBg} position="sticky" top={4}>
            <CardHeader>
              <Heading size="md">Resumen del Pedido</Heading>
            </CardHeader>
            <CardBody pt={0}>
              <VStack spacing={4} align="stretch">
                {/* Price Breakdown */}
                <VStack spacing={2} align="stretch" position="relative">
                  {isCalculatingTotals && (
                    <Box
                      position="absolute"
                      top={0}
                      left={0}
                      right={0}
                      bottom={0}
                      bg="rgba(255,255,255,0.8)"
                      display="flex"
                      alignItems="center"
                      justifyContent="center"
                      zIndex={1}
                      rounded="md"
                    >
                      <HStack>
                        <Spinner size="sm" color="blue.500" />
                        <Text fontSize="sm" color="gray.600">
                          Calculando...
                        </Text>
                      </HStack>
                    </Box>
                  )}

                  <HStack justify="space-between">
                    <Text>Subtotal ({getTotalItems()} artículos)</Text>
                    <Skeleton
                      isLoaded={!isCalculatingTotals}
                      height="20px"
                      width="60px"
                    >
                      <Text>${subtotal.toFixed(2)}</Text>
                    </Skeleton>
                  </HStack>

                  <HStack justify="space-between">
                    <HStack>
                      <Icon as={FaTruck} size="sm" color="green.500" />
                      <Text>Envío</Text>
                    </HStack>
                    <Skeleton
                      isLoaded={!isCalculatingTotals}
                      height="20px"
                      width="60px"
                    >
                      <Text
                        color={shippingCost === 0 ? "green.500" : "inherit"}
                      >
                        {shippingCost === 0
                          ? "GRATIS"
                          : `$${shippingCost.toFixed(2)}`}
                      </Text>
                    </Skeleton>
                  </HStack>

                  <HStack justify="space-between">
                    <Text>Impuestos (16%)</Text>
                    <Skeleton
                      isLoaded={!isCalculatingTotals}
                      height="20px"
                      width="60px"
                    >
                      <Text>${taxAmount.toFixed(2)}</Text>
                    </Skeleton>
                  </HStack>

                  <Divider />

                  <HStack
                    justify="space-between"
                    fontSize="lg"
                    fontWeight="bold"
                  >
                    <Text>Total</Text>
                    <Skeleton
                      isLoaded={!isCalculatingTotals}
                      height="24px"
                      width="80px"
                    >
                      <Text color="blue.500">${total.toFixed(2)}</Text>
                    </Skeleton>
                  </HStack>
                </VStack>

                {/* Shipping Info */}
                <Box bg="green.50" p={3} rounded="md">
                  <Text fontSize="sm" color="green.700" textAlign="center">
                    <Icon as={FaTruck} mr={2} />
                    <strong>Entrega estimada:</strong> 2-5 días hábiles
                  </Text>
                </Box>

                {/* Terms and Conditions */}
                <VStack spacing={3}>
                  <Checkbox size="sm" defaultChecked>
                    <Text fontSize="sm">
                      Acepto los{" "}
                      <Link color="blue.500" href="/terms" isExternal>
                        términos y condiciones
                      </Link>
                    </Text>
                  </Checkbox>

                  <Checkbox size="sm" defaultChecked>
                    <Text fontSize="sm">
                      Acepto la{" "}
                      <Link color="blue.500" href="/privacy" isExternal>
                        política de privacidad
                      </Link>
                    </Text>
                  </Checkbox>

                  <Checkbox size="sm">
                    <Text fontSize="sm">
                      Quiero recibir ofertas especiales por email
                    </Text>
                  </Checkbox>
                </VStack>

                {/* Place Order Button */}
                <Button
                  colorScheme="blue"
                  size="lg"
                  onClick={onPlaceOrder}
                  isLoading={isLoading}
                  loadingText="Procesando..."
                  w="full"
                  h={12}
                >
                  Confirmar Pedido
                </Button>

                {/* Security Info */}
                <Box bg="blue.50" p={3} rounded="md" textAlign="center">
                  <Text fontSize="xs" color="blue.700">
                    🔒 Tu información está protegida con SSL
                    <br />
                    Garantía de devolución de 30 días
                  </Text>
                </Box>
              </VStack>
            </CardBody>
          </Card>
        </GridItem>
      </Grid>
    </VStack>
  )
}

export default OrderConfirmationStep
