// src/components/CatalogoPage.tsx
import { SimpleGrid, Box, Image, Text, Heading } from '@chakra-ui/react';

interface Producto {
  id: number;
  nombre: string;
  descripcion?: string;
  precio: number;
  imagen: string;
}

const productosEjemplo: Producto[] = [
  {
    id: 1,
    nombre: 'Creatina Birdman',
    descripcion: 'Alta calidad para potenciar tu fuerza',
    precio: 589.99,
    imagen: '/imagenes/creatina_catalogo.jpg',
  },
  {
    id: 2,
    nombre: 'Proteína IsoFlex',
    descripcion: 'Proteína de rápida absorción',
    precio: 1599.99,
    imagen: '/imagenes/proteina_catalogo.jpg',
  },
  {
    id: 3,
    nombre: 'Preworkout VENOM INFERNO',
    descripcion: 'Energía y enfoque en cada entrenamiento',
    precio: 549.99,
    imagen: '/imagenes/preworkout_catalogo.jpg',
  },
  {
    id: 3,
    nombre: 'Preworkout VENOM INFERNO',
    descripcion: 'Energía y enfoque en cada entrenamiento',
    precio: 549.99,
    imagen: '/imagenes/preworkout_catalogo.jpg',
  },
];

const CatalogoPage = () => {
  return (
    <Box p={8}>
      <Heading mb={6} textAlign="center">
        Catálogo de Productos
      </Heading>
      <SimpleGrid columns={{ base: 1, md: 3 }} spacing={6}>
        {productosEjemplo.map((producto) => (
          <Box
            key={producto.id}
            borderWidth="1px"
            borderRadius="lg"
            overflow="hidden"
            p={4}
            _hover={{ boxShadow: 'md' }}
          >
            <Image src={producto.imagen} alt={producto.nombre} borderRadius="md" />
            <Text mt={4} fontSize="xl" fontWeight="bold">
              {producto.nombre}
            </Text>
            <Text mt={2}>{producto.descripcion}</Text>
            <Text mt={2} fontSize="lg" color="ui.main" fontWeight="bold">
              ${producto.precio}
            </Text>
          </Box>
        ))}
      </SimpleGrid>
    </Box>
  );
};

export default CatalogoPage;
