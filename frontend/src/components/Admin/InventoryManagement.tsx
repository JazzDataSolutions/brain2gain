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
  FormControl,
  FormLabel,
  useToast,
  Flex,
  Image,
  IconButton,
  NumberInput,
  NumberInputField,
  NumberInputStepper,
  NumberIncrementStepper,
  NumberDecrementStepper,
  Textarea,
} from "@chakra-ui/react"
import { useState, useEffect } from "react"
import { FiSearch, FiPlus, FiPackage, FiAlertTriangle, FiEdit, FiTrash2, FiEye } from "react-icons/fi"
import { ProductsService } from "../../client"

interface Product {
  id: string
  name: string
  description: string | null
  price: number
  stock: number
  category: string | null
  status: "active" | "inactive" | "draft"
  created_at: string
  updated_at: string
  image_url?: string
}

interface ProductStats {
  total_products: number
  low_stock_products: number
  active_products: number
  draft_products: number
}

const InventoryManagement = () => {
  const cardBg = useColorModeValue("white", "gray.800")
  const [products, setProducts] = useState<Product[]>([])
  const [filteredProducts, setFilteredProducts] = useState<Product[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [searchTerm, setSearchTerm] = useState("")
  const [filterStatus, setFilterStatus] = useState<string>("all")
  const [filterCategory, setFilterCategory] = useState<string>("all")
  const [stats, setStats] = useState<ProductStats>({
    total_products: 0,
    low_stock_products: 0,
    active_products: 0,
    draft_products: 0
  })

  // Modal states
  const { isOpen: isCreateOpen, onOpen: onCreateOpen, onClose: onCreateClose } = useDisclosure()
  const { isOpen: isEditOpen, onOpen: onEditOpen, onClose: onEditClose } = useDisclosure()
  const { isOpen: isViewOpen, onOpen: onViewOpen, onClose: onViewClose } = useDisclosure()
  
  const [selectedProduct, setSelectedProduct] = useState<Product | null>(null)
  const [formData, setFormData] = useState({
    name: "",
    description: "",
    price: 0,
    stock: 0,
    category: "",
    status: "active" as "active" | "inactive" | "draft",
    image_url: ""
  })

  const toast = useToast()

  // Categories for select dropdown
  const categories = [
    "Proteínas",
    "Creatinas", 
    "Pre-entrenos",
    "Vitaminas",
    "Aminoácidos",
    "Quemadores",
    "Ganadores de masa",
    "Otros"
  ]

  // Fetch products data
  const fetchProducts = async () => {
    try {
      setLoading(true)
      setError(null)
      
      // Get all products (admin can see all statuses)
      const response = await ProductsService.readProducts({
        skip: 0,
        limit: 1000
      })
      
      setProducts(response)
      setFilteredProducts(response)
      
      // Calculate stats
      const lowStockThreshold = 10
      const lowStockProducts = response.filter(product => product.stock <= lowStockThreshold).length
      const activeProducts = response.filter(product => product.status === "active").length
      const draftProducts = response.filter(product => product.status === "draft").length

      setStats({
        total_products: response.length,
        low_stock_products: lowStockProducts,
        active_products: activeProducts,
        draft_products: draftProducts
      })
      
    } catch (err: any) {
      setError(err.message || "Error al cargar productos")
      console.error("Error fetching products:", err)
    } finally {
      setLoading(false)
    }
  }

  // Filter products based on search, status and category
  useEffect(() => {
    let filtered = products
    
    // Search filter
    if (searchTerm) {
      filtered = filtered.filter(product =>
        product.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        product.description?.toLowerCase().includes(searchTerm.toLowerCase()) ||
        product.category?.toLowerCase().includes(searchTerm.toLowerCase())
      )
    }
    
    // Status filter
    if (filterStatus !== "all") {
      filtered = filtered.filter(product => product.status === filterStatus)
    }
    
    // Category filter
    if (filterCategory !== "all") {
      filtered = filtered.filter(product => product.category === filterCategory)
    }
    
    setFilteredProducts(filtered)
  }, [products, searchTerm, filterStatus, filterCategory])

  useEffect(() => {
    fetchProducts()
  }, [])

  // Handle create product
  const handleCreateProduct = async () => {
    try {
      await ProductsService.createProduct({
        requestBody: {
          name: formData.name,
          description: formData.description || null,
          price: formData.price,
          stock: formData.stock,
          category: formData.category || null,
          status: formData.status,
          image_url: formData.image_url || null
        }
      })
      
      await fetchProducts() // Refresh data
      onCreateClose()
      setFormData({ 
        name: "", 
        description: "", 
        price: 0, 
        stock: 0, 
        category: "", 
        status: "active",
        image_url: ""
      })
      
      toast({
        title: "Producto creado",
        description: "El producto ha sido creado exitosamente",
        status: "success",
        duration: 3000,
        isClosable: true,
      })
    } catch (err: any) {
      toast({
        title: "Error",
        description: err.message || "Error al crear producto",
        status: "error",
        duration: 5000,
        isClosable: true,
      })
    }
  }

  // Handle edit product
  const handleEditProduct = async () => {
    if (!selectedProduct) return
    
    try {
      await ProductsService.updateProduct({
        productId: selectedProduct.id,
        requestBody: {
          name: formData.name,
          description: formData.description || null,
          price: formData.price,
          stock: formData.stock,
          category: formData.category || null,
          status: formData.status,
          image_url: formData.image_url || null
        }
      })
      
      await fetchProducts() // Refresh data
      onEditClose()
      
      toast({
        title: "Producto actualizado",
        description: "Los datos del producto han sido actualizados",
        status: "success",
        duration: 3000,
        isClosable: true,
      })
    } catch (err: any) {
      toast({
        title: "Error",
        description: err.message || "Error al actualizar producto",
        status: "error",
        duration: 5000,
        isClosable: true,
      })
    }
  }

  // Handle delete product
  const handleDeleteProduct = async (productId: string) => {
    if (!confirm("¿Estás seguro de que quieres eliminar este producto?")) return
    
    try {
      await ProductsService.deleteProduct({ productId })
      await fetchProducts() // Refresh data
      
      toast({
        title: "Producto eliminado",
        description: "El producto ha sido eliminado exitosamente",
        status: "success",
        duration: 3000,
        isClosable: true,
      })
    } catch (err: any) {
      toast({
        title: "Error",
        description: err.message || "Error al eliminar producto",
        status: "error",
        duration: 5000,
        isClosable: true,
      })
    }
  }

  // Open edit modal
  const openEditModal = (product: Product) => {
    setSelectedProduct(product)
    setFormData({
      name: product.name,
      description: product.description || "",
      price: product.price,
      stock: product.stock,
      category: product.category || "",
      status: product.status,
      image_url: product.image_url || ""
    })
    onEditOpen()
  }

  // Open view modal
  const openViewModal = (product: Product) => {
    setSelectedProduct(product)
    onViewOpen()
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
      day: "numeric"
    })
  }

  const getStockStatus = (stock: number) => {
    if (stock === 0) return { color: "red", text: "Sin stock" }
    if (stock <= 10) return { color: "orange", text: "Stock bajo" }
    if (stock <= 50) return { color: "yellow", text: "Stock medio" }
    return { color: "green", text: "Stock alto" }
  }

  return (
    <Box w="full">
      <VStack spacing={6} align="stretch">
        {/* Header */}
        <Flex justify="space-between" align="center">
          <Box>
            <Heading size="lg" mb={2}>
              Gestión de Inventario
            </Heading>
            <Text color="gray.600">Control de stock y productos</Text>
          </Box>
          <Button 
            leftIcon={<FiPlus />} 
            colorScheme="blue" 
            onClick={onCreateOpen}
          >
            Nuevo Producto
          </Button>
        </Flex>

        {/* Quick Stats */}
        <HStack spacing={4}>
          <Card bg={cardBg} flex={1}>
            <CardBody>
              <HStack>
                <Box bg="blue.100" p={3} rounded="lg">
                  <FiPackage color="blue" size={24} />
                </Box>
                <Box>
                  <Text fontSize="2xl" fontWeight="bold">
                    {stats.total_products}
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
                  <FiAlertTriangle color="red" size={24} />
                </Box>
                <Box>
                  <Text fontSize="2xl" fontWeight="bold" color="red.500">
                    {stats.low_stock_products}
                  </Text>
                  <Text fontSize="sm" color="gray.600">
                    Stock Bajo
                  </Text>
                </Box>
              </HStack>
            </CardBody>
          </Card>

          <Card bg={cardBg} flex={1}>
            <CardBody>
              <HStack>
                <Box bg="green.100" p={3} rounded="lg">
                  <FiPackage color="green" size={24} />
                </Box>
                <Box>
                  <Text fontSize="2xl" fontWeight="bold" color="green.500">
                    {stats.active_products}
                  </Text>
                  <Text fontSize="sm" color="gray.600">
                    Activos
                  </Text>
                </Box>
              </HStack>
            </CardBody>
          </Card>

          <Card bg={cardBg} flex={1}>
            <CardBody>
              <HStack>
                <Box bg="yellow.100" p={3} rounded="lg">
                  <FiPackage color="orange" size={24} />
                </Box>
                <Box>
                  <Text fontSize="2xl" fontWeight="bold" color="yellow.500">
                    {stats.draft_products}
                  </Text>
                  <Text fontSize="sm" color="gray.600">
                    Borradores
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
                  placeholder="Buscar productos..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                />
              </InputGroup>
              <Select
                value={filterStatus}
                onChange={(e) => setFilterStatus(e.target.value)}
                w="150px"
              >
                <option value="all">Todos</option>
                <option value="active">Activos</option>
                <option value="inactive">Inactivos</option>
                <option value="draft">Borradores</option>
              </Select>
              <Select
                value={filterCategory}
                onChange={(e) => setFilterCategory(e.target.value)}
                w="200px"
              >
                <option value="all">Todas las categorías</option>
                {categories.map(category => (
                  <option key={category} value={category}>{category}</option>
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
                      <Th>Producto</Th>
                      <Th>Precio</Th>
                      <Th>Stock</Th>
                      <Th>Categoría</Th>
                      <Th>Estado</Th>
                      <Th>Actualizado</Th>
                      <Th>Acciones</Th>
                    </Tr>
                  </Thead>
                  <Tbody>
                    {filteredProducts.map((product) => {
                      const stockStatus = getStockStatus(product.stock)
                      return (
                        <Tr key={product.id}>
                          <Td>
                            <HStack>
                              <Image
                                src={product.image_url || "/api/placeholder/40/40"}
                                alt={product.name}
                                boxSize="40px"
                                objectFit="cover"
                                rounded="md"
                                fallbackSrc="/api/placeholder/40/40"
                              />
                              <Box>
                                <Text fontWeight="medium">
                                  {product.name}
                                </Text>
                                <Text fontSize="sm" color="gray.500" noOfLines={1}>
                                  {product.description || "Sin descripción"}
                                </Text>
                              </Box>
                            </HStack>
                          </Td>
                          <Td fontWeight="medium">{formatPrice(product.price)}</Td>
                          <Td>
                            <Badge colorScheme={stockStatus.color}>
                              {product.stock} unidades
                            </Badge>
                          </Td>
                          <Td>{product.category || "Sin categoría"}</Td>
                          <Td>
                            <Badge 
                              colorScheme={
                                product.status === "active" ? "green" : 
                                product.status === "draft" ? "yellow" : "red"
                              }
                            >
                              {product.status === "active" ? "Activo" : 
                               product.status === "draft" ? "Borrador" : "Inactivo"}
                            </Badge>
                          </Td>
                          <Td>{formatDate(product.updated_at)}</Td>
                          <Td>
                            <HStack spacing={1}>
                              <IconButton
                                aria-label="Ver detalles"
                                icon={<FiEye />}
                                size="sm"
                                variant="ghost"
                                onClick={() => openViewModal(product)}
                              />
                              <IconButton
                                aria-label="Editar producto"
                                icon={<FiEdit />}
                                size="sm"
                                variant="ghost"
                                onClick={() => openEditModal(product)}
                              />
                              <IconButton
                                aria-label="Eliminar producto"
                                icon={<FiTrash2 />}
                                size="sm"
                                variant="ghost"
                                colorScheme="red"
                                onClick={() => handleDeleteProduct(product.id)}
                              />
                            </HStack>
                          </Td>
                        </Tr>
                      )
                    })}
                  </Tbody>
                </Table>
                {filteredProducts.length === 0 && (
                  <Box textAlign="center" py={8}>
                    <Text color="gray.500">No se encontraron productos</Text>
                  </Box>
                )}
              </TableContainer>
            )}
          </CardBody>
        </Card>
      </VStack>

      {/* Create Product Modal */}
      <Modal isOpen={isCreateOpen} onClose={onCreateClose} size="lg">
        <ModalOverlay />
        <ModalContent>
          <ModalHeader>Crear Nuevo Producto</ModalHeader>
          <ModalCloseButton />
          <ModalBody>
            <VStack spacing={4}>
              <FormControl isRequired>
                <FormLabel>Nombre del Producto</FormLabel>
                <Input
                  value={formData.name}
                  onChange={(e) => setFormData({...formData, name: e.target.value})}
                  placeholder="Nombre del producto"
                />
              </FormControl>
              
              <FormControl>
                <FormLabel>Descripción</FormLabel>
                <Textarea
                  value={formData.description}
                  onChange={(e) => setFormData({...formData, description: e.target.value})}
                  placeholder="Descripción del producto"
                  rows={3}
                />
              </FormControl>

              <HStack w="full">
                <FormControl isRequired>
                  <FormLabel>Precio</FormLabel>
                  <NumberInput
                    value={formData.price}
                    onChange={(valueString, valueNumber) => 
                      setFormData({...formData, price: valueNumber || 0})
                    }
                    min={0}
                    precision={2}
                  >
                    <NumberInputField placeholder="0.00" />
                    <NumberInputStepper>
                      <NumberIncrementStepper />
                      <NumberDecrementStepper />
                    </NumberInputStepper>
                  </NumberInput>
                </FormControl>

                <FormControl isRequired>
                  <FormLabel>Stock</FormLabel>
                  <NumberInput
                    value={formData.stock}
                    onChange={(valueString, valueNumber) => 
                      setFormData({...formData, stock: valueNumber || 0})
                    }
                    min={0}
                  >
                    <NumberInputField placeholder="0" />
                    <NumberInputStepper>
                      <NumberIncrementStepper />
                      <NumberDecrementStepper />
                    </NumberInputStepper>
                  </NumberInput>
                </FormControl>
              </HStack>

              <HStack w="full">
                <FormControl>
                  <FormLabel>Categoría</FormLabel>
                  <Select
                    value={formData.category}
                    onChange={(e) => setFormData({...formData, category: e.target.value})}
                    placeholder="Seleccionar categoría"
                  >
                    {categories.map(category => (
                      <option key={category} value={category}>{category}</option>
                    ))}
                  </Select>
                </FormControl>

                <FormControl>
                  <FormLabel>Estado</FormLabel>
                  <Select
                    value={formData.status}
                    onChange={(e) => setFormData({...formData, status: e.target.value as any})}
                  >
                    <option value="active">Activo</option>
                    <option value="draft">Borrador</option>
                    <option value="inactive">Inactivo</option>
                  </Select>
                </FormControl>
              </HStack>

              <FormControl>
                <FormLabel>URL de Imagen</FormLabel>
                <Input
                  value={formData.image_url}
                  onChange={(e) => setFormData({...formData, image_url: e.target.value})}
                  placeholder="https://ejemplo.com/imagen.jpg"
                />
              </FormControl>
            </VStack>
          </ModalBody>
          <ModalFooter>
            <Button variant="ghost" mr={3} onClick={onCreateClose}>
              Cancelar
            </Button>
            <Button colorScheme="blue" onClick={handleCreateProduct}>
              Crear Producto
            </Button>
          </ModalFooter>
        </ModalContent>
      </Modal>

      {/* Edit Product Modal */}
      <Modal isOpen={isEditOpen} onClose={onEditClose} size="lg">
        <ModalOverlay />
        <ModalContent>
          <ModalHeader>Editar Producto</ModalHeader>
          <ModalCloseButton />
          <ModalBody>
            <VStack spacing={4}>
              <FormControl isRequired>
                <FormLabel>Nombre del Producto</FormLabel>
                <Input
                  value={formData.name}
                  onChange={(e) => setFormData({...formData, name: e.target.value})}
                />
              </FormControl>
              
              <FormControl>
                <FormLabel>Descripción</FormLabel>
                <Textarea
                  value={formData.description}
                  onChange={(e) => setFormData({...formData, description: e.target.value})}
                  rows={3}
                />
              </FormControl>

              <HStack w="full">
                <FormControl isRequired>
                  <FormLabel>Precio</FormLabel>
                  <NumberInput
                    value={formData.price}
                    onChange={(valueString, valueNumber) => 
                      setFormData({...formData, price: valueNumber || 0})
                    }
                    min={0}
                    precision={2}
                  >
                    <NumberInputField />
                    <NumberInputStepper>
                      <NumberIncrementStepper />
                      <NumberDecrementStepper />
                    </NumberInputStepper>
                  </NumberInput>
                </FormControl>

                <FormControl isRequired>
                  <FormLabel>Stock</FormLabel>
                  <NumberInput
                    value={formData.stock}
                    onChange={(valueString, valueNumber) => 
                      setFormData({...formData, stock: valueNumber || 0})
                    }
                    min={0}
                  >
                    <NumberInputField />
                    <NumberInputStepper>
                      <NumberIncrementStepper />
                      <NumberDecrementStepper />
                    </NumberInputStepper>
                  </NumberInput>
                </FormControl>
              </HStack>

              <HStack w="full">
                <FormControl>
                  <FormLabel>Categoría</FormLabel>
                  <Select
                    value={formData.category}
                    onChange={(e) => setFormData({...formData, category: e.target.value})}
                  >
                    <option value="">Sin categoría</option>
                    {categories.map(category => (
                      <option key={category} value={category}>{category}</option>
                    ))}
                  </Select>
                </FormControl>

                <FormControl>
                  <FormLabel>Estado</FormLabel>
                  <Select
                    value={formData.status}
                    onChange={(e) => setFormData({...formData, status: e.target.value as any})}
                  >
                    <option value="active">Activo</option>
                    <option value="draft">Borrador</option>
                    <option value="inactive">Inactivo</option>
                  </Select>
                </FormControl>
              </HStack>

              <FormControl>
                <FormLabel>URL de Imagen</FormLabel>
                <Input
                  value={formData.image_url}
                  onChange={(e) => setFormData({...formData, image_url: e.target.value})}
                />
              </FormControl>
            </VStack>
          </ModalBody>
          <ModalFooter>
            <Button variant="ghost" mr={3} onClick={onEditClose}>
              Cancelar
            </Button>
            <Button colorScheme="blue" onClick={handleEditProduct}>
              Guardar Cambios
            </Button>
          </ModalFooter>
        </ModalContent>
      </Modal>

      {/* View Product Modal */}
      <Modal isOpen={isViewOpen} onClose={onViewClose} size="lg">
        <ModalOverlay />
        <ModalContent>
          <ModalHeader>Detalles del Producto</ModalHeader>
          <ModalCloseButton />
          <ModalBody>
            {selectedProduct && (
              <VStack spacing={4} align="stretch">
                <HStack>
                  <Image
                    src={selectedProduct.image_url || "/api/placeholder/80/80"}
                    alt={selectedProduct.name}
                    boxSize="80px"
                    objectFit="cover"
                    rounded="md"
                    fallbackSrc="/api/placeholder/80/80"
                  />
                  <Box flex={1}>
                    <Text fontWeight="bold" fontSize="lg">
                      {selectedProduct.name}
                    </Text>
                    <Text color="gray.600" mb={2}>
                      {selectedProduct.description || "Sin descripción"}
                    </Text>
                    <Badge 
                      colorScheme={
                        selectedProduct.status === "active" ? "green" : 
                        selectedProduct.status === "draft" ? "yellow" : "red"
                      }
                    >
                      {selectedProduct.status === "active" ? "Activo" : 
                       selectedProduct.status === "draft" ? "Borrador" : "Inactivo"}
                    </Badge>
                  </Box>
                </HStack>

                <HStack justify="space-between">
                  <Box>
                    <Text fontWeight="medium">Precio:</Text>
                    <Text fontSize="xl" fontWeight="bold" color="green.500">
                      {formatPrice(selectedProduct.price)}
                    </Text>
                  </Box>
                  <Box>
                    <Text fontWeight="medium">Stock:</Text>
                    <Text fontSize="xl" fontWeight="bold">
                      {selectedProduct.stock} unidades
                    </Text>
                  </Box>
                </HStack>

                <Box>
                  <Text fontWeight="medium">Categoría:</Text>
                  <Text color="gray.600">{selectedProduct.category || "Sin categoría"}</Text>
                </Box>

                <HStack justify="space-between">
                  <Box>
                    <Text fontWeight="medium">Creado:</Text>
                    <Text color="gray.600">{formatDate(selectedProduct.created_at)}</Text>
                  </Box>
                  <Box>
                    <Text fontWeight="medium">Actualizado:</Text>
                    <Text color="gray.600">{formatDate(selectedProduct.updated_at)}</Text>
                  </Box>
                </HStack>

                <Box>
                  <Text fontWeight="medium">ID del Producto:</Text>
                  <Text color="gray.600" fontSize="sm">{selectedProduct.id}</Text>
                </Box>
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

export default InventoryManagement