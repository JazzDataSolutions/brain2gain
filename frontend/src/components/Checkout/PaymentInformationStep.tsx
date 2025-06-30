import {
  Alert,
  AlertDescription,
  AlertIcon,
  Badge,
  Box,
  Divider,
  FormControl,
  FormErrorMessage,
  FormLabel,
  Grid,
  GridItem,
  HStack,
  Icon,
  Input,
  Radio,
  RadioGroup,
  Tab,
  TabList,
  TabPanel,
  TabPanels,
  Tabs,
  Text,
  VStack,
  useColorModeValue,
} from "@chakra-ui/react"
import { useEffect, useState } from "react"
import { useForm } from "react-hook-form"
import { FaCreditCard, FaPaypal, FaUniversity } from "react-icons/fa"
import { FiBookmark, FiCreditCard } from "react-icons/fi"
import SavedPaymentMethods from "./SavedPaymentMethods"

export interface PaymentInformation {
  paymentMethod: "stripe" | "paypal" | "bank_transfer"
  cardNumber?: string
  expiryDate?: string
  cvv?: string
  cardholderName?: string
  billingAddress?: {
    addressLine1: string
    city: string
    state: string
    postalCode: string
    country: string
  }
}

interface PaymentInformationStepProps {
  data: PaymentInformation
  onDataChange: (data: PaymentInformation) => void
  onValidationChange: (isValid: boolean) => void
  sameAsBilling?: boolean
  shippingAddress?: any
}

