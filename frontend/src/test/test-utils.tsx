import { ChakraProvider } from "@chakra-ui/react"
import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { type RenderOptions, render } from "@testing-library/react"
import type React from "react"
import type { ReactElement } from "react"
import { AuthProvider } from "../contexts/AuthContext"
import theme from "../theme"

// Mock TanStack Router components for testing
const MockRouterProvider = ({ children }: { children: React.ReactNode }) => {
  return <div data-testid="mock-router-provider">{children}</div>
}

const MockLink = ({ children, to, ...props }: any) => {
  return (
    <a href={to} {...props} data-testid="mock-link">
      {children}
    </a>
  )
}

// Create a custom render function that includes providers
const AllTheProviders = ({ children }: { children: React.ReactNode }) => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
    },
  })

  return (
    <MockRouterProvider>
      <AuthProvider>
        <ChakraProvider theme={theme}>
          <QueryClientProvider client={queryClient}>
            {children}
          </QueryClientProvider>
        </ChakraProvider>
      </AuthProvider>
    </MockRouterProvider>
  )
}

const customRender = (
  ui: ReactElement,
  options?: Omit<RenderOptions, "wrapper">,
) => render(ui, { wrapper: AllTheProviders, ...options })

export * from "@testing-library/react"
export { customRender as render }

// Export mock components for manual use in tests if needed
export { MockRouterProvider, MockLink }
