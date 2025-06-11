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
} from '@chakra-ui/react'
import { useState } from 'react'
import { Link } from '@tanstack/react-router'

import { Product } from '../../services/ProductsService'
import { useCartStore } from '../../stores/cartStore'

interface ProductCardProps {
  product: Product
}

const ProductCard = ({ product }: ProductCardProps) => {
  const [quantity, setQuantity] = useState(1)
  const [isAdding, setIsAdding] = useState(false)
  
  const { addItem } = useCartStore()
  const toast = useToast()

  const cardBg = useColorModeValue('white', 'gray.800')
  const borderColor = useColorModeValue('gray.200', 'gray.600')

  const handleAddToCart = async () => {
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


  return (
    <Box
      bg={cardBg}
      border="1px"
      borderColor={borderColor}
      borderRadius="lg"
      overflow="hidden"
      shadow="sm"
      _hover={{ shadow: 'md' }}
      transition="all 0.2s"
    >
      {/* Product Image */}
      <Box position="relative">
        <Image
          src={product.image || `/imagenes/${product.sku.toLowerCase()}.jpg`}
          alt={product.name}
          h="200px"
          w="100%"
          objectFit="cover"
          fallbackSrc="https://via.placeholder.com/300x200?text=Brain2Gain"
        />
        
        {product.status === 'ACTIVE' ? (
          <Badge
            position="absolute"
            top={2}
            left={2}
            colorScheme="green"
            variant="solid"
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
          >
            Agotado
          </Badge>
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
          color="blue.600"
        >
          ${product.price.toFixed(2)}
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
    </Box>
  )
}

export default ProductCard