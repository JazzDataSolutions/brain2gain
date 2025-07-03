/**
 * ErrorBoundary Component - React Error Boundary with Recovery
 * 
 * Catches and handles React component errors gracefully:
 * - Prevents entire app crashes
 * - Provides user-friendly error messages
 * - Offers error recovery options
 * - Integrates with centralized error handling
 * - Logs errors for debugging
 */

import React, { Component, ReactNode } from "react"
import {
  Alert,
  AlertIcon,
  AlertTitle,
  AlertDescription,
  Box,
  Button,
  VStack,
  Text,
  Code,
  Collapse,
  useDisclosure,
  Flex,
  Spacer
} from "@chakra-ui/react"
import { FiRefreshCw, FiChevronDown, FiChevronUp, FiHome, FiAlertTriangle } from "react-icons/fi"
import { errorHandler, ErrorContext } from "../../utils/errorHandling"

interface Props {
  children: ReactNode
  fallback?: ReactNode
  onError?: (error: Error, errorInfo: React.ErrorInfo) => void
  showDetails?: boolean
}

interface State {
  hasError: boolean
  error: Error | null
  errorInfo: React.ErrorInfo | null
  errorId: string | null
}

class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props)
    
    this.state = {
      hasError: false,
      error: null,
      errorInfo: null,
      errorId: null
    }
  }

  static getDerivedStateFromError(error: Error): Partial<State> {
    // Update state to render fallback UI
    return {
      hasError: true,
      error,
      errorId: `error_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
    }
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    // Log error to centralized error handler
    const context: ErrorContext = {
      component: 'ErrorBoundary',
      action: 'componentDidCatch',
      stackTrace: error.stack,
      url: window.location.href,
      userAgent: navigator.userAgent
    }

    const appError = errorHandler.processError(error, context)
    
    // Update state with error info
    this.setState({
      errorInfo,
      error
    })

    // Call custom error handler if provided
    if (this.props.onError) {
      this.props.onError(error, errorInfo)
    }

    // Log additional error info
    console.group('🔥 React Error Boundary Caught Error')
    console.error('Error:', error)
    console.error('Error Info:', errorInfo)
    console.error('Component Stack:', errorInfo.componentStack)
    console.groupEnd()
  }

  handleRetry = () => {
    // Reset error state to retry rendering
    this.setState({
      hasError: false,
      error: null,
      errorInfo: null,
      errorId: null
    })
  }

  handleGoHome = () => {
    // Navigate to home page
    window.location.href = '/'
  }

  handleReload = () => {
    // Reload the entire page
    window.location.reload()
  }

  render() {
    if (this.state.hasError) {
      // Custom fallback UI
      if (this.props.fallback) {
        return this.props.fallback
      }

      // Default error UI
      return <ErrorFallback 
        error={this.state.error}
        errorInfo={this.state.errorInfo}
        errorId={this.state.errorId}
        onRetry={this.handleRetry}
        onGoHome={this.handleGoHome}
        onReload={this.handleReload}
        showDetails={this.props.showDetails}
      />
    }

    return this.props.children
  }
}

// Error Fallback Component
interface ErrorFallbackProps {
  error: Error | null
  errorInfo: React.ErrorInfo | null
  errorId: string | null
  onRetry: () => void
  onGoHome: () => void
  onReload: () => void
  showDetails?: boolean
}

function ErrorFallback({ 
  error, 
  errorInfo, 
  errorId,
  onRetry, 
  onGoHome, 
  onReload,
  showDetails = false 
}: ErrorFallbackProps) {
  const { isOpen, onToggle } = useDisclosure()

  const getErrorMessage = () => {
    if (error?.message.includes('ChunkLoadError') || error?.message.includes('Loading chunk')) {
      return {
        title: "Error de Carga",
        description: "Hubo un problema cargando una parte de la aplicación. Esto suele ocurrir después de una actualización.",
        suggestion: "Intenta recargar la página para obtener la versión más reciente."
      }
    }

    if (error?.message.includes('NetworkError') || error?.message.includes('fetch')) {
      return {
        title: "Error de Conexión",
        description: "No se pudo conectar al servidor. Verifica tu conexión a internet.",
        suggestion: "Revisa tu conexión e intenta nuevamente."
      }
    }

    return {
      title: "Error Inesperado",
      description: "Ocurrió un error inesperado en la aplicación.",
      suggestion: "Intenta recargar la página o volver al inicio."
    }
  }

  const { title, description, suggestion } = getErrorMessage()

  return (
    <Box 
      minH="50vh" 
      display="flex" 
      alignItems="center" 
      justifyContent="center" 
      p={6}
      bg="gray.50"
    >
      <Box maxW="lg" w="full">
        <Alert
          status="error"
          variant="subtle"
          flexDirection="column"
          alignItems="center"
          justifyContent="center"
          textAlign="center"
          borderRadius="lg"
          p={8}
          bg="white"
          boxShadow="lg"
        >
          <AlertIcon boxSize="40px" mr={0} />
          
          <AlertTitle mt={4} mb={2} fontSize="xl">
            <Flex align="center" gap={2}>
              <FiAlertTriangle />
              {title}
            </Flex>
          </AlertTitle>
          
          <AlertDescription maxWidth="sm" mb={6}>
            <VStack spacing={3} textAlign="center">
              <Text>{description}</Text>
              <Text fontSize="sm" color="gray.600" fontStyle="italic">
                {suggestion}
              </Text>
            </VStack>
          </AlertDescription>

          {/* Action Buttons */}
          <VStack spacing={3} w="full" maxW="sm">
            <Flex w="full" gap={3}>
              <Button
                leftIcon={<FiRefreshCw />}
                colorScheme="blue"
                onClick={onRetry}
                flex={1}
                size="md"
              >
                Reintentar
              </Button>
              
              <Button
                leftIcon={<FiHome />}
                variant="outline"
                onClick={onGoHome}
                flex={1}
                size="md"
              >
                Ir al Inicio
              </Button>
            </Flex>

            <Button
              variant="ghost"
              size="sm"
              onClick={onReload}
              colorScheme="gray"
              w="full"
            >
              Recargar Página Completa
            </Button>
          </VStack>

          {/* Error Details (for development or debugging) */}
          {(showDetails || import.meta.env.DEV) && error && (
            <Box w="full" mt={6}>
              <Button
                variant="ghost"
                size="sm"
                onClick={onToggle}
                rightIcon={isOpen ? <FiChevronUp /> : <FiChevronDown />}
                colorScheme="gray"
              >
                {isOpen ? 'Ocultar' : 'Mostrar'} Detalles Técnicos
              </Button>
              
              <Collapse in={isOpen} animateOpacity>
                <Box
                  mt={4}
                  p={4}
                  bg="gray.100"
                  borderRadius="md"
                  textAlign="left"
                  fontSize="sm"
                  maxH="300px"
                  overflowY="auto"
                >
                  <VStack spacing={3} align="stretch">
                    {errorId && (
                      <Box>
                        <Text fontWeight="bold" color="gray.700">Error ID:</Text>
                        <Code colorScheme="red" fontSize="xs">{errorId}</Code>
                      </Box>
                    )}
                    
                    <Box>
                      <Text fontWeight="bold" color="gray.700">Mensaje:</Text>
                      <Code colorScheme="red" fontSize="xs" whiteSpace="pre-wrap">
                        {error.message}
                      </Code>
                    </Box>
                    
                    {error.stack && (
                      <Box>
                        <Text fontWeight="bold" color="gray.700">Stack Trace:</Text>
                        <Code colorScheme="red" fontSize="xs" whiteSpace="pre-wrap">
                          {error.stack}
                        </Code>
                      </Box>
                    )}
                    
                    {errorInfo?.componentStack && (
                      <Box>
                        <Text fontWeight="bold" color="gray.700">Component Stack:</Text>
                        <Code colorScheme="red" fontSize="xs" whiteSpace="pre-wrap">
                          {errorInfo.componentStack}
                        </Code>
                      </Box>
                    )}
                    
                    <Box>
                      <Text fontWeight="bold" color="gray.700">Timestamp:</Text>
                      <Code fontSize="xs">{new Date().toISOString()}</Code>
                    </Box>
                    
                    <Box>
                      <Text fontWeight="bold" color="gray.700">URL:</Text>
                      <Code fontSize="xs" wordBreak="break-all">{window.location.href}</Code>
                    </Box>
                  </VStack>
                </Box>
              </Collapse>
            </Box>
          )}
        </Alert>
      </Box>
    </Box>
  )
}

// Higher-order component to wrap components with error boundary
export function withErrorBoundary<P extends object>(
  Component: React.ComponentType<P>,
  errorBoundaryProps?: Omit<Props, 'children'>
) {
  const WrappedComponent = (props: P) => (
    <ErrorBoundary {...errorBoundaryProps}>
      <Component {...props} />
    </ErrorBoundary>
  )
  
  WrappedComponent.displayName = `withErrorBoundary(${Component.displayName || Component.name})`
  
  return WrappedComponent
}

export default ErrorBoundary