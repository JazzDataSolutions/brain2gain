import { useMutation, useQueryClient } from "@tanstack/react-query"
import { useNavigate } from "@tanstack/react-router"
import { useState, useEffect, useCallback } from "react"

import { AxiosError } from "axios"
import {
  type Body_login_login_access_token as AccessToken,
  type ApiError,
  LoginService,
  type UserRegister,
  UsersService,
} from "../client"
import { useAuth as useAuthContext } from "../contexts/AuthContext"
import useCustomToast from "./useCustomToast"

// Enhanced token validation with expiration check
const isLoggedIn = () => {
  const token = localStorage.getItem("access_token")
  if (!token) return false

  try {
    const payload = JSON.parse(atob(token.split('.')[1]))
    const now = Date.now() / 1000
    
    // Check if token is expired (with 5 minute buffer)
    if (payload.exp && payload.exp < (now + 300)) {
      return false
    }
    
    return true
  } catch (error) {
    console.error('Token validation error:', error)
    return false
  }
}

// Get token expiration time
const getTokenExpiration = (): Date | null => {
  const token = localStorage.getItem("access_token")
  if (!token) return null

  try {
    const payload = JSON.parse(atob(token.split('.')[1]))
    return payload.exp ? new Date(payload.exp * 1000) : null
  } catch (error) {
    return null
  }
}

// Check if user has admin privileges
const isAdmin = (user: any): boolean => {
  return user?.is_superuser === true
}

// Check if user has specific role
const hasRole = (user: any, role: string): boolean => {
  if (role === 'admin') return isAdmin(user)
  if (role === 'user') return user?.is_active === true
  return false
}

