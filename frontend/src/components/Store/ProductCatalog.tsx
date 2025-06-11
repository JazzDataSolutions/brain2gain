import {
  Box,
  Container,
  VStack,
  Heading,
  Text,
  SimpleGrid,
  Card,
  CardBody,
  Image,
  Badge,
  Button,
  HStack,
  Select,
  Input,
  InputGroup,
  InputLeftElement,
  useColorModeValue,
  Flex,
  Skeleton,
} from '@chakra-ui/react'
import { FiSearch, FiFilter } from 'react-icons/fi'
import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { useNavigate } from '@tanstack/react-router'

import { ProductsService } from '../../client'
import { useCartStore } from '../../stores/cartStore'

const ProductCatalog = () => {
  const navigate = useNavigate()
  const cardBg = useColorModeValue('white', 'gray.800')
  const { addItem } = useCartStore()
  
  const [searchTerm, setSearchTerm] = useState('')
  const [selectedCategory, setSelectedCategory] = useState('')
  const [sortBy, setSortBy] = useState('name')

  // Consultar productos
  const { data: products, isLoading } = useQuery({
    queryKey: ['products', 'catalog'],
    queryFn: () => ProductsService.readProducts({ skip: 0, limit: 50 }),
  })

  const categories = [
    { value: '', label: 'Todas las categorías' },
    { value: 'proteinas', label: 'Proteínas' },
    { value: 'creatina', label: 'Creatina' },
    { value: 'pre-workout', label: 'Pre-Workout' },
    { value: 'vitaminas', label: 'Vitaminas' },
    { value: 'aminoacidos', label: 'Aminoácidos' },
  ]

  const sortOptions = [
    { value: 'name', label: 'Nombre A-Z' },
    { value: 'price-low', label: 'Precio: Menor a Mayor' },
    { value: 'price-high', label: 'Precio: Mayor a Menor' },
    { value: 'newest', label: 'Más Recientes' },
  ]

  const handleAddToCart = (product: any) => {
    addItem({
      id: product.id,
      name: product.name,
      price: product.unit_price,
      quantity: 1,
      image: product.image || '/imagenes/proteina_catalogo.jpg'
    })
  }

  const ProductCardSkeleton = () => (
    <Card bg={cardBg}>
      <CardBody>
        <Skeleton height="200px" rounded="md" mb={4} />
        <Skeleton height="20px" mb={2} />
        <Skeleton height="16px" width="60%" mb={4} />
        <Skeleton height="40px" />
      </CardBody>
    </Card>
  )

  const ProductCard = ({ product }: { product: any }) => (
    <Card
      bg={cardBg}
      shadow="md"
      transition="transform 0.2s"
      _hover={{ transform: 'translateY(-4px)', shadow: 'lg' }}
      cursor="pointer"
    >
      <CardBody>
        <Box position="relative" mb={4}>
          <Image
            src={product.image || '/imagenes/proteina_catalogo.jpg'}
            alt={product.name}
            h="200px"
            w="full"
            objectFit="cover"
            rounded="md"
            onClick={() => navigate({ to: `/store/products/${product.id}` })}
          />
          {product.status === 'ACTIVE' && (
            <Badge
              position="absolute"
              top="2"
              left="2"
              colorScheme="green"
              size="sm"
            >
              Disponible
            </Badge>
          )}
        </Box>
        
        <VStack align="start" spacing={2}>
          <Text
            fontWeight="semibold"
            fontSize="md"
            noOfLines={2}
            onClick={() => navigate({ to: `/store/products/${product.id}` })}
          >
            {product.name}
          </Text>
          
          <Text fontSize="sm" color="gray.600" noOfLines={1}>
            SKU: {product.sku}
          </Text>
          
          <HStack justify="space-between" w="full">
            <Text fontSize="xl" fontWeight="bold" color="blue.500">
              ${product.unit_price}
            </Text>
            <Button
              colorScheme="blue"
              size="sm"
              onClick={() => handleAddToCart(product)}
            >
              Agregar
            </Button>
          </HStack>
        </VStack>
      </CardBody>
    </Card>
  )

  return (
    <Container maxW="7xl" py={8}>
      <VStack spacing={8} align="stretch">
        {/* Header */}
        <Box textAlign="center">
          <Heading size="xl" mb={4}>
            Catálogo de Productos
          </Heading>
          <Text color="gray.600" fontSize="lg">
            Descubre nuestra selección completa de suplementos deportivos
          </Text>
        </Box>

        {/* Filters */}
        <Card bg={cardBg} p={4}>
          <Flex
            direction={{ base: 'column', md: 'row' }}
            gap={4}
            align={{ base: 'stretch', md: 'center' }}
          >
            {/* Search */}
            <InputGroup flex={2}>
              <InputLeftElement>
                <FiSearch color="gray.300" />
              </InputLeftElement>
              <Input
                placeholder="Buscar productos..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
              />
            </InputGroup>

            {/* Category Filter */}
            <Select
              flex={1}
              value={selectedCategory}
              onChange={(e) => setSelectedCategory(e.target.value)}
            >
              {categories.map((category) => (
                <option key={category.value} value={category.value}>
                  {category.label}
                </option>
              ))}
            </Select>

            {/* Sort */}
            <Select
              flex={1}
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value)}
            >
              {sortOptions.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </Select>

            <Button leftIcon={<FiFilter />} variant="outline">
              Filtros
            </Button>
          </Flex>
        </Card>

        {/* Results */}
        <Box>
          <HStack justify="space-between" mb={6}>
            <Text color="gray.600">
              {isLoading ? 'Cargando...' : `${products?.data?.length || 0} productos encontrados`}
            </Text>
          </HStack>

          <SimpleGrid columns={{ base: 1, sm: 2, md: 3, lg: 4 }} spacing={6}>
            {isLoading ? (
              Array.from({ length: 8 }).map((_, i) => (
                <ProductCardSkeleton key={i} />
              ))
            ) : (
              products?.data?.map((product) => (
                <ProductCard key={product.id} product={product} />
              ))
            )}
          </SimpleGrid>

          {/* Empty State */}
          {!isLoading && (!products?.data || products.data.length === 0) && (
            <Box textAlign="center" py={12}>
              <Text fontSize="lg" color="gray.500" mb={4}>
                No se encontraron productos
              </Text>
              <Text color="gray.400">
                Intenta ajustar los filtros de búsqueda
              </Text>
            </Box>
          )}
        </Box>
      </VStack>
    </Container>
  )
}

export default ProductCatalog