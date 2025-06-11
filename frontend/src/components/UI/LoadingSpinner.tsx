import React from 'react'
import { motion } from 'framer-motion'
import { Box, Text, VStack, useColorModeValue } from '@chakra-ui/react'

interface LoadingSpinnerProps {
  size?: 'sm' | 'md' | 'lg' | 'xl'
  text?: string
  variant?: 'dots' | 'circle' | 'pulse' | 'skeleton'
  color?: string
}

const LoadingSpinner: React.FC<LoadingSpinnerProps> = ({
  size = 'md',
  text,
  variant = 'circle',
  color
}) => {
  const defaultColor = useColorModeValue('brand.500', 'brand.200')
  const spinnerColor = color || defaultColor
  
  const sizes = {
    sm: { container: 20, spinner: 16, text: 'sm' },
    md: { container: 32, spinner: 24, text: 'md' },
    lg: { container: 48, spinner: 36, text: 'lg' },
    xl: { container: 64, spinner: 48, text: 'xl' }
  }

  const currentSize = sizes[size]

  // Dots Variant
  const DotsSpinner = () => (
    <motion.div
      style={{
        display: 'flex',
        gap: '4px',
        alignItems: 'center',
        justifyContent: 'center'
      }}
    >
      {[0, 1, 2].map((index) => (
        <motion.div
          key={index}
          style={{
            width: currentSize.spinner / 3,
            height: currentSize.spinner / 3,
            backgroundColor: spinnerColor,
            borderRadius: '50%'
          }}
          animate={{
            scale: [1, 1.5, 1],
            opacity: [0.5, 1, 0.5]
          }}
          transition={{
            duration: 0.6,
            repeat: Infinity,
            delay: index * 0.1
          }}
        />
      ))}
    </motion.div>
  )

  // Circle Variant
  const CircleSpinner = () => (
    <motion.div
      style={{
        width: currentSize.spinner,
        height: currentSize.spinner,
        border: `3px solid transparent`,
        borderTop: `3px solid ${spinnerColor}`,
        borderRadius: '50%'
      }}
      animate={{ rotate: 360 }}
      transition={{
        duration: 1,
        repeat: Infinity,
        ease: 'linear'
      }}
    />
  )

  // Pulse Variant
  const PulseSpinner = () => (
    <motion.div
      style={{
        width: currentSize.spinner,
        height: currentSize.spinner,
        backgroundColor: spinnerColor,
        borderRadius: '50%'
      }}
      animate={{
        scale: [1, 1.2, 1],
        opacity: [0.7, 1, 0.7]
      }}
      transition={{
        duration: 1.5,
        repeat: Infinity,
        ease: 'easeInOut'
      }}
    />
  )

  // Skeleton Variant
  const SkeletonSpinner = () => (
    <VStack spacing={2} w="full">
      {[...Array(3)].map((_, index) => (
        <motion.div
          key={index}
          style={{
            width: '100%',
            height: '16px',
            backgroundColor: useColorModeValue('#f0f0f0', '#2d3748'),
            borderRadius: '4px'
          }}
          animate={{
            opacity: [0.3, 0.7, 0.3]
          }}
          transition={{
            duration: 1.5,
            repeat: Infinity,
            delay: index * 0.2
          }}
        />
      ))}
    </VStack>
  )

  const renderSpinner = () => {
    switch (variant) {
      case 'dots':
        return <DotsSpinner />
      case 'circle':
        return <CircleSpinner />
      case 'pulse':
        return <PulseSpinner />
      case 'skeleton':
        return <SkeletonSpinner />
      default:
        return <CircleSpinner />
    }
  }

  return (
    <VStack spacing={3} align="center">
      <Box
        display="flex"
        alignItems="center"
        justifyContent="center"
        minH={currentSize.container}
        minW={currentSize.container}
      >
        {renderSpinner()}
      </Box>
      
      {text && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.2 }}
        >
          <Text
            fontSize={currentSize.text}
            color="gray.500"
            textAlign="center"
          >
            {text}
          </Text>
        </motion.div>
      )}
    </VStack>
  )
}

export default LoadingSpinner

// Quick loading variants for common use cases
export const ProductCardSkeleton = () => (
  <LoadingSpinner variant="skeleton" size="md" />
)

export const PageLoadingSpinner = () => (
  <LoadingSpinner 
    variant="circle" 
    size="lg" 
    text="Cargando página..." 
  />
)

export const ButtonLoadingSpinner = () => (
  <LoadingSpinner variant="dots" size="sm" />
)

export const SearchLoadingSpinner = () => (
  <LoadingSpinner 
    variant="pulse" 
    size="sm" 
    text="Buscando productos..." 
  />
)