import {
  Badge,
  Box,
  Button,
  Card,
  CardBody,
  HStack,
  Heading,
  Text,
  VStack,
  useColorModeValue,
} from "@chakra-ui/react"
import { FiAlertTriangle, FiPackage, FiPlus } from "react-icons/fi"

const InventoryManagement = () => {
  const cardBg = useColorModeValue("white", "gray.800")

  return (
    <Box w="full">
      <VStack spacing={6} align="stretch">
        {/* Header */}
        <HStack justify="space-between">
          <Box>
            <Heading size="lg" mb={2}>
              Gestión de Inventario
            </Heading>
            <Text color="gray.600">Control de stock y productos</Text>
          </Box>
          <Button leftIcon={<FiPlus />} colorScheme="blue">
            Nuevo Producto
          </Button>
        </HStack>

        {/* Quick Stats */}
        <HStack spacing={4}>
          <Card bg={cardBg} flex={1}>
            <CardBody>
              <HStack>
                <Box bg="blue.100" p={3} rounded="lg">
                  <FiPackage color="blue.500" size={24} />
                </Box>
                <Box>
                  <Text fontSize="2xl" fontWeight="bold">
                    156
                  </Text>
                  <Text fontSize="sm" color="gray.600">
                    Total Productos
                  </Text>
                </Box>
              </HStack>
            </CardBody>
          </Card>

          <Card bg={cardBg} flex={1}>
            <CardBody>
              <HStack>
                <Box bg="red.100" p={3} rounded="lg">
                  <FiAlertTriangle color="red.500" size={24} />
                </Box>
                <Box>
                  <Text fontSize="2xl" fontWeight="bold" color="red.500">
                    8
                  </Text>
                  <Text fontSize="sm" color="gray.600">
                    Stock Bajo
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
                  🏗️ Gestión de Inventario en Desarrollo
                </Text>
                <Text color="gray.400" textAlign="center">
                  Aquí estará la tabla de productos con funcionalidades de:
                  <br />• CRUD de productos
                  <br />• Control de stock en tiempo real
                  <br />• Alertas de stock bajo
                  <br />• Categorización y filtros
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

export default InventoryManagement
