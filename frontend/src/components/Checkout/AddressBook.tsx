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
  Flex,
} from '@chakra-ui/react'
import { FiPlus, FiEdit2, FiMapPin, FiHome, FiBriefcase } from 'react-icons/fi'
import { useState, useEffect } from 'react'
import { type ShippingInformation } from './ShippingInformationStep'

interface SavedAddress extends ShippingInformation {
  id: string
  name: string
  isDefault: boolean
  type: 'home' | 'work' | 'other'
}

interface AddressBookProps {
  onSelectAddress: (address: ShippingInformation) => void
  selectedAddressId?: string
}

const AddressBook = ({ onSelectAddress, selectedAddressId }: AddressBookProps) => {
  const cardBg = useColorModeValue('white', 'gray.800')
  const { isOpen, onOpen, onClose } = useDisclosure()
  const [savedAddresses, setSavedAddresses] = useState<SavedAddress[]>([])
  const [selectedId, setSelectedId] = useState<string>(selectedAddressId || '')

  // Mock data - in real app, this would come from user profile API
  useEffect(() => {
    const mockAddresses: SavedAddress[] = [
      {
        id: '1',
        name: 'Casa',
        type: 'home',
        isDefault: true,
        firstName: 'Juan',
        lastName: 'Pérez',
        addressLine1: 'Av. Insurgentes Sur 123',
        addressLine2: 'Col. Roma Norte',
        city: 'Ciudad de México',
        state: 'Ciudad de México',
        postalCode: '06700',
        country: 'MX',
        phone: '+52 55 1234 5678',
        isBusinessAddress: false,
        sameAsBilling: true,
      },
      {
        id: '2',
        name: 'Oficina',
        type: 'work',
        isDefault: false,
        firstName: 'Juan',
        lastName: 'Pérez',
        company: 'Mi Empresa S.A.',
        addressLine1: 'Paseo de la Reforma 456',
        addressLine2: 'Piso 10, Oficina 1001',
        city: 'Ciudad de México',
        state: 'Ciudad de México',
        postalCode: '11000',
        country: 'MX',
        phone: '+52 55 9876 5432',
        isBusinessAddress: true,
        sameAsBilling: false,
      },
    ]
    setSavedAddresses(mockAddresses)
    
    // Set default selection
    const defaultAddress = mockAddresses.find(addr => addr.isDefault)
    if (defaultAddress && !selectedAddressId) {
      setSelectedId(defaultAddress.id)
      onSelectAddress(defaultAddress)
    }
  }, [selectedAddressId, onSelectAddress])

  const handleAddressSelect = (addressId: string) => {
    setSelectedId(addressId)
    const address = savedAddresses.find(addr => addr.id === addressId)
    if (address) {
      onSelectAddress(address)
    }
  }

  const getAddressIcon = (type: SavedAddress['type']) => {
    switch (type) {
      case 'home':
        return FiHome
      case 'work':
        return FiBriefcase
      default:
        return FiMapPin
    }
  }

  const getAddressTypeColor = (type: SavedAddress['type']) => {
    switch (type) {
      case 'home':
        return 'green'
      case 'work':
        return 'blue'
      default:
        return 'gray'
    }
  }

  return (
    <Box>
      <VStack spacing={4} align="stretch">
        <HStack justify="space-between">
          <Text fontSize="lg" fontWeight="semibold" color="gray.700">
            Direcciones Guardadas
          </Text>
          <Button
            size="sm"
            leftIcon={<Icon as={FiPlus} />}
            variant="outline"
            onClick={onOpen}
          >
            Nueva Dirección
          </Button>
        </HStack>

        {savedAddresses.length === 0 ? (
          <Card bg={cardBg}>
            <CardBody textAlign="center" py={8}>
              <Icon as={FiMapPin} boxSize={10} color="gray.400" mb={4} />
              <Text color="gray.500" mb={4}>
                No tienes direcciones guardadas
              </Text>
              <Button
                leftIcon={<Icon as={FiPlus} />}
                colorScheme="blue"
                onClick={onOpen}
              >
                Agregar Dirección
              </Button>
            </CardBody>
          </Card>
        ) : (
          <RadioGroup value={selectedId} onChange={handleAddressSelect}>
            <VStack spacing={3} align="stretch">
              {savedAddresses.map((address) => (
                <Card 
                  key={address.id} 
                  bg={cardBg}
                  border="2px"
                  borderColor={selectedId === address.id ? 'blue.200' : 'gray.200'}
                  cursor="pointer"
                  onClick={() => handleAddressSelect(address.id)}
                  _hover={{ borderColor: 'blue.300' }}
                >
                  <CardBody>
                    <HStack justify="space-between" align="start">
                      <HStack spacing={3} align="start" flex={1}>
                        <Radio value={address.id} colorScheme="blue" mt={1} />
                        <VStack align="start" spacing={2} flex={1}>
                          <HStack>
                            <Icon as={getAddressIcon(address.type)} color={`${getAddressTypeColor(address.type)}.500`} />
                            <Text fontWeight="semibold">{address.name}</Text>
                            {address.isDefault && (
                              <Badge colorScheme="green" size="sm">Por Defecto</Badge>
                            )}
                            <Badge colorScheme={getAddressTypeColor(address.type)} size="sm">
                              {address.type === 'home' ? 'Casa' : address.type === 'work' ? 'Trabajo' : 'Otro'}
                            </Badge>
                          </HStack>
                          
                          <VStack align="start" spacing={1} fontSize="sm" color="gray.600">
                            <Text fontWeight="medium" color="gray.800">
                              {address.firstName} {address.lastName}
                            </Text>
                            {address.company && (
                              <Text>{address.company}</Text>
                            )}
                            <Text>{address.addressLine1}</Text>
                            {address.addressLine2 && (
                              <Text>{address.addressLine2}</Text>
                            )}
                            <Text>
                              {address.city}, {address.state} {address.postalCode}
                            </Text>
                            {address.phone && (
                              <Text>Tel: {address.phone}</Text>
                            )}
                          </VStack>
                        </VStack>
                      </HStack>
                      
                      <Button
                        size="sm"
                        variant="ghost"
                        leftIcon={<Icon as={FiEdit2} />}
                        onClick={(e) => {
                          e.stopPropagation()
                          // Handle edit address
                          console.log('Edit address:', address.id)
                        }}
                      >
                        Editar
                      </Button>
                    </HStack>
                  </CardBody>
                </Card>
              ))}
            </VStack>
          </RadioGroup>
        )}

        <Box bg="blue.50" p={3} rounded="md">
          <Text fontSize="sm" color="blue.700">
            💡 <strong>Tip:</strong> Guarda múltiples direcciones para hacer checkout más rápido en futuras compras.
          </Text>
        </Box>
      </VStack>

      {/* Add/Edit Address Modal */}
      <Modal isOpen={isOpen} onClose={onClose} size="xl">
        <ModalOverlay />
        <ModalContent>
          <ModalHeader>Nueva Dirección</ModalHeader>
          <ModalCloseButton />
          <ModalBody>
            <Text color="gray.600" mb={4}>
              Esta funcionalidad se implementará próximamente. Por ahora, puedes usar el formulario de envío en el checkout.
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

export default AddressBook