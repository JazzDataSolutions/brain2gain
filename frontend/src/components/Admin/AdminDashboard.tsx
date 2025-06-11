import {
  Box,
  SimpleGrid,
  Stat,
  StatLabel,
  StatNumber,
  StatHelpText,
  StatArrow,
  Card,
  CardHeader,
  CardBody,
  Heading,
  Text,
  Progress,
  VStack,
  HStack,
  Table,
  Thead,
  Tbody,
  Tr,
  Th,
  Td,
  Badge,
  Avatar,
  useColorModeValue,
  Flex,
  Icon,
} from '@chakra-ui/react'
import {
  FiDollarSign,
  FiShoppingCart,
  FiUsers,
  FiTrendingUp,
  FiPackage,
  FiAlertTriangle,
} from 'react-icons/fi'

const AdminDashboard = () => {
  const cardBg = useColorModeValue('white', 'gray.800')
  
  // Mock data - En el futuro se conectará con el backend
  const stats = [
    {
      label: 'Ventas Totales',
      value: '$12,426',
      change: 12.5,
      icon: FiDollarSign,
      color: 'green',
    },
    {
      label: 'Pedidos',
      value: '1,847',
      change: 8.2,
      icon: FiShoppingCart,
      color: 'blue',
    },
    {
      label: 'Clientes',
      value: '892',
      change: 5.7,
      icon: FiUsers,
      color: 'purple',
    },
    {
      label: 'Productos',
      value: '156',
      change: -2.1,
      icon: FiPackage,
      color: 'orange',
    },
  ]

  const recentOrders = [
    {
      id: '#1023',
      customer: 'Juan Pérez',
      email: 'juan@email.com',
      amount: 156.99,
      status: 'completed',
      date: '2024-06-10',
    },
    {
      id: '#1022',
      customer: 'María García',
      email: 'maria@email.com',
      amount: 89.50,
      status: 'pending',
      date: '2024-06-10',
    },
    {
      id: '#1021',
      customer: 'Carlos López',
      email: 'carlos@email.com',
      amount: 234.75,
      status: 'processing',
      date: '2024-06-09',
    },
    {
      id: '#1020',
      customer: 'Ana Martínez',
      email: 'ana@email.com',
      amount: 67.25,
      status: 'completed',
      date: '2024-06-09',
    },
  ]

  const lowStockProducts = [
    {
      name: 'Whey Protein Gold',
      sku: 'WPG-001',
      stock: 5,
      minStock: 20,
      category: 'Proteínas',
    },
    {
      name: 'Creatina Monohidrato',
      sku: 'CRE-002',
      stock: 3,
      minStock: 15,
      category: 'Creatina',
    },
    {
      name: 'Pre-Workout Extreme',
      sku: 'PWO-003',
      stock: 8,
      minStock: 25,
      category: 'Pre-Workout',
    },
  ]

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed':
        return 'green'
      case 'pending':
        return 'yellow'
      case 'processing':
        return 'blue'
      case 'cancelled':
        return 'red'
      default:
        return 'gray'
    }
  }

  const getStatusText = (status: string) => {
    switch (status) {
      case 'completed':
        return 'Completado'
      case 'pending':
        return 'Pendiente'
      case 'processing':
        return 'Procesando'
      case 'cancelled':
        return 'Cancelado'
      default:
        return status
    }
  }

  return (
    <Box w="full">
      <VStack spacing={6} align="stretch">
        {/* Header */}
        <Box>
          <Heading size="lg" mb={2}>
            Dashboard
          </Heading>
          <Text color="gray.600">
            Resumen general de tu tienda de suplementos
          </Text>
        </Box>

        {/* Stats Cards */}
        <SimpleGrid columns={{ base: 1, md: 2, lg: 4 }} spacing={6}>
          {stats.map((stat, index) => (
            <Card key={index} bg={cardBg}>
              <CardBody>
                <Flex justify="space-between" align="start">
                  <Box>
                    <Stat>
                      <StatLabel fontSize="sm" color="gray.600">
                        {stat.label}
                      </StatLabel>
                      <StatNumber fontSize="2xl" fontWeight="bold">
                        {stat.value}
                      </StatNumber>
                      <StatHelpText mb={0}>
                        <StatArrow
                          type={stat.change > 0 ? 'increase' : 'decrease'}
                        />
                        {Math.abs(stat.change)}% vs mes anterior
                      </StatHelpText>
                    </Stat>
                  </Box>
                  <Box
                    bg={`${stat.color}.100`}
                    p={3}
                    rounded="lg"
                  >
                    <Icon
                      as={stat.icon}
                      boxSize={6}
                      color={`${stat.color}.500`}
                    />
                  </Box>
                </Flex>
              </CardBody>
            </Card>
          ))}
        </SimpleGrid>

        {/* Content Grid */}
        <SimpleGrid columns={{ base: 1, lg: 2 }} spacing={6}>
          {/* Recent Orders */}
          <Card bg={cardBg}>
            <CardHeader>
              <Flex justify="space-between" align="center">
                <Heading size="md">Pedidos Recientes</Heading>
                <Text fontSize="sm" color="blue.500" cursor="pointer">
                  Ver todos
                </Text>
              </Flex>
            </CardHeader>
            <CardBody pt={0}>
              <Table variant="simple" size="sm">
                <Thead>
                  <Tr>
                    <Th>Cliente</Th>
                    <Th>Pedido</Th>
                    <Th>Estado</Th>
                    <Th isNumeric>Total</Th>
                  </Tr>
                </Thead>
                <Tbody>
                  {recentOrders.map((order) => (
                    <Tr key={order.id}>
                      <Td>
                        <HStack>
                          <Avatar size="sm" name={order.customer} />
                          <Box>
                            <Text fontSize="sm" fontWeight="medium">
                              {order.customer}
                            </Text>
                            <Text fontSize="xs" color="gray.500">
                              {order.email}
                            </Text>
                          </Box>
                        </HStack>
                      </Td>
                      <Td>
                        <Text fontSize="sm" fontWeight="medium">
                          {order.id}
                        </Text>
                        <Text fontSize="xs" color="gray.500">
                          {order.date}
                        </Text>
                      </Td>
                      <Td>
                        <Badge
                          colorScheme={getStatusColor(order.status)}
                          size="sm"
                        >
                          {getStatusText(order.status)}
                        </Badge>
                      </Td>
                      <Td isNumeric>
                        <Text fontSize="sm" fontWeight="medium">
                          ${order.amount}
                        </Text>
                      </Td>
                    </Tr>
                  ))}
                </Tbody>
              </Table>
            </CardBody>
          </Card>

          {/* Low Stock Alert */}
          <Card bg={cardBg}>
            <CardHeader>
              <Flex justify="space-between" align="center">
                <HStack>
                  <Icon as={FiAlertTriangle} color="red.500" />
                  <Heading size="md">Stock Bajo</Heading>
                </HStack>
                <Text fontSize="sm" color="blue.500" cursor="pointer">
                  Ver inventario
                </Text>
              </Flex>
            </CardHeader>
            <CardBody pt={0}>
              <VStack spacing={4} align="stretch">
                {lowStockProducts.map((product, index) => (
                  <Box key={index} p={4} bg="red.50" rounded="lg" border="1px" borderColor="red.200">
                    <Flex justify="space-between" align="start" mb={2}>
                      <Box>
                        <Text fontSize="sm" fontWeight="medium">
                          {product.name}
                        </Text>
                        <Text fontSize="xs" color="gray.600">
                          SKU: {product.sku} • {product.category}
                        </Text>
                      </Box>
                      <Badge colorScheme="red" size="sm">
                        {product.stock} unidades
                      </Badge>
                    </Flex>
                    <Progress
                      value={(product.stock / product.minStock) * 100}
                      colorScheme="red"
                      size="sm"
                      bg="red.100"
                    />
                    <Text fontSize="xs" color="gray.600" mt={1}>
                      Mínimo recomendado: {product.minStock} unidades
                    </Text>
                  </Box>
                ))}
              </VStack>
            </CardBody>
          </Card>
        </SimpleGrid>

        {/* Sales Chart Placeholder */}
        <Card bg={cardBg}>
          <CardHeader>
            <Heading size="md">Ventas de los Últimos 7 Días</Heading>
          </CardHeader>
          <CardBody>
            <Box h="200px" bg="gray.50" rounded="lg" display="flex" align="center" justify="center">
              <Text color="gray.500">
                📊 Aquí irá el gráfico de ventas (Chart.js/Recharts)
              </Text>
            </Box>
          </CardBody>
        </Card>
      </VStack>
    </Box>
  )
}

export default AdminDashboard