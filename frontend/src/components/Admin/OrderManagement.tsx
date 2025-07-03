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
  Input,
  InputGroup,
  InputLeftElement,
  Select,
  Table,
  TableContainer,
  Tbody,
  Td,
  Th,
  Thead,
  Tr,
  Spinner,
  Alert,
  AlertIcon,
  Modal,
  ModalOverlay,
  ModalContent,
  ModalHeader,
  ModalFooter,
  ModalBody,
  ModalCloseButton,
  useDisclosure,
  useToast,
  Flex,
  IconButton,
  Divider,
  List,
  ListItem,
  Tag,
} from "@chakra-ui/react"
import { useState, useEffect } from "react"
import { FiSearch, FiShoppingCart, FiClock, FiCheck, FiEye, FiEdit, FiTruck, FiDownload } from "react-icons/fi"
import { OrdersService } from "../../client"

interface OrderItem {
  id: string
  product_name: string
  quantity: number
  price: number
  subtotal: number
}

interface Order {
  id: string
  user_id: string
  status: "pending" | "processing" | "shipped" | "delivered" | "cancelled"
  total_amount: number
  created_at: string
  updated_at: string
  items: OrderItem[]
  shipping_address?: {
    street: string
    city: string
    state: string
    postal_code: string
    country: string
  }
  customer_email?: string
  customer_name?: string
}

interface OrderStats {
  total_orders: number
  pending_orders: number
  completed_orders: number
  shipped_orders: number
  cancelled_orders: number
  total_revenue: number
}

