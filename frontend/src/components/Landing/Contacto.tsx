// src/components/Contacto.tsx
import {
  Box,
  Button,
  FormControl,
  FormLabel,
  FormErrorMessage,
  Input,
  Textarea,
  Heading,
  VStack,
  useToast,
} from '@chakra-ui/react';
import { useForm, SubmitHandler } from 'react-hook-form';

interface ContactoFormInputs {
  name: string;
  email: string;
  message: string;
}

const Contacto = () => {
  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isSubmitting },
  } = useForm<ContactoFormInputs>();
  const toast = useToast();

  const onSubmit: SubmitHandler<ContactoFormInputs> = async (data) => {
    // Aquí puedes integrar la llamada a FastAPI usando fetch, axios, etc.
    // Por ahora, simulamos el envío.
    console.log('Datos enviados:', data);
    toast({
      title: 'Mensaje enviado',
      description: 'Gracias por contactarnos. Pronto nos pondremos en contacto contigo.',
      status: 'success',
      duration: 5000,
      isClosable: true,
    });
    reset();
  };

  return (
    <Box p={8}>
      <Heading textAlign="center" mb={6}>
        Contáctanos
      </Heading>
      <VStack
        as="form"
        spacing={4}
        onSubmit={handleSubmit(onSubmit)}
        maxW="600px"
        mx="auto"
      >
        <FormControl isInvalid={!!errors.name}>
          <FormLabel htmlFor="name">Nombre</FormLabel>
          <Input
            id="name"
            placeholder="Tu nombre"
            {...register('name', { required: 'El nombre es requerido' })}
          />
          <FormErrorMessage>{errors.name && errors.name.message}</FormErrorMessage>
        </FormControl>

        <FormControl isInvalid={!!errors.email}>
          <FormLabel htmlFor="email">Correo electrónico</FormLabel>
          <Input
            id="email"
            type="email"
            placeholder="tu@email.com"
            {...register('email', {
              required: 'El email es requerido',
              pattern: {
                value: /^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}$/i,
                message: 'Email inválido',
              },
            })}
          />
          <FormErrorMessage>
            {errors.email && errors.email.message}
          </FormErrorMessage>
        </FormControl>

        <FormControl isInvalid={!!errors.message}>
          <FormLabel htmlFor="message">Mensaje</FormLabel>
          <Textarea
            id="message"
            placeholder="Escribe tu mensaje..."
            {...register('message', { required: 'El mensaje es requerido' })}
          />
          <FormErrorMessage>
            {errors.message && errors.message.message}
          </FormErrorMessage>
        </FormControl>

        <Button
          colorScheme="green"
          isLoading={isSubmitting}
          type="submit"
          width="full"
        >
          Enviar
        </Button>
      </VStack>
    </Box>
  );
};

export default Contacto;
