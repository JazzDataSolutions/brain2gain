import {
  Box,
  Container,
  Stack,
  Text,
  Link,
  useColorModeValue,
  SimpleGrid,
  HStack,
  Icon,
  Divider,
} from '@chakra-ui/react'
import { FaInstagram, FaTwitter, FaFacebook, FaWhatsapp } from 'react-icons/fa'
import { Link as RouterLink } from '@tanstack/react-router'

const StoreFooter = () => {
  return (
    <Box
      bg={useColorModeValue('gray.50', 'gray.900')}
      color={useColorModeValue('gray.700', 'gray.200')}
      mt="auto"
    >
      <Container as={Stack} maxW="7xl" py={10}>
        <SimpleGrid columns={{ base: 1, sm: 2, md: 4 }} spacing={8}>
          {/* Información de la empresa */}
          <Stack align="flex-start">
            <Text fontWeight="bold" fontSize="lg" color="blue.500">
              Brain2Gain
            </Text>
            <Text fontSize="sm">
              Tu tienda de confianza para suplementos deportivos de alta calidad.
              Potencia tu rendimiento y alcanza tus objetivos fitness.
            </Text>
            <HStack spacing={4}>
              <Link href="https://instagram.com/brain2gain" isExternal>
                <Icon as={FaInstagram} boxSize={5} _hover={{ color: 'blue.500' }} />
              </Link>
              <Link href="https://facebook.com/brain2gain" isExternal>
                <Icon as={FaFacebook} boxSize={5} _hover={{ color: 'blue.500' }} />
              </Link>
              <Link href="https://twitter.com/brain2gain" isExternal>
                <Icon as={FaTwitter} boxSize={5} _hover={{ color: 'blue.500' }} />
              </Link>
              <Link href="https://wa.me/1234567890" isExternal>
                <Icon as={FaWhatsapp} boxSize={5} _hover={{ color: 'green.500' }} />
              </Link>
            </HStack>
          </Stack>

          {/* Productos */}
          <Stack align="flex-start">
            <Text fontWeight="500">Productos</Text>
            <RouterLink to="/store/products?category=proteinas">
              <Link>Proteínas</Link>
            </RouterLink>
            <RouterLink to="/store/products?category=creatina">
              <Link>Creatina</Link>
            </RouterLink>
            <RouterLink to="/store/products?category=pre-workout">
              <Link>Pre-Workout</Link>
            </RouterLink>
            <RouterLink to="/store/products?category=vitaminas">
              <Link>Vitaminas</Link>
            </RouterLink>
            <RouterLink to="/store/products?category=aminoacidos">
              <Link>Aminoácidos</Link>
            </RouterLink>
          </Stack>

          {/* Soporte */}
          <Stack align="flex-start">
            <Text fontWeight="500">Soporte</Text>
            <RouterLink to="/store/help">
              <Link>Centro de Ayuda</Link>
            </RouterLink>
            <RouterLink to="/store/shipping">
              <Link>Información de Envío</Link>
            </RouterLink>
            <RouterLink to="/store/returns">
              <Link>Devoluciones</Link>
            </RouterLink>
            <RouterLink to="/store/contact">
              <Link>Contacto</Link>
            </RouterLink>
            <RouterLink to="/store/faq">
              <Link>Preguntas Frecuentes</Link>
            </RouterLink>
          </Stack>

          {/* Legal */}
          <Stack align="flex-start">
            <Text fontWeight="500">Legal</Text>
            <RouterLink to="/store/privacy">
              <Link>Política de Privacidad</Link>
            </RouterLink>
            <RouterLink to="/store/terms">
              <Link>Términos de Servicio</Link>
            </RouterLink>
            <RouterLink to="/store/cookies">
              <Link>Política de Cookies</Link>
            </RouterLink>
            <RouterLink to="/store/about">
              <Link>Acerca de Nosotros</Link>
            </RouterLink>
          </Stack>
        </SimpleGrid>
      </Container>

      <Divider />

      <Container as={Stack} maxW="7xl" py={4}>
        <Stack
          direction={{ base: 'column', md: 'row' }}
          spacing={4}
          justify={{ base: 'center', md: 'space-between' }}
          align={{ base: 'center', md: 'center' }}
        >
          <Text fontSize="sm">
            © 2024 Brain2Gain. Todos los derechos reservados.
          </Text>
          <HStack spacing={4} fontSize="sm">
            <Text>Métodos de pago:</Text>
            <Text>💳 Visa</Text>
            <Text>💳 Mastercard</Text>
            <Text>💰 PayPal</Text>
            <Text>🏦 Transferencia</Text>
          </HStack>
        </Stack>
      </Container>
    </Box>
  )
}

export default StoreFooter