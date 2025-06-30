// src/components/LoginPage.tsx
import {
  Box,
  Button,
  FormControl,
  FormErrorMessage,
  FormLabel,
  Input,
} from "@chakra-ui/react"
import { type SubmitHandler, useForm } from "react-hook-form"

// Definimos la interfaz para los datos del formulario de login
interface LoginFormInputs {
  email: string
  password: string
}

const LoginPage: React.FC = () => {
  // Usamos useForm con el tipado definido
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<LoginFormInputs>()

  // Función de envío con tipado explícito
  const onSubmit: SubmitHandler<LoginFormInputs> = async (
    data: LoginFormInputs,
  ) => {
    // Aquí se podría llamar a la API para autenticar al usuario.
    console.log("Datos de login:", data)
  }

  return (
    <Box p={4}>
      <form onSubmit={handleSubmit(onSubmit)}>
        <FormControl isInvalid={!!errors.email}>
          <FormLabel htmlFor="email">Correo electrónico</FormLabel>
          <Input
            id="email"
            type="email"
            placeholder="tu@correo.com"
            {...register("email", { required: "El correo es obligatorio" })}
          />
          <FormErrorMessage>{errors.email?.message}</FormErrorMessage>
        </FormControl>
        <FormControl mt={4} isInvalid={!!errors.password}>
          <FormLabel htmlFor="password">Contraseña</FormLabel>
          <Input
            id="password"
            type="password"
            placeholder="contraseña"
            {...register("password", {
              required: "La contraseña es obligatoria",
            })}
          />
          <FormErrorMessage>{errors.password?.message}</FormErrorMessage>
        </FormControl>
        <Button mt={4} colorScheme="teal" type="submit">
          Iniciar sesión
        </Button>
      </form>
    </Box>
  )
}

export default LoginPage
