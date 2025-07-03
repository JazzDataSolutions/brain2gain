import {
  Badge,
  Box,
  Button,
  Card,
  CardBody,
  HStack,
  Heading,
  Input,
  InputGroup,
  InputLeftElement,
  Select,
  Table,
  TableContainer,
  Tbody,
  Td,
  Text,
  Th,
  Thead,
  Tr,
  VStack,
  useColorModeValue,
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
  FormControl,
  FormLabel,
  useToast,
  Flex,
  Avatar,
  IconButton,
} from "@chakra-ui/react"
import { useState, useEffect } from "react"
import { FiSearch, FiUserPlus, FiUsers, FiStar, FiEdit, FiTrash2, FiEye } from "react-icons/fi"
import { UsersService } from "../../client"

interface Customer {
  id: string
  email: string
  full_name: string | null
  is_active: boolean
  is_superuser: boolean
  created_at: string
  last_login?: string
}

interface CustomerStats {
  total_customers: number
  new_this_month: number
  vip_customers: number
}

const CustomerManagement = () => {
  const cardBg = useColorModeValue("white", "gray.800")
  const [customers, setCustomers] = useState<Customer[]>([])
  const [filteredCustomers, setFilteredCustomers] = useState<Customer[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [searchTerm, setSearchTerm] = useState("")
  const [filterStatus, setFilterStatus] = useState<string>("all")
  const [stats, setStats] = useState<CustomerStats>({
    total_customers: 0,
    new_this_month: 0,
    vip_customers: 0
  })

  // Modal states
  const { isOpen: isCreateOpen, onOpen: onCreateOpen, onClose: onCreateClose } = useDisclosure()
  const { isOpen: isEditOpen, onOpen: onEditOpen, onClose: onEditClose } = useDisclosure()
  const { isOpen: isViewOpen, onOpen: onViewOpen, onClose: onViewClose } = useDisclosure()
  
  const [selectedCustomer, setSelectedCustomer] = useState<Customer | null>(null)
  const [formData, setFormData] = useState({
    email: "",
    full_name: "",
    password: "",
    is_active: true,
    is_superuser: false
  })

  const toast = useToast()

  // Fetch customers data
  const fetchCustomers = async () => {
    try {
      setLoading(true)
      setError(null)
      
      // Get all users (customers)
      const response = await UsersService.readUsers({
        skip: 0,
        limit: 1000
      })
      
      setCustomers(response)
      setFilteredCustomers(response)
      
      // Calculate stats
      const now = new Date()
      const thisMonth = new Date(now.getFullYear(), now.getMonth(), 1)
      
      const newThisMonth = response.filter(customer => 
        new Date(customer.created_at) >= thisMonth
      ).length
      
      const vipCustomers = response.filter(customer => 
        customer.is_superuser || customer.full_name?.includes("VIP")
      ).length

      setStats({
        total_customers: response.length,
        new_this_month: newThisMonth,
        vip_customers: vipCustomers
      })
      
    } catch (err: any) {
      setError(err.message || "Error al cargar clientes")
      console.error("Error fetching customers:", err)
    } finally {
      setLoading(false)
    }
  }

  // Filter customers based on search and status
  useEffect(() => {
    let filtered = customers
    
    // Search filter
    if (searchTerm) {
      filtered = filtered.filter(customer =>
        customer.email.toLowerCase().includes(searchTerm.toLowerCase()) ||
        customer.full_name?.toLowerCase().includes(searchTerm.toLowerCase())
      )
    }
    
    // Status filter
    if (filterStatus !== "all") {
      if (filterStatus === "active") {
        filtered = filtered.filter(customer => customer.is_active)
      } else if (filterStatus === "inactive") {
        filtered = filtered.filter(customer => !customer.is_active)
      } else if (filterStatus === "vip") {
        filtered = filtered.filter(customer => customer.is_superuser)
      }
    }
    
    setFilteredCustomers(filtered)
  }, [customers, searchTerm, filterStatus])

  useEffect(() => {
    fetchCustomers()
  }, [])

  // Handle create customer
  const handleCreateCustomer = async () => {
    try {
      const newCustomer = await UsersService.createUser({
        requestBody: {
          email: formData.email,
          full_name: formData.full_name || null,
          password: formData.password,
          is_active: formData.is_active,
          is_superuser: formData.is_superuser
        }
      })
      
      await fetchCustomers() // Refresh data
      onCreateClose()
      setFormData({ email: "", full_name: "", password: "", is_active: true, is_superuser: false })
      
      toast({
        title: "Cliente creado",
        description: "El cliente ha sido creado exitosamente",
        status: "success",
        duration: 3000,
        isClosable: true,
      })
    } catch (err: any) {
      toast({
        title: "Error",
        description: err.message || "Error al crear cliente",
        status: "error",
        duration: 5000,
        isClosable: true,
      })
    }
  }

  // Handle edit customer
  const handleEditCustomer = async () => {
    if (!selectedCustomer) return
    
    try {
      await UsersService.updateUser({
        userId: selectedCustomer.id,
        requestBody: {
          email: formData.email,
          full_name: formData.full_name || null,
          is_active: formData.is_active,
          is_superuser: formData.is_superuser
        }
      })
      
      await fetchCustomers() // Refresh data
      onEditClose()
      
      toast({
        title: "Cliente actualizado",
        description: "Los datos del cliente han sido actualizados",
        status: "success",
        duration: 3000,
        isClosable: true,
      })
    } catch (err: any) {
      toast({
        title: "Error",
        description: err.message || "Error al actualizar cliente",
        status: "error",
        duration: 5000,
        isClosable: true,
      })
    }
  }

  // Handle delete customer
  const handleDeleteCustomer = async (customerId: string) => {
    if (!confirm("¿Estás seguro de que quieres eliminar este cliente?")) return
    
    try {
      await UsersService.deleteUser({ userId: customerId })
      await fetchCustomers() // Refresh data
      
      toast({
        title: "Cliente eliminado",
        description: "El cliente ha sido eliminado exitosamente",
        status: "success",
        duration: 3000,
        isClosable: true,
      })
    } catch (err: any) {
      toast({
        title: "Error",
        description: err.message || "Error al eliminar cliente",
        status: "error",
        duration: 5000,
        isClosable: true,
      })
    }
  }

  // Open edit modal
  const openEditModal = (customer: Customer) => {
    setSelectedCustomer(customer)
    setFormData({
      email: customer.email,
      full_name: customer.full_name || "",
      password: "",
      is_active: customer.is_active,
      is_superuser: customer.is_superuser
    })
    onEditOpen()
  }

  // Open view modal
  const openViewModal = (customer: Customer) => {
    setSelectedCustomer(customer)
    onViewOpen()
  }

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString("es-ES", {
      year: "numeric",
      month: "short",
      day: "numeric"
    })
  }

  return (
    <Box w="full">
      <VStack spacing={6} align="stretch">
        {/* Header */}
        <Flex justify="space-between" align="center">
          <Box>
            <Heading size="lg" mb={2}>
              Gestión de Clientes
            </Heading>
            <Text color="gray.600">CRM y gestión de relaciones con clientes</Text>
          </Box>
          <Button 
            leftIcon={<FiUserPlus />} 
            colorScheme="blue" 
            onClick={onCreateOpen}
          >
            Nuevo Cliente
          </Button>
        </Flex>

        {/* Quick Stats */}
        <HStack spacing={4}>
          <Card bg={cardBg} flex={1}>
            <CardBody>
              <HStack>
                <Box bg="purple.100" p={3} rounded="lg">
                  <FiUsers color="purple" size={24} />
                </Box>
                <Box>
                  <Text fontSize="2xl" fontWeight="bold">
                    {stats.total_customers}
                  </Text>
                  <Text fontSize="sm" color="gray.600">
                    Total Clientes
                  </Text>
                </Box>
              </HStack>
            </CardBody>
          </Card>

          <Card bg={cardBg} flex={1}>
            <CardBody>
              <HStack>
                <Box bg="green.100" p={3} rounded="lg">
                  <FiUserPlus color="green" size={24} />
                </Box>
                <Box>
                  <Text fontSize="2xl" fontWeight="bold" color="green.500">
                    {stats.new_this_month}
                  </Text>
                  <Text fontSize="sm" color="gray.600">
                    Nuevos Este Mes
                  </Text>
                </Box>
              </HStack>
            </CardBody>
          </Card>

          <Card bg={cardBg} flex={1}>
            <CardBody>
              <HStack>
                <Box bg="yellow.100" p={3} rounded="lg">
                  <FiStar color="orange" size={24} />
                </Box>
                <Box>
                  <Text fontSize="2xl" fontWeight="bold" color="yellow.500">
                    {stats.vip_customers}
                  </Text>
                  <Text fontSize="sm" color="gray.600">
                    Clientes VIP
                  </Text>
                </Box>
              </HStack>
            </CardBody>
          </Card>
        </HStack>

        {/* Filters */}
        <Card bg={cardBg}>
          <CardBody>
            <HStack spacing={4}>
              <InputGroup flex={1}>
                <InputLeftElement>
                  <FiSearch color="gray" />
                </InputLeftElement>
                <Input
                  placeholder="Buscar por email o nombre..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                />
              </InputGroup>
              <Select
                value={filterStatus}
                onChange={(e) => setFilterStatus(e.target.value)}
                w="200px"
              >
                <option value="all">Todos los clientes</option>
                <option value="active">Activos</option>
                <option value="inactive">Inactivos</option>
                <option value="vip">VIP/Admin</option>
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
                      <Th>Cliente</Th>
                      <Th>Email</Th>
                      <Th>Estado</Th>
                      <Th>Tipo</Th>
                      <Th>Registro</Th>
                      <Th>Acciones</Th>
                    </Tr>
                  </Thead>
                  <Tbody>
                    {filteredCustomers.map((customer) => (
                      <Tr key={customer.id}>
                        <Td>
                          <HStack>
                            <Avatar size="sm" name={customer.full_name || customer.email} />
                            <Box>
                              <Text fontWeight="medium">
                                {customer.full_name || "Sin nombre"}
                              </Text>
                              <Text fontSize="sm" color="gray.500">
                                ID: {customer.id.slice(0, 8)}...
                              </Text>
                            </Box>
                          </HStack>
                        </Td>
                        <Td>{customer.email}</Td>
                        <Td>
                          <Badge colorScheme={customer.is_active ? "green" : "red"}>
                            {customer.is_active ? "Activo" : "Inactivo"}
                          </Badge>
                        </Td>
                        <Td>
                          <Badge colorScheme={customer.is_superuser ? "purple" : "gray"}>
                            {customer.is_superuser ? "Admin" : "Cliente"}
                          </Badge>
                        </Td>
                        <Td>{formatDate(customer.created_at)}</Td>
                        <Td>
                          <HStack spacing={1}>
                            <IconButton
                              aria-label="Ver detalles"
                              icon={<FiEye />}
                              size="sm"
                              variant="ghost"
                              onClick={() => openViewModal(customer)}
                            />
                            <IconButton
                              aria-label="Editar cliente"
                              icon={<FiEdit />}
                              size="sm"
                              variant="ghost"
                              onClick={() => openEditModal(customer)}
                            />
                            <IconButton
                              aria-label="Eliminar cliente"
                              icon={<FiTrash2 />}
                              size="sm"
                              variant="ghost"
                              colorScheme="red"
                              onClick={() => handleDeleteCustomer(customer.id)}
                            />
                          </HStack>
                        </Td>
                      </Tr>
                    ))}
                  </Tbody>
                </Table>
                {filteredCustomers.length === 0 && (
                  <Box textAlign="center" py={8}>
                    <Text color="gray.500">No se encontraron clientes</Text>
                  </Box>
                )}
              </TableContainer>
            )}
          </CardBody>
        </Card>
      </VStack>

      {/* Create Customer Modal */}
      <Modal isOpen={isCreateOpen} onClose={onCreateClose}>
        <ModalOverlay />
        <ModalContent>
          <ModalHeader>Crear Nuevo Cliente</ModalHeader>
          <ModalCloseButton />
          <ModalBody>
            <VStack spacing={4}>
              <FormControl isRequired>
                <FormLabel>Email</FormLabel>
                <Input
                  type="email"
                  value={formData.email}
                  onChange={(e) => setFormData({...formData, email: e.target.value})}
                  placeholder="cliente@ejemplo.com"
                />
              </FormControl>
              <FormControl>
                <FormLabel>Nombre Completo</FormLabel>
                <Input
                  value={formData.full_name}
                  onChange={(e) => setFormData({...formData, full_name: e.target.value})}
                  placeholder="Nombre completo del cliente"
                />
              </FormControl>
              <FormControl isRequired>
                <FormLabel>Contraseña</FormLabel>
                <Input
                  type="password"
                  value={formData.password}
                  onChange={(e) => setFormData({...formData, password: e.target.value})}
                  placeholder="Contraseña del cliente"
                />
              </FormControl>
            </VStack>
          </ModalBody>
          <ModalFooter>
            <Button variant="ghost" mr={3} onClick={onCreateClose}>
              Cancelar
            </Button>
            <Button colorScheme="blue" onClick={handleCreateCustomer}>
              Crear Cliente
            </Button>
          </ModalFooter>
        </ModalContent>
      </Modal>

      {/* Edit Customer Modal */}
      <Modal isOpen={isEditOpen} onClose={onEditClose}>
        <ModalOverlay />
        <ModalContent>
          <ModalHeader>Editar Cliente</ModalHeader>
          <ModalCloseButton />
          <ModalBody>
            <VStack spacing={4}>
              <FormControl isRequired>
                <FormLabel>Email</FormLabel>
                <Input
                  type="email"
                  value={formData.email}
                  onChange={(e) => setFormData({...formData, email: e.target.value})}
                />
              </FormControl>
              <FormControl>
                <FormLabel>Nombre Completo</FormLabel>
                <Input
                  value={formData.full_name}
                  onChange={(e) => setFormData({...formData, full_name: e.target.value})}
                />
              </FormControl>
              <FormControl>
                <FormLabel>Estado</FormLabel>
                <Select
                  value={formData.is_active ? "active" : "inactive"}
                  onChange={(e) => setFormData({...formData, is_active: e.target.value === "active"})}
                >
                  <option value="active">Activo</option>
                  <option value="inactive">Inactivo</option>
                </Select>
              </FormControl>
              <FormControl>
                <FormLabel>Tipo de Usuario</FormLabel>
                <Select
                  value={formData.is_superuser ? "admin" : "customer"}
                  onChange={(e) => setFormData({...formData, is_superuser: e.target.value === "admin"})}
                >
                  <option value="customer">Cliente</option>
                  <option value="admin">Administrador</option>
                </Select>
              </FormControl>
            </VStack>
          </ModalBody>
          <ModalFooter>
            <Button variant="ghost" mr={3} onClick={onEditClose}>
              Cancelar
            </Button>
            <Button colorScheme="blue" onClick={handleEditCustomer}>
              Guardar Cambios
            </Button>
          </ModalFooter>
        </ModalContent>
      </Modal>

      {/* View Customer Modal */}
      <Modal isOpen={isViewOpen} onClose={onViewClose}>
        <ModalOverlay />
        <ModalContent>
          <ModalHeader>Detalles del Cliente</ModalHeader>
          <ModalCloseButton />
          <ModalBody>
            {selectedCustomer && (
              <VStack spacing={4} align="stretch">
                <HStack>
                  <Avatar size="lg" name={selectedCustomer.full_name || selectedCustomer.email} />
                  <Box>
                    <Text fontWeight="bold" fontSize="lg">
                      {selectedCustomer.full_name || "Sin nombre"}
                    </Text>
                    <Text color="gray.600">{selectedCustomer.email}</Text>
                  </Box>
                </HStack>
                <Box>
                  <Text fontWeight="medium">ID del Cliente:</Text>
                  <Text color="gray.600">{selectedCustomer.id}</Text>
                </Box>
                <HStack justify="space-between">
                  <Box>
                    <Text fontWeight="medium">Estado:</Text>
                    <Badge colorScheme={selectedCustomer.is_active ? "green" : "red"}>
                      {selectedCustomer.is_active ? "Activo" : "Inactivo"}
                    </Badge>
                  </Box>
                  <Box>
                    <Text fontWeight="medium">Tipo:</Text>
                    <Badge colorScheme={selectedCustomer.is_superuser ? "purple" : "gray"}>
                      {selectedCustomer.is_superuser ? "Administrador" : "Cliente"}
                    </Badge>
                  </Box>
                </HStack>
                <Box>
                  <Text fontWeight="medium">Fecha de Registro:</Text>
                  <Text color="gray.600">{formatDate(selectedCustomer.created_at)}</Text>
                </Box>
                {selectedCustomer.last_login && (
                  <Box>
                    <Text fontWeight="medium">Último Acceso:</Text>
                    <Text color="gray.600">{formatDate(selectedCustomer.last_login)}</Text>
                  </Box>
                )}
              </VStack>
            )}
          </ModalBody>
          <ModalFooter>
            <Button onClick={onViewClose}>Cerrar</Button>
          </ModalFooter>
        </ModalContent>
      </Modal>
    </Box>
  )
}

export default CustomerManagement