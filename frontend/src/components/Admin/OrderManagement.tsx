import {
  Badge,
  Box,
  Card,
  CardBody,
  HStack,
  Heading,
  Text,
  VStack,
  useColorModeValue,
} from "@chakra-ui/react"
import { FiCheck, FiClock, FiShoppingCart } from "react-icons/fi"

const OrderManagement = () => {
  const cardBg = useColorModeValue("white", "gray.800")

  return (
    <Box w="full">
      <VStack spacing={6} align="stretch">
        {/* Header */}
        <Box>
          <Heading size="lg" mb={2}>
            Gestión de Pedidos
          </Heading>
          <Text color="gray.600">Control y seguimiento de pedidos</Text>
        </Box>

        {/* Quick Stats */}
        <HStack spacing={4}>
          <Card bg={cardBg} flex={1}>
            <CardBody>
              <HStack>
                <Box bg="blue.100" p={3} rounded="lg">
                  <FiShoppingCart color="blue.500" size={24} />
                </Box>
                <Box>
                  <Text fontSize="2xl" fontWeight="bold">
                    247
                  </Text>
                  <Text fontSize="sm" color="gray.600">
                    Total Pedidos
                  </Text>
                </Box>
              </HStack>
            </CardBody>
          </Card>

          <Card bg={cardBg} flex={1}>
            <CardBody>
              <HStack>
                <Box bg="yellow.100" p={3} rounded="lg">
                  <FiClock color="yellow.500" size={24} />
                </Box>
                <Box>
                  <Text fontSize="2xl" fontWeight="bold" color="yellow.500">
                    12
                  </Text>
                  <Text fontSize="sm" color="gray.600">
                    Pendientes
                  </Text>
                </Box>
              </HStack>
            </CardBody>
          </Card>

          <Card bg={cardBg} flex={1}>
            <CardBody>
              <HStack>
                <Box bg="green.100" p={3} rounded="lg">
                  <FiCheck color="green.500" size={24} />
                </Box>
                <Box>
                  <Text fontSize="2xl" fontWeight="bold" color="green.500">
                    235
                  </Text>
                  <Text fontSize="sm" color="gray.600">
                    Completados
                  </Text>
                </Box>
              </HStack>
            </CardBody>
          </Card>
        </HStack>

        {/* Content Area */}
        <Card bg={cardBg}>
          <CardBody>
            <Box
              h="400px"
              display="flex"
              alignItems="center"
              justifyContent="center"
            >
              <VStack spacing={4}>
                <Text fontSize="lg" color="gray.500">
                  📦 Gestión de Pedidos en Desarrollo
                </Text>
                <Text color="gray.400" textAlign="center">
                  Aquí estará la interfaz completa de pedidos con:
                  <br />• Lista de pedidos con filtros y búsqueda
                  <br />• Estados de pedidos (Pendiente, Procesando, Enviado,
                  Entregado)
                  <br />• Detalles completos de cada pedido
                  <br />• Integración con sistemas de envío
                  <br />• Generación de facturas y etiquetas
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

export default OrderManagement
