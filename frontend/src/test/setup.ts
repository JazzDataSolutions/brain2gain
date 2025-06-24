import '@testing-library/jest-dom'
import { vi } from 'vitest'

// Mock framer-motion FIRST before other imports
vi.mock('framer-motion', () => {
  const React = require('react')
  
  // Create a motion factory that works with any component
  const createMotionComponent = (Component: any) => {
    return React.forwardRef((props: any, ref: any) => {
      // Filter out motion-specific props
      const { 
        initial, animate, exit, transition, variants, 
        whileHover, whileTap, whileFocus, whileInView,
        drag, dragConstraints, onDrag, onDragEnd,
        layout, layoutId, style,
        onHoverStart, onHoverEnd, onAnimationStart, onAnimationComplete,
        onDragStart, onDragTransitionEnd, onTap, onTapStart, onTapCancel,
        onPan, onPanStart, onPanEnd, onViewportEnter, onViewportLeave,
        ...restProps 
      } = props
      
      return React.createElement(Component, {
        ...restProps,
        ref,
        style
      })
    })
  }
  
  // Simple motion function that returns wrapped component
  const motion = (Component: any) => createMotionComponent(Component)
  
  // Add properties for motion.div, motion.span, etc.
  motion.div = createMotionComponent('div')
  motion.span = createMotionComponent('span')
  motion.img = createMotionComponent('img')
  motion.button = createMotionComponent('button')
  motion.a = createMotionComponent('a')
  motion.section = createMotionComponent('section')
  
  return {
    motion,
    AnimatePresence: ({ children }: { children: React.ReactNode }) => children,
    useAnimation: () => ({
      start: vi.fn(),
      stop: vi.fn(), 
      set: vi.fn(),
      mount: vi.fn(),
      unmount: vi.fn()
    }),
    useReducedMotion: () => false,
    useMotionValue: (initial: any) => ({
      get: () => initial,
      set: vi.fn(),
      stop: vi.fn()
    }),
    useTransform: () => ({
      get: () => 0,
      set: vi.fn()
    }),
    useSpring: (initial: any) => ({
      get: () => initial,
      set: vi.fn()
    })
  }
})

// Import router mocks
import './setup-router-mocks'

// Mock AuthContext to prevent act() warnings
vi.mock('../contexts/AuthContext', () => {
  const React = require('react')
  return {
    useAuth: vi.fn(() => ({
      user: null,
      token: null,
      isAuthenticated: false,
      isLoading: false,
      login: vi.fn(),
      logout: vi.fn(),
      refreshToken: vi.fn(),
      checkAuth: vi.fn(),
    })),
    AuthProvider: ({ children }: { children: React.ReactNode }) => children,
  }
})

// Mock environment variables
process.env.VITE_API_URL = 'http://localhost:8000'
process.env.VITE_WS_URL = 'ws://localhost:8000'

// Mock localStorage
const localStorageMock = (() => {
  let store: Record<string, string> = {}

  return {
    getItem: (key: string) => store[key] || null,
    setItem: (key: string, value: string) => {
      store[key] = String(value)
    },
    removeItem: (key: string) => {
      delete store[key]
    },
    clear: () => {
      store = {}
    },
  }
})()

Object.defineProperty(window, 'localStorage', {
  value: localStorageMock,
})

// Mock matchMedia
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: vi.fn().mockImplementation((query) => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: vi.fn(), // deprecated
    removeListener: vi.fn(), // deprecated
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    dispatchEvent: vi.fn(),
  })),
})