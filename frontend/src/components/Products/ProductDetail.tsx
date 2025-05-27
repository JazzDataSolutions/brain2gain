import {
  Box,
  Container,
  Image,
  Text,
  Button,
  VStack,
  HStack,
  Heading,
  Badge,
  useToast,
  NumberInput,
  NumberInputField,
  NumberInputStepper,
  NumberIncrementStepper,
  NumberDecrementStepper,
  Grid,
  GridItem,
  Spinner,
  Alert,
  AlertIcon,
  Breadcrumb,
  BreadcrumbItem,
  BreadcrumbLink,
  useColorModeValue,
} from '@chakra-ui/react'
import { ChevronRightIcon } from '@chakra-ui/icons'
import { useState } from 'react'
import { useParams, Link } from '@tanstack/react-router'
import { useQuery } from '@tanstack/react-query'

import { useCartStore } from '../../stores/cartStore'
import { ProductsService } from '../../client'

const ProductDetail = () => {
  const { productId } = useParams({ from: '/products/$productId' })
  const [quantity, setQuantity] = useState(1)
  const [isAdding, setIsAdding] = useState(false)
  
  const addToCart = useCartStore((state) => state.addToCart)
  const toast = useToast()

  const cardBg = useColorModeValue('white', 'gray.800')
  const borderColor = useColorModeValue('gray.200', 'gray.600')

  const { 
    data: product, 
    isLoading, 
    error 
  } = useQuery({
    queryKey: ['product', productId],
    queryFn: () => ProductsService.getProduct({ productId: parseInt(productId) }),
    enabled: !!productId,
  })

  const handleAddToCart = async () => {
    if (!product) return
    
    setIsAdding(true)
    
    try {
      addToCart(product, quantity)
      
      toast({
        title: '¡Agregado al carrito!',
        description: `${quantity} x ${product.name}`,
        status: 'success',
        duration: 3000,
        isClosable: true,
      })
    } catch (error) {
      toast({
        title: 'Error',
        description: 'No se pudo agregar el producto al carrito',
        status: 'error',
        duration: 3000,
        isClosable: true,
      })
    } finally {
      setIsAdding(false)
    }
  }

  const formatPrice = (price: number) => {
    return new Intl.NumberFormat('es-CO', {
      style: 'currency',
      currency: 'COP',
    }).format(price)
  }

  if (isLoading) {
    return (
      <Container maxW="7xl" py={8}>
        <Box textAlign="center" py={12}>
          <Spinner size="xl" color="blue.500" />
          <Text mt={4} color="gray.600">
            Cargando producto...
          </Text>
        </Box>
      </Container>
    )
  }

  if (error || !product) {
    return (
      <Container maxW="7xl" py={8}>
        <Alert status="error">
          <AlertIcon />
          Producto no encontrado o error al cargar.
        </Alert>
      </Container>
    )
  }

  return (
    <Container maxW="7xl" py={8}>
      <VStack spacing={8} align="stretch">
        {/* Breadcrumb */}
        <Breadcrumb spacing="8px" separator={<ChevronRightIcon color="gray.500" />}>
          <BreadcrumbItem>
            <BreadcrumbLink as={Link} to="/">Inicio</BreadcrumbLink>
          </BreadcrumbItem>
          <BreadcrumbItem>
            <BreadcrumbLink as={Link} to="/products">Productos</BreadcrumbLink>
          </BreadcrumbItem>
          <BreadcrumbItem isCurrentPage>
            <BreadcrumbLink>{product.name}</BreadcrumbLink>
          </BreadcrumbItem>
        </Breadcrumb>

        {/* Product Details */}
        <Grid templateColumns={{ base: '1fr', lg: '1fr 1fr' }} gap={8}>
          {/* Product Image */}
          <GridItem>
            <Box
              bg={cardBg}
              border="1px"
              borderColor={borderColor}
              borderRadius="lg"
              overflow="hidden"
              position="relative"
            >
              <Image
                src={`/imagenes/${product.sku.toLowerCase()}.jpg`}
                alt={product.name}
                w="100%"
                h={{ base: '300px', md: '400px' }}
                objectFit="cover"
                fallbackSrc="https://via.placeholder.com/400x400?text=Brain2Gain"
              />
              
              {product.status === 'ACTIVE' ? (
                <Badge
                  position="absolute"
                  top={4}
                  left={4}
                  colorScheme="green"
                  variant="solid"
                  fontSize="sm"
                  px={3}
                  py={1}
                >
                  Disponible
                </Badge>
              ) : (
                <Badge
                  position="absolute"
                  top={4}
                  left={4}
                  colorScheme="red"
                  variant="solid"
                  fontSize="sm"
                  px={3}
                  py={1}
                >
                  Agotado
                </Badge>
              )}
            </Box>
          </GridItem>

          {/* Product Info */}
          <GridItem>
            <VStack align="stretch" spacing={6}>
              <VStack align="stretch" spacing={3}>
                <Heading size="xl">{product.name}</Heading>
                
                <Text color="gray.500" fontSize="lg">
                  SKU: {product.sku}
                </Text>

                <Text fontSize="3xl" fontWeight="bold" color="blue.600">
                  {formatPrice(product.unit_price)}
                </Text>
              </VStack>

              {/* Description Placeholder */}
              <Box>
                <Heading size="md" mb={3}>Descripción</Heading>
                <Text color="gray.600" lineHeight="tall">
                  {product.name} es un suplemento de alta calidad diseñado para apoyar tus objetivos de fitness y bienestar. 
                  Formulado con ingredientes premium para garantizar la máxima efectividad y pureza.
                </Text>
              </Box>

              {/* Benefits Placeholder */}
              <Box>
                <Heading size="md" mb={3}>Beneficios</Heading>
                <VStack align="stretch" spacing={2}>
                  <Text color="gray.600">• Mejora el rendimiento deportivo</Text>
                  <Text color="gray.600">• Acelera la recuperación muscular</Text>
                  <Text color="gray.600">• Ingredientes de alta calidad</Text>
                  <Text color="gray.600">• Sin aditivos artificiales</Text>
                </VStack>
              </Box>

              {/* Purchase Section */}
              {product.status === 'ACTIVE' && (
                <Box>
                  <Heading size="md" mb={4}>Cantidad</Heading>
                  
                  <HStack spacing={4} mb={6}>
                    <NumberInput
                      size="lg"
                      maxW="120px"
                      min={1}
                      max={10}
                      value={quantity}
                      onChange={(_, value) => setQuantity(value || 1)}
                    >
                      <NumberInputField />
                      <NumberInputStepper>
                        <NumberIncrementStepper />
                        <NumberDecrementStepper />
                      </NumberInputStepper>
                    </NumberInput>
                    
                    <Text fontSize="lg" color="gray.600">
                      Total: {formatPrice(product.unit_price * quantity)}
                    </Text>
                  </HStack>

                  <Button
                    colorScheme="blue"
                    size="lg"
                    w="100%"
                    isLoading={isAdding}
                    loadingText="Agregando al carrito..."
                    onClick={handleAddToCart}
                  >
                    Agregar al Carrito
                  </Button>
                </Box>
              )}

              {product.status !== 'ACTIVE' && (
                <Alert status="warning">
                  <AlertIcon />
                  Este producto no está disponible actualmente.
                </Alert>
              )}
            </VStack>
          </GridItem>
        </Grid>
      </VStack>
    </Container>
  )
}

export default ProductDetail