const PaymentInformationStep = ({
  data,
  onDataChange,
  onValidationChange,
  sameAsBilling = true,
  shippingAddress,
}: PaymentInformationStepProps) => {
  const {
    register,
    watch,
    formState: { errors },
    setValue,
  } = useForm<PaymentInformation>({
    mode: "onChange",
    defaultValues: data,
  })

  const inputBg = useColorModeValue("white", "gray.700")
  const cardBg = useColorModeValue("gray.50", "gray.700")
  const watchedValues = watch()
  const paymentMethod = watch("paymentMethod")
  const [activeTab, setActiveTab] = useState(0)

  // Format card number input
  const formatCardNumber = (value: string) => {
    const v = value.replace(/\s+/g, "").replace(/[^0-9]/gi, "")
    const matches = v.match(/\d{4,16}/g)
    const match = matches?.[0] || ""
    const parts = []
    for (let i = 0, len = match.length; i < len; i += 4) {
      parts.push(match.substring(i, i + 4))
    }
    if (parts.length) {
      return parts.join(" ")
    }
    return v
  }

  // Format expiry date
  const formatExpiryDate = (value: string) => {
    const v = value.replace(/\D/g, "")
    if (v.length >= 2) {
      return v.substring(0, 2) + (v.length > 2 ? `/${v.substring(2, 4)}` : "")
    }
    return v
  }

  // Update parent component when form data changes
  useEffect(() => {
    onDataChange(watchedValues)
  }, [watchedValues, onDataChange])

  // Update parent component when validation changes
  useEffect(() => {
    const isCardValid =
      paymentMethod !== "stripe" ||
      (watchedValues.cardNumber &&
        watchedValues.expiryDate &&
        watchedValues.cvv &&
        watchedValues.cardholderName)
    onValidationChange(!!isCardValid)
  }, [watchedValues, paymentMethod, onValidationChange])

  // Set billing address same as shipping if enabled
  useEffect(() => {
    if (sameAsBilling && shippingAddress) {
      setValue("billingAddress", {
        addressLine1: shippingAddress.addressLine1,
        city: shippingAddress.city,
        state: shippingAddress.state,
        postalCode: shippingAddress.postalCode,
        country: shippingAddress.country || "MX",
      })
    }
  }, [sameAsBilling, shippingAddress, setValue])

  const handleSavedPaymentSelect = (method: any) => {
    if (method.type === "card") {
      setValue("paymentMethod", "stripe")
      setValue("cardNumber", `•••• •••• •••• ${method.last4}`)
      setValue("cardholderName", method.name)
    } else if (method.type === "paypal") {
      setValue("paymentMethod", "paypal")
    }
    setActiveTab(1) // Switch to payment form tab
  }

  return (
    <Box>
      <VStack spacing={6} align="stretch">
        <Text fontSize="lg" fontWeight="semibold" color="gray.700">
          Método de Pago
        </Text>

        <Tabs index={activeTab} onChange={setActiveTab} variant="enclosed">
          <TabList>
            <Tab>
              <HStack>
                <Icon as={FiBookmark} />
                <Text>Métodos Guardados</Text>
              </HStack>
            </Tab>
            <Tab>
              <HStack>
                <Icon as={FiCreditCard} />
                <Text>Nuevo Método</Text>
              </HStack>
            </Tab>
          </TabList>

          <TabPanels>
            <TabPanel p={0} pt={6}>
              <SavedPaymentMethods
                onSelectPaymentMethod={handleSavedPaymentSelect}
              />
            </TabPanel>

            <TabPanel p={0} pt={6}>
              <VStack spacing={6} align="stretch">
                <FormControl>
                  <RadioGroup
                    value={paymentMethod}
                    onChange={(value) =>
                      setValue(
                        "paymentMethod",
                        value as "stripe" | "paypal" | "bank_transfer",
                      )
                    }
                    defaultValue={data.paymentMethod || "stripe"}
                  >
                    <VStack spacing={3} align="stretch">
                      {/* Credit Card Option */}
                      <Box
                        p={4}
                        bg={paymentMethod === "stripe" ? "blue.50" : cardBg}
                        rounded="md"
                        border="2px"
                        borderColor={
                          paymentMethod === "stripe" ? "blue.200" : "gray.200"
                        }
                        cursor="pointer"
                      >
                        <HStack justify="space-between">
                          <HStack>
                            <Radio value="stripe" colorScheme="blue" />
                            <Icon as={FaCreditCard} color="blue.500" />
                            <Text fontWeight="medium">
                              Tarjeta de Crédito/Débito
                            </Text>
                          </HStack>
                          <HStack spacing={2}>
                            <Badge colorScheme="green">Más Popular</Badge>
                            <Text fontSize="xs" color="gray.500">
                              Visa, MC, Amex
                            </Text>
                          </HStack>
                        </HStack>
                      </Box>

                      {/* PayPal Option */}
                      <Box
                        p={4}
                        bg={paymentMethod === "paypal" ? "blue.50" : cardBg}
                        rounded="md"
                        border="2px"
                        borderColor={
                          paymentMethod === "paypal" ? "blue.200" : "gray.200"
                        }
                        cursor="pointer"
                      >
                        <HStack justify="space-between">
                          <HStack>
                            <Radio value="paypal" colorScheme="blue" />
                            <Icon as={FaPaypal} color="blue.600" />
                            <Text fontWeight="medium">PayPal</Text>
                          </HStack>
                          <Badge colorScheme="blue">Seguro</Badge>
                        </HStack>
                      </Box>

                      {/* Bank Transfer Option */}
                      <Box
                        p={4}
                        bg={
                          paymentMethod === "bank_transfer" ? "blue.50" : cardBg
                        }
                        rounded="md"
                        border="2px"
                        borderColor={
                          paymentMethod === "bank_transfer"
                            ? "blue.200"
                            : "gray.200"
                        }
                        cursor="pointer"
                      >
                        <HStack justify="space-between">
                          <HStack>
                            <Radio value="bank_transfer" colorScheme="blue" />
                            <Icon as={FaUniversity} color="green.500" />
                            <Text fontWeight="medium">
                              Transferencia Bancaria
                            </Text>
                          </HStack>
                          <Badge colorScheme="orange">2-3 días</Badge>
                        </HStack>
                      </Box>
                    </VStack>
                  </RadioGroup>
                </FormControl>

                {/* Credit Card Form */}
                {paymentMethod === "stripe" && (
                  <Box
                    p={6}
                    bg={cardBg}
                    rounded="lg"
                    border="1px"
                    borderColor="gray.200"
                  >
                    <VStack spacing={4} align="stretch">
                      <Text fontWeight="semibold" mb={2}>
                        Información de la Tarjeta
                      </Text>

                      <FormControl isInvalid={!!errors.cardholderName}>
                        <FormLabel htmlFor="cardholderName">
                          Nombre del Tarjetahabiente *
                        </FormLabel>
                        <Input
                          id="cardholderName"
                          placeholder="Nombre como aparece en la tarjeta"
                          bg={inputBg}
                          {...register("cardholderName", {
                            required:
                              paymentMethod === "stripe"
                                ? "El nombre es requerido"
                                : false,
                          })}
                        />
                        <FormErrorMessage>
                          {errors.cardholderName?.message}
                        </FormErrorMessage>
                      </FormControl>

                      <FormControl isInvalid={!!errors.cardNumber}>
                        <FormLabel htmlFor="cardNumber">
                          Número de Tarjeta *
                        </FormLabel>
                        <Input
                          id="cardNumber"
                          placeholder="1234 5678 9012 3456"
                          maxLength={19}
                          bg={inputBg}
                          {...register("cardNumber", {
                            required:
                              paymentMethod === "stripe"
                                ? "El número de tarjeta es requerido"
                                : false,
                            pattern: {
                              value: /^[\d\s]{16,19}$/,
                              message: "Ingresa un número de tarjeta válido",
                            },
                            onChange: (e) => {
                              e.target.value = formatCardNumber(e.target.value)
                            },
                          })}
                        />
                        <FormErrorMessage>
                          {errors.cardNumber?.message}
                        </FormErrorMessage>
                      </FormControl>

                      <Grid templateColumns="2fr 1fr" gap={4}>
                        <GridItem>
                          <FormControl isInvalid={!!errors.expiryDate}>
                            <FormLabel htmlFor="expiryDate">
                              Fecha de Vencimiento *
                            </FormLabel>
                            <Input
                              id="expiryDate"
                              placeholder="MM/AA"
                              maxLength={5}
                              bg={inputBg}
                              {...register("expiryDate", {
                                required:
                                  paymentMethod === "stripe"
                                    ? "La fecha de vencimiento es requerida"
                                    : false,
                                pattern: {
                                  value: /^(0[1-9]|1[0-2])\/\d{2}$/,
                                  message: "Formato: MM/AA",
                                },
                                onChange: (e) => {
                                  e.target.value = formatExpiryDate(
                                    e.target.value,
                                  )
                                },
                              })}
                            />
                            <FormErrorMessage>
                              {errors.expiryDate?.message}
                            </FormErrorMessage>
                          </FormControl>
                        </GridItem>

                        <GridItem>
                          <FormControl isInvalid={!!errors.cvv}>
                            <FormLabel htmlFor="cvv">CVV *</FormLabel>
                            <Input
                              id="cvv"
                              placeholder="123"
                              maxLength={4}
                              type="password"
                              bg={inputBg}
                              {...register("cvv", {
                                required:
                                  paymentMethod === "stripe"
                                    ? "El CVV es requerido"
                                    : false,
                                pattern: {
                                  value: /^\d{3,4}$/,
                                  message: "3-4 dígitos",
                                },
                              })}
                            />
                            <FormErrorMessage>
                              {errors.cvv?.message}
                            </FormErrorMessage>
                          </FormControl>
                        </GridItem>
                      </Grid>

                      <Alert status="info" size="sm">
                        <AlertIcon />
                        <AlertDescription fontSize="sm">
                          Tu información de pago está protegida con encriptación
                          SSL de 256 bits.
                        </AlertDescription>
                      </Alert>
                    </VStack>
                  </Box>
                )}

                {/* PayPal Info */}
                {paymentMethod === "paypal" && (
                  <Box
                    p={6}
                    bg="blue.50"
                    rounded="lg"
                    border="1px"
                    borderColor="blue.200"
                  >
                    <VStack spacing={3} align="center">
                      <Icon as={FaPaypal} size="2xl" color="blue.600" />
                      <Text fontWeight="semibold">Pago con PayPal</Text>
                      <Text fontSize="sm" textAlign="center" color="gray.600">
                        Serás redirigido a PayPal para completar tu pago de
                        forma segura. PayPal protege tu información financiera.
                      </Text>
                    </VStack>
                  </Box>
                )}

                {/* Bank Transfer Info */}
                {paymentMethod === "bank_transfer" && (
                  <Box
                    p={6}
                    bg="orange.50"
                    rounded="lg"
                    border="1px"
                    borderColor="orange.200"
                  >
                    <VStack spacing={3} align="start">
                      <HStack>
                        <Icon as={FaUniversity} color="orange.500" />
                        <Text fontWeight="semibold">
                          Transferencia Bancaria
                        </Text>
                      </HStack>
                      <Text fontSize="sm" color="gray.600">
                        Recibirás un email con los datos bancarios para realizar
                        la transferencia. Tu pedido será procesado una vez que
                        confirmemos el pago (2-3 días hábiles).
                      </Text>
                      <Alert status="warning" size="sm">
                        <AlertIcon />
                        <AlertDescription fontSize="sm">
                          Los productos se reservarán por 5 días. Pasado este
                          tiempo, el pedido será cancelado.
                        </AlertDescription>
                      </Alert>
                    </VStack>
                  </Box>
                )}

                <Divider />

                {/* Security Info */}
                <Box bg="green.50" p={4} rounded="md">
                  <Text fontSize="sm" color="green.700" textAlign="center">
                    🔒 <strong>Pago 100% Seguro</strong>
                    <br />
                    Utilizamos encriptación de grado bancario para proteger tu
                    información.
                    <br />
                    Nunca almacenamos datos de tarjetas de crédito en nuestros
                    servidores.
                  </Text>
                </Box>
              </VStack>
            </TabPanel>
          </TabPanels>
        </Tabs>
      </VStack>
    </Box>
  )
}

export default PaymentInformationStep
