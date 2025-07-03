/**
 * Centralized Error Handling System
 * 
 * Provides consistent error handling across the entire application:
 * - API error processing and user-friendly messages
 * - Error logging and reporting
 * - Retry mechanisms and offline fallbacks
 * - Error boundary integration
 * - Network error detection
 */

import { AxiosError } from "axios"

// Error types
export interface AppError {
  code: string
  message: string
  details?: any
  timestamp: Date
  userMessage: string
  canRetry: boolean
  severity: 'low' | 'medium' | 'high' | 'critical'
}

export interface ErrorContext {
  component?: string
  action?: string
  userId?: string
  url?: string
  userAgent?: string
  stackTrace?: string
}

export interface RetryConfig {
  maxAttempts: number
  baseDelay: number
  maxDelay: number
  backoffFactor: number
}

// Default retry configuration
const DEFAULT_RETRY_CONFIG: RetryConfig = {
  maxAttempts: 3,
  baseDelay: 1000,
  maxDelay: 10000,
  backoffFactor: 2
}

// Error categories and user-friendly messages
const ERROR_MESSAGES = {
  // Network errors
  NETWORK_ERROR: {
    message: "Error de conexión",
    userMessage: "No se pudo conectar al servidor. Verifica tu conexión a internet.",
    canRetry: true,
    severity: 'medium' as const
  },
  TIMEOUT_ERROR: {
    message: "Tiempo de espera agotado",
    userMessage: "La operación está tardando más de lo esperado. Inténtalo de nuevo.",
    canRetry: true,
    severity: 'medium' as const
  },
  
  // Authentication errors
  UNAUTHORIZED: {
    message: "No autorizado",
    userMessage: "Tu sesión ha expirado. Por favor, inicia sesión nuevamente.",
    canRetry: false,
    severity: 'high' as const
  },
  FORBIDDEN: {
    message: "Acceso denegado",
    userMessage: "No tienes permisos para realizar esta acción.",
    canRetry: false,
    severity: 'high' as const
  },
  
  // Validation errors
  VALIDATION_ERROR: {
    message: "Error de validación",
    userMessage: "Los datos proporcionados no son válidos. Revisa la información e inténtalo de nuevo.",
    canRetry: false,
    severity: 'low' as const
  },
  
  // Server errors
  SERVER_ERROR: {
    message: "Error interno del servidor",
    userMessage: "Hubo un problema en nuestros servidores. Estamos trabajando para solucionarlo.",
    canRetry: true,
    severity: 'high' as const
  },
  SERVICE_UNAVAILABLE: {
    message: "Servicio no disponible",
    userMessage: "El servicio no está disponible temporalmente. Inténtalo más tarde.",
    canRetry: true,
    severity: 'high' as const
  },
  
  // Resource errors
  NOT_FOUND: {
    message: "Recurso no encontrado",
    userMessage: "El elemento solicitado no se pudo encontrar.",
    canRetry: false,
    severity: 'medium' as const
  },
  CONFLICT: {
    message: "Conflicto de datos",
    userMessage: "Los datos han sido modificados por otro usuario. Actualiza la página e inténtalo de nuevo.",
    canRetry: false,
    severity: 'medium' as const
  },
  
  // Generic errors
  UNKNOWN_ERROR: {
    message: "Error desconocido",
    userMessage: "Ocurrió un error inesperado. Si el problema persiste, contacta al soporte.",
    canRetry: true,
    severity: 'medium' as const
  }
}

/**
 * Error Handler Class
 */
export class ErrorHandler {
  private static instance: ErrorHandler
  private errorLog: AppError[] = []
  private maxLogSize = 1000
  
  static getInstance(): ErrorHandler {
    if (!ErrorHandler.instance) {
      ErrorHandler.instance = new ErrorHandler()
    }
    return ErrorHandler.instance
  }