const OrderManagement = () => {
  const cardBg = useColorModeValue("white", "gray.800")
  const [orders, setOrders] = useState<Order[]>([])
  const [filteredOrders, setFilteredOrders] = useState<Order[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [searchTerm, setSearchTerm] = useState("")
  const [filterStatus, setFilterStatus] = useState<string>("all")
  const [stats, setStats] = useState<OrderStats>({
    total_orders: 0,
    pending_orders: 0,
    completed_orders: 0,
    shipped_orders: 0,
    cancelled_orders: 0,
    total_revenue: 0
  })

  // Modal states
  const { isOpen: isViewOpen, onOpen: onViewOpen, onClose: onViewClose } = useDisclosure()
  const { isOpen: isEditOpen, onOpen: onEditOpen, onClose: onEditClose } = useDisclosure()
  
  const [selectedOrder, setSelectedOrder] = useState<Order | null>(null)
  const [editStatus, setEditStatus] = useState<string>("")

  const toast = useToast()

  // Order status options
  const statusOptions = [
    { value: "pending", label: "Pendiente", color: "yellow" },
    { value: "processing", label: "Procesando", color: "blue" },
    { value: "shipped", label: "Enviado", color: "purple" },
    { value: "delivered", label: "Entregado", color: "green" },
    { value: "cancelled", label: "Cancelado", color: "red" }
  ]

  // Fetch orders data
  const fetchOrders = async () => {
    try {
      setLoading(true)
      setError(null)
      
      // Get all orders
      const response = await OrdersService.readOrders({
        skip: 0,
        limit: 1000
      })
      
      setOrders(response)
      setFilteredOrders(response)
      
      // Calculate stats
      const pendingOrders = response.filter(order => order.status === "pending").length
      const completedOrders = response.filter(order => order.status === "delivered").length
      const shippedOrders = response.filter(order => order.status === "shipped").length
      const cancelledOrders = response.filter(order => order.status === "cancelled").length
      const totalRevenue = response
        .filter(order => order.status === "delivered")
        .reduce((sum, order) => sum + order.total_amount, 0)

      setStats({
        total_orders: response.length,
        pending_orders: pendingOrders,
        completed_orders: completedOrders,
        shipped_orders: shippedOrders,
        cancelled_orders: cancelledOrders,
        total_revenue: totalRevenue
      })
      
    } catch (err: any) {
      setError(err.message || "Error al cargar pedidos")
      console.error("Error fetching orders:", err)
    } finally {
      setLoading(false)
    }
  }

  // Filter orders based on search and status
  useEffect(() => {
    let filtered = orders
    
    // Search filter
    if (searchTerm) {
      filtered = filtered.filter(order =>
        order.id.toLowerCase().includes(searchTerm.toLowerCase()) ||
        order.customer_email?.toLowerCase().includes(searchTerm.toLowerCase()) ||
        order.customer_name?.toLowerCase().includes(searchTerm.toLowerCase())
      )
    }
    
    // Status filter
    if (filterStatus !== "all") {
      filtered = filtered.filter(order => order.status === filterStatus)
    }
    
    setFilteredOrders(filtered)
  }, [orders, searchTerm, filterStatus])

  useEffect(() => {
    fetchOrders()
  }, [])

  // Handle update order status
  const handleUpdateOrderStatus = async () => {
    if (!selectedOrder) return
    
    try {
      await OrdersService.updateOrder({
        orderId: selectedOrder.id,
        requestBody: {
          status: editStatus as any
        }
      })
      
      await fetchOrders() // Refresh data
      onEditClose()
      
      toast({
        title: "Pedido actualizado",
        description: "El estado del pedido ha sido actualizado",
        status: "success",
        duration: 3000,
        isClosable: true,
      })
    } catch (err: any) {
      toast({
        title: "Error",
        description: err.message || "Error al actualizar pedido",
        status: "error",
        duration: 5000,
        isClosable: true,
      })
    }
  }

  // Open view modal
  const openViewModal = (order: Order) => {
    setSelectedOrder(order)
    onViewOpen()
  }

  // Open edit modal
  const openEditModal = (order: Order) => {
    setSelectedOrder(order)
    setEditStatus(order.status)
    onEditOpen()
  }

  const formatPrice = (price: number) => {
    return new Intl.NumberFormat("es-MX", {
      style: "currency",
      currency: "MXN"
    }).format(price)
  }

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString("es-ES", {
      year: "numeric",
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit"
    })
  }

  const getStatusBadge = (status: string) => {
    const statusConfig = statusOptions.find(opt => opt.value === status)
    return {
      color: statusConfig?.color || "gray",
      text: statusConfig?.label || status
    }
  }

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
                  <FiShoppingCart color="blue" size={24} />
                </Box>
                <Box>
                  <Text fontSize="2xl" fontWeight="bold">
                    {stats.total_orders}
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
                  <FiClock color="orange" size={24} />
                </Box>
                <Box>
                  <Text fontSize="2xl" fontWeight="bold" color="yellow.500">
                    {stats.pending_orders}
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
                <Box bg="purple.100" p={3} rounded="lg">
                  <FiTruck color="purple" size={24} />
                </Box>
                <Box>
                  <Text fontSize="2xl" fontWeight="bold" color="purple.500">
                    {stats.shipped_orders}
                  </Text>
                  <Text fontSize="sm" color="gray.600">
                    Enviados
                  </Text>
                </Box>
              </HStack>
            </CardBody>
          </Card>

          <Card bg={cardBg} flex={1}>
            <CardBody>
              <HStack>
                <Box bg="green.100" p={3} rounded="lg">
                  <FiCheck color="green" size={24} />
                </Box>
                <Box>
                  <Text fontSize="2xl" fontWeight="bold" color="green.500">
                    {stats.completed_orders}
                  </Text>
                  <Text fontSize="sm" color="gray.600">
                    Completados
                  </Text>
                </Box>
              </HStack>
            </CardBody>
          </Card>
        </HStack>

        {/* Revenue Card */}
        <Card bg={cardBg}>
          <CardBody>
            <HStack justify="space-between">
              <Box>
                <Text fontSize="lg" fontWeight="medium">Ingresos Totales</Text>
                <Text fontSize="3xl" fontWeight="bold" color="green.500">
                  {formatPrice(stats.total_revenue)}
                </Text>
              </Box>
              <Box textAlign="right">
                <Text fontSize="sm" color="gray.600">Promedio por pedido</Text>
                <Text fontSize="xl" fontWeight="bold">
                  {formatPrice(stats.completed_orders > 0 ? stats.total_revenue / stats.completed_orders : 0)}
                </Text>
              </Box>
            </HStack>
          </CardBody>
        </Card>

        {/* Filters */}
        <Card bg={cardBg}>
          <CardBody>
            <HStack spacing={4}>
              <InputGroup flex={1}>
                <InputLeftElement>
                  <FiSearch color="gray" />
                </InputLeftElement>
                <Input
                  placeholder="Buscar por ID, email o nombre..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                />
              </InputGroup>
              <Select
                value={filterStatus}
                onChange={(e) => setFilterStatus(e.target.value)}
                w="200px"
              >
                <option value="all">Todos los estados</option>
                {statusOptions.map(status => (
                  <option key={status.value} value={status.value}>{status.label}</option>
                ))}
              </Select>
            </HStack>
          </CardBody>
        </Card>

        {/* Content Area */}
        <Card bg={cardBg}>
          <CardBody>
            {loading ? (
              <Flex justify="center" align="center" h="400px">
                <Spinner size="xl" />
              </Flex>
            ) : error ? (
              <Alert status="error">
                <AlertIcon />
                {error}
              </Alert>
            ) : (
              <TableContainer>
                <Table variant="simple">
                  <Thead>
                    <Tr>
                      <Th>Pedido</Th>
                      <Th>Cliente</Th>
                      <Th>Total</Th>
                      <Th>Estado</Th>
                      <Th>Fecha</Th>
                      <Th>Acciones</Th>
                    </Tr>
                  </Thead>
                  <Tbody>
                    {filteredOrders.map((order) => {
                      const statusBadge = getStatusBadge(order.status)
                      return (
                        <Tr key={order.id}>
                          <Td>
                            <Box>
                              <Text fontWeight="medium">
                                #{order.id.slice(0, 8)}
                              </Text>
                              <Text fontSize="sm" color="gray.500">
                                {order.items.length} productos
                              </Text>
                            </Box>
                          </Td>
                          <Td>
                            <Box>
                              <Text fontWeight="medium">
                                {order.customer_name || "Cliente"}
                              </Text>
                              <Text fontSize="sm" color="gray.500">
                                {order.customer_email || "Sin email"}
                              </Text>
                            </Box>
                          </Td>
                          <Td fontWeight="bold">{formatPrice(order.total_amount)}</Td>
                          <Td>
                            <Badge colorScheme={statusBadge.color}>
                              {statusBadge.text}
                            </Badge>
                          </Td>
                          <Td>{formatDate(order.created_at)}</Td>
                          <Td>
                            <HStack spacing={1}>
                              <IconButton
                                aria-label="Ver detalles"
                                icon={<FiEye />}
                                size="sm"
                                variant="ghost"
                                onClick={() => openViewModal(order)}
                              />
                              <IconButton
                                aria-label="Editar estado"
                                icon={<FiEdit />}
                                size="sm"
                                variant="ghost"
                                onClick={() => openEditModal(order)}
                              />
                              <IconButton
                                aria-label="Descargar factura"
                                icon={<FiDownload />}
                                size="sm"
                                variant="ghost"
                                onClick={() => {
                                  toast({
                                    title: "Función en desarrollo",
                                    description: "La descarga de facturas estará disponible pronto",
                                    status: "info",
                                    duration: 3000,
                                    isClosable: true,
                                  })
                                }}
                              />
                            </HStack>
                          </Td>
                        </Tr>
                      )
                    })}
                  </Tbody>
                </Table>
                {filteredOrders.length === 0 && (
                  <Box textAlign="center" py={8}>
                    <Text color="gray.500">No se encontraron pedidos</Text>
                  </Box>
                )}
              </TableContainer>
            )}
          </CardBody>
        </Card>
      </VStack>

      {/* View Order Modal */}
      <Modal isOpen={isViewOpen} onClose={onViewClose} size="xl">
        <ModalOverlay />
        <ModalContent>
          <ModalHeader>Detalles del Pedido</ModalHeader>
          <ModalCloseButton />
          <ModalBody>
            {selectedOrder && (
              <VStack spacing={4} align="stretch">
                {/* Order Header */}
                <HStack justify="space-between">
                  <Box>
                    <Text fontSize="lg" fontWeight="bold">
                      Pedido #{selectedOrder.id.slice(0, 8)}
                    </Text>
                    <Text color="gray.600">{formatDate(selectedOrder.created_at)}</Text>
                  </Box>
                  <Badge 
                    colorScheme={getStatusBadge(selectedOrder.status).color}
                    fontSize="md"
                    p={2}
                  >
                    {getStatusBadge(selectedOrder.status).text}
                  </Badge>
                </HStack>

                <Divider />

                {/* Customer Info */}
                <Box>
                  <Text fontWeight="bold" mb={2}>Información del Cliente</Text>
                  <Text>Nombre: {selectedOrder.customer_name || "No disponible"}</Text>
                  <Text>Email: {selectedOrder.customer_email || "No disponible"}</Text>
                  <Text>ID Usuario: {selectedOrder.user_id}</Text>
                </Box>

                {/* Shipping Address */}
                {selectedOrder.shipping_address && (
                  <Box>
                    <Text fontWeight="bold" mb={2}>Dirección de Envío</Text>
                    <Text>{selectedOrder.shipping_address.street}</Text>
                    <Text>
                      {selectedOrder.shipping_address.city}, {selectedOrder.shipping_address.state} {selectedOrder.shipping_address.postal_code}
                    </Text>
                    <Text>{selectedOrder.shipping_address.country}</Text>
                  </Box>
                )}

                <Divider />

                {/* Order Items */}
                <Box>
                  <Text fontWeight="bold" mb={2}>Productos</Text>
                  <List spacing={2}>
                    {selectedOrder.items.map((item) => (
                      <ListItem key={item.id}>
                        <HStack justify="space-between">
                          <HStack>
                            <Text>{item.product_name}</Text>
                            <Tag size="sm">x{item.quantity}</Tag>
                          </HStack>
                          <HStack>
                            <Text>{formatPrice(item.price)}</Text>
                            <Text fontWeight="bold">{formatPrice(item.subtotal)}</Text>
                          </HStack>
                        </HStack>
                      </ListItem>
                    ))}
                  </List>
                </Box>

                <Divider />

                {/* Order Total */}
                <HStack justify="space-between">
                  <Text fontSize="lg" fontWeight="bold">Total:</Text>
                  <Text fontSize="xl" fontWeight="bold" color="green.500">
                    {formatPrice(selectedOrder.total_amount)}
                  </Text>
                </HStack>
              </VStack>
            )}
          </ModalBody>
          <ModalFooter>
            <Button onClick={onViewClose}>Cerrar</Button>
          </ModalFooter>
        </ModalContent>
      </Modal>

      {/* Edit Order Status Modal */}
      <Modal isOpen={isEditOpen} onClose={onEditClose}>
        <ModalOverlay />
        <ModalContent>
          <ModalHeader>Actualizar Estado del Pedido</ModalHeader>
          <ModalCloseButton />
          <ModalBody>
            {selectedOrder && (
              <VStack spacing={4}>
                <Box w="full">
                  <Text fontWeight="medium" mb={2}>
                    Pedido #{selectedOrder.id.slice(0, 8)}
                  </Text>
                  <Text color="gray.600" mb={4}>
                    Total: {formatPrice(selectedOrder.total_amount)}
                  </Text>
                </Box>
                
                <Box w="full">
                  <Text fontWeight="medium" mb={2}>Nuevo Estado:</Text>
                  <Select
                    value={editStatus}
                    onChange={(e) => setEditStatus(e.target.value)}
                  >
                    {statusOptions.map(status => (
                      <option key={status.value} value={status.value}>
                        {status.label}
                      </option>
                    ))}
                  </Select>
                </Box>
              </VStack>
            )}
          </ModalBody>
          <ModalFooter>
            <Button variant="ghost" mr={3} onClick={onEditClose}>
              Cancelar
            </Button>
            <Button colorScheme="blue" onClick={handleUpdateOrderStatus}>
              Actualizar Estado
            </Button>
          </ModalFooter>
        </ModalContent>
      </Modal>
    </Box>
  )
}

export default OrderManagement