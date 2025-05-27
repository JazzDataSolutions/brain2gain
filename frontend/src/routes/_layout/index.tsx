import { createFileRoute } from '@tanstack/react-router'
import { Box, Heading, Text, SimpleGrid, Stat, StatLabel, StatNumber, StatHelpText } from '@chakra-ui/react'

const Dashboard = () => {
  return (
    <Box p={6}>
      <Heading mb={6}>Dashboard</Heading>
      
      <SimpleGrid columns={{ base: 1, md: 2, lg: 4 }} spacing={6} mb={8}>
        <Stat>
          <StatLabel>Total Products</StatLabel>
          <StatNumber>45</StatNumber>
          <StatHelpText>Active products in catalog</StatHelpText>
        </Stat>
        
        <Stat>
          <StatLabel>Orders Today</StatLabel>
          <StatNumber>12</StatNumber>
          <StatHelpText>+23% from yesterday</StatHelpText>
        </Stat>
        
        <Stat>
          <StatLabel>Revenue</StatLabel>
          <StatNumber>$1,245</StatNumber>
          <StatHelpText>This month</StatHelpText>
        </Stat>
        
        <Stat>
          <StatLabel>Customers</StatLabel>
          <StatNumber>284</StatNumber>
          <StatHelpText>Registered users</StatHelpText>
        </Stat>
      </SimpleGrid>

      <Text color="gray.600">
        Welcome to your Brain2Gain dashboard. Here you can manage your orders, view analytics, and update your profile.
      </Text>
    </Box>
  )
}

export const Route = createFileRoute('/_layout/')({
  component: Dashboard,
})
