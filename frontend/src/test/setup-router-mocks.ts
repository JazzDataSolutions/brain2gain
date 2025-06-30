import React from "react"
// setup-router-mocks.ts - Global mocks for TanStack Router
import { vi } from "vitest"

// Mock TanStack Router hooks and components
vi.mock("@tanstack/react-router", () => ({
  // Router components
  RouterProvider: ({ children }: { children: React.ReactNode }) => children,
  Router: vi.fn(),
  Link: React.forwardRef(({ children, to, ...props }: any, ref: any) =>
    React.createElement(
      "a",
      { href: to, ...props, "data-testid": "mock-link", ref },
      children,
    ),
  ),

  // Router hooks
  useRouter: vi.fn(() => ({
    navigate: vi.fn(),
    state: { location: { pathname: "/" } },
  })),

  useNavigate: vi.fn(() => vi.fn()),

  useRouterState: vi.fn(() => ({
    location: { pathname: "/" },
    matches: [],
  })),

  useParams: vi.fn(() => ({})),

  useSearch: vi.fn(() => ({})),

  // Router utilities
  createRouter: vi.fn(),
  createRoute: vi.fn(),
  createRootRoute: vi.fn(),
  createLazyRoute: vi.fn(),
  Outlet: ({ children }: { children?: React.ReactNode }) => children || null,

  // Navigation functions
  redirect: vi.fn(),
}))

// Mock useNavigate for components that use it
const mockNavigateFn = vi.fn()

// Export mock functions for use in tests
export const mockNavigate = mockNavigateFn
export const mockRouter = {
  navigate: vi.fn(),
  state: { location: { pathname: "/" } },
}
