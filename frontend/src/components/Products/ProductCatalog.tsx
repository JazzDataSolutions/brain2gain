import { SearchIcon } from "@chakra-ui/icons"
import {
  Alert,
  AlertIcon,
  Box,
  Container,
  HStack,
  Heading,
  Input,
  InputGroup,
  InputLeftElement,
  Select,
  SimpleGrid,
  Spinner,
  Text,
  VStack,
} from "@chakra-ui/react"
import { useQuery } from "@tanstack/react-query"
import { useState } from "react"

import { type Product, ProductsService } from "../../services/ProductsService"
import ProductCard from "./ProductCard"

const ProductCatalog = () => {
  const [searchTerm, setSearchTerm] = useState("")
  const [sortBy, setSortBy] = useState("name")

  const {
    data: products = { data: [], count: 0 },
    isLoading,
    error,
  } = useQuery({
    queryKey: ["products"],
    queryFn: () => ProductsService.readProducts(),
    staleTime: 5 * 60 * 1000, // 5 minutes
  })

  const filteredProducts = products.data
    .filter(
      (product: Product) =>
        product.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        product.sku.toLowerCase().includes(searchTerm.toLowerCase()),
    )
    .sort((a: Product, b: Product) => {
      switch (sortBy) {
        case "price-low":
          return a.price - b.price
        case "price-high":
          return b.price - a.price
        default:
          return a.name.localeCompare(b.name)
      }
    })

  if (error) {
    return (
      <Container maxW="7xl" py={8}>
        <Alert status="error">
          <AlertIcon />
          Error loading products. Please try again later.
        </Alert>
      </Container>
    )
  }

  return (
    <Container maxW="7xl" py={8}>
      <VStack spacing={8} align="stretch">
        {/* Header */}
        <Box textAlign="center">
          <Heading size="xl" mb={4}>
            Catálogo de Productos
          </Heading>
          <Text color="gray.600" fontSize="lg">
            Descubre nuestra selección de suplementos de alta calidad
          </Text>
        </Box>

        {/* Filters */}
        <HStack spacing={4} flexWrap="wrap">
          <InputGroup maxW="300px">
            <InputLeftElement pointerEvents="none">
              <SearchIcon color="gray.300" />
            </InputLeftElement>
            <Input
              placeholder="Buscar productos..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
            />
          </InputGroup>

          <Select
            maxW="200px"
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value)}
          >
            <option value="name">Ordenar por nombre</option>
            <option value="price-low">Precio: menor a mayor</option>
            <option value="price-high">Precio: mayor a menor</option>
          </Select>
        </HStack>

        {/* Loading State */}
        {isLoading && (
          <Box textAlign="center" py={12}>
            <Spinner size="xl" color="blue.500" />
            <Text mt={4} color="gray.600">
              Cargando productos...
            </Text>
          </Box>
        )}

        {/* Products Grid */}
        {!isLoading && filteredProducts.length > 0 && (
          <SimpleGrid columns={{ base: 1, md: 2, lg: 3, xl: 4 }} spacing={6}>
            {filteredProducts.map((product: Product) => (
              <ProductCard key={product.id} product={product} />
            ))}
          </SimpleGrid>
        )}

        {/* No Results */}
        {!isLoading && filteredProducts.length === 0 && searchTerm && (
          <Box textAlign="center" py={12}>
            <Text fontSize="lg" color="gray.600">
              No se encontraron productos que coincidan con "{searchTerm}"
            </Text>
          </Box>
        )}

        {/* Empty State */}
        {!isLoading && products.data.length === 0 && !searchTerm && (
          <Box textAlign="center" py={12}>
            <Text fontSize="lg" color="gray.600">
              No hay productos disponibles en este momento.
            </Text>
          </Box>
        )}
      </VStack>
    </Container>
  )
}

export default ProductCatalog
