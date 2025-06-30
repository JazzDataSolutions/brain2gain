import {
  Alert,
  AlertIcon,
  Box,
  Button,
  Container,
  Heading,
  SimpleGrid,
  Spinner,
  Text,
  VStack,
} from "@chakra-ui/react"
import { useQuery } from "@tanstack/react-query"
import { Link } from "@tanstack/react-router"

import { type Product, ProductsService } from "../../services/ProductsService"
import ProductCard from "../Products/ProductCard"

const FeaturedProducts = () => {
  const {
    data: productsResponse,
    isLoading,
    error,
  } = useQuery({
    queryKey: ["featured-products"],
    queryFn: () =>
      ProductsService.getProductsWithFallback({ skip: 0, limit: 6 }), // Limit to 6 for homepage
    staleTime: 5 * 60 * 1000, // 5 minutes
  })

  const products = productsResponse?.data || []

  if (error) {
    return (
      <Box as="section" py={16} bg="gray.50">
        <Container maxW="7xl">
          <Alert status="error">
            <AlertIcon />
            Error loading featured products.
          </Alert>
        </Container>
      </Box>
    )
  }

  return (
    <Box as="section" py={16} bg="gray.50">
      <Container maxW="7xl">
        <VStack spacing={12} align="stretch">
          {/* Section Header */}
          <VStack spacing={4} textAlign="center">
            <Heading size="xl" color="gray.800">
              Productos Destacados
            </Heading>
            <Text fontSize="lg" color="gray.600" maxW="2xl">
              Descubre nuestra selección de suplementos premium, cuidadosamente
              elegidos para potenciar tu rendimiento
            </Text>
          </VStack>

          {/* Loading State */}
          {isLoading && (
            <Box textAlign="center" py={12}>
              <Spinner size="xl" color="blue.500" />
              <Text mt={4} color="gray.600">
                Cargando productos destacados...
              </Text>
            </Box>
          )}

          {/* Products Grid */}
          {!isLoading && products.length > 0 && (
            <>
              <SimpleGrid columns={{ base: 1, md: 2, lg: 3 }} spacing={8}>
                {products.map((product: Product) => (
                  <ProductCard key={product.id} product={product} />
                ))}
              </SimpleGrid>

              {/* View All Button */}
              <Box textAlign="center">
                <Button
                  as={Link}
                  to="/products"
                  size="lg"
                  colorScheme="blue"
                  variant="outline"
                >
                  Ver Todos los Productos
                </Button>
              </Box>
            </>
          )}

          {/* Empty State */}
          {!isLoading && products.length === 0 && (
            <Box textAlign="center" py={12}>
              <Text fontSize="lg" color="gray.600">
                No hay productos disponibles en este momento.
              </Text>
              <Button
                as={Link}
                to="/products"
                mt={4}
                colorScheme="blue"
                variant="outline"
              >
                Explorar Catálogo
              </Button>
            </Box>
          )}
        </VStack>
      </Container>
    </Box>
  )
}

export default FeaturedProducts
