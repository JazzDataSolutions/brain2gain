import { ChakraProvider } from "@chakra-ui/react"
import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { RouterProvider, createRouter } from "@tanstack/react-router"
import { StrictMode } from "react"
import ReactDOM from "react-dom/client"
import { OpenAPI } from "./client"
import ErrorBoundary from "./components/ErrorBoundary" // Importamos el ErrorBoundary
import { AuthProvider } from "./contexts/AuthContext"
import { routeTree } from "./routeTree.gen"
import "./styles/globals.css"
import "./styles/landing.css"
import theme from "./theme"

OpenAPI.BASE = import.meta.env.VITE_API_URL
OpenAPI.TOKEN = async () => {
  return localStorage.getItem("access_token") || ""
}

const queryClient = new QueryClient()

const router = createRouter({ routeTree })
// Google Tag Manager - push initial pageview and on route changes
window.dataLayer = window.dataLayer || []
window.dataLayer.push({
  event: "pageview",
  pagePath: window.location.pathname + window.location.search,
})
router.subscribe(() => {
  window.dataLayer = window.dataLayer || []
  window.dataLayer.push({
    event: "pageview",
    pagePath: window.location.pathname + window.location.search,
  })
})
declare module "@tanstack/react-router" {
  interface Register {
    router: typeof router
  }
}

ReactDOM.createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <AuthProvider>
      <ChakraProvider theme={theme}>
        <QueryClientProvider client={queryClient}>
          <ErrorBoundary
            showDetails={import.meta.env.DEV}
            onError={(error, errorInfo) => {
              // Custom error handling - could send to analytics service
              console.warn("Application error caught by boundary:", error)
            }}
          >
            <RouterProvider router={router} />
          </ErrorBoundary>
        </QueryClientProvider>
      </ChakraProvider>
    </AuthProvider>
  </StrictMode>,
)
