import { 
  Box, 
  Container,
  Heading, 
  Text, 
  Button, 
  VStack,
  HStack,
  useColorModeValue 
} from '@chakra-ui/react'
import { Link } from '@tanstack/react-router'

const HeroSection = () => {
  const overlayBg = useColorModeValue('blackAlpha.600', 'blackAlpha.700')

  return (
    <Box
      position="relative"
      bgImage="url('/imagenes/fondo.jpg')"
      bgSize="cover"
      bgPos="center"
      bgAttachment="fixed"
      height="100vh"
      display="flex"
      alignItems="center"
      justifyContent="center"
    >
      {/* Overlay */}
      <Box
        position="absolute"
        top={0}
        left={0}
        right={0}
        bottom={0}
        bg={overlayBg}
      />
      
      {/* Content */}
      <Container maxW="7xl" position="relative" zIndex={1}>
        <VStack 
          spacing={8} 
          textAlign="center" 
          color="white"
          maxW="4xl"
          mx="auto"
        >
          <VStack spacing={4}>
            <Heading 
              fontSize={{ base: "3xl", md: "5xl", lg: "6xl" }} 
              fontWeight="bold"
              lineHeight="shorter"
            >
              Potencia Tu{' '}
              <Text as="span" color="blue.400">
                Rendimiento
              </Text>
            </Heading>
            
            <Text 
              fontSize={{ base: "lg", md: "xl", lg: "2xl" }}
              color="gray.200"
              maxW="3xl"
              lineHeight="tall"
            >
              Descubre los suplementos deportivos de más alta calidad. 
              Transforma tu entrenamiento y alcanza tus objetivos con Brain2Gain.
            </Text>
          </VStack>

          <HStack 
            spacing={4} 
            flexDirection={{ base: "column", sm: "row" }}
            w={{ base: "100%", sm: "auto" }}
          >
            <Button
              as={Link}
              to="/products"
              size="lg"
              colorScheme="blue"
              fontSize="lg"
              px={8}
              py={6}
              h="auto"
              w={{ base: "100%", sm: "auto" }}
            >
              Ver Productos
            </Button>
            
            <Button
              as={Link}
              to="/#conocenos"
              size="lg"
              variant="outline"
              colorScheme="whiteAlpha"
              color="white"
              borderColor="white"
              fontSize="lg"
              px={8}
              py={6}
              h="auto"
              w={{ base: "100%", sm: "auto" }}
              _hover={{
                bg: "whiteAlpha.200",
                borderColor: "blue.400",
                color: "blue.400"
              }}
            >
              Conoce Más
            </Button>
          </HStack>

          {/* Trust Indicators */}
          <HStack 
            spacing={8} 
            mt={8}
            fontSize="sm"
            color="gray.300"
            flexWrap="wrap"
            justify="center"
          >
            <Text>✓ Productos Certificados</Text>
            <Text>✓ Envío Gratis +$100k</Text>
            <Text>✓ Garantía de Calidad</Text>
          </HStack>
        </VStack>
      </Container>
    </Box>
  )
}

export default HeroSection;

