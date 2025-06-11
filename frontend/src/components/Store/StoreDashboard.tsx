import {
  Box,
  Container,
  VStack,
  Heading,
  Text,
  Button,
  SimpleGrid,
  useColorModeValue,
  Stack,
  Image,
  Badge,
  Flex,
} from '@chakra-ui/react'
import { useNavigate } from '@tanstack/react-router'
import { useQuery } from '@tanstack/react-query'

import { ProductsService } from '../../client'
import ProductCard from '../Products/ProductCard'

const StoreDashboard = () => {
  const navigate = useNavigate()
  const bg = useColorModeValue('white', 'gray.800')
  
  // Consultar productos destacados
  const { data: featuredProducts, isLoading } = useQuery({
    queryKey: ['products', 'featured'],
    queryFn: () => ProductsService.readProducts({ skip: 0, limit: 8 }),
  })

  return (
    <Box>
      {/* Hero Section */}
      <Box
        bgGradient="linear(to-r, blue.400, blue.600)"
        color="white"
        py={20}
        textAlign="center"
      >
        <Container maxW="6xl">
          <VStack spacing={6}>
            <Heading fontSize={{ base: '3xl', md: '5xl' }} fontWeight="bold">
              Potencia Tu Rendimiento
            </Heading>
            <Text fontSize={{ base: 'lg', md: 'xl' }} maxW="2xl">
              Descubre nuestra selección premium de suplementos deportivos.
              Calidad garantizada para alcanzar tus objetivos fitness.
            </Text>
            <Stack direction={{ base: 'column', sm: 'row' }} spacing={4}>
              <Button
                size="lg"
                bg="white"
                color="blue.600"
                _hover={{ bg: 'gray.50' }}
                onClick={() => navigate({ to: '/store/products' })}
              >
                Ver Productos
              </Button>
              <Button
                size="lg"
                variant="outline"
                borderColor="white"
                color="white"
                _hover={{ bg: 'whiteAlpha.200' }}
                onClick={() => navigate({ to: '/store/offers' })}
              >
                Ofertas Especiales
              </Button>
            </Stack>
          </VStack>
        </Container>
      </Box>

      {/* Categorías Destacadas */}
      <Container maxW="7xl" py={16}>
        <VStack spacing={8} align="stretch">
          <Box textAlign="center">
            <Heading size="lg" mb={4}>
              Categorías Populares
            </Heading>
            <Text color="gray.600">
              Explora nuestras categorías más vendidas
            </Text>
          </Box>

          <SimpleGrid columns={{ base: 2, md: 4 }} spacing={6}>
            {[
              {
                name: 'Proteínas',
                image: '/imagenes/proteina_catalogo.jpg',
                description: 'Whey, Caseína y más',
                href: '/store/products?category=proteinas'
              },
              {
                name: 'Creatina',
                image: '/imagenes/creatina_catalogo.jpg',
                description: 'Potencia y fuerza',
                href: '/store/products?category=creatina'
              },
              {
                name: 'Pre-Workout',
                image: '/imagenes/preworkout_catalogo.jpg',
                description: 'Energía y enfoque',
                href: '/store/products?category=pre-workout'
              },
              {
                name: 'Quemadores',
                image: '/imagenes/cafeina.jpg',
                description: 'Definición muscular',
                href: '/store/products?category=quemadores'
              },
            ].map((category) => (
              <Box
                key={category.name}
                bg={bg}
                rounded="lg"
                shadow="md"
                overflow="hidden"
                cursor="pointer"
                transition="transform 0.2s"
                _hover={{ transform: 'translateY(-4px)', shadow: 'lg' }}
                onClick={() => navigate({ to: category.href })}
              >
                <Image
                  src={category.image}
                  alt={category.name}
                  h="150px"
                  w="full"
                  objectFit="cover"
                />
                <Box p={4}>
                  <Heading size="md" mb={2}>
                    {category.name}
                  </Heading>
                  <Text fontSize="sm" color="gray.600">
                    {category.description}
                  </Text>
                </Box>
              </Box>
            ))}
          </SimpleGrid>
        </VStack>
      </Container>

      {/* Productos Destacados */}
      <Box bg={useColorModeValue('gray.50', 'gray.900')} py={16}>
        <Container maxW="7xl">
          <VStack spacing={8} align="stretch">
            <Flex justify="space-between" align="center">
              <Box>
                <Heading size="lg" mb={2}>
                  Productos Destacados
                </Heading>
                <Text color="gray.600">
                  Los más vendidos de la semana
                </Text>
              </Box>
              <Button
                variant="outline"
                colorScheme="blue"
                onClick={() => navigate({ to: '/store/products' })}
              >
                Ver Todos
              </Button>
            </Flex>

            <SimpleGrid columns={{ base: 1, sm: 2, md: 3, lg: 4 }} spacing={6}>
              {isLoading ? (
                // Skeleton loading
                Array.from({ length: 8 }).map((_, i) => (
                  <Box key={i} bg={bg} rounded="lg" p={4}>
                    <Box h="200px" bg="gray.200" rounded="md" mb={4} />
                    <Box h="20px" bg="gray.200" rounded="md" mb={2} />
                    <Box h="16px" bg="gray.200" rounded="md" w="60%" />
                  </Box>
                ))
              ) : (
                featuredProducts?.data?.map((product) => (
                  <ProductCard key={product.id} product={product} />
                ))
              )}
            </SimpleGrid>
          </VStack>
        </Container>
      </Box>

      {/* CTA Section */}
      <Container maxW="6xl" py={16}>
        <Box
          bg="blue.50"
          rounded="xl"
          p={8}
          textAlign="center"
        >
          <VStack spacing={6}>
            <Badge colorScheme="blue" px={3} py={1} rounded="full">
              Oferta Especial
            </Badge>
            <Heading size="lg">
              ¡Envío Gratis en Pedidos Mayores a $50!
            </Heading>
            <Text color="gray.600" maxW="md">
              Aprovecha nuestra promoción especial. Envío gratuito a todo el país
              en compras superiores a $50 USD.
            </Text>
            <Button
              colorScheme="blue"
              size="lg"
              onClick={() => navigate({ to: '/store/products' })}
            >
              Comprar Ahora
            </Button>
          </VStack>
        </Box>
      </Container>
    </Box>
  )
}

export default StoreDashboard