import {
  Flex,
  Box,
  Text,
  Menu,
  MenuButton,
  MenuList,
  MenuItem,
  MenuDivider,
  Avatar,
  HStack,
  useColorModeValue,
  Button,
  Input,
  InputGroup,
  InputLeftElement,
} from '@chakra-ui/react'
import {
  FiSearch,
  FiSettings,
  FiLogOut,
  FiUser,
  FiExternalLink,
} from 'react-icons/fi'
import { useNavigate } from '@tanstack/react-router'
import useAuth from '../../hooks/useAuth'
import { NotificationBell } from '../Notifications/NotificationBell'

const AdminHeader = () => {
  const { user, logout } = useAuth()
  const navigate = useNavigate()
  const bg = useColorModeValue('white', 'gray.800')
  const borderColor = useColorModeValue('gray.200', 'gray.700')

  const handleLogout = () => {
    logout()
    navigate({ to: '/login' })
  }

  return (
    <Flex
      bg={bg}
      borderBottom="1px"
      borderBottomColor={borderColor}
      px={6}
      py={4}
      align="center"
      justify="space-between"
      h="60px"
      position="sticky"
      top={0}
      zIndex={1}
    >
      {/* Left side - Search */}
      <Flex flex={1} maxW="400px">
        <InputGroup>
          <InputLeftElement pointerEvents="none">
            <FiSearch color="gray.300" />
          </InputLeftElement>
          <Input
            placeholder="Buscar productos, pedidos, clientes..."
            bg={useColorModeValue('gray.50', 'gray.700')}
            border="1px"
            borderColor={useColorModeValue('gray.200', 'gray.600')}
            _focus={{
              borderColor: 'blue.500',
              boxShadow: '0 0 0 1px blue.500',
            }}
          />
        </InputGroup>
      </Flex>

      {/* Right side - Actions and User */}
      <HStack spacing={4}>
        {/* Quick Actions */}
        <Button
          variant="ghost"
          leftIcon={<FiExternalLink />}
          size="sm"
          onClick={() => navigate({ to: '/store' })}
        >
          Ver Tienda
        </Button>

        {/* Notifications */}
        <NotificationBell />

        {/* User Menu */}
        <Menu>
          <MenuButton>
            <HStack spacing={3} cursor="pointer">
              <Box textAlign="right" display={{ base: 'none', md: 'block' }}>
                <Text fontSize="sm" fontWeight="medium">
                  {user?.full_name || 'Administrador'}
                </Text>
                <Text fontSize="xs" color="gray.500">
                  {user?.email}
                </Text>
              </Box>
              <Avatar
                size="sm"
                name={user?.full_name || user?.email}
                bg="blue.500"
              />
            </HStack>
          </MenuButton>
          <MenuList>
            <MenuItem icon={<FiUser />} onClick={() => navigate({ to: '/admin/profile' })}>
              Mi Perfil
            </MenuItem>
            <MenuItem icon={<FiSettings />} onClick={() => navigate({ to: '/admin/settings' })}>
              Configuración
            </MenuItem>
            <MenuDivider />
            <MenuItem icon={<FiExternalLink />} onClick={() => navigate({ to: '/store' })}>
              Ver Tienda
            </MenuItem>
            <MenuDivider />
            <MenuItem icon={<FiLogOut />} onClick={handleLogout} color="red.500">
              Cerrar Sesión
            </MenuItem>
          </MenuList>
        </Menu>
      </HStack>
    </Flex>
  )
}

export default AdminHeader