// src/components/Navbar.tsx
import { Box, Flex, Link as ChakraLink, Button, Image } from '@chakra-ui/react'; // <-- Link de Chakra ahora es ChakraLink
import { Link as RouterLink } from '@tanstack/react-router'; // <-- Link de TanStack Router es RouterLink

// ... resto del componente ...
const Navbar = () => {
  return (
    <Flex
      as="nav"
      bg="black"
      color="white"
      align="center"
      justify="space-between"
      p={4}
      //border="2px solid red" // Para depurar
    >
      <Box>
        <Image src="/imagenes/logo.png" alt="Logo Brain2Gain" height="30px" mx={2} />
      </Box>
      <Flex gap={4}>
       <ChakraLink as={RouterLink} to="/">Inicio</ChakraLink> {/* Ejemplo */}
       <ChakraLink as={RouterLink} to="/catalogo">Catálogo</ChakraLink>
       <ChakraLink as={RouterLink} to="/conocenos">Conócenos</ChakraLink>
       <ChakraLink as={RouterLink} to="/contacto">Contacto</ChakraLink>
      </Flex>
      <Box>
        <Button as={RouterLink} to="/login" colorScheme="green"> {/* Ejemplo con Button */}
          Iniciar sesión
        </Button>
      </Box>
    </Flex>
  );
};

export default Navbar;
