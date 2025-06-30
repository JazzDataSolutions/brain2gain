import { HamburgerIcon } from "@chakra-ui/icons"
import {
  Box,
  Button,
  Link as ChakraLink,
  Container,
  Drawer,
  DrawerBody,
  DrawerCloseButton,
  DrawerContent,
  DrawerHeader,
  DrawerOverlay,
  Flex,
  HStack,
  Hide,
  IconButton,
  Image,
  Show,
  VStack,
  useColorModeValue,
  useDisclosure,
} from "@chakra-ui/react"
import { Link as RouterLink } from "@tanstack/react-router"

import useAuth from "../../hooks/useAuth"
import MiniCart from "../Cart/MiniCart"

const Navbar = () => {
  const { isOpen, onOpen, onClose } = useDisclosure()
  const { user, logout } = useAuth()

  const bg = useColorModeValue("white", "gray.800")
  const borderColor = useColorModeValue("gray.200", "gray.600")

  const NavLinks = () => (
    <>
      <ChakraLink
        as={RouterLink}
        to="/"
        _hover={{ color: "blue.500" }}
        fontWeight="medium"
      >
        Inicio
      </ChakraLink>
      <ChakraLink
        as={RouterLink}
        to="/products"
        _hover={{ color: "blue.500" }}
        fontWeight="medium"
      >
        Productos
      </ChakraLink>
      <ChakraLink
        as={RouterLink}
        to="/#conocenos"
        _hover={{ color: "blue.500" }}
        fontWeight="medium"
      >
        Conócenos
      </ChakraLink>
      <ChakraLink
        as={RouterLink}
        to="/#contacto"
        _hover={{ color: "blue.500" }}
        fontWeight="medium"
      >
        Contacto
      </ChakraLink>
    </>
  )

  return (
    <Box
      bg={bg}
      borderBottom="1px"
      borderColor={borderColor}
      position="sticky"
      top={0}
      zIndex={1000}
      shadow="sm"
    >
      <Container maxW="7xl">
        <Flex as="nav" align="center" justify="space-between" py={4}>
          {/* Logo */}
          <Box>
            <ChakraLink as={RouterLink} to="/">
              <Image
                src="/imagenes/logo.png"
                alt="Brain2Gain"
                height="40px"
                fallbackSrc="https://via.placeholder.com/120x40?text=Brain2Gain"
              />
            </ChakraLink>
          </Box>

          {/* Desktop Navigation */}
          <Show above="md">
            <HStack spacing={8}>
              <NavLinks />
            </HStack>
          </Show>

          {/* Right Side Actions */}
          <HStack spacing={4}>
            {/* Cart */}
            <MiniCart />

            {/* Authentication */}
            {user ? (
              <HStack spacing={2}>
                <Button as={RouterLink} to="/_layout" variant="ghost" size="sm">
                  Dashboard
                </Button>
                <Button
                  onClick={logout}
                  variant="outline"
                  size="sm"
                  colorScheme="red"
                >
                  Salir
                </Button>
              </HStack>
            ) : (
              <HStack spacing={2}>
                <Button as={RouterLink} to="/login" variant="ghost" size="sm">
                  Iniciar Sesión
                </Button>
                <Button
                  as={RouterLink}
                  to="/signup"
                  colorScheme="blue"
                  size="sm"
                >
                  Registrarse
                </Button>
              </HStack>
            )}

            {/* Mobile Menu Button */}
            <Hide above="md">
              <IconButton
                aria-label="Abrir menú"
                icon={<HamburgerIcon />}
                variant="ghost"
                onClick={onOpen}
              />
            </Hide>
          </HStack>
        </Flex>
      </Container>

      {/* Mobile Drawer */}
      <Drawer isOpen={isOpen} placement="right" onClose={onClose}>
        <DrawerOverlay />
        <DrawerContent>
          <DrawerCloseButton />
          <DrawerHeader>Navegación</DrawerHeader>
          <DrawerBody>
            <VStack spacing={4} align="stretch">
              <NavLinks />
            </VStack>
          </DrawerBody>
        </DrawerContent>
      </Drawer>
    </Box>
  )
}

export default Navbar