  /**
   * Process and categorize an error
   */
  processError(error: any, context?: ErrorContext): AppError {
    const timestamp = new Date()
    let appError: AppError

    // Handle Axios/HTTP errors
    if (error instanceof AxiosError || error.response) {
      appError = this.processHttpError(error, timestamp, context)
    }
    // Handle network errors
    else if (error.code === 'NETWORK_ERROR' || !navigator.onLine) {
      appError = this.createAppError('NETWORK_ERROR', error, timestamp, context)
    }
    // Handle timeout errors
    else if (error.code === 'ECONNABORTED' || error.message?.includes('timeout')) {
      appError = this.createAppError('TIMEOUT_ERROR', error, timestamp, context)
    }
    // Handle generic JavaScript errors
    else if (error instanceof Error) {
      appError = this.createAppError('UNKNOWN_ERROR', error, timestamp, context)
    }
    // Handle unknown error types
    else {
      appError = this.createAppError('UNKNOWN_ERROR', { message: String(error) }, timestamp, context)
    }

    // Log the error
    this.logError(appError, context)

    return appError
  }

  /**
   * Process HTTP errors from API responses
   */
  private processHttpError(error: AxiosError, timestamp: Date, context?: ErrorContext): AppError {
    const status = error.response?.status
    const responseData = error.response?.data as any

    let errorCode: keyof typeof ERROR_MESSAGES

    switch (status) {
      case 401:
        errorCode = 'UNAUTHORIZED'
        break
      case 403:
        errorCode = 'FORBIDDEN'
        break
      case 404:
        errorCode = 'NOT_FOUND'
        break
      case 409:
        errorCode = 'CONFLICT'
        break
      case 422:
        errorCode = 'VALIDATION_ERROR'
        break
      case 500:
      case 502:
      case 503:
        errorCode = status === 503 ? 'SERVICE_UNAVAILABLE' : 'SERVER_ERROR'
        break
      default:
        errorCode = 'UNKNOWN_ERROR'
    }

    const errorTemplate = ERROR_MESSAGES[errorCode]
    
    return {
      code: errorCode,
      message: errorTemplate.message,
      userMessage: responseData?.detail || errorTemplate.userMessage,
      details: {
        status,
        url: error.config?.url,
        method: error.config?.method,
        responseData,
        requestData: error.config?.data
      },
      timestamp,
      canRetry: errorTemplate.canRetry && status !== 401 && status !== 403,
      severity: errorTemplate.severity
    }
  }

  /**
   * Create an AppError from error template
   */
  private createAppError(
    errorCode: keyof typeof ERROR_MESSAGES, 
    originalError: any, 
    timestamp: Date,
    context?: ErrorContext
  ): AppError {
    const errorTemplate = ERROR_MESSAGES[errorCode]
    
    return {
      code: errorCode,
      message: errorTemplate.message,
      userMessage: errorTemplate.userMessage,
      details: {
        originalError: originalError.message || String(originalError),
        stack: originalError.stack,
        context
      },
      timestamp,
      canRetry: errorTemplate.canRetry,
      severity: errorTemplate.severity
    }
  }

  /**
   * Log error for debugging and monitoring
   */
  private logError(error: AppError, context?: ErrorContext) {
    // Add to in-memory log
    this.errorLog.unshift(error)
    
    // Maintain log size limit
    if (this.errorLog.length > this.maxLogSize) {
      this.errorLog = this.errorLog.slice(0, this.maxLogSize)
    }

    // Console logging based on severity
    const logData = {
      error,
      context,
      timestamp: error.timestamp.toISOString(),
      userAgent: navigator.userAgent,
      url: window.location.href
    }

    switch (error.severity) {
      case 'critical':
      case 'high':
        console.error('🔴 Error:', logData)
        break
      case 'medium':
        console.warn('🟠 Warning:', logData)
        break
      case 'low':
        console.info('🟡 Info:', logData)
        break
    }

    // Send to monitoring service in production
    if (import.meta.env.PROD && error.severity === 'critical') {
      this.sendToMonitoring(error, context)
    }
  }

