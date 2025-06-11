import {
  Box,
  Image,
  Text,
  Button,
  VStack,
  HStack,
  Badge,
  useToast,
  NumberInput,
  NumberInputField,
  NumberInputStepper,
  NumberIncrementStepper,
  NumberDecrementStepper,
  useColorModeValue,
  IconButton,
  Tooltip,
  Skeleton,
  SkeletonText,
} from '@chakra-ui/react'
import { useState, memo, useCallback } from 'react'
import { Link } from '@tanstack/react-router'
import { motion, useReducedMotion } from 'framer-motion'
import { FiHeart, FiEye, FiShoppingCart, FiStar } from 'react-icons/fi'

import { Product } from '../../services/ProductsService'
import { useCartStore } from '../../stores/cartStore'
import { formatCurrency } from '../../utils'

interface ProductCardProps {
  product: Product
  isLoading?: boolean
  onWishlistToggle?: (productId: string) => void
  isInWishlist?: boolean
  showQuickActions?: boolean
  variant?: 'default' | 'compact' | 'detailed'
}

// Motion components
const MotionBox = motion(Box)

const ProductCard = memo(({ 
  product, 
  isLoading = false,
  onWishlistToggle,
  isInWishlist = false,
  showQuickActions = true,
  variant = 'default'
}: ProductCardProps) => {
  const [quantity, setQuantity] = useState(1)
  const [isAdding, setIsAdding] = useState(false)
  const [imageLoaded, setImageLoaded] = useState(false)
  const [isHovered, setIsHovered] = useState(false)
  
  const { addItem } = useCartStore()
  const toast = useToast()
  const prefersReducedMotion = useReducedMotion()

  // Theme colors
  const cardBg = useColorModeValue('white', 'gray.800')
  const borderColor = useColorModeValue('gray.200', 'gray.600')
  const hoverBorderColor = useColorModeValue('brand.300', 'brand.400')
  const overlayBg = useColorModeValue('rgba(0,0,0,0.7)', 'rgba(0,0,0,0.8)')

  const handleAddToCart = useCallback(async () => {
    setIsAdding(true)
    
    try {
      addItem({
        id: product.id.toString(),
        name: product.name,
        price: product.price,
        quantity: quantity,
        image: product.image
      })
      
      toast({
        title: '¡Agregado al carrito!',
        description: `${quantity} x ${product.name}`,
        status: 'success',
        duration: 2000,
        isClosable: true,
        position: 'bottom-right'
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
  }, [product, quantity, addItem, toast])

  const handleWishlistToggle = useCallback(() => {
    if (onWishlistToggle) {
      onWishlistToggle(product.id.toString())
    }
  }, [product.id, onWishlistToggle])

  // Animation variants
  const cardVariants = {
    initial: { scale: 1, y: 0 },
    hover: { 
      scale: prefersReducedMotion ? 1 : 1.02, 
      y: prefersReducedMotion ? 0 : -4,
      transition: { duration: 0.2, ease: 'easeOut' }
    }
  }

  const overlayVariants = {
    hidden: { opacity: 0 },
    visible: { opacity: 1, transition: { duration: 0.2 } }
  }

  if (isLoading) {
    return <ProductCardSkeleton variant={variant} />
  }


  return (
    <MotionBox
      bg={cardBg}
      border="1px"
      borderColor={isHovered ? hoverBorderColor : borderColor}
      borderRadius="lg"
      overflow="hidden"
      shadow="sm"
      cursor="pointer"
      variants={cardVariants}
      initial="initial"
      whileHover="hover"
      onHoverStart={() => setIsHovered(true)}
      onHoverEnd={() => setIsHovered(false)}
      transition={{ duration: 0.2 }}
      _hover={{ shadow: 'lg' }}
    >
      {/* Product Image */}
      <Box position="relative" bg="gray.100">
        {!imageLoaded && (
          <Skeleton
            position="absolute"
            top={0}
            left={0}
            w="100%"
            h="200px"
            borderRadius="0"
          />
        )}
        
        <Image
          src={product.image || `/imagenes/${product.sku.toLowerCase()}.jpg`}
          alt={product.name}
          h="200px"
          w="100%"
          objectFit="cover"
          fallbackSrc="https://via.placeholder.com/300x200?text=Brain2Gain"
          onLoad={() => setImageLoaded(true)}
          opacity={imageLoaded ? 1 : 0}
          transition="opacity 0.3s ease"
        />

        {/* Status Badge */}
        <motion.div
          initial={{ scale: 0.8, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          transition={{ delay: 0.1 }}
        >
          {product.status === 'ACTIVE' ? (
            <Badge
              position="absolute"
              top={2}
              left={2}
              colorScheme="green"
              variant="solid"
              fontSize="xs"
            >
              Disponible
            </Badge>
          ) : (
            <Badge
              position="absolute"
              top={2}
              left={2}
              colorScheme="red"
              variant="solid"
              fontSize="xs"
            >
              Agotado
            </Badge>
          )}
        </motion.div>

        {/* Quick Actions Overlay */}
        {showQuickActions && (
          <motion.div
            style={{
              position: 'absolute',
              top: 0,
              left: 0,
              right: 0,
              bottom: 0,
              background: overlayBg,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '8px'
            }}
            variants={overlayVariants}
            initial="hidden"
            animate={isHovered ? "visible" : "hidden"}
          >
            <Tooltip label="Ver detalles" hasArrow>
              <IconButton
                as={Link}
                to="/products/$productId"
                params={{ productId: product.id.toString() }}
                aria-label="Ver detalles"
                icon={<FiEye />}
                colorScheme="whiteAlpha"
                variant="solid"
                size="md"
                bg="whiteAlpha.200"
                backdropFilter="blur(4px)"
                _hover={{ bg: 'whiteAlpha.300' }}
              />
            </Tooltip>

            {onWishlistToggle && (
              <Tooltip label={isInWishlist ? "Quitar de favoritos" : "Agregar a favoritos"} hasArrow>
                <IconButton
                  aria-label={isInWishlist ? "Quitar de favoritos" : "Agregar a favoritos"}
                  icon={<FiHeart />}
                  colorScheme={isInWishlist ? "red" : "whiteAlpha"}
                  variant="solid"
                  size="md"
                  bg={isInWishlist ? "red.500" : "whiteAlpha.200"}
                  backdropFilter="blur(4px)"
                  _hover={{ bg: isInWishlist ? "red.600" : "whiteAlpha.300" }}
                  onClick={handleWishlistToggle}
                />
              </Tooltip>
            )}

            {product.status === 'ACTIVE' && (
              <Tooltip label="Agregar al carrito" hasArrow>
                <IconButton
                  aria-label="Agregar al carrito rápido"
                  icon={<FiShoppingCart />}
                  colorScheme="brand"
                  variant="solid"
                  size="md"
                  isLoading={isAdding}
                  onClick={handleAddToCart}
                />
              </Tooltip>
            )}
          </motion.div>
        )}

        {/* Rating Stars (if available) */}
        {product.rating && (
          <HStack
            position="absolute"
            bottom={2}
            right={2}
            bg="whiteAlpha.900"
            px={2}
            py={1}
            borderRadius="md"
            spacing={1}
          >
            <FiStar size="12px" color="#FFD700" />
            <Text fontSize="xs" fontWeight="medium">
              {product.rating.toFixed(1)}
            </Text>
          </HStack>
        )}
      </Box>

      {/* Product Info */}
      <VStack p={4} align="stretch" spacing={3}>
        <VStack align="stretch" spacing={1}>
          <Text
            fontWeight="semibold"
            fontSize="lg"
            noOfLines={2}
            minH="3em"
          >
            {product.name}
          </Text>
          
          <Text
            color="gray.500"
            fontSize="sm"
          >
            SKU: {product.sku}
          </Text>
        </VStack>

        <Text
          fontSize="xl"
          fontWeight="bold"
          color="brand.500"
        >
          {formatCurrency(product.price)}
        </Text>

        {/* Quantity Selector */}
        {product.status === 'ACTIVE' && (
          <HStack>
            <Text fontSize="sm" color="gray.600">
              Cantidad:
            </Text>
            <NumberInput
              size="sm"
              maxW="80px"
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
          </HStack>
        )}

        {/* Actions */}
        <VStack spacing={2}>
          <Button
            as={Link}
            to="/products/$productId"
            params={{ productId: product.id.toString() }}
            variant="outline"
            colorScheme="blue"
            size="sm"
            w="100%"
          >
            Ver Detalles
          </Button>
          
          {product.status === 'ACTIVE' && (
            <Button
              colorScheme="blue"
              size="sm"
              w="100%"
              isLoading={isAdding}
              loadingText="Agregando..."
              onClick={handleAddToCart}
            >
              Agregar al Carrito
            </Button>
          )}
        </VStack>
      </VStack>
    </MotionBox>
  )
})

ProductCard.displayName = 'ProductCard'

// Skeleton component for loading state
const ProductCardSkeleton = ({ variant = 'default' }: { variant?: string }) => {
  return (
    <Box
      bg={useColorModeValue('white', 'gray.800')}
      border="1px"
      borderColor={useColorModeValue('gray.200', 'gray.600')}
      borderRadius="lg"
      overflow="hidden"
      shadow="sm"
    >
      {/* Image Skeleton */}
      <Skeleton h="200px" w="100%" />
      
      {/* Content Skeleton */}
      <VStack p={4} align="stretch" spacing={3}>
        <SkeletonText noOfLines={2} spacing="2" />
        <Skeleton h="24px" w="60%" />
        <HStack>
          <Skeleton h="32px" w="80px" />
          <Skeleton h="32px" flex={1} />
        </HStack>
        <VStack spacing={2}>
          <Skeleton h="32px" w="100%" />
          <Skeleton h="32px" w="100%" />
        </VStack>
      </VStack>
    </Box>
  )
}

export default ProductCard
export { ProductCardSkeleton }