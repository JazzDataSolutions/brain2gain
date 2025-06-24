import {
  Box,
  VStack,
  Text,
  Link,
  Icon,
  useColorModeValue,
  Divider,
  Flex,
  Badge,
} from '@chakra-ui/react'
import {
  FiHome,
  FiPackage,
  FiShoppingCart,
  FiUsers,
  FiBarChart,
  FiSettings,
  FiDollarSign,
  FiTrendingUp,
} from 'react-icons/fi'
import { Link as RouterLink, useLocation } from '@tanstack/react-router'

const AdminSidebar = () => {
  const location = useLocation()
  const bg = useColorModeValue('white', 'gray.800')
  const borderColor = useColorModeValue('gray.200', 'gray.700')
  
  const menuItems = [
    {
      name: 'Dashboard',
      icon: FiHome,
      href: '/admin',
      badge: null,
    },
    {
      name: 'Inventario',
      icon: FiPackage,
      href: '/admin/inventory',
      badge: 'Low Stock',
      badgeColor: 'red',
    },
    {
      name: 'Pedidos',
      icon: FiShoppingCart,
      href: '/admin/orders',
      badge: '5',
      badgeColor: 'blue',
    },
    {
      name: 'Clientes',
      icon: FiUsers,
      href: '/admin/customers',
      badge: null,
    },
    {
      name: 'Reportes',
      icon: FiBarChart,
      href: '/admin/reports',
      badge: null,
    },
    {
      name: 'Ventas',
      icon: FiDollarSign,
      href: '/admin/sales',
      badge: null,
    },
    {
      name: 'Analytics',
      icon: FiTrendingUp,
      href: '/admin/analytics',
      badge: 'New',
      badgeColor: 'green',
    },
  ]

  const secondaryItems = [
    {
      name: 'Configuración',
      icon: FiSettings,
      href: '/admin/settings',
    },
  ]

  const isActive = (href: string) => {
    if (href === '/admin') {
      return location.pathname === '/admin' || location.pathname === '/admin/'
    }
    return location.pathname.startsWith(href)
  }

  const renderMenuItem = (item: any) => (
    <RouterLink key={item.name} to={item.href}>
      <Link
        display="flex"
        alignItems="center"
        justifyContent="space-between"
        px={4}
        py={3}
        rounded="lg"
        transition="all 0.2s"
        bg={isActive(item.href) ? 'blue.50' : 'transparent'}
        color={isActive(item.href) ? 'blue.600' : 'gray.600'}
        borderLeft={isActive(item.href) ? '3px solid' : '3px solid transparent'}
        borderColor={isActive(item.href) ? 'blue.500' : 'transparent'}
        _hover={{
          bg: 'blue.50',
          color: 'blue.600',
          textDecoration: 'none',
        }}
        w="full"
      >
        <Flex align="center">
          <Icon as={item.icon} mr={3} boxSize={5} />
          <Text fontWeight={isActive(item.href) ? 'semibold' : 'medium'}>
            {item.name}
          </Text>
        </Flex>
        {item.badge && (
          <Badge
            colorScheme={item.badgeColor || 'gray'}
            size="sm"
            borderRadius="full"
          >
            {item.badge}
          </Badge>
        )}
      </Link>
    </RouterLink>
  )

  return (
    <Box
      w="280px"
      bg={bg}
      borderRight="1px"
      borderRightColor={borderColor}
      h="full"
      overflowY="auto"
    >
      {/* Logo/Header */}
      <Box p={6} borderBottom="1px" borderBottomColor={borderColor}>
        <RouterLink to="/admin">
          <Text fontSize="xl" fontWeight="bold" color="blue.500">
            Brain2Gain
          </Text>
        </RouterLink>
        <Text fontSize="sm" color="gray.500" mt={1}>
          Panel de Administración
        </Text>
      </Box>

      {/* Main Navigation */}
      <VStack spacing={1} align="stretch" p={4}>
        <Text
          fontSize="xs"
          fontWeight="semibold"
          color="gray.400"
          textTransform="uppercase"
          letterSpacing="wide"
          mb={2}
        >
          Principal
        </Text>
        {menuItems.map(renderMenuItem)}
      </VStack>

      <Divider />

      {/* Secondary Navigation */}
      <VStack spacing={1} align="stretch" p={4}>
        <Text
          fontSize="xs"
          fontWeight="semibold"
          color="gray.400"
          textTransform="uppercase"
          letterSpacing="wide"
          mb={2}
        >
          Sistema
        </Text>
        {secondaryItems.map(renderMenuItem)}
      </VStack>

      {/* Quick Stats */}
      <Box p={4} mt="auto">
        <Box
          bg={useColorModeValue('blue.50', 'blue.900')}
          p={4}
          rounded="lg"
          border="1px"
          borderColor={useColorModeValue('blue.200', 'blue.700')}
        >
          <Text fontSize="sm" fontWeight="semibold" color="blue.600" mb={2}>
            Resumen Rápido
          </Text>
          <VStack spacing={2} align="stretch">
            <Flex justify="space-between">
              <Text fontSize="xs" color="gray.600">
                Ventas Hoy
              </Text>
              <Text fontSize="xs" fontWeight="bold">
                $1,247
              </Text>
            </Flex>
            <Flex justify="space-between">
              <Text fontSize="xs" color="gray.600">
                Pedidos Pendientes
              </Text>
              <Text fontSize="xs" fontWeight="bold">
                8
              </Text>
            </Flex>
            <Flex justify="space-between">
              <Text fontSize="xs" color="gray.600">
                Stock Bajo
              </Text>
              <Text fontSize="xs" fontWeight="bold" color="red.500">
                3 productos
              </Text>
            </Flex>
          </VStack>
        </Box>
      </Box>
    </Box>
  )
}

export default AdminSidebar