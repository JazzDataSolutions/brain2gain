import {
  Box,
  Container,
  VStack,
  HStack,
  Heading,
  Text,
  Card,
  CardBody,
  CardHeader,
  Button,
  useColorModeValue,
  Badge,
  Divider,
  Grid,
  GridItem,
  Icon,
  Alert,
  AlertIcon,
  AlertDescription,
  Spinner,
  Center,
  Flex,
  Select,
  Input,
  InputGroup,
  InputLeftElement,
} from '@chakra-ui/react'
import { FiCalendar, FiPackage, FiEye, FiSearch, FiFilter } from 'react-icons/fi'
import { useNavigate } from '@tanstack/react-router'
import { useEffect, useState } from 'react'
import orderService, { type Order } from '../../services/orderService'

interface OrderFilters {
  status: string
  search: string
  sortBy: 'created_at' | 'total_amount' | 'status'
  sortOrder: 'asc' | 'desc'
}

const UserOrdersPage = () => {
  const navigate = useNavigate()
  const cardBg = useColorModeValue('white', 'gray.800')
  const [orders, setOrders] = useState<Order[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [pagination, setPagination] = useState({
    page: 1,
    pageSize: 10,
    total: 0,
    totalPages: 0,
  })
  const [filters, setFilters] = useState<OrderFilters>({
    status: '',
    search: '',
    sortBy: 'created_at',
    sortOrder: 'desc',
  })

  const fetchOrders = async () => {
    setLoading(true)
    try {
      const statusFilter = filters.status ? [filters.status] : undefined
      const result = await orderService.getMyOrders(
        pagination.page,
        pagination.pageSize,
        statusFilter
      )
      
      // Client-side filtering and sorting if needed
      let filteredOrders = result.orders
      
      if (filters.search) {
        filteredOrders = filteredOrders.filter(order =>
          order.order_id.toLowerCase().includes(filters.search.toLowerCase()) ||
          order.items.some(item => 
            item.product_name.toLowerCase().includes(filters.search.toLowerCase())
          )
        )
      }
      
      // Sort orders
      filteredOrders.sort((a, b) => {
        const multiplier = filters.sortOrder === 'asc' ? 1 : -1
        if (filters.sortBy === 'created_at') {
          return multiplier * (new Date(a.created_at).getTime() - new Date(b.created_at).getTime())
        } else if (filters.sortBy === 'total_amount') {
          return multiplier * (a.total_amount - b.total_amount)
        } else if (filters.sortBy === 'status') {
          return multiplier * a.status.localeCompare(b.status)
        }
        return 0
      })
      
      setOrders(filteredOrders)
      setPagination(prev => ({
        ...prev,
        total: result.total,
        totalPages: result.total_pages,
      }))
    } catch (err) {
      console.error('Error fetching orders:', err)
      setError('No se pudieron cargar los pedidos')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchOrders()
  }, [pagination.page, pagination.pageSize, filters.status])

  const getStatusColor = (status: string) => {
    switch (status.toLowerCase()) {
      case 'confirmed':
        return 'green'
      case 'pending':
        return 'yellow'
      case 'processing':
        return 'blue'
      case 'shipped':
        return 'purple'
      case 'delivered':
        return 'green'
      case 'cancelled':
        return 'red'
      default:
        return 'gray'
    }
  }

  const getStatusText = (status: string) => {
    switch (status.toLowerCase()) {
      case 'confirmed':
        return 'Confirmado'
      case 'pending':
        return 'Pendiente'
      case 'processing':
        return 'Procesando'
      case 'shipped':
        return 'Enviado'
      case 'delivered':
        return 'Entregado'
      case 'cancelled':
        return 'Cancelado'
      default:
        return status
    }
  }

  const handleSearch = () => {
    fetchOrders()
  }

  const handlePageChange = (newPage: number) => {
    setPagination(prev => ({ ...prev, page: newPage }))
  }

  if (loading && orders.length === 0) {
    return (
      <Container maxW="6xl" py={8}>
        <Center minH="400px">
          <VStack spacing={4}>
            <Spinner size="xl" color="blue.500" />
            <Text>Cargando pedidos...</Text>
          </VStack>
        </Center>
      </Container>
    )
  }

  if (error) {
    return (
      <Container maxW="6xl" py={8}>
        <Alert status="error">
          <AlertIcon />
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      </Container>
    )
  }

  return (
    <Container maxW="6xl" py={8}>
      <VStack spacing={8} align="stretch">
        {/* Header */}
        <Box>
          <Heading size="xl" mb={2}>
            Mis Pedidos
          </Heading>
          <Text color="gray.600">
            Gestiona y rastrea tus pedidos
          </Text>
        </Box>

        {/* Filters */}
        <Card bg={cardBg}>
          <CardHeader>
            <Heading size="md">Filtros y Búsqueda</Heading>
          </CardHeader>
          <CardBody>
            <Grid templateColumns={{ base: '1fr', md: '1fr 1fr', lg: '2fr 1fr 1fr 1fr' }} gap={4}>
              <GridItem>
                <InputGroup>
                  <InputLeftElement>
                    <Icon as={FiSearch} color="gray.400" />
                  </InputLeftElement>
                  <Input
                    placeholder="Buscar por ID de pedido o producto..."
                    value={filters.search}
                    onChange={(e) => setFilters(prev => ({ ...prev, search: e.target.value }))}
                    onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
                  />
                </InputGroup>
              </GridItem>
              
              <GridItem>
                <Select
                  placeholder="Todos los estados"
                  value={filters.status}
                  onChange={(e) => setFilters(prev => ({ ...prev, status: e.target.value }))}
                >
                  <option value="PENDING">Pendiente</option>
                  <option value="CONFIRMED">Confirmado</option>
                  <option value="PROCESSING">Procesando</option>
                  <option value="SHIPPED">Enviado</option>
                  <option value="DELIVERED">Entregado</option>
                  <option value="CANCELLED">Cancelado</option>
                </Select>
              </GridItem>
              
              <GridItem>
                <Select
                  value={filters.sortBy}
                  onChange={(e) => setFilters(prev => ({ 
                    ...prev, 
                    sortBy: e.target.value as OrderFilters['sortBy']
                  }))}
                >
                  <option value="created_at">Fecha</option>
                  <option value="total_amount">Total</option>
                  <option value="status">Estado</option>
                </Select>
              </GridItem>
              
              <GridItem>
                <Select
                  value={filters.sortOrder}
                  onChange={(e) => setFilters(prev => ({ 
                    ...prev, 
                    sortOrder: e.target.value as OrderFilters['sortOrder']
                  }))}
                >
                  <option value="desc">Descendente</option>
                  <option value="asc">Ascendente</option>
                </Select>
              </GridItem>
            </Grid>
            
            <HStack mt={4}>
              <Button
                leftIcon={<Icon as={FiSearch} />}
                colorScheme="blue"
                onClick={handleSearch}
              >
                Buscar
              </Button>
              <Button
                leftIcon={<Icon as={FiFilter} />}
                variant="outline"
                onClick={() => {
                  setFilters({
                    status: '',
                    search: '',
                    sortBy: 'created_at',
                    sortOrder: 'desc',
                  })
                  fetchOrders()
                }}
              >
                Limpiar Filtros
              </Button>
            </HStack>
          </CardBody>
        </Card>

        {/* Orders List */}
        {orders.length === 0 ? (
          <Card bg={cardBg}>
            <CardBody textAlign="center" py={12}>
              <Icon as={FiPackage} boxSize={16} color="gray.400" mb={4} />
              <Heading size="md" color="gray.600" mb={2}>
                No tienes pedidos
              </Heading>
              <Text color="gray.500" mb={6}>
                Cuando realices tu primera compra, aparecerá aquí
              </Text>
              <Button
                colorScheme="blue"
                onClick={() => navigate({ to: '/store/products' })}
              >
                Explorar Productos
              </Button>
            </CardBody>
          </Card>
        ) : (
          <VStack spacing={4} align="stretch">
            {orders.map((order) => (
              <Card key={order.order_id} bg={cardBg}>
                <CardBody>
                  <Grid templateColumns={{ base: '1fr', lg: '2fr 1fr 1fr 1fr' }} gap={4} alignItems="center">
                    {/* Order Info */}
                    <GridItem>
                      <VStack align="start" spacing={2}>
                        <HStack>
                          <Heading size="sm">
                            Pedido #{order.order_id.slice(-8).toUpperCase()}
                          </Heading>
                          <Badge colorScheme={getStatusColor(order.status)}>
                            {getStatusText(order.status)}
                          </Badge>
                        </HStack>
                        <HStack spacing={4} fontSize="sm" color="gray.600">
                          <HStack>
                            <Icon as={FiCalendar} />
                            <Text>
                              {new Date(order.created_at).toLocaleDateString('es-MX', {
                                year: 'numeric',
                                month: 'short',
                                day: 'numeric'
                              })}
                            </Text>
                          </HStack>
                          <HStack>
                            <Icon as={FiPackage} />
                            <Text>{order.items.length} productos</Text>
                          </HStack>
                        </HStack>
                        <Text fontSize="sm" color="gray.500" noOfLines={1}>
                          {order.items.map(item => item.product_name).join(', ')}
                        </Text>
                      </VStack>
                    </GridItem>

                    {/* Payment Status */}
                    <GridItem>
                      <VStack align="start" spacing={1}>
                        <Text fontSize="sm" fontWeight="medium">Pago</Text>
                        <Badge 
                          colorScheme={
                            order.payment_status === 'CAPTURED' ? 'green' :
                            order.payment_status === 'PENDING' ? 'yellow' :
                            order.payment_status === 'FAILED' ? 'red' : 'gray'
                          }
                        >
                          {order.payment_status}
                        </Badge>
                      </VStack>
                    </GridItem>

                    {/* Total */}
                    <GridItem>
                      <VStack align="start" spacing={1}>
                        <Text fontSize="sm" fontWeight="medium">Total</Text>
                        <Text fontSize="lg" fontWeight="bold" color="blue.500">
                          ${order.total_amount.toFixed(2)}
                        </Text>
                      </VStack>
                    </GridItem>

                    {/* Actions */}
                    <GridItem>
                      <HStack spacing={2} justify={{ base: 'start', lg: 'end' }}>
                        <Button
                          size="sm"
                          leftIcon={<Icon as={FiEye} />}
                          onClick={() => navigate({ 
                            to: '/store/orders/$orderId', 
                            params: { orderId: order.order_id }
                          })}
                        >
                          Ver Detalles
                        </Button>
                        {(order.status === 'PENDING' || order.status === 'CONFIRMED') && (
                          <Button
                            size="sm"
                            variant="outline"
                            colorScheme="red"
                            onClick={async () => {
                              try {
                                await orderService.cancelOrder(order.order_id, 'Cancelado por el usuario')
                                fetchOrders()
                              } catch (error) {
                                console.error('Error canceling order:', error)
                              }
                            }}
                          >
                            Cancelar
                          </Button>
                        )}
                      </HStack>
                    </GridItem>
                  </Grid>
                </CardBody>
              </Card>
            ))}
          </VStack>
        )}

        {/* Pagination */}
        {pagination.totalPages > 1 && (
          <Card bg={cardBg}>
            <CardBody>
              <Flex justify="space-between" align="center">
                <Text fontSize="sm" color="gray.600">
                  Mostrando {orders.length} de {pagination.total} pedidos
                </Text>
                <HStack spacing={2}>
                  <Button
                    size="sm"
                    isDisabled={pagination.page === 1}
                    onClick={() => handlePageChange(pagination.page - 1)}
                  >
                    Anterior
                  </Button>
                  {Array.from({ length: Math.min(5, pagination.totalPages) }, (_, i) => {
                    const page = i + 1
                    return (
                      <Button
                        key={page}
                        size="sm"
                        variant={pagination.page === page ? 'solid' : 'outline'}
                        colorScheme={pagination.page === page ? 'blue' : 'gray'}
                        onClick={() => handlePageChange(page)}
                      >
                        {page}
                      </Button>
                    )
                  })}
                  <Button
                    size="sm"
                    isDisabled={pagination.page === pagination.totalPages}
                    onClick={() => handlePageChange(pagination.page + 1)}
                  >
                    Siguiente
                  </Button>
                </HStack>
              </Flex>
            </CardBody>
          </Card>
        )}
      </VStack>
    </Container>
  )
}

export default UserOrdersPage