const useAuth = () => {
  const [error, setError] = useState<string | null>(null)
  const [tokenCheckInterval, setTokenCheckInterval] = useState<NodeJS.Timeout | null>(null)
  const navigate = useNavigate()
  const showToast = useCustomToast()
  const queryClient = useQueryClient()
  const {
    user,
    isLoading,
    login: contextLogin,
    logout: contextLogout,
  } = useAuthContext()

  // Enhanced logout with cleanup
  const enhancedLogout = useCallback(() => {
    // Clear token check interval
    if (tokenCheckInterval) {
      clearInterval(tokenCheckInterval)
      setTokenCheckInterval(null)
    }

    // Clear all auth-related localStorage
    localStorage.removeItem("access_token")
    localStorage.removeItem("refresh_token")
    localStorage.removeItem("user_data")
    
    // Clear admin audit log on logout for security
    localStorage.removeItem("admin_audit_log")
    
    // Invalidate all queries
    queryClient.clear()
    
    // Context logout
    contextLogout()
    
    showToast(
      "Sesión cerrada",
      "Has cerrado sesión correctamente",
      "info"
    )
  }, [contextLogout, queryClient, showToast, tokenCheckInterval])

  // Token refresh functionality (placeholder for future implementation)
  const refreshToken = useCallback(async () => {
    try {
      // TODO: Implement token refresh with backend
      const refreshToken = localStorage.getItem("refresh_token")
      if (!refreshToken) {
        throw new Error("No refresh token available")
      }

      // For now, just log the attempt
      console.log("🔄 Token refresh needed - implement with backend")
      
      // Placeholder: would call refresh endpoint
      // const response = await LoginService.refreshToken({ refresh_token: refreshToken })
      // localStorage.setItem("access_token", response.access_token)
      
      return false // Return false until implemented
    } catch (error) {
      console.error("Token refresh failed:", error)
      enhancedLogout()
      return false
    }
  }, [enhancedLogout])

  // Token expiration monitor
  const startTokenMonitoring = useCallback(() => {
    // Clear existing interval
    if (tokenCheckInterval) {
      clearInterval(tokenCheckInterval)
    }

    const interval = setInterval(() => {
      if (!isLoggedIn()) {
        console.log("🔒 Token expired, logging out...")
        enhancedLogout()
        return
      }

      const expiration = getTokenExpiration()
      if (expiration) {
        const now = new Date()
        const timeUntilExpiry = expiration.getTime() - now.getTime()
        const minutesUntilExpiry = Math.floor(timeUntilExpiry / (1000 * 60))

        // Warn when 10 minutes remaining
        if (minutesUntilExpiry <= 10 && minutesUntilExpiry > 0) {
          showToast(
            "Sesión próxima a expirar",
            `Tu sesión expirará en ${minutesUntilExpiry} minutos`,
            "warning"
          )
        }

        // Try to refresh when 5 minutes remaining
        if (minutesUntilExpiry <= 5 && minutesUntilExpiry > 0) {
          refreshToken()
        }
      }
    }, 60000) // Check every minute

    setTokenCheckInterval(interval)
  }, [tokenCheckInterval, enhancedLogout, refreshToken, showToast])

  // Start monitoring when user is logged in
  useEffect(() => {
    if (user && isLoggedIn()) {
      startTokenMonitoring()
    } else {
      if (tokenCheckInterval) {
        clearInterval(tokenCheckInterval)
        setTokenCheckInterval(null)
      }
    }

    return () => {
      if (tokenCheckInterval) {
        clearInterval(tokenCheckInterval)
      }
    }
  }, [user, startTokenMonitoring, tokenCheckInterval])

  // Validate session on app load
  useEffect(() => {
    if (!isLoading && !user && isLoggedIn()) {
      // Token exists but user not loaded - possible expired token
      enhancedLogout()
    }
  }, [user, isLoading, enhancedLogout])

  const signUpMutation = useMutation({
    mutationFn: (data: UserRegister) =>
      UsersService.registerUser({ requestBody: data }),

    onSuccess: () => {
      navigate({ to: "/login" })
      showToast(
        "Account created.",
        "Your account has been created successfully.",
        "success",
      )
    },
    onError: (err: ApiError) => {
      let errDetail = (err.body as any)?.detail

      if (err instanceof AxiosError) {
        errDetail = err.message
      }

      showToast("Something went wrong.", errDetail, "error")
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ["users"] })
    },
  })

  const login = async (data: AccessToken) => {
    const response = await LoginService.loginAccessToken({
      formData: data,
    })
    // Use the context login method for proper token management
    await contextLogin(response.access_token)
  }

  const loginMutation = useMutation({
    mutationFn: login,
    onSuccess: () => {
      navigate({ to: "/" })
    },
    onError: (err: ApiError) => {
      let errDetail = (err.body as any)?.detail

      if (err instanceof AxiosError) {
        errDetail = err.message
      }

      if (Array.isArray(errDetail)) {
        errDetail = "Something went wrong"
      }

      setError(errDetail)
    },
  })

  const logout = () => {
    enhancedLogout()
    navigate({ to: "/login" })
  }

  // Enhanced login with token monitoring
  const enhancedLogin = async (data: AccessToken) => {
    try {
      const response = await LoginService.loginAccessToken({
        formData: data,
      })
      
      // Store tokens
      localStorage.setItem("access_token", response.access_token)
      // TODO: Store refresh token when backend supports it
      // localStorage.setItem("refresh_token", response.refresh_token)
      
      // Use context login
      await contextLogin(response.access_token)
      
      // Start token monitoring
      setTimeout(() => {
        startTokenMonitoring()
      }, 1000)
      
    } catch (error) {
      throw error
    }
  }

  const loginMutation = useMutation({
    mutationFn: enhancedLogin,
    onSuccess: () => {
      showToast(
        "Bienvenido",
        "Has iniciado sesión correctamente",
        "success"
      )
      navigate({ to: "/" })
    },
    onError: (err: ApiError) => {
      let errDetail = (err.body as any)?.detail

      if (err instanceof AxiosError) {
        errDetail = err.message
      }

      if (Array.isArray(errDetail)) {
        errDetail = "Something went wrong"
      }

      setError(errDetail)
      
      showToast(
        "Error de autenticación",
        errDetail || "No se pudo iniciar sesión",
        "error"
      )
    },
  })

  return {
    signUpMutation,
    loginMutation,
    logout,
    user,
    isLoading,
    error,
    resetError: () => setError(null),
    // Enhanced auth utilities
    isAdmin: () => isAdmin(user),
    hasRole: (role: string) => hasRole(user, role),
    getTokenExpiration,
    refreshToken,
    tokenExpiresIn: () => {
      const expiration = getTokenExpiration()
      if (!expiration) return null
      return Math.max(0, expiration.getTime() - Date.now())
    }
  }
}

export { 
  isLoggedIn, 
  getTokenExpiration, 
  isAdmin, 
  hasRole 
}
export default useAuth