  /**
   * Send critical errors to monitoring service
   */
  private async sendToMonitoring(error: AppError, context?: ErrorContext) {
    try {
      // This would integrate with your monitoring service (e.g., Sentry, LogRocket)
      const errorReport = {
        error,
        context,
        userAgent: navigator.userAgent,
        url: window.location.href,
        timestamp: error.timestamp.toISOString()
      }

      // Example: Send to your backend monitoring endpoint
      await fetch('/api/v1/monitoring/errors', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(errorReport)
      })
    } catch (monitoringError) {
      console.error('Failed to send error to monitoring:', monitoringError)
    }
  }

  /**
   * Retry mechanism with exponential backoff
   */
  async withRetry<T>(
    operation: () => Promise<T>,
    config: Partial<RetryConfig> = {},
    context?: ErrorContext
  ): Promise<T> {
    const retryConfig = { ...DEFAULT_RETRY_CONFIG, ...config }
    let lastError: any

    for (let attempt = 1; attempt <= retryConfig.maxAttempts; attempt++) {
      try {
        return await operation()
      } catch (error) {
        lastError = error
        const appError = this.processError(error, {
          ...context,
          action: `${context?.action || 'operation'} (attempt ${attempt}/${retryConfig.maxAttempts})`
        })

        // Don't retry if the error is not retryable
        if (!appError.canRetry) {
          throw error
        }

        // Don't retry on the last attempt
        if (attempt === retryConfig.maxAttempts) {
          break
        }

        // Calculate delay with exponential backoff
        const delay = Math.min(
          retryConfig.baseDelay * Math.pow(retryConfig.backoffFactor, attempt - 1),
          retryConfig.maxDelay
        )

        await new Promise(resolve => setTimeout(resolve, delay))
      }
    }

    throw lastError
  }

  /**
   * Get error logs for debugging
   */
  getErrorLog(): AppError[] {
    return [...this.errorLog]
  }

  /**
   * Clear error log
   */
  clearErrorLog(): void {
    this.errorLog = []
  }

  /**
   * Get error statistics
   */
  getErrorStats() {
    const now = new Date()
    const last24Hours = new Date(now.getTime() - 24 * 60 * 60 * 1000)
    
    const recentErrors = this.errorLog.filter(error => error.timestamp > last24Hours)
    
    return {
      total: this.errorLog.length,
      last24Hours: recentErrors.length,
      bySeverity: {
        critical: recentErrors.filter(e => e.severity === 'critical').length,
        high: recentErrors.filter(e => e.severity === 'high').length,
        medium: recentErrors.filter(e => e.severity === 'medium').length,
        low: recentErrors.filter(e => e.severity === 'low').length
      },
      byType: recentErrors.reduce((acc, error) => {
        acc[error.code] = (acc[error.code] || 0) + 1
        return acc
      }, {} as Record<string, number>)
    }
  }
}

// Export singleton instance
export const errorHandler = ErrorHandler.getInstance()

/**
 * Utility functions for common error handling patterns
 */

/**
 * Handle API errors with toast notifications
 */
export function handleApiError(error: any, showToast: (title: string, message: string, status: string) => void, context?: ErrorContext) {
  const appError = errorHandler.processError(error, context)
  
  showToast(
    appError.message,
    appError.userMessage,
    appError.severity === 'low' ? 'warning' : 'error'
  )
  
  return appError
}

/**
 * Wrap async operations with error handling
 */
export async function withErrorHandling<T>(
  operation: () => Promise<T>,
  onError: (error: AppError) => void,
  context?: ErrorContext
): Promise<T | null> {
  try {
    return await operation()
  } catch (error) {
    const appError = errorHandler.processError(error, context)
    onError(appError)
    return null
  }
}

/**
 * Network status detection
 */
export function isOnline(): boolean {
  return navigator.onLine
}

/**
 * Check if error is a network error
 */
export function isNetworkError(error: any): boolean {
  return (
    !isOnline() ||
    error.code === 'NETWORK_ERROR' ||
    error.message?.includes('Network Error') ||
    error.message?.includes('fetch')
  )
}

/**
 * Check if error is retryable
 */
export function isRetryableError(error: any): boolean {
  const appError = errorHandler.processError(error)
  return appError.canRetry
}

/**
 * Format error for display
 */
export function formatErrorForDisplay(error: any): { title: string; message: string; canRetry: boolean } {
  const appError = errorHandler.processError(error)
  
  return {
    title: appError.message,
    message: appError.userMessage,
    canRetry: appError.canRetry
  }
}

// Default export
export default errorHandler