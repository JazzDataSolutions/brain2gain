import {
  Box,
  Heading,
  Text,
  Card,
  CardBody,
  HStack,
  VStack,
  Badge,
  useColorModeValue,
} from '@chakra-ui/react'
import { FiUsers, FiUserPlus, FiStar } from 'react-icons/fi'

const CustomerManagement = () => {
  const cardBg = useColorModeValue('white', 'gray.800')
  
  return (
    <Box w="full">
      <VStack spacing={6} align="stretch">
        {/* Header */}
        <Box>
          <Heading size="lg" mb={2}>
            Gestión de Clientes
          </Heading>
          <Text color="gray.600">
            CRM y gestión de relaciones con clientes
          </Text>
        </Box>

        {/* Quick Stats */}
        <HStack spacing={4}>
          <Card bg={cardBg} flex={1}>
            <CardBody>
              <HStack>
                <Box bg="purple.100" p={3} rounded="lg">
                  <FiUsers color="purple.500" size={24} />
                </Box>
                <Box>
                  <Text fontSize="2xl" fontWeight="bold">892</Text>
                  <Text fontSize="sm" color="gray.600">Total Clientes</Text>
                </Box>
              </HStack>
            </CardBody>
          </Card>
          
          <Card bg={cardBg} flex={1}>
            <CardBody>
              <HStack>
                <Box bg="green.100" p={3} rounded="lg">
                  <FiUserPlus color="green.500" size={24} />
                </Box>
                <Box>
                  <Text fontSize="2xl" fontWeight="bold" color="green.500">47</Text>
                  <Text fontSize="sm" color="gray.600">Nuevos Este Mes</Text>
                </Box>
              </HStack>
            </CardBody>
          </Card>

          <Card bg={cardBg} flex={1}>
            <CardBody>
              <HStack>
                <Box bg="yellow.100" p={3} rounded="lg">
                  <FiStar color="yellow.500" size={24} />
                </Box>
                <Box>
                  <Text fontSize="2xl" fontWeight="bold" color="yellow.500">156</Text>
                  <Text fontSize="sm" color="gray.600">Clientes VIP</Text>
                </Box>
              </HStack>
            </CardBody>
          </Card>
        </HStack>

        {/* Content Area */}
        <Card bg={cardBg}>
          <CardBody>
            <Box h="400px" display="flex" align="center" justify="center">
              <VStack spacing={4}>
                <Text fontSize="lg" color="gray.500">
                  👥 CRM de Clientes en Desarrollo
                </Text>
                <Text color="gray.400" textAlign="center">
                  Sistema completo de gestión de clientes:
                  <br />• Lista de clientes con búsqueda y filtros
                  <br />• Perfiles detallados con historial de compras
                  <br />• Segmentación automática (VIP, Nuevos, Inactivos)
                  <br />• Campañas de email marketing
                  <br />• Programa de fidelización y puntos
                  <br />• Soporte y tickets de ayuda
                </Text>
                <Badge colorScheme="orange">Próximamente</Badge>
              </VStack>
            </Box>
          </CardBody>
        </Card>
      </VStack>
    </Box>
  )
}

export default CustomerManagement