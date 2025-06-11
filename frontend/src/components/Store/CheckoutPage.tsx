import {
  Box,
  Container,
  VStack,
  Heading,
  Text,
  Card,
  CardBody,
  Button,
  useColorModeValue,
  Flex,
  Badge,
  Stepper,
  Step,
  StepIndicator,
  StepStatus,
  StepIcon,
  StepNumber,
  StepTitle,
  StepDescription,
  StepSeparator,
  useSteps,
} from '@chakra-ui/react'
import { FiArrowLeft, FiShoppingCart, FiCreditCard, FiCheck } from 'react-icons/fi'
import { useNavigate } from '@tanstack/react-router'
import { useState } from 'react'

import { useCartStore } from '../../stores/cartStore'

const CheckoutPage = () => {
  const navigate = useNavigate()
  const cardBg = useColorModeValue('white', 'gray.800')
  const { items, getTotalPrice, getTotalItems } = useCartStore()
  
  const steps = [
    { title: 'Información', description: 'Datos de contacto' },
    { title: 'Envío', description: 'Dirección de entrega' },
    { title: 'Pago', description: 'Método de pago' },
    { title: 'Confirmación', description: 'Revisar pedido' },
  ]

  const { activeStep, setActiveStep } = useSteps({
    index: 0,
    count: steps.length,
  })

  // Redirect if cart is empty
  if (items.length === 0) {
    navigate({ to: '/store/cart' })
    return null
  }

  return (
    <Container maxW="6xl" py={8}>
      <VStack spacing={8} align="stretch">
        {/* Header */}
        <Flex align="center" gap={4}>
          <Button
            leftIcon={<FiArrowLeft />}
            variant="ghost"
            onClick={() => navigate({ to: '/store/cart' })}
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
            <Stepper size="lg" index={activeStep}>
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
        <Flex direction={{ base: 'column', lg: 'row' }} gap={8}>
          {/* Checkout Form */}
          <Box flex={2}>
            <Card bg={cardBg}>
              <CardBody>
                <VStack spacing={8} align="stretch" h="400px" justify="center">
                  <Box textAlign="center">
                    <Text fontSize="lg" color="gray.500" mb={4}>
                      🚧 Proceso de Checkout en Desarrollo
                    </Text>
                    <Text color="gray.400" mb={6}>
                      Aquí estará el formulario completo de checkout con:
                      <br />• Información de contacto y facturación
                      <br />• Dirección de envío con validación
                      <br />• Opciones de envío y fechas de entrega
                      <br />• Integración con pasarelas de pago
                      <br />• Confirmación y resumen del pedido
                    </Text>
                    <Badge colorScheme="orange" size="lg">
                      Próximamente
                    </Badge>
                  </Box>

                  {/* Demo Navigation */}
                  <Flex justify="space-between">
                    <Button
                      variant="outline"
                      onClick={() => setActiveStep(Math.max(0, activeStep - 1))}
                      isDisabled={activeStep === 0}
                    >
                      Anterior
                    </Button>
                    <Button
                      colorScheme="blue"
                      onClick={() => setActiveStep(Math.min(steps.length - 1, activeStep + 1))}
                      isDisabled={activeStep === steps.length - 1}
                    >
                      Siguiente
                    </Button>
                  </Flex>
                </VStack>
              </CardBody>
            </Card>
          </Box>

          {/* Order Summary */}
          <Box flex={1}>
            <Card bg={cardBg}>
              <CardBody>
                <VStack spacing={4} align="stretch">
                  <Heading size="md">Resumen del Pedido</Heading>
                  
                  {/* Items Summary */}
                  <VStack spacing={2} align="stretch">
                    {items.map((item) => (
                      <Flex key={item.id} justify="space-between" align="center">
                        <Box>
                          <Text fontSize="sm" fontWeight="medium" noOfLines={1}>
                            {item.name}
                          </Text>
                          <Text fontSize="xs" color="gray.500">
                            Cantidad: {item.quantity}
                          </Text>
                        </Box>
                        <Text fontSize="sm" fontWeight="semibold">
                          ${(item.price * item.quantity).toFixed(2)}
                        </Text>
                      </Flex>
                    ))}
                  </VStack>

                  <Box border="1px" borderColor="gray.200" rounded="md" p={3}>
                    <VStack spacing={2}>
                      <Flex justify="space-between" w="full">
                        <Text fontSize="sm">Subtotal</Text>
                        <Text fontSize="sm">${getTotalPrice().toFixed(2)}</Text>
                      </Flex>
                      <Flex justify="space-between" w="full">
                        <Text fontSize="sm">Envío</Text>
                        <Text fontSize="sm" color="green.500">
                          {getTotalPrice() >= 50 ? 'GRATIS' : '$5.99'}
                        </Text>
                      </Flex>
                      <Flex justify="space-between" w="full">
                        <Text fontSize="sm">Impuestos (16%)</Text>
                        <Text fontSize="sm">${(getTotalPrice() * 0.16).toFixed(2)}</Text>
                      </Flex>
                      <Box h="1px" bg="gray.200" w="full" />
                      <Flex justify="space-between" w="full">
                        <Text fontWeight="bold">Total</Text>
                        <Text fontWeight="bold" color="blue.500">
                          ${(getTotalPrice() + (getTotalPrice() >= 50 ? 0 : 5.99) + (getTotalPrice() * 0.16)).toFixed(2)}
                        </Text>
                      </Flex>
                    </VStack>
                  </Box>

                  {/* Security Info */}
                  <Box bg="blue.50" p={3} rounded="md" textAlign="center">
                    <Text fontSize="xs" color="blue.700">
                      🔒 Pago 100% seguro con encriptación SSL
                      <br />Aceptamos todas las tarjetas principales
                    </Text>
                  </Box>
                </VStack>
              </CardBody>
            </Card>
          </Box>
        </Flex>
      </VStack>
    </Container>
  )
}

export default CheckoutPage