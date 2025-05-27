import {
  Box,
  Button,
  HStack,
  VStack,
  Text,
  Badge,
  Popover,
  PopoverTrigger,
  PopoverContent,
  PopoverHeader,
  PopoverBody,
  PopoverFooter,
  PopoverArrow,
  PopoverCloseButton,
  Image,
  IconButton,
  Divider,
  useColorModeValue,
} from '@chakra-ui/react'
import { ShoppingCartIcon, DeleteIcon } from '@chakra-ui/icons'
import { Link } from '@tanstack/react-router'

import { useCartStore } from '../../stores/cartStore'

const MiniCart = () => {
  const { items, item_count, total_amount, removeFromCart } = useCartStore()
  
  const cardBg = useColorModeValue('white', 'gray.800')
  const borderColor = useColorModeValue('gray.200', 'gray.600')

  const formatPrice = (price: number) => {
    return new Intl.NumberFormat('es-CO', {
      style: 'currency',
      currency: 'COP',
    }).format(price)
  }

  return (
    <Popover placement="bottom-end">
      <PopoverTrigger>
        <Button
          variant="ghost"
          size="sm"
          position="relative"
          leftIcon={<ShoppingCartIcon />}
        >
          Carrito
          {item_count > 0 && (
            <Badge
              position="absolute"
              top="-1"
              right="-1"
              colorScheme="red"
              borderRadius="full"
              fontSize="xs"
              minW="20px"
              h="20px"
              display="flex"
              alignItems="center"
              justifyContent="center"
            >
              {item_count > 99 ? '99+' : item_count}
            </Badge>
          )}
        </Button>
      </PopoverTrigger>

      <PopoverContent w="400px" maxW="90vw">
        <PopoverArrow />
        <PopoverCloseButton />
        <PopoverHeader>
          <Text fontWeight="semibold">
            Carrito de Compras {item_count > 0 && `(${item_count})`}
          </Text>
        </PopoverHeader>

        <PopoverBody p={0}>
          {items.length === 0 ? (
            <Box p={4} textAlign="center">
              <Text color="gray.500" mb={4}>
                Tu carrito está vacío
              </Text>
              <Button
                as={Link}
                to="/products"
                colorScheme="blue"
                size="sm"
              >
                Ver Productos
              </Button>
            </Box>
          ) : (
            <VStack spacing={0} align="stretch" maxH="300px" overflowY="auto">
              {items.slice(0, 3).map((item, index) => (
                <Box key={item.product_id}>
                  <HStack p={3} spacing={3} align="start">
                    <Image
                      src={`/imagenes/${item.product_sku.toLowerCase()}.jpg`}
                      alt={item.product_name}
                      boxSize="50px"
                      objectFit="cover"
                      borderRadius="md"
                      fallbackSrc="https://via.placeholder.com/50x50?text=Brain2Gain"
                    />
                    
                    <VStack align="stretch" flex={1} spacing={1}>
                      <Text fontSize="sm" fontWeight="medium" noOfLines={2}>
                        {item.product_name}
                      </Text>
                      <HStack justify="space-between" align="center">
                        <Text fontSize="xs" color="gray.500">
                          {item.quantity} x {formatPrice(item.unit_price)}
                        </Text>
                        <Text fontSize="sm" fontWeight="semibold" color="blue.600">
                          {formatPrice(item.total_price)}
                        </Text>
                      </HStack>
                    </VStack>

                    <IconButton
                      aria-label="Eliminar"
                      icon={<DeleteIcon />}
                      size="xs"
                      variant="ghost"
                      colorScheme="red"
                      onClick={() => removeFromCart(item.product_id)}
                    />
                  </HStack>
                  {index < Math.min(items.length, 3) - 1 && <Divider />}
                </Box>
              ))}

              {items.length > 3 && (
                <Box p={3} bg={useColorModeValue('gray.50', 'gray.700')}>
                  <Text fontSize="sm" color="gray.600" textAlign="center">
                    y {items.length - 3} producto{items.length - 3 !== 1 ? 's' : ''} más...
                  </Text>
                </Box>
              )}
            </VStack>
          )}
        </PopoverBody>

        {items.length > 0 && (
          <PopoverFooter>
            <VStack spacing={3} align="stretch">
              <HStack justify="space-between">
                <Text fontWeight="semibold">Total:</Text>
                <Text fontWeight="bold" color="blue.600">
                  {formatPrice(total_amount)}
                </Text>
              </HStack>

              <HStack spacing={2}>
                <Button
                  as={Link}
                  to="/cart"
                  variant="outline"
                  size="sm"
                  flex={1}
                >
                  Ver Carrito
                </Button>
                <Button
                  as={Link}
                  to="/checkout"
                  colorScheme="blue"
                  size="sm"
                  flex={1}
                >
                  Checkout
                </Button>
              </HStack>
            </VStack>
          </PopoverFooter>
        )}
      </PopoverContent>
    </Popover>
  )
}

export default MiniCart