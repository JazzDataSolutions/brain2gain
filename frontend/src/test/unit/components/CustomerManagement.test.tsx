/**
 * Unit tests for CustomerManagement component.
 * Tests CRUD operations, filtering, and data management.
 */

import { fireEvent, screen, waitFor } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { beforeEach, describe, expect, it, vi } from "vitest"
import { render } from "../../test-utils"
import CustomerManagement from "../../../components/Admin/CustomerManagement"

// Mock the UsersService
vi.mock("../../../client", () => ({
  UsersService: {
    readUsers: vi.fn(),
    createUser: vi.fn(),
    updateUser: vi.fn(),
    deleteUser: vi.fn(),
  },
}))

// Mock toast
vi.mock("@chakra-ui/react", async () => {
  const actual = await vi.importActual("@chakra-ui/react")
  return {
    ...actual,
    useToast: () => vi.fn(),
  }
})

// Mock customers data
const mockCustomers = [
  {
    id: "1",
    email: "juan@email.com",
    full_name: "Juan Pérez",
    is_active: true,
    is_superuser: false,
    created_at: "2024-01-01T00:00:00Z",
    last_login: "2024-01-10T10:00:00Z",
  },
  {
    id: "2",
    email: "maria@email.com", 
    full_name: "María García",
    is_active: true,
    is_superuser: true,
    created_at: "2024-01-15T00:00:00Z",
    last_login: "2024-01-10T15:30:00Z",
  },
  {
    id: "3",
    email: "inactive@email.com",
    full_name: "Usuario Inactivo",
    is_active: false,
    is_superuser: false,
    created_at: "2023-12-01T00:00:00Z",
  },
]

