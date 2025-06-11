import React, { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { 
  Box, 
  VStack, 
  HStack, 
  Text, 
  Button, 
  IconButton,
  Image,
  Divider,
  Badge,
  useColorModeValue,
  Portal,
  useDisclosure
} from '@chakra-ui/react'
import { FiX, FiShoppingCart, FiPlus, FiMinus, FiArrowRight } from 'react-icons/fi'
import { useCartStore } from '../../stores/cartStore'
import { useNavigate } from '@tanstack/react-router'

interface QuickCartProps {
  isOpen: boolean
  onClose: () => void
}

const QuickCart: React.FC<QuickCartProps> = ({ isOpen, onClose }) => {
  const navigate = useNavigate()
  const { items, updateQuantity, removeItem, getTotalPrice, getTotalItems } = useCartStore()
  
  // Theme colors
  const bgColor = useColorModeValue('white', 'gray.800')
  const borderColor = useColorModeValue('gray.200', 'gray.600')
  const shadowColor = useColorModeValue('rgba(0, 0, 0, 0.1)', 'rgba(255, 255, 255, 0.1)')

  const total = getTotalPrice()
  const totalItems = getTotalItems()

  const handleCheckout = () => {
    onClose()
    navigate({ to: '/store/checkout' })
  }

  const handleViewCart = () => {
    onClose()
    navigate({ to: '/store/cart' })
  }

  const formatPrice = (price: number) => {
    return new Intl.NumberFormat('es-CO', {
      style: 'currency',
      currency: 'COP',
      minimumFractionDigits: 0,
    }).format(price)
  }

  return (
    <Portal>
      <AnimatePresence>
        {isOpen && (
          <>
            {/* Backdrop */}
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              onClick={onClose}
              style={{
                position: 'fixed',
                top: 0,
                left: 0,
                right: 0,
                bottom: 0,
                backgroundColor: 'rgba(0, 0, 0, 0.4)',
                zIndex: 1000,
                backdropFilter: 'blur(4px)'
              }}
            />

            {/* Quick Cart Panel */}
            <motion.div
              initial={{ x: 400, opacity: 0 }}
              animate={{ x: 0, opacity: 1 }}
              exit={{ x: 400, opacity: 0 }}
              transition={{ 
                type: 'spring', 
                stiffness: 300, 
                damping: 30 
              }}
              style={{
                position: 'fixed',
                top: '80px',
                right: '20px',
                width: '400px',
                maxHeight: 'calc(100vh - 120px)',
                zIndex: 1001,
                backgroundColor: bgColor,
                borderRadius: '12px',
                boxShadow: `0 20px 40px ${shadowColor}`,
                border: `1px solid ${borderColor}`,
                overflow: 'hidden'
              }}
            >
              <Box p={6}>
                {/* Header */}
                <HStack justify="space-between" mb={4}>
                  <HStack>
                    <FiShoppingCart size={20} />
                    <Text fontSize="lg" fontWeight="bold">
                      Tu Carrito
                    </Text>
                    {totalItems > 0 && (
                      <Badge colorScheme="brand" borderRadius="full">
                        {totalItems}
                      </Badge>
                    )}
                  </HStack>
                  <IconButton
                    aria-label="Cerrar carrito"
                    icon={<FiX />}
                    variant="ghost"
                    size="sm"
                    onClick={onClose}
                  />
                </HStack>

                {/* Empty State */}
                {items.length === 0 ? (
                  <VStack spacing={4} py={8} textAlign="center">
                    <Box opacity={0.5}>
                      <FiShoppingCart size={48} />
                    </Box>
                    <Text color="gray.500">
                      Tu carrito está vacío
                    </Text>
                    <Button
                      variant="outline"
                      onClick={() => {
                        onClose()
                        navigate({ to: '/store/products' })
                      }}
                    >
                      Explorar Productos
                    </Button>
                  </VStack>
                ) : (
                  <>
                    {/* Items List */}
                    <VStack
                      spacing={3}
                      maxH="400px"
                      overflowY="auto"
                      sx={{
                        '&::-webkit-scrollbar': {
                          width: '4px',
                        },
                        '&::-webkit-scrollbar-track': {
                          bg: 'transparent',
                        },
                        '&::-webkit-scrollbar-thumb': {
                          bg: 'gray.300',
                          borderRadius: '2px',
                        },
                      }}
                    >
                      {items.map((item) => (
                        <motion.div
                          key={item.id}
                          layout
                          initial={{ opacity: 0, y: 20 }}
                          animate={{ opacity: 1, y: 0 }}
                          exit={{ opacity: 0, y: -20 }}
                          style={{ width: '100%' }}
                        >
                          <Box
                            p={3}
                            borderRadius="lg"
                            border="1px solid"
                            borderColor={borderColor}
                            bg={useColorModeValue('gray.50', 'gray.700')}
                          >
                            <HStack spacing={3}>
                              {/* Product Image */}
                              {item.image && (
                                <Image
                                  src={item.image}
                                  alt={item.name}
                                  boxSize="50px"
                                  objectFit="cover"
                                  borderRadius="md"
                                  fallback={
                                    <Box
                                      boxSize="50px"
                                      bg="gray.200"
                                      borderRadius="md"
                                      display="flex"
                                      alignItems="center"
                                      justifyContent="center"
                                    >
                                      <FiShoppingCart />
                                    </Box>
                                  }
                                />
                              )}

                              {/* Product Info */}
                              <VStack flex={1} align="start" spacing={1}>
                                <Text fontSize="sm" fontWeight="medium" noOfLines={2}>
                                  {item.name}
                                </Text>
                                <Text fontSize="sm" color="brand.500" fontWeight="bold">
                                  {formatPrice(item.price)}
                                </Text>
                              </VStack>

                              {/* Quantity Controls */}
                              <VStack spacing={1}>
                                <HStack spacing={1}>
                                  <IconButton
                                    aria-label="Disminuir cantidad"
                                    icon={<FiMinus />}
                                    size="xs"
                                    variant="outline"
                                    onClick={() => updateQuantity(item.id, item.quantity - 1)}
                                    isDisabled={item.quantity <= 1}
                                  />
                                  <Text
                                    minW="30px"
                                    textAlign="center"
                                    fontSize="sm"
                                    fontWeight="medium"
                                  >
                                    {item.quantity}
                                  </Text>
                                  <IconButton
                                    aria-label="Aumentar cantidad"
                                    icon={<FiPlus />}
                                    size="xs"
                                    variant="outline"
                                    onClick={() => updateQuantity(item.id, item.quantity + 1)}
                                  />
                                </HStack>
                                <Button
                                  size="xs"
                                  variant="ghost"
                                  colorScheme="red"
                                  onClick={() => removeItem(item.id)}
                                >
                                  Eliminar
                                </Button>
                              </VStack>
                            </HStack>
                          </Box>
                        </motion.div>
                      ))}
                    </VStack>

                    <Divider my={4} />

                    {/* Total */}
                    <HStack justify="space-between" mb={4}>
                      <Text fontSize="lg" fontWeight="bold">
                        Total:
                      </Text>
                      <Text fontSize="xl" fontWeight="bold" color="brand.500">
                        {formatPrice(total)}
                      </Text>
                    </HStack>

                    {/* Action Buttons */}
                    <VStack spacing={2}>
                      <Button
                        w="full"
                        colorScheme="brand"
                        size="lg"
                        rightIcon={<FiArrowRight />}
                        onClick={handleCheckout}
                        bg="brand.500"
                        _hover={{ bg: 'brand.600' }}
                      >
                        Finalizar Compra
                      </Button>
                      
                      <Button
                        w="full"
                        variant="outline"
                        size="md"
                        onClick={handleViewCart}
                      >
                        Ver Carrito Completo
                      </Button>
                    </VStack>
                  </>
                )}
              </Box>
            </motion.div>
          </>
        )}
      </AnimatePresence>
    </Portal>
  )
}

export default QuickCart

// Hook personalizado para manejar el estado del QuickCart
export const useQuickCart = () => {
  const { isOpen, onOpen, onClose } = useDisclosure()
  
  return {
    isOpen,
    openCart: onOpen,
    closeCart: onClose,
    toggleCart: () => isOpen ? onClose() : onOpen()
  }
}