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
import { FiBarChart, FiPieChart, FiTrendingUp } from "react-icons/fi"

const ReportsAndAnalytics = () => {
  const cardBg = useColorModeValue("white", "gray.800")

  return (
    <Box w="full">
      <VStack spacing={6} align="stretch">
        {/* Header */}
        <Box>
          <Heading size="lg" mb={2}>
            Reportes y Analytics
          </Heading>
          <Text color="gray.600">Métricas de negocio y análisis de datos</Text>
        </Box>

        {/* Quick Stats */}
        <HStack spacing={4}>
          <Card bg={cardBg} flex={1}>
            <CardBody>
              <HStack>
                <Box bg="blue.100" p={3} rounded="lg">
                  <FiBarChart color="blue.500" size={24} />
                </Box>
                <Box>
                  <Text fontSize="2xl" fontWeight="bold">
                    $12,426
                  </Text>
                  <Text fontSize="sm" color="gray.600">
                    Ventas del Mes
                  </Text>
                </Box>
              </HStack>
            </CardBody>
          </Card>

          <Card bg={cardBg} flex={1}>
            <CardBody>
              <HStack>
                <Box bg="green.100" p={3} rounded="lg">
                  <FiTrendingUp color="green.500" size={24} />
                </Box>
                <Box>
                  <Text fontSize="2xl" fontWeight="bold" color="green.500">
                    +23%
                  </Text>
                  <Text fontSize="sm" color="gray.600">
                    Crecimiento
                  </Text>
                </Box>
              </HStack>
            </CardBody>
          </Card>

          <Card bg={cardBg} flex={1}>
            <CardBody>
              <HStack>
                <Box bg="purple.100" p={3} rounded="lg">
                  <FiPieChart color="purple.500" size={24} />
                </Box>
                <Box>
                  <Text fontSize="2xl" fontWeight="bold">
                    3.2%
                  </Text>
                  <Text fontSize="sm" color="gray.600">
                    Conversión
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
                  📊 Analytics Dashboard en Desarrollo
                </Text>
                <Text color="gray.400" textAlign="center">
                  Plataforma completa de analytics con:
                  <br />• Gráficos de ventas y tendencias temporales
                  <br />• Análisis de productos más vendidos
                  <br />• Métricas de conversión y embudo de ventas
                  <br />• Reportes de inventario y rotación
                  <br />• Análisis de comportamiento de clientes
                  <br />• Exportación de datos (PDF, Excel, CSV)
                  <br />• KPIs personalizables y alertas
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

export default ReportsAndAnalytics