describe("CustomerManagement Component", () => {
  const user = userEvent.setup()

  beforeEach(() => {
    vi.clearAllMocks()
    
    const { UsersService } = require("../../../client")
    UsersService.readUsers.mockResolvedValue(mockCustomers)
    UsersService.createUser.mockResolvedValue({
      id: "4",
      email: "nuevo@email.com",
      full_name: "Nuevo Usuario",
      is_active: true,
      is_superuser: false,
      created_at: new Date().toISOString(),
    })
    UsersService.updateUser.mockResolvedValue(mockCustomers[0])
    UsersService.deleteUser.mockResolvedValue(true)
  })

  describe("Data Loading and Display", () => {
    it("should display loading state initially", () => {
      render(<CustomerManagement />)
      
      expect(screen.getByRole("status")).toBeInTheDocument()
    })

    it("should load and display customers", async () => {
      render(<CustomerManagement />)
      
      await waitFor(() => {
        expect(screen.getByText("Juan Pérez")).toBeInTheDocument()
        expect(screen.getByText("María García")).toBeInTheDocument()
        expect(screen.getByText("Usuario Inactivo")).toBeInTheDocument()
      })
    })

    it("should display customer statistics", async () => {
      render(<CustomerManagement />)
      
      await waitFor(() => {
        expect(screen.getByText("3")).toBeInTheDocument() // Total customers
        expect(screen.getByText("1")).toBeInTheDocument() // New this month
        expect(screen.getByText("1")).toBeInTheDocument() // VIP customers
      })
    })

    it("should display customer status badges", async () => {
      render(<CustomerManagement />)
      
      await waitFor(() => {
        const activeBadges = screen.getAllByText("Activo")
        const inactiveBadge = screen.getByText("Inactivo")
        const adminBadge = screen.getByText("Admin")
        
        expect(activeBadges).toHaveLength(2)
        expect(inactiveBadge).toBeInTheDocument()
        expect(adminBadge).toBeInTheDocument()
      })
    })
  })

  describe("Search and Filtering", () => {
    it("should filter customers by search term", async () => {
      render(<CustomerManagement />)
      
      await waitFor(() => {
        expect(screen.getByText("Juan Pérez")).toBeInTheDocument()
      })
      
      const searchInput = screen.getByPlaceholderText("Buscar por email o nombre...")
      await user.type(searchInput, "juan")
      
      await waitFor(() => {
        expect(screen.getByText("Juan Pérez")).toBeInTheDocument()
        expect(screen.queryByText("María García")).not.toBeInTheDocument()
      })
    })

    it("should filter customers by status", async () => {
      render(<CustomerManagement />)
      
      await waitFor(() => {
        expect(screen.getByText("Juan Pérez")).toBeInTheDocument()
      })
      
      const statusFilter = screen.getByDisplayValue("Todos los clientes")
      await user.selectOptions(statusFilter, "inactive")
      
      await waitFor(() => {
        expect(screen.queryByText("Juan Pérez")).not.toBeInTheDocument()
        expect(screen.getByText("Usuario Inactivo")).toBeInTheDocument()
      })
    })

    it("should filter VIP customers", async () => {
      render(<CustomerManagement />)
      
      await waitFor(() => {
        expect(screen.getByText("María García")).toBeInTheDocument()
      })
      
      const statusFilter = screen.getByDisplayValue("Todos los clientes")
      await user.selectOptions(statusFilter, "vip")
      
      await waitFor(() => {
        expect(screen.queryByText("Juan Pérez")).not.toBeInTheDocument()
        expect(screen.getByText("María García")).toBeInTheDocument()
      })
    })

    it("should search by email", async () => {
      render(<CustomerManagement />)
      
      await waitFor(() => {
        expect(screen.getByText("Juan Pérez")).toBeInTheDocument()
      })
      
      const searchInput = screen.getByPlaceholderText("Buscar por email o nombre...")
      await user.type(searchInput, "maria@email.com")
      
      await waitFor(() => {
        expect(screen.queryByText("Juan Pérez")).not.toBeInTheDocument()
        expect(screen.getByText("María García")).toBeInTheDocument()
      })
    })
  })

  describe("Customer Creation", () => {
    it("should open create customer modal", async () => {
      render(<CustomerManagement />)
      
      const createButton = screen.getByText("Nuevo Cliente")
      await user.click(createButton)
      
      expect(screen.getByText("Crear Nuevo Cliente")).toBeInTheDocument()
    })

    it("should create new customer", async () => {
      const { UsersService } = require("../../../client")
      
      render(<CustomerManagement />)
      
      // Open create modal
      const createButton = screen.getByText("Nuevo Cliente")
      await user.click(createButton)
      
      // Fill form
      const emailInput = screen.getByPlaceholderText("cliente@ejemplo.com")
      const nameInput = screen.getByPlaceholderText("Nombre completo del cliente")
      const passwordInput = screen.getByPlaceholderText("Contraseña del cliente")
      
      await user.type(emailInput, "nuevo@email.com")
      await user.type(nameInput, "Nuevo Usuario")
      await user.type(passwordInput, "password123")
      
      // Submit form
      const submitButton = screen.getByText("Crear Cliente")
      await user.click(submitButton)
      
      await waitFor(() => {
        expect(UsersService.createUser).toHaveBeenCalledWith({
          requestBody: {
            email: "nuevo@email.com",
            full_name: "Nuevo Usuario",
            password: "password123",
            is_active: true,
            is_superuser: false,
          },
        })
      })
    })

    it("should validate required fields", async () => {
      render(<CustomerManagement />)
      
      // Open create modal
      const createButton = screen.getByText("Nuevo Cliente")
      await user.click(createButton)
      
      // Try to submit without required fields
      const submitButton = screen.getByText("Crear Cliente")
      await user.click(submitButton)
      
      // Check that form validation prevents submission
      expect(screen.getByText("Crear Nuevo Cliente")).toBeInTheDocument()
    })
  })

  describe("Customer Editing", () => {
    it("should open edit customer modal", async () => {
      render(<CustomerManagement />)
      
      await waitFor(() => {
        expect(screen.getByText("Juan Pérez")).toBeInTheDocument()
      })
      
      const editButtons = screen.getAllByLabelText("Editar cliente")
      await user.click(editButtons[0])
      
      expect(screen.getByText("Editar Cliente")).toBeInTheDocument()
    })

    it("should pre-fill edit form with customer data", async () => {
      render(<CustomerManagement />)
      
      await waitFor(() => {
        expect(screen.getByText("Juan Pérez")).toBeInTheDocument()
      })
      
      const editButtons = screen.getAllByLabelText("Editar cliente")
      await user.click(editButtons[0])
      
      await waitFor(() => {
        const emailInput = screen.getByDisplayValue("juan@email.com")
        const nameInput = screen.getByDisplayValue("Juan Pérez")
        
        expect(emailInput).toBeInTheDocument()
        expect(nameInput).toBeInTheDocument()
      })
    })

    it("should update customer information", async () => {
      const { UsersService } = require("../../../client")
      
      render(<CustomerManagement />)
      
      await waitFor(() => {
        expect(screen.getByText("Juan Pérez")).toBeInTheDocument()
      })
      
      const editButtons = screen.getAllByLabelText("Editar cliente")
      await user.click(editButtons[0])
      
      // Update name
      const nameInput = screen.getByDisplayValue("Juan Pérez")
      await user.clear(nameInput)
      await user.type(nameInput, "Juan Carlos Pérez")
      
      // Submit changes
      const submitButton = screen.getByText("Guardar Cambios")
      await user.click(submitButton)
      
      await waitFor(() => {
        expect(UsersService.updateUser).toHaveBeenCalledWith({
          userId: "1",
          requestBody: {
            email: "juan@email.com",
            full_name: "Juan Carlos Pérez",
            is_active: true,
            is_superuser: false,
          },
        })
      })
    })

    it("should toggle customer status", async () => {
      render(<CustomerManagement />)
      
      await waitFor(() => {
        expect(screen.getByText("Juan Pérez")).toBeInTheDocument()
      })
      
      const editButtons = screen.getAllByLabelText("Editar cliente")
      await user.click(editButtons[0])
      
      // Change status
      const statusSelect = screen.getByDisplayValue("Activo")
      await user.selectOptions(statusSelect, "inactive")
      
      const submitButton = screen.getByText("Guardar Cambios")
      await user.click(submitButton)
      
      await waitFor(() => {
        expect(require("../../../client").UsersService.updateUser).toHaveBeenCalledWith(
          expect.objectContaining({
            requestBody: expect.objectContaining({
              is_active: false,
            }),
          })
        )
      })
    })
  })

  describe("Customer Deletion", () => {
    it("should show delete confirmation", async () => {
      // Mock window.confirm
      window.confirm = vi.fn(() => true)
      
      render(<CustomerManagement />)
      
      await waitFor(() => {
        expect(screen.getByText("Juan Pérez")).toBeInTheDocument()
      })
      
      const deleteButtons = screen.getAllByLabelText("Eliminar cliente")
      await user.click(deleteButtons[0])
      
      expect(window.confirm).toHaveBeenCalledWith(
        "¿Estás seguro de que quieres eliminar este cliente?"
      )
    })

    it("should delete customer when confirmed", async () => {
      const { UsersService } = require("../../../client")
      window.confirm = vi.fn(() => true)
      
      render(<CustomerManagement />)
      
      await waitFor(() => {
        expect(screen.getByText("Juan Pérez")).toBeInTheDocument()
      })
      
      const deleteButtons = screen.getAllByLabelText("Eliminar cliente")
      await user.click(deleteButtons[0])
      
      await waitFor(() => {
        expect(UsersService.deleteUser).toHaveBeenCalledWith({ userId: "1" })
      })
    })

    it("should not delete customer when cancelled", async () => {
      const { UsersService } = require("../../../client")
      window.confirm = vi.fn(() => false)
      
      render(<CustomerManagement />)
      
      await waitFor(() => {
        expect(screen.getByText("Juan Pérez")).toBeInTheDocument()
      })
      
      const deleteButtons = screen.getAllByLabelText("Eliminar cliente")
      await user.click(deleteButtons[0])
      
      expect(UsersService.deleteUser).not.toHaveBeenCalled()
    })
  })

  describe("View Customer Details", () => {
    it("should open customer details modal", async () => {
      render(<CustomerManagement />)
      
      await waitFor(() => {
        expect(screen.getByText("Juan Pérez")).toBeInTheDocument()
      })
      
      const viewButtons = screen.getAllByLabelText("Ver detalles")
      await user.click(viewButtons[0])
      
      expect(screen.getByText("Detalles del Cliente")).toBeInTheDocument()
    })

    it("should display customer details", async () => {
      render(<CustomerManagement />)
      
      await waitFor(() => {
        expect(screen.getByText("Juan Pérez")).toBeInTheDocument()
      })
      
      const viewButtons = screen.getAllByLabelText("Ver detalles")
      await user.click(viewButtons[0])
      
      await waitFor(() => {
        expect(screen.getByText("juan@email.com")).toBeInTheDocument()
        expect(screen.getByText("1 ene 2024")).toBeInTheDocument() // Registration date
      })
    })
  })

  describe("Error Handling", () => {
    it("should handle API errors gracefully", async () => {
      const { UsersService } = require("../../../client")
      UsersService.readUsers.mockRejectedValue(new Error("API Error"))
      
      render(<CustomerManagement />)
      
      await waitFor(() => {
        expect(screen.getByText("Error al cargar clientes")).toBeInTheDocument()
      })
    })

    it("should handle create customer error", async () => {
      const { UsersService } = require("../../../client")
      UsersService.createUser.mockRejectedValue(new Error("Creation failed"))
      
      render(<CustomerManagement />)
      
      // Open create modal and submit
      const createButton = screen.getByText("Nuevo Cliente")
      await user.click(createButton)
      
      const emailInput = screen.getByPlaceholderText("cliente@ejemplo.com")
      const nameInput = screen.getByPlaceholderText("Nombre completo del cliente")
      const passwordInput = screen.getByPlaceholderText("Contraseña del cliente")
      
      await user.type(emailInput, "test@email.com")
      await user.type(nameInput, "Test User")
      await user.type(passwordInput, "password123")
      
      const submitButton = screen.getByText("Crear Cliente")
      await user.click(submitButton)
      
      // Error should be handled (toast would show in real app)
      await waitFor(() => {
        expect(UsersService.createUser).toHaveBeenCalled()
      })
    })
  })

  describe("Responsive Design", () => {
    it("should display properly on mobile", () => {
      Object.defineProperty(window, "innerWidth", {
        writable: true,
        configurable: true,
        value: 375,
      })
      
      render(<CustomerManagement />)
      
      expect(screen.getByText("Gestión de Clientes")).toBeInTheDocument()
    })
  })

  describe("Performance", () => {
    it("should not reload data unnecessarily", async () => {
      const { UsersService } = require("../../../client")
      
      render(<CustomerManagement />)
      
      await waitFor(() => {
        expect(screen.getByText("Juan Pérez")).toBeInTheDocument()
      })
      
      // Initial load should call API once
      expect(UsersService.readUsers).toHaveBeenCalledTimes(1)
    })
  })
})