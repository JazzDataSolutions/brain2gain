import {
  Box,
  Flex,
  HStack,
  Link,
  IconButton,
  Button,
  Menu,
  MenuButton,
  MenuList,
  MenuItem,
  useDisclosure,
  useColorModeValue,
  Stack,
  Input,
  InputGroup,
  InputLeftElement,
  Badge,
  Avatar,
  Text,
} from '@chakra-ui/react'
import { HamburgerIcon, CloseIcon, SearchIcon, ShoppingCartIcon } from '@chakra-ui/icons'
import { Link as RouterLink, useNavigate } from '@tanstack/react-router'
import { useAuth } from '../../hooks/useAuth'
import { useCartStore } from '../../stores/cartStore'

const StoreNavbar = () => {
  const { isOpen, onOpen, onClose } = useDisclosure()
  const { user, logout } = useAuth()
  const navigate = useNavigate()
  const { items } = useCartStore()
  
  const cartItemsCount = items.reduce((total, item) => total + item.quantity, 0)

  const navLinks = [
    { name: 'Inicio', href: '/store' },
    { name: 'Productos', href: '/store/products' },
    { name: 'Ofertas', href: '/store/offers' },
    { name: 'Categorías', href: '/store/categories' },
  ]

  return (
    <Box bg={useColorModeValue('white', 'gray.900')} px={4} shadow="md">
      <Flex h={16} alignItems="center" justifyContent="space-between">
        {/* Logo */}
        <HStack spacing={8} alignItems="center">
          <Box>
            <RouterLink to="/store">
              <Text
                fontSize="xl"
                fontWeight="bold"
                color="blue.500"
                _hover={{ color: 'blue.600' }}
              >
                Brain2Gain
              </Text>
            </RouterLink>
          </Box>
          
          {/* Desktop Navigation */}
          <HStack as="nav" spacing={4} display={{ base: 'none', md: 'flex' }}>
            {navLinks.map((link) => (
              <RouterLink key={link.name} to={link.href}>
                <Link
                  px={2}
                  py={1}
                  rounded="md"
                  _hover={{
                    textDecoration: 'none',
                    bg: useColorModeValue('gray.200', 'gray.700'),
                  }}
                >
                  {link.name}
                </Link>
              </RouterLink>
            ))}
          </HStack>
        </HStack>

        {/* Search Bar */}
        <Flex flex={1} mx={8} maxW="400px" display={{ base: 'none', md: 'flex' }}>
          <InputGroup>
            <InputLeftElement pointerEvents="none">
              <SearchIcon color="gray.300" />
            </InputLeftElement>
            <Input
              placeholder="Buscar productos..."
              bg={useColorModeValue('gray.50', 'gray.800')}
              border="1px"
              borderColor={useColorModeValue('gray.200', 'gray.600')}
              _focus={{
                borderColor: 'blue.500',
                boxShadow: '0 0 0 1px blue.500',
              }}
            />
          </InputGroup>
        </Flex>

        {/* Right side actions */}
        <Flex alignItems="center">
          {/* Cart */}
          <Box position="relative" mr={4}>
            <IconButton
              icon={<ShoppingCartIcon />}
              variant="ghost"
              onClick={() => navigate({ to: '/store/cart' })}
              aria-label="Carrito de compras"
            />
            {cartItemsCount > 0 && (
              <Badge
                position="absolute"
                top="-1"
                right="-1"
                colorScheme="red"
                borderRadius="full"
                minW="20px"
                h="20px"
                display="flex"
                alignItems="center"
                justifyContent="center"
                fontSize="xs"
              >
                {cartItemsCount}
              </Badge>
            )}
          </Box>

          {/* User Menu */}
          {user ? (
            <Menu>
              <MenuButton
                as={Button}
                rounded="full"
                variant="link"
                cursor="pointer"
                minW={0}
              >
                <Avatar size="sm" name={user.full_name || user.email} />
              </MenuButton>
              <MenuList>
                <MenuItem onClick={() => navigate({ to: '/admin' })}>
                  Panel Admin
                </MenuItem>
                <MenuItem onClick={() => navigate({ to: '/store/profile' })}>
                  Mi Perfil
                </MenuItem>
                <MenuItem onClick={() => navigate({ to: '/store/orders' })}>
                  Mis Pedidos
                </MenuItem>
                <MenuItem onClick={logout}>Cerrar Sesión</MenuItem>
              </MenuList>
            </Menu>
          ) : (
            <HStack spacing={2}>
              <Button
                variant="ghost"
                onClick={() => navigate({ to: '/login' })}
              >
                Iniciar Sesión
              </Button>
              <Button
                colorScheme="blue"
                onClick={() => navigate({ to: '/signup' })}
              >
                Registrarse
              </Button>
            </HStack>
          )}

          {/* Mobile menu button */}
          <IconButton
            size="md"
            icon={isOpen ? <CloseIcon /> : <HamburgerIcon />}
            aria-label="Abrir menú"
            display={{ md: 'none' }}
            onClick={isOpen ? onClose : onOpen}
            ml={2}
          />
        </Flex>
      </Flex>

      {/* Mobile Navigation */}
      {isOpen && (
        <Box pb={4} display={{ md: 'none' }}>
          <Stack as="nav" spacing={4}>
            {navLinks.map((link) => (
              <RouterLink key={link.name} to={link.href}>
                <Link
                  px={2}
                  py={1}
                  rounded="md"
                  _hover={{
                    textDecoration: 'none',
                    bg: useColorModeValue('gray.200', 'gray.700'),
                  }}
                  onClick={onClose}
                >
                  {link.name}
                </Link>
              </RouterLink>
            ))}
            
            {/* Mobile Search */}
            <InputGroup mt={4}>
              <InputLeftElement pointerEvents="none">
                <SearchIcon color="gray.300" />
              </InputLeftElement>
              <Input
                placeholder="Buscar productos..."
                bg={useColorModeValue('gray.50', 'gray.800')}
              />
            </InputGroup>
          </Stack>
        </Box>
      )}
    </Box>
  )
}

export default StoreNavbar