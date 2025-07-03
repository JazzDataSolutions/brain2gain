/**
 * AdminGuard Component - Critical Security Component
 * 
 * Protects admin routes with robust authentication and authorization
 * - Verifies is_superuser status
 * - Handles token expiration
 * - Provides loading and error states
 * - Implements audit logging
 */

import { ReactNode, useEffect, useState } from "react"
import {
  Alert,
  AlertIcon,
  AlertTitle,
  AlertDescription,
  Box,
  Button,
  Center,
  Spinner,
  VStack,
  Text,
  useColorModeValue,
} from "@chakra-ui/react"
import { useNavigate } from "@tanstack/react-router"
import { FiShield, FiArrowLeft, FiUser } from "react-icons/fi"
import useAuth, { isLoggedIn } from "../../hooks/useAuth"
import useCustomToast from "../../hooks/useCustomToast"

interface AdminGuardProps {
  children: ReactNode
  fallback?: ReactNode
  redirectTo?: string
}

interface AccessAttempt {
  timestamp: string
  userId?: string
  userEmail?: string
  isAuthorized: boolean
  route: string
  userAgent: string
}

const AdminGuard = ({ 
  children, 
  fallback,
  redirectTo = "/login"
}: AdminGuardProps) => {
  const { user, isLoading, logout } = useAuth()
  const navigate = useNavigate()
  const showToast = useCustomToast()
  const [verificationStatus, setVerificationStatus] = useState<'checking' | 'authorized' | 'unauthorized' | 'error'>('checking')
  const [errorMessage, setErrorMessage] = useState<string>('')

  const bgColor = useColorModeValue("white", "gray.800")
  const borderColor = useColorModeValue("gray.200", "gray.600")

  // Audit logging function
  const logAccessAttempt = (isAuthorized: boolean, errorReason?: string) => {
    const attempt: AccessAttempt = {
      timestamp: new Date().toISOString(),
      userId: user?.id || 'unknown',
      userEmail: user?.email || 'unknown',
      isAuthorized,
      route: window.location.pathname,
      userAgent: navigator.userAgent
    }

    // Store in localStorage for audit (in production, send to backend)
    const auditLog = JSON.parse(localStorage.getItem('admin_audit_log') || '[]')
    auditLog.push(attempt)
    
    // Keep only last 100 entries
    if (auditLog.length > 100) {
      auditLog.splice(0, auditLog.length - 100)
    }
    
    localStorage.setItem('admin_audit_log', JSON.stringify(auditLog))

    // Log to console for development
    console.log('🔒 Admin Access Attempt:', {
      ...attempt,
      errorReason
    })

    // Show warning for unauthorized attempts
    if (!isAuthorized) {
      showToast(
        "Acceso Denegado",
        errorReason || "No tienes permisos para acceder al panel administrativo",
        "error"
      )
    }
  }

  // Token validation
  const validateToken = async () => {
    try {
      if (!isLoggedIn()) {
        setVerificationStatus('unauthorized')
        logAccessAttempt(false, 'No token found')
        return
      }

      // Check token expiration
      const token = localStorage.getItem('access_token')
      if (token) {
        try {
          const payload = JSON.parse(atob(token.split('.')[1]))
          const now = Date.now() / 1000
          
          if (payload.exp && payload.exp < now) {
            setVerificationStatus('unauthorized')
            logAccessAttempt(false, 'Token expired')
            logout()
            return
          }
        } catch (tokenError) {
          console.error('Token validation error:', tokenError)
          setVerificationStatus('error')
          setErrorMessage('Token inválido')
          logAccessAttempt(false, 'Invalid token format')
          return
        }
      }

      // Check user authentication status
      if (isLoading) {
        return // Still loading, wait
      }

      if (!user) {
        setVerificationStatus('unauthorized')
        logAccessAttempt(false, 'User not authenticated')
        return
      }

      // Critical: Check superuser status
      if (!user.is_superuser) {
        setVerificationStatus('unauthorized')
        logAccessAttempt(false, `User ${user.email} is not superuser`)
        return
      }

      // All checks passed
      setVerificationStatus('authorized')
      logAccessAttempt(true)

    } catch (error) {
      console.error('AdminGuard validation error:', error)
      setVerificationStatus('error')
      setErrorMessage('Error de verificación de permisos')
      logAccessAttempt(false, `Validation error: ${error}`)
    }
  }

  useEffect(() => {
    validateToken()
  }, [user, isLoading])

  // Auto-redirect for unauthorized users
  useEffect(() => {
    if (verificationStatus === 'unauthorized') {
      const timer = setTimeout(() => {
        navigate({ to: redirectTo })
      }, 3000) // 3 second delay to show message

      return () => clearTimeout(timer)
    }
  }, [verificationStatus, navigate, redirectTo])

  // Loading state
  if (verificationStatus === 'checking' || isLoading) {
    return (
      <Center h="100vh" bg={bgColor}>
        <VStack spacing={4}>
          <Spinner size="xl" color="blue.500" thickness="4px" />
          <Text fontSize="lg" color="gray.600">
            Verificando permisos administrativos...
          </Text>
          <Text fontSize="sm" color="gray.500">
            🔒 Validando credenciales de seguridad
          </Text>
        </VStack>
      </Center>
    )
  }

  // Error state
  if (verificationStatus === 'error') {
    return (
      <Center h="100vh" bg={bgColor}>
        <Box maxW="md" w="full" p={6}>
          <Alert status="error" borderRadius="lg" border="1px" borderColor={borderColor}>
            <AlertIcon />
            <Box>
              <AlertTitle>Error de Seguridad</AlertTitle>
              <AlertDescription>
                {errorMessage || 'Ocurrió un error verificando tus permisos administrativos.'}
              </AlertDescription>
            </Box>
          </Alert>
          <VStack mt={6} spacing={4}>
            <Button
              leftIcon={<FiArrowLeft />}
              colorScheme="blue"
              onClick={() => navigate({ to: "/" })}
            >
              Volver al Inicio
            </Button>
            <Button
              variant="outline"
              onClick={() => window.location.reload()}
            >
              Reintentar
            </Button>
          </VStack>
        </Box>
      </Center>
    )
  }

  // Unauthorized state
  if (verificationStatus === 'unauthorized') {
    return fallback || (
      <Center h="100vh" bg={bgColor}>
        <Box maxW="md" w="full" p={6}>
          <Alert status="warning" borderRadius="lg" border="1px" borderColor={borderColor}>
            <AlertIcon />
            <Box>
              <AlertTitle>Acceso Restringido</AlertTitle>
              <AlertDescription>
                No tienes permisos para acceder al panel administrativo. 
                Solo usuarios con permisos de administrador pueden acceder.
              </AlertDescription>
            </Box>
          </Alert>
          
          <VStack mt={6} spacing={4}>
            <Box textAlign="center" p={4} bg="orange.50" borderRadius="md" border="1px" borderColor="orange.200">
              <FiShield size={24} color="orange" />
              <Text fontSize="sm" color="gray.600" mt={2}>
                <strong>Información del Usuario:</strong><br />
                Email: {user?.email || 'No disponible'}<br />
                Tipo: {user?.is_superuser ? 'Administrador' : 'Usuario Regular'}<br />
                Estado: {user?.is_active ? 'Activo' : 'Inactivo'}
              </Text>
            </Box>

            <VStack spacing={2}>
              <Button
                leftIcon={<FiArrowLeft />}
                colorScheme="blue"
                onClick={() => navigate({ to: "/" })}
              >
                Volver al Inicio
              </Button>
              
              <Button
                leftIcon={<FiUser />}
                variant="outline"
                onClick={() => navigate({ to: "/store" })}
              >
                Ir a la Tienda
              </Button>

              <Text fontSize="xs" color="gray.500" textAlign="center" mt={2}>
                Serás redirigido automáticamente en unos segundos...
              </Text>
            </VStack>
          </VStack>
        </Box>
      </Center>
    )
  }

  // Authorized - render children
  return <>{children}</>
}

export default AdminGuard

// Utility function to get audit log
export const getAdminAuditLog = (): AccessAttempt[] => {
  return JSON.parse(localStorage.getItem('admin_audit_log') || '[]')
}

// Utility function to clear audit log (admin only)
export const clearAdminAuditLog = (): void => {
  localStorage.removeItem('admin_audit_log')
}