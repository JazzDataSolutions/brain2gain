/**
 * ProtectedRoute Component - Generic Route Protection
 * 
 * Provides flexible route protection with customizable requirements
 * - Role-based access control
 * - Custom validation functions
 * - Flexible fallback components
 * - Audit logging integration
 */

import { ReactNode } from "react"
import {
  Alert,
  AlertIcon,
  AlertTitle,
  AlertDescription,
  Box,
  Button,
  Center,
  VStack,
  Text,
  useColorModeValue,
} from "@chakra-ui/react"
import { useNavigate } from "@tanstack/react-router"
import { FiLock, FiArrowLeft } from "react-icons/fi"
import useAuth from "../../hooks/useAuth"

interface ProtectedRouteProps {
  children: ReactNode
  /** Required role: 'admin', 'user', or custom validator */
  requireRole?: string | ((user: any) => boolean)
  /** Custom validation function */
  customValidator?: (user: any) => { isValid: boolean; reason?: string }
  /** Redirect path for unauthorized users */
  redirectTo?: string
  /** Custom fallback component */
  fallback?: ReactNode
  /** Show loading state while checking auth */
  showLoading?: boolean
  /** Enable audit logging */
  enableAudit?: boolean
}

const ProtectedRoute = ({
  children,
  requireRole,
  customValidator,
  redirectTo = "/login",
  fallback,
  showLoading = true,
  enableAudit = false
}: ProtectedRouteProps) => {
  const { user, isLoading, hasRole } = useAuth()
  const navigate = useNavigate()
  const bgColor = useColorModeValue("white", "gray.800")
  const borderColor = useColorModeValue("gray.200", "gray.600")

  // Audit logging
  const logAccess = (isAuthorized: boolean, reason?: string) => {
    if (!enableAudit) return

    const logEntry = {
      timestamp: new Date().toISOString(),
      route: window.location.pathname,
      userId: user?.id || 'anonymous',
      userEmail: user?.email || 'unknown',
      isAuthorized,
      reason,
      requiredRole: typeof requireRole === 'string' ? requireRole : 'custom'
    }

    console.log('🔐 Protected Route Access:', logEntry)

    // Store in audit log if needed
    const auditLog = JSON.parse(localStorage.getItem('route_audit_log') || '[]')
    auditLog.push(logEntry)
    if (auditLog.length > 50) auditLog.splice(0, auditLog.length - 50)
    localStorage.setItem('route_audit_log', JSON.stringify(auditLog))
  }

  // Check authentication first
  if (isLoading && showLoading) {
    return (
      <Center h="400px">
        <VStack spacing={4}>
          <Box>Loading...</Box>
          <Text fontSize="sm" color="gray.500">
            Verificando permisos...
          </Text>
        </VStack>
      </Center>
    )
  }

  if (!user) {
    logAccess(false, 'User not authenticated')
    
    if (fallback) return <>{fallback}</>
    
    return (
      <Center h="400px">
        <Box maxW="md" w="full" p={6}>
          <Alert status="warning" borderRadius="lg">
            <AlertIcon />
            <Box>
              <AlertTitle>Autenticación Requerida</AlertTitle>
              <AlertDescription>
                Debes iniciar sesión para acceder a esta página.
              </AlertDescription>
            </Box>
          </Alert>
          <VStack mt={4} spacing={2}>
            <Button
              colorScheme="blue"
              onClick={() => navigate({ to: redirectTo })}
            >
              Iniciar Sesión
            </Button>
          </VStack>
        </Box>
      </Center>
    )
  }

  // Role-based validation
  if (requireRole) {
    let hasAccess = false
    let accessReason = ''

    if (typeof requireRole === 'string') {
      hasAccess = hasRole(requireRole)
      accessReason = `Required role: ${requireRole}`
    } else if (typeof requireRole === 'function') {
      hasAccess = requireRole(user)
      accessReason = 'Custom role validation failed'
    }

    if (!hasAccess) {
      logAccess(false, accessReason)
      
      if (fallback) return <>{fallback}</>
      
      return (
        <Center h="400px">
          <Box maxW="md" w="full" p={6}>
            <Alert status="error" borderRadius="lg">
              <AlertIcon />
              <Box>
                <AlertTitle>Acceso Denegado</AlertTitle>
                <AlertDescription>
                  No tienes los permisos necesarios para acceder a esta página.
                </AlertDescription>
              </Box>
            </Alert>
            <VStack mt={4} spacing={2}>
              <Text fontSize="sm" color="gray.600" textAlign="center">
                Usuario: {user.email}<br />
                Rol requerido: {typeof requireRole === 'string' ? requireRole : 'Personalizado'}
              </Text>
              <Button
                leftIcon={<FiArrowLeft />}
                onClick={() => navigate({ to: "/" })}
              >
                Volver al Inicio
              </Button>
            </VStack>
          </Box>
        </Center>
      )
    }
  }

  // Custom validation
  if (customValidator) {
    const validation = customValidator(user)
    
    if (!validation.isValid) {
      logAccess(false, validation.reason || 'Custom validation failed')
      
      if (fallback) return <>{fallback}</>
      
      return (
        <Center h="400px">
          <Box maxW="md" w="full" p={6}>
            <Alert status="warning" borderRadius="lg">
              <AlertIcon />
              <Box>
                <AlertTitle>Acceso Restringido</AlertTitle>
                <AlertDescription>
                  {validation.reason || 'No cumples los requisitos para acceder a esta página.'}
                </AlertDescription>
              </Box>
            </Alert>
            <VStack mt={4} spacing={2}>
              <Button
                leftIcon={<FiArrowLeft />}
                onClick={() => navigate({ to: "/" })}
              >
                Volver
              </Button>
            </VStack>
          </Box>
        </Center>
      )
    }
  }

  // All validations passed
  logAccess(true, 'Access granted')
  
  return <>{children}</>
}

export default ProtectedRoute

// Convenience components for common use cases
export const AdminProtectedRoute = ({ children, ...props }: Omit<ProtectedRouteProps, 'requireRole'>) => (
  <ProtectedRoute requireRole="admin" enableAudit={true} {...props}>
    {children}
  </ProtectedRoute>
)

export const UserProtectedRoute = ({ children, ...props }: Omit<ProtectedRouteProps, 'requireRole'>) => (
  <ProtectedRoute requireRole="user" {...props}>
    {children}
  </ProtectedRoute>
)