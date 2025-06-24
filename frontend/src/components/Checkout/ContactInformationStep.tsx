import {
  Box,
  VStack,
  FormControl,
  FormLabel,
  Input,
  FormErrorMessage,
  Checkbox,
  Text,
  useColorModeValue,
} from '@chakra-ui/react'
import { useForm } from 'react-hook-form'
import { useEffect } from 'react'

export interface ContactInformation {
  email: string
  customerName: string
  customerPhone: string
  createAccount: boolean
  password?: string
}

interface ContactInformationStepProps {
  data: ContactInformation
  onDataChange: (data: ContactInformation) => void
  onValidationChange: (isValid: boolean) => void
}

const ContactInformationStep = ({ 
  data, 
  onDataChange, 
  onValidationChange 
}: ContactInformationStepProps) => {
  const {
    register,
    watch,
    formState: { errors, isValid },
    trigger,
  } = useForm<ContactInformation>({
    mode: 'onChange',
    defaultValues: data,
  })

  const inputBg = useColorModeValue('white', 'gray.700')
  const watchedValues = watch()
  const createAccount = watch('createAccount')

  // Update parent component when form data changes
  useEffect(() => {
    onDataChange(watchedValues)
  }, [watchedValues, onDataChange])

  // Update parent component when validation changes
  useEffect(() => {
    onValidationChange(isValid)
  }, [isValid, onValidationChange])

  return (
    <Box>
      <VStack spacing={6} align="stretch">
        <Text fontSize="lg" fontWeight="semibold" color="gray.700">
          Información de Contacto
        </Text>

        <FormControl isInvalid={!!errors.email}>
          <FormLabel htmlFor="email">Correo Electrónico *</FormLabel>
          <Input
            id="email"
            type="email"
            placeholder="tu@ejemplo.com"
            bg={inputBg}
            {...register('email', {
              required: 'El correo electrónico es requerido',
              pattern: {
                value: /^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}$/i,
                message: 'Ingresa un correo electrónico válido',
              },
            })}
          />
          <FormErrorMessage>{errors.email?.message}</FormErrorMessage>
        </FormControl>

        <FormControl isInvalid={!!errors.customerName}>
          <FormLabel htmlFor="customerName">Nombre Completo *</FormLabel>
          <Input
            id="customerName"
            placeholder="Juan Pérez"
            bg={inputBg}
            {...register('customerName', {
              required: 'El nombre es requerido',
              minLength: {
                value: 2,
                message: 'El nombre debe tener al menos 2 caracteres',
              },
            })}
          />
          <FormErrorMessage>{errors.customerName?.message}</FormErrorMessage>
        </FormControl>

        <FormControl isInvalid={!!errors.customerPhone}>
          <FormLabel htmlFor="customerPhone">Teléfono *</FormLabel>
          <Input
            id="customerPhone"
            type="tel"
            placeholder="+52 55 1234 5678"
            bg={inputBg}
            {...register('customerPhone', {
              required: 'El teléfono es requerido',
              pattern: {
                value: /^[\+]?[1-9][\d]{0,15}$/,
                message: 'Ingresa un número de teléfono válido',
              },
            })}
          />
          <FormErrorMessage>{errors.customerPhone?.message}</FormErrorMessage>
        </FormControl>

        <Box>
          <Checkbox 
            {...register('createAccount')}
            colorScheme="blue"
          >
            Crear cuenta para futuras compras
          </Checkbox>
        </Box>

        {createAccount && (
          <FormControl isInvalid={!!errors.password}>
            <FormLabel htmlFor="password">Contraseña *</FormLabel>
            <Input
              id="password"
              type="password"
              placeholder="Mínimo 8 caracteres"
              bg={inputBg}
              {...register('password', {
                required: createAccount ? 'La contraseña es requerida' : false,
                minLength: {
                  value: 8,
                  message: 'La contraseña debe tener al menos 8 caracteres',
                },
              })}
            />
            <FormErrorMessage>{errors.password?.message}</FormErrorMessage>
          </FormControl>
        )}

        <Box bg="blue.50" p={4} rounded="md">
          <Text fontSize="sm" color="blue.700">
            💡 <strong>Tip:</strong> Usaremos esta información para enviar actualizaciones 
            sobre tu pedido y contactarte en caso de cualquier problema con la entrega.
          </Text>
        </Box>
      </VStack>
    </Box>
  )
}

export default ContactInformationStep