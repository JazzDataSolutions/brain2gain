import {
  Box,
  VStack,
  HStack,
  Text,
  Card,
  CardBody,
  Button,
  useColorModeValue,
  Badge,
  Icon,
  Modal,
  ModalOverlay,
  ModalContent,
  ModalHeader,
  ModalCloseButton,
  ModalBody,
  ModalFooter,
  useDisclosure,
  RadioGroup,
  Radio,
  Image,
} from '@chakra-ui/react'
import { FiPlus, FiEdit2, FiTrash2, FiShield } from 'react-icons/fi'
import { FaCreditCard, FaPaypal } from 'react-icons/fa'
import { useState, useEffect } from 'react'

interface SavedPaymentMethod {
  id: string
  type: 'card' | 'paypal'
  name: string
  isDefault: boolean
  // Card specific
  last4?: string
  brand?: string
  expiryMonth?: string
  expiryYear?: string
  // PayPal specific
  email?: string
}

interface SavedPaymentMethodsProps {
  onSelectPaymentMethod: (method: SavedPaymentMethod) => void
  selectedMethodId?: string
}

const SavedPaymentMethods = ({ onSelectPaymentMethod, selectedMethodId }: SavedPaymentMethodsProps) => {
  const cardBg = useColorModeValue('white', 'gray.800')
  const { isOpen, onOpen, onClose } = useDisclosure()
  const [savedMethods, setSavedMethods] = useState<SavedPaymentMethod[]>([])
  const [selectedId, setSelectedId] = useState<string>(selectedMethodId || '')

  // Mock data - in real app, this would come from user profile API
  useEffect(() => {
    const mockMethods: SavedPaymentMethod[] = [
      {
        id: '1',
        type: 'card',
        name: 'Visa Principal',
        isDefault: true,
        last4: '4242',
        brand: 'visa',
        expiryMonth: '12',
        expiryYear: '25',
      },
      {
        id: '2',
        type: 'card',
        name: 'Mastercard Trabajo',
        isDefault: false,
        last4: '8888',
        brand: 'mastercard',
        expiryMonth: '06',
        expiryYear: '26',
      },
      {
        id: '3',
        type: 'paypal',
        name: 'PayPal Personal',
        isDefault: false,
        email: 'usuario@example.com',
      },
    ]
    setSavedMethods(mockMethods)
    
    // Set default selection
    const defaultMethod = mockMethods.find(method => method.isDefault)
    if (defaultMethod && !selectedMethodId) {
      setSelectedId(defaultMethod.id)
      onSelectPaymentMethod(defaultMethod)
    }
  }, [selectedMethodId, onSelectPaymentMethod])

  const handleMethodSelect = (methodId: string) => {
    setSelectedId(methodId)
    const method = savedMethods.find(m => m.id === methodId)
    if (method) {
      onSelectPaymentMethod(method)
    }
  }

  const getCardBrandIcon = (brand?: string) => {
    switch (brand?.toLowerCase()) {
      case 'visa':
        return '/images/visa-logo.png'
      case 'mastercard':
        return '/images/mastercard-logo.png'
      case 'amex':
        return '/images/amex-logo.png'
      default:
        return null
    }
  }

  const getCardBrandName = (brand?: string) => {
    switch (brand?.toLowerCase()) {
      case 'visa':
        return 'Visa'
      case 'mastercard':
        return 'Mastercard'
      case 'amex':
        return 'American Express'
      default:
        return 'Tarjeta'
    }
  }

  const removePaymentMethod = (methodId: string) => {
    setSavedMethods(prev => prev.filter(method => method.id !== methodId))
    if (selectedId === methodId) {
      setSelectedId('')
    }
  }

  return (
    <Box>
      <VStack spacing={4} align="stretch">
        <HStack justify="space-between">
          <Text fontSize="lg" fontWeight="semibold" color="gray.700">
            Métodos de Pago Guardados
          </Text>
          <Button
            size="sm"
            leftIcon={<Icon as={FiPlus} />}
            variant="outline"
            onClick={onOpen}
          >
            Nuevo Método
          </Button>
        </HStack>

        {savedMethods.length === 0 ? (
          <Card bg={cardBg}>
            <CardBody textAlign="center" py={8}>
              <Icon as={FaCreditCard} boxSize={10} color="gray.400" mb={4} />
              <Text color="gray.500" mb={4}>
                No tienes métodos de pago guardados
              </Text>
              <Button
                leftIcon={<Icon as={FiPlus} />}
                colorScheme="blue"
                onClick={onOpen}
              >
                Agregar Método de Pago
              </Button>
            </CardBody>
          </Card>
        ) : (
          <RadioGroup value={selectedId} onChange={handleMethodSelect}>
            <VStack spacing={3} align="stretch">
              {savedMethods.map((method) => (
                <Card 
                  key={method.id} 
                  bg={cardBg}
                  border="2px"
                  borderColor={selectedId === method.id ? 'blue.200' : 'gray.200'}
                  cursor="pointer"
                  onClick={() => handleMethodSelect(method.id)}
                  _hover={{ borderColor: 'blue.300' }}
                >
                  <CardBody>
                    <HStack justify="space-between" align="center">
                      <HStack spacing={3} align="center" flex={1}>
                        <Radio value={method.id} colorScheme="blue" />
                        
                        {method.type === 'card' ? (
                          <HStack spacing={3} flex={1}>
                            {getCardBrandIcon(method.brand) ? (
                              <Image
                                src={getCardBrandIcon(method.brand)}
                                alt={getCardBrandName(method.brand)}
                                h="24px"
                                fallback={<Icon as={FaCreditCard} boxSize={6} color="gray.500" />}
                              />
                            ) : (
                              <Icon as={FaCreditCard} boxSize={6} color="gray.500" />
                            )}
                            <VStack align="start" spacing={1}>
                              <HStack>
                                <Text fontWeight="semibold">{method.name}</Text>
                                {method.isDefault && (
                                  <Badge colorScheme="green" size="sm">Por Defecto</Badge>
                                )}
                              </HStack>
                              <Text fontSize="sm" color="gray.600">
                                {getCardBrandName(method.brand)} •••• {method.last4} • {method.expiryMonth}/{method.expiryYear}
                              </Text>
                            </VStack>
                          </HStack>
                        ) : (
                          <HStack spacing={3} flex={1}>
                            <Icon as={FaPaypal} boxSize={6} color="blue.600" />
                            <VStack align="start" spacing={1}>
                              <HStack>
                                <Text fontWeight="semibold">{method.name}</Text>
                                {method.isDefault && (
                                  <Badge colorScheme="green" size="sm">Por Defecto</Badge>
                                )}
                              </HStack>
                              <Text fontSize="sm" color="gray.600">
                                {method.email}
                              </Text>
                            </VStack>
                          </HStack>
                        )}
                      </HStack>
                      
                      <HStack>
                        <Button
                          size="sm"
                          variant="ghost"
                          leftIcon={<Icon as={FiEdit2} />}
                          onClick={(e) => {
                            e.stopPropagation()
                            console.log('Edit payment method:', method.id)
                          }}
                        >
                          Editar
                        </Button>
                        <Button
                          size="sm"
                          variant="ghost"
                          colorScheme="red"
                          leftIcon={<Icon as={FiTrash2} />}
                          onClick={(e) => {
                            e.stopPropagation()
                            removePaymentMethod(method.id)
                          }}
                        >
                          Eliminar
                        </Button>
                      </HStack>
                    </HStack>
                  </CardBody>
                </Card>
              ))}
            </VStack>
          </RadioGroup>
        )}

        <Box bg="green.50" p={3} rounded="md">
          <HStack>
            <Icon as={FiShield} color="green.500" />
            <Text fontSize="sm" color="green.700">
              <strong>Seguro:</strong> Tus métodos de pago están protegidos con encriptación de grado bancario. 
              Nunca almacenamos números de tarjeta completos.
            </Text>
          </HStack>
        </Box>
      </VStack>

      {/* Add Payment Method Modal */}
      <Modal isOpen={isOpen} onClose={onClose} size="xl">
        <ModalOverlay />
        <ModalContent>
          <ModalHeader>Nuevo Método de Pago</ModalHeader>
          <ModalCloseButton />
          <ModalBody>
            <Text color="gray.600" mb={4}>
              Esta funcionalidad se implementará próximamente con integración segura de Stripe y PayPal.
            </Text>
          </ModalBody>
          <ModalFooter>
            <Button onClick={onClose}>Cerrar</Button>
          </ModalFooter>
        </ModalContent>
      </Modal>
    </Box>
  )
}

export default SavedPaymentMethods