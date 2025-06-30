import { type VariantProps, cva } from "class-variance-authority"
import React from "react"
import { cn } from "../../utils"

const inputVariants = cva(
  "block w-full rounded-md shadow-sm transition-colors duration-200 focus:outline-none focus:ring-2 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed",
  {
    variants: {
      variant: {
        default:
          "border border-secondary-300 bg-white text-secondary-900 placeholder-secondary-400 focus:border-primary-500 focus:ring-primary-500",
        error:
          "border border-error-300 bg-white text-secondary-900 placeholder-secondary-400 focus:border-error-500 focus:ring-error-500",
        success:
          "border border-success-300 bg-white text-secondary-900 placeholder-secondary-400 focus:border-success-500 focus:ring-success-500",
      },
      size: {
        sm: "px-2 py-1 text-sm",
        md: "px-3 py-2 text-sm",
        lg: "px-4 py-3 text-base",
      },
    },
    defaultVariants: {
      variant: "default",
      size: "md",
    },
  },
)

export interface InputProps
  extends Omit<React.InputHTMLAttributes<HTMLInputElement>, "size">,
    VariantProps<typeof inputVariants> {
  label?: string
  error?: string
  helperText?: string
  leftIcon?: React.ReactNode
  rightIcon?: React.ReactNode
}

const Input = React.forwardRef<HTMLInputElement, InputProps>(
  (
    {
      className,
      variant,
      size,
      label,
      error,
      helperText,
      leftIcon,
      rightIcon,
      id,
      ...props
    },
    ref,
  ) => {
    const inputId = id || `input-${Math.random().toString(36).substr(2, 9)}`
    const hasError = Boolean(error)
    const actualVariant = hasError ? "error" : variant

    return (
      <div className="form-group">
        {label && (
          <label htmlFor={inputId} className="form-label">
            {label}
          </label>
        )}
        <div className="relative">
          {leftIcon && (
            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
              <span className="text-secondary-400">{leftIcon}</span>
            </div>
          )}
          <input
            id={inputId}
            ref={ref}
            className={cn(
              inputVariants({ variant: actualVariant, size }),
              leftIcon && "pl-10",
              rightIcon && "pr-10",
              className,
            )}
            {...props}
          />
          {rightIcon && (
            <div className="absolute inset-y-0 right-0 pr-3 flex items-center pointer-events-none">
              <span className="text-secondary-400">{rightIcon}</span>
            </div>
          )}
        </div>
        {error && <p className="form-error">{error}</p>}
        {helperText && !error && (
          <p className="mt-1 text-sm text-secondary-600">{helperText}</p>
        )}
      </div>
    )
  },
)

Input.displayName = "Input"

export { Input, inputVariants }
