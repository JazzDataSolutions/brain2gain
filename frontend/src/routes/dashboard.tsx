import { Box, Container, Text } from "@chakra-ui/react"
// frontend/src/routes/dashboard.tsx
import { createFileRoute } from "@tanstack/react-router"
import useAuth from "../hooks/useAuth"

const Dashboard = () => {
  const { user: currentUser } = useAuth()
  return (
    <Container maxW="full">
      <Box pt={12} m={4}>
        <Text fontSize="2xl">
          Hi, {currentUser?.full_name || currentUser?.email} 👋🏼
        </Text>
        <Text>Welcome back, nice to see you again!</Text>
      </Box>
    </Container>
  )
}

export const Route = createFileRoute("/dashboard")({
  component: Dashboard,
})
