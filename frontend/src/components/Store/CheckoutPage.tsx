import {
  Alert,
  AlertDescription,
  AlertIcon,
  Box,
  Button,
  Card,
  CardBody,
  Container,
  Flex,
  Heading,
  Step,
  StepDescription,
  StepIcon,
  StepIndicator,
  StepNumber,
  StepSeparator,
  StepStatus,
  StepTitle,
  Stepper,
  Text,
  VStack,
  useColorModeValue,
  useSteps,
  useToast,
} from "@chakra-ui/react"
import { useNavigate } from "@tanstack/react-router"
import { useCallback, useEffect, useState } from "react"
import { FiArrowLeft, FiCheck } from "react-icons/fi"

import orderService, {
  type CheckoutData,
  type OrderAddress,
} from "../../services/orderService"
import { useCartStore } from "../../stores/cartStore"
import ContactInformationStep, {
  type ContactInformation,
} from "../Checkout/ContactInformationStep"
import OrderConfirmationStep from "../Checkout/OrderConfirmationStep"
import PaymentInformationStep, {
  type PaymentInformation,
} from "../Checkout/PaymentInformationStep"
import ShippingInformationStep, {
  type ShippingInformation,
} from "../Checkout/ShippingInformationStep"

const CheckoutPage = () => {
  const navigate = useNavigate()
  const toast = useToast()
  const cardBg = useColorModeValue("white", "gray.800")
  const { items, getTotalPrice, getTotalItems, clearCart } = useCartStore()

  const steps = [
    { title: "Contacto", description: "Información personal" },
    { title: "Envío", description: "Dirección de entrega" },
    { title: "Pago", description: "Método de pago" },
    { title: "Confirmar", description: "Revisar pedido" },
  ]

  const { activeStep, setActiveStep } = useSteps({
    index: 0,
    count: steps.length,
  })

  // Form data states
  const [contactInfo, setContactInfo] = useState<ContactInformation>({
    email: "",
    customerName: "",
    customerPhone: "",
    createAccount: false,
  })

  const [shippingInfo, setShippingInfo] = useState<ShippingInformation>({
    firstName: "",
    lastName: "",
    addressLine1: "",
    city: "",
    state: "",
    postalCode: "",
    country: "MX",
    isBusinessAddress: false,
    sameAsBilling: true,
  })

  const [paymentInfo, setPaymentInfo] = useState<PaymentInformation>({
    paymentMethod: "stripe",
  })

  // Validation states
  const [stepValidations, setStepValidations] = useState({
    0: false, // Contact
    1: false, // Shipping
    2: false, // Payment
    3: true, // Confirmation
  })

  const [isPlacingOrder, setIsPlacingOrder] = useState(false)
  const [calculatedTotals, setCalculatedTotals] = useState<{
    subtotal: number
    tax_amount: number
    shipping_cost: number
    total_amount: number
  } | null>(null)
  const [isCalculatingTotals, setIsCalculatingTotals] = useState(false)

  // Redirect if cart is empty
  if (items.length === 0) {
    return (
      <Container maxW="4xl" py={8}>
        <VStack spacing={6} align="center" textAlign="center">
          <Heading size="lg" color="gray.600">
            Tu carrito está vacío
          </Heading>
          <Text color="gray.500">
            Agrega algunos productos a tu carrito antes de proceder al checkout.
          </Text>
          <Button
            colorScheme="blue"
            onClick={() => navigate({ to: "/store/products" })}
          >
            Explorar Productos
          </Button>
        </VStack>
      </Container>
    )
  }

  const handleStepValidation = useCallback((step: number, isValid: boolean) => {
    setStepValidations((prev) => ({
      ...prev,
      [step]: isValid,
    }))
  }, [])

  const handleNext = () => {
    if (activeStep < steps.length - 1) {
      setActiveStep(activeStep + 1)
    }
  }

  const handleBack = () => {
    if (activeStep > 0) {
      setActiveStep(activeStep - 1)
    }
  }

  const handleEditStep = (step: number) => {
    setActiveStep(step)
  }

  const isCurrentStepValid =
    stepValidations[activeStep as keyof typeof stepValidations]

  // Calculate totals when payment method or shipping info changes
  useEffect(() => {
    const calculateTotals = async () => {
      if (!stepValidations[1] || !stepValidations[2]) return // Need shipping and payment info

      setIsCalculatingTotals(true)
      try {
        const shippingAddress: OrderAddress = {
          first_name: shippingInfo.firstName,
          last_name: shippingInfo.lastName,
          company: shippingInfo.company,
          address_line_1: shippingInfo.addressLine1,
          address_line_2: shippingInfo.addressLine2,
          city: shippingInfo.city,
          state: shippingInfo.state,
          postal_code: shippingInfo.postalCode,
          country: shippingInfo.country,
          phone: shippingInfo.phone,
        }

        const checkoutData: CheckoutData = {
          payment_method: paymentInfo.paymentMethod,
          shipping_address: shippingAddress,
          billing_address: shippingAddress, // Use shipping as billing for calculation
        }

        const totals = await orderService.calculateOrderTotals(checkoutData)
        setCalculatedTotals(totals)
      } catch (error) {
        console.error("Error calculating totals:", error)
        // Fall back to local calculation
        setCalculatedTotals({
          subtotal: getTotalPrice(),
          shipping_cost: getTotalPrice() >= 50 ? 0 : 5.99,
          tax_amount: getTotalPrice() * 0.16,
          total_amount:
            getTotalPrice() +
            (getTotalPrice() >= 50 ? 0 : 5.99) +
            getTotalPrice() * 0.16,
        })
      } finally {
        setIsCalculatingTotals(false)
      }
    }

    calculateTotals()
  }, [paymentInfo.paymentMethod, shippingInfo, stepValidations, getTotalPrice])

  const handlePlaceOrder = async () => {
    setIsPlacingOrder(true)

    try {
      // Convert frontend data to backend format
      const shippingAddress: OrderAddress = {
        first_name: shippingInfo.firstName,
        last_name: shippingInfo.lastName,
        company: shippingInfo.company,
        address_line_1: shippingInfo.addressLine1,
        address_line_2: shippingInfo.addressLine2,
        city: shippingInfo.city,
        state: shippingInfo.state,
        postal_code: shippingInfo.postalCode,
        country: shippingInfo.country,
        phone: shippingInfo.phone,
      }

      const billingAddress: OrderAddress = shippingInfo.sameAsBilling
        ? shippingAddress
        : {
            first_name: contactInfo.customerName.split(" ")[0],
            last_name: contactInfo.customerName.split(" ").slice(1).join(" "),
            address_line_1: shippingInfo.addressLine1, // Use shipping for now
            city: shippingInfo.city,
            state: shippingInfo.state,
            postal_code: shippingInfo.postalCode,
            country: shippingInfo.country,
            phone: contactInfo.customerPhone,
          }

      const checkoutData: CheckoutData = {
        payment_method: paymentInfo.paymentMethod,
        shipping_address: shippingAddress,
        billing_address: billingAddress,
      }

      // Create order via API
      const result = await orderService.confirmCheckout(checkoutData)

      // Handle payment method specific logic
      if (paymentInfo.paymentMethod === "paypal" && result.payment_url) {
        // Redirect to PayPal
        window.location.href = result.payment_url
        return
      }

      if (paymentInfo.paymentMethod === "stripe" && result.client_secret) {
        // Handle Stripe payment (would need Stripe SDK integration)
        console.log("Stripe client secret:", result.client_secret)
        // For now, just proceed as if payment succeeded
      }

      // Clear cart after successful order creation
      clearCart()

      // Show success message
      toast({
        title: "¡Pedido Confirmado!",
        description: `Pedido #${result.order.order_id.slice(
          -8,
        )} creado exitosamente. Recibirás un email de confirmación.`,
        status: "success",
        duration: 7000,
        isClosable: true,
      })

      // Navigate to order success page
      navigate({
        to: "/store/order-success",
        search: { orderId: result.order.order_id },
      })
    } catch (error) {
      console.error("Error placing order:", error)
      const errorMessage =
        error instanceof Error ? error.message : "Error desconocido"

      toast({
        title: "Error al procesar el pedido",
        description: `${errorMessage}. Por favor inténtalo de nuevo o contacta soporte.`,
        status: "error",
        duration: 8000,
        isClosable: true,
      })
    } finally {
      setIsPlacingOrder(false)
    }
  }

  const renderStepContent = () => {
    switch (activeStep) {
      case 0:
        return (
          <ContactInformationStep
            data={contactInfo}
            onDataChange={setContactInfo}
            onValidationChange={(isValid) => handleStepValidation(0, isValid)}
          />
        )
      case 1:
        return (
          <ShippingInformationStep
            data={shippingInfo}
            onDataChange={setShippingInfo}
            onValidationChange={(isValid) => handleStepValidation(1, isValid)}
          />
        )
      case 2:
        return (
          <PaymentInformationStep
            data={paymentInfo}
            onDataChange={setPaymentInfo}
            onValidationChange={(isValid) => handleStepValidation(2, isValid)}
            sameAsBilling={shippingInfo.sameAsBilling}
            shippingAddress={shippingInfo}
          />
        )
      case 3:
        return (
          <OrderConfirmationStep
            contactInfo={contactInfo}
            shippingInfo={shippingInfo}
            paymentInfo={paymentInfo}
            onPlaceOrder={handlePlaceOrder}
            isLoading={isPlacingOrder}
            onEditStep={handleEditStep}
            calculatedTotals={calculatedTotals}
            isCalculatingTotals={isCalculatingTotals}
          />
        )
      default:
        return null
    }
  }

  return (
    <Container maxW="7xl" py={8}>
      <VStack spacing={8} align="stretch">
        {/* Header */}
        <Flex align="center" gap={4}>
          <Button
            leftIcon={<FiArrowLeft />}
            variant="ghost"
            onClick={() => navigate({ to: "/store/cart" })}
          >
            Volver al Carrito
          </Button>
          <Box>
            <Heading size="xl" mb={2}>
              Finalizar Compra
            </Heading>
            <Text color="gray.600">
              {getTotalItems()} artículos • Total: ${getTotalPrice().toFixed(2)}
            </Text>
          </Box>
        </Flex>

        {/* Progress Stepper */}
        <Card bg={cardBg}>
          <CardBody>
            <Stepper size="lg" index={activeStep} colorScheme="blue">
              {steps.map((step, index) => (
                <Step key={index}>
                  <StepIndicator>
                    <StepStatus
                      complete={<StepIcon />}
                      incomplete={<StepNumber />}
                      active={<StepNumber />}
                    />
                  </StepIndicator>

                  <Box flexShrink="0">
                    <StepTitle>{step.title}</StepTitle>
                    <StepDescription>{step.description}</StepDescription>
                  </Box>

                  <StepSeparator />
                </Step>
              ))}
            </Stepper>
          </CardBody>
        </Card>

        {/* Main Content */}
        <Card bg={cardBg}>
          <CardBody>{renderStepContent()}</CardBody>
        </Card>

        {/* Navigation Buttons */}
        {activeStep < 3 && (
          <Flex justify="space-between" align="center">
            <Button
              variant="outline"
              onClick={handleBack}
              isDisabled={activeStep === 0}
            >
              Anterior
            </Button>

            <Box flex={1} mx={4}>
              {!isCurrentStepValid && (
                <Alert status="warning" size="sm">
                  <AlertIcon />
                  <AlertDescription fontSize="sm">
                    Por favor completa todos los campos requeridos para
                    continuar.
                  </AlertDescription>
                </Alert>
              )}
            </Box>

            <Button
              colorScheme="blue"
              onClick={handleNext}
              isDisabled={!isCurrentStepValid}
              rightIcon={
                activeStep === steps.length - 2 ? <FiCheck /> : undefined
              }
            >
              {activeStep === steps.length - 2 ? "Revisar Pedido" : "Siguiente"}
            </Button>
          </Flex>
        )}

        {/* Security Footer */}
        <Box textAlign="center" py={4}>
          <Text fontSize="sm" color="gray.500">
            🔒 Sitio seguro protegido con SSL • 📞 Soporte:
            contacto@brain2gain.com
          </Text>
        </Box>
      </VStack>
    </Container>
  )
}

export default CheckoutPage
