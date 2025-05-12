// src/components/Conocenos.tsx
import { Box, Heading, Text, Image, Flex } from '@chakra-ui/react';

const Conocenos = () => {
  return (
    <Box p={8}>
      <Heading textAlign="center" mb={6}>
        Conócenos
      </Heading>
      <Flex direction={{ base: 'column', md: 'row' }} align="center" justify="center" gap={6}>
        <Box flex="1">
          <Image 
            src="/imagenes/fundadores.jpg" 
            alt="Fundadores de Brain2Gain" 
            borderRadius="md" 
            boxSize="100%" 
            objectFit="cover"
          />
        </Box>
        <Box flex="1">
          <Text fontSize="lg" mb={4}>
            En Brain2Gain nos apasiona el bienestar y el rendimiento. Fundada por profesionales comprometidos con la
            salud, nuestra misión es ofrecer suplementos de la más alta calidad para ayudarte a alcanzar tus metas.
          </Text>
          <Text fontSize="md">
            [Aquí puedes agregar más información sobre la historia, los valores y los fundadores de Brain2Gain.
            Personaliza este contenido según la identidad y la historia de la marca.]
          </Text>
        </Box>
      </Flex>
    </Box>
  );
};

export default Conocenos;
