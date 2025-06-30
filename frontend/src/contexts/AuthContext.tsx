import { jwtDecode } from "jwt-decode"
import type React from "react"
import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useState,
} from "react"
import { OpenAPI } from "../client"
import type { UserPublic } from "../client"

interface JWTPayload {
  sub: string
  exp: number
  iat: number
  user_id: string
  email: string
  role: string
}

interface AuthContextType {
  user: UserPublic | null
  token: string | null
  isAuthenticated: boolean
  isLoading: boolean
  login: (token: string) => Promise<void>
  logout: () => void
  refreshToken: () => Promise<boolean>
  checkAuth: () => Promise<boolean>
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export const useAuth = () => {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error("useAuth must be used within an AuthProvider")
  }
  return context
}

interface AuthProviderProps {
  children: React.ReactNode
}

const TOKEN_KEY = "access_token"
const REFRESH_TOKEN_KEY = "refresh_token"
const TOKEN_REFRESH_THRESHOLD = 5 * 60 * 1000 // 5 minutes in milliseconds

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [user, setUser] = useState<UserPublic | null>(null)
  const [token, setToken] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  const isAuthenticated = Boolean(user && token)

  // Get user info from token
  const getUserFromToken = useCallback((token: string): UserPublic | null => {
    try {
      const decoded = jwtDecode<JWTPayload>(token)
      return {
        id: decoded.user_id,
        email: decoded.email,
        full_name: "", // This would need to come from the API
        is_active: true,
        is_superuser: decoded.role === "admin",
      }
    } catch (error) {
      console.error("Error decoding token:", error)
      return null
    }
  }, [])

  // Check if token is expired or will expire soon
  const isTokenExpired = useCallback(
    (token: string, threshold = 0): boolean => {
      try {
        const decoded = jwtDecode<JWTPayload>(token)
        const currentTime = Date.now()
        const expirationTime = decoded.exp * 1000 // Convert to milliseconds
        return currentTime >= expirationTime - threshold
      } catch (error) {
        return true
      }
    },
    [],
  )

  // Login function
  const login = useCallback(
    async (newToken: string): Promise<void> => {
      try {
        if (isTokenExpired(newToken)) {
          throw new Error("Token is expired")
        }

        const userData = getUserFromToken(newToken)
        if (!userData) {
          throw new Error("Invalid token format")
        }

        // Store token
        localStorage.setItem(TOKEN_KEY, newToken)

        // Update OpenAPI configuration
        OpenAPI.TOKEN = async () => newToken

        // Update state
        setToken(newToken)
        setUser(userData)

        console.log("Login successful for user:", userData.email)
      } catch (error) {
        console.error("Login error:", error)
        throw error
      }
    },
    [isTokenExpired, getUserFromToken],
  )

  // Logout function
  const logout = useCallback(() => {
    // Clear storage
    localStorage.removeItem(TOKEN_KEY)
    localStorage.removeItem(REFRESH_TOKEN_KEY)

    // Reset OpenAPI configuration
    OpenAPI.TOKEN = async () => ""

    // Reset state
    setToken(null)
    setUser(null)

    console.log("User logged out")
  }, [])

  // Refresh token function
  const refreshToken = useCallback(async (): Promise<boolean> => {
    try {
      const refreshTokenValue = localStorage.getItem(REFRESH_TOKEN_KEY)
      if (!refreshTokenValue) {
        return false
      }

      // TODO: Implement refresh token API call
      // For now, we'll check if the current token is still valid
      const currentToken = localStorage.getItem(TOKEN_KEY)
      if (!currentToken || isTokenExpired(currentToken)) {
        logout()
        return false
      }

      // If token is still valid, no need to refresh
      return true
    } catch (error) {
      console.error("Token refresh error:", error)
      logout()
      return false
    }
  }, [isTokenExpired, logout])

  // Check authentication status
  const checkAuth = useCallback(async (): Promise<boolean> => {
    try {
      const storedToken = localStorage.getItem(TOKEN_KEY)

      if (!storedToken) {
        return false
      }

      // Check if token is expired
      if (isTokenExpired(storedToken)) {
        // Try to refresh token
        const refreshSuccess = await refreshToken()
        if (!refreshSuccess) {
          logout()
          return false
        }
      }

      // Check if token will expire soon and refresh proactively
      if (isTokenExpired(storedToken, TOKEN_REFRESH_THRESHOLD)) {
        console.log("Token will expire soon, attempting refresh...")
        await refreshToken()
      }

      // Get user data from token
      const userData = getUserFromToken(storedToken)
      if (!userData) {
        logout()
        return false
      }

      // Update OpenAPI configuration
      OpenAPI.TOKEN = async () => storedToken

      // Update state
      setToken(storedToken)
      setUser(userData)

      return true
    } catch (error) {
      console.error("Auth check error:", error)
      logout()
      return false
    }
  }, [isTokenExpired, refreshToken, logout, getUserFromToken])

  // Initialize authentication on mount
  useEffect(() => {
    const initAuth = async () => {
      setIsLoading(true)
      try {
        await checkAuth()
      } catch (error) {
        console.error("Auth initialization error:", error)
      } finally {
        setIsLoading(false)
      }
    }

    initAuth()
  }, [checkAuth])

  // Set up periodic token refresh check
  useEffect(() => {
    if (!isAuthenticated) return

    const interval = setInterval(async () => {
      const currentToken = localStorage.getItem(TOKEN_KEY)
      if (
        currentToken &&
        isTokenExpired(currentToken, TOKEN_REFRESH_THRESHOLD)
      ) {
        console.log("Periodic token refresh check triggered")
        await refreshToken()
      }
    }, 60000) // Check every minute

    return () => clearInterval(interval)
  }, [isAuthenticated, isTokenExpired, refreshToken])

  // Handle visibility change to check auth when tab becomes visible
  useEffect(() => {
    const handleVisibilityChange = () => {
      if (document.visibilityState === "visible" && isAuthenticated) {
        checkAuth()
      }
    }

    document.addEventListener("visibilitychange", handleVisibilityChange)
    return () =>
      document.removeEventListener("visibilitychange", handleVisibilityChange)
  }, [isAuthenticated, checkAuth])

  const value: AuthContextType = {
    user,
    token,
    isAuthenticated,
    isLoading,
    login,
    logout,
    refreshToken,
    checkAuth,
  }

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}
