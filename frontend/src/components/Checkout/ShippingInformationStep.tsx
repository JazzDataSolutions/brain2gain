import {
  Box,
  Checkbox,
  FormControl,
  FormErrorMessage,
  FormLabel,
  Grid,
  GridItem,
  HStack,
  Icon,
  Input,
  Select,
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
import { FiBookmark, FiEdit3 } from "react-icons/fi"
import AddressBook from "./AddressBook"

export interface ShippingInformation {
  firstName: string
  lastName: string
  company?: string
  addressLine1: string
  addressLine2?: string
  city: string
  state: string
  postalCode: string
  country: string
  phone?: string
  isBusinessAddress: boolean
  sameAsBilling: boolean
}

interface ShippingInformationStepProps {
  data: ShippingInformation
  onDataChange: (data: ShippingInformation) => void
  onValidationChange: (isValid: boolean) => void
}

const mexicanStates = [
  "Aguascalientes",
  "Baja California",
  "Baja California Sur",
  "Campeche",
  "Chiapas",
  "Chihuahua",
  "Coahuila",
  "Colima",
  "Ciudad de México",
  "Durango",
  "Estado de México",
  "Guanajuato",
  "Guerrero",
  "Hidalgo",
  "Jalisco",
  "Michoacán",
  "Morelos",
  "Nayarit",
  "Nuevo León",
  "Oaxaca",
  "Puebla",
  "Querétaro",
  "Quintana Roo",
  "San Luis Potosí",
  "Sinaloa",
  "Sonora",
  "Tabasco",
  "Tamaulipas",
  "Tlaxcala",
  "Veracruz",
  "Yucatán",
  "Zacatecas",
]

const ShippingInformationStep = ({
  data,
  onDataChange,
  onValidationChange,
}: ShippingInformationStepProps) => {
  const {
    register,
    watch,
    formState: { errors, isValid },
    reset,
  } = useForm<ShippingInformation>({
    mode: "onChange",
    defaultValues: data,
  })

  const inputBg = useColorModeValue("white", "gray.700")
  const watchedValues = watch()
  const isBusinessAddress = watch("isBusinessAddress")
  const [activeTab, setActiveTab] = useState(0)
  const [selectedAddressId, setSelectedAddressId] = useState<string>("")

  // Update parent component when form data changes
  useEffect(() => {
    onDataChange(watchedValues)
  }, [watchedValues, onDataChange])

  // Update parent component when validation changes
  useEffect(() => {
    onValidationChange(isValid)
  }, [isValid, onValidationChange])

  const handleAddressSelect = (address: ShippingInformation) => {
    // Fill form with selected address
    reset(address)
    setSelectedAddressId(address.firstName + address.lastName) // Mock ID
    setActiveTab(1) // Switch to manual form tab
  }

  return (
    <Box>
      <VStack spacing={6} align="stretch">
        <Text fontSize="lg" fontWeight="semibold" color="gray.700">
          Información de Envío
        </Text>

        <Tabs index={activeTab} onChange={setActiveTab} variant="enclosed">
          <TabList>
            <Tab>
              <HStack>
                <Icon as={FiBookmark} />
                <Text>Direcciones Guardadas</Text>
              </HStack>
            </Tab>
            <Tab>
              <HStack>
                <Icon as={FiEdit3} />
                <Text>Nueva Dirección</Text>
              </HStack>
            </Tab>
          </TabList>

          <TabPanels>
            <TabPanel p={0} pt={6}>
              <AddressBook
                onSelectAddress={handleAddressSelect}
                selectedAddressId={selectedAddressId}
              />
            </TabPanel>

            <TabPanel p={0} pt={6}>
              <VStack spacing={6} align="stretch">
                <Box>
                  <Checkbox
                    {...register("isBusinessAddress")}
                    colorScheme="blue"
                    mb={4}
                  >
                    Esta es una dirección comercial/empresarial
                  </Checkbox>
                </Box>

                <Grid templateColumns={{ base: "1fr", md: "1fr 1fr" }} gap={4}>
                  <GridItem>
                    <FormControl isInvalid={!!errors.firstName}>
                      <FormLabel htmlFor="firstName">Nombre *</FormLabel>
                      <Input
                        id="firstName"
                        placeholder="Juan"
                        bg={inputBg}
                        {...register("firstName", {
                          required: "El nombre es requerido",
                          minLength: {
                            value: 2,
                            message: "Mínimo 2 caracteres",
                          },
                        })}
                      />
                      <FormErrorMessage>
                        {errors.firstName?.message}
                      </FormErrorMessage>
                    </FormControl>
                  </GridItem>

                  <GridItem>
                    <FormControl isInvalid={!!errors.lastName}>
                      <FormLabel htmlFor="lastName">Apellido *</FormLabel>
                      <Input
                        id="lastName"
                        placeholder="Pérez"
                        bg={inputBg}
                        {...register("lastName", {
                          required: "El apellido es requerido",
                          minLength: {
                            value: 2,
                            message: "Mínimo 2 caracteres",
                          },
                        })}
                      />
                      <FormErrorMessage>
                        {errors.lastName?.message}
                      </FormErrorMessage>
                    </FormControl>
                  </GridItem>
                </Grid>

                {isBusinessAddress && (
                  <FormControl>
                    <FormLabel htmlFor="company">Empresa</FormLabel>
                    <Input
                      id="company"
                      placeholder="Nombre de la empresa"
                      bg={inputBg}
                      {...register("company")}
                    />
                  </FormControl>
                )}

                <FormControl isInvalid={!!errors.addressLine1}>
                  <FormLabel htmlFor="addressLine1">Dirección *</FormLabel>
                  <Input
                    id="addressLine1"
                    placeholder="Calle, número exterior"
                    bg={inputBg}
                    {...register("addressLine1", {
                      required: "La dirección es requerida",
                      minLength: {
                        value: 5,
                        message: "Mínimo 5 caracteres",
                      },
                    })}
                  />
                  <FormErrorMessage>
                    {errors.addressLine1?.message}
                  </FormErrorMessage>
                </FormControl>

                <FormControl>
                  <FormLabel htmlFor="addressLine2">
                    Dirección Línea 2 (Opcional)
                  </FormLabel>
                  <Input
                    id="addressLine2"
                    placeholder="Número interior, colonia, referencias"
                    bg={inputBg}
                    {...register("addressLine2")}
                  />
                </FormControl>

                <Grid
                  templateColumns={{ base: "1fr", md: "1fr 1fr 1fr" }}
                  gap={4}
                >
                  <GridItem>
                    <FormControl isInvalid={!!errors.city}>
                      <FormLabel htmlFor="city">Ciudad *</FormLabel>
                      <Input
                        id="city"
                        placeholder="Ciudad de México"
                        bg={inputBg}
                        {...register("city", {
                          required: "La ciudad es requerida",
                          minLength: {
                            value: 2,
                            message: "Mínimo 2 caracteres",
                          },
                        })}
                      />
                      <FormErrorMessage>
                        {errors.city?.message}
                      </FormErrorMessage>
                    </FormControl>
                  </GridItem>

                  <GridItem>
                    <FormControl isInvalid={!!errors.state}>
                      <FormLabel htmlFor="state">Estado *</FormLabel>
                      <Select
                        id="state"
                        placeholder="Selecciona estado"
                        bg={inputBg}
                        {...register("state", {
                          required: "El estado es requerido",
                        })}
                      >
                        {mexicanStates.map((state) => (
                          <option key={state} value={state}>
                            {state}
                          </option>
                        ))}
                      </Select>
                      <FormErrorMessage>
                        {errors.state?.message}
                      </FormErrorMessage>
                    </FormControl>
                  </GridItem>

                  <GridItem>
                    <FormControl isInvalid={!!errors.postalCode}>
                      <FormLabel htmlFor="postalCode">
                        Código Postal *
                      </FormLabel>
                      <Input
                        id="postalCode"
                        placeholder="12345"
                        maxLength={5}
                        bg={inputBg}
                        {...register("postalCode", {
                          required: "El código postal es requerido",
                          pattern: {
                            value: /^\d{5}$/,
                            message:
                              "Debe ser un código postal mexicano válido (5 dígitos)",
                          },
                        })}
                      />
                      <FormErrorMessage>
                        {errors.postalCode?.message}
                      </FormErrorMessage>
                    </FormControl>
                  </GridItem>
                </Grid>

                <FormControl>
                  <FormLabel htmlFor="country">País</FormLabel>
                  <Select
                    id="country"
                    bg={inputBg}
                    {...register("country")}
                    defaultValue="MX"
                    isDisabled
                  >
                    <option value="MX">México</option>
                  </Select>
                </FormControl>

                <FormControl>
                  <FormLabel htmlFor="phone">Teléfono (Opcional)</FormLabel>
                  <Input
                    id="phone"
                    type="tel"
                    placeholder="+52 55 1234 5678"
                    bg={inputBg}
                    {...register("phone", {
                      pattern: {
                        value: /^[\+]?[1-9][\d]{0,15}$/,
                        message: "Ingresa un número de teléfono válido",
                      },
                    })}
                  />
                  <FormErrorMessage>{errors.phone?.message}</FormErrorMessage>
                </FormControl>

                <Box>
                  <Checkbox {...register("sameAsBilling")} colorScheme="blue">
                    Usar esta dirección para facturación
                  </Checkbox>
                </Box>

                <Box bg="green.50" p={4} rounded="md">
                  <Text fontSize="sm" color="green.700">
                    🚚 <strong>Envío gratuito</strong> en pedidos mayores a
                    $50.00 USD
                    <br />📦 Tiempo de entrega estimado: 2-5 días hábiles
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

export default ShippingInformationStep
