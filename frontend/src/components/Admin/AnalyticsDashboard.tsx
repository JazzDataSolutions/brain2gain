// frontend/src/components/Admin/AnalyticsDashboard.tsx

import React, { useState, useEffect } from 'react'
import {
  Box,
  Grid,
  GridItem,
  Card,
  CardBody,
  Stat,
  StatLabel,
  StatNumber,
  StatHelpText,
  StatArrow,
  Heading,
  Text,
  VStack,
  HStack,
  Badge,
  Alert,
  AlertIcon,
  AlertTitle,
  AlertDescription,
  Spinner,
  useToast
} from '@chakra-ui/react'
import { TrendingUp, TrendingDown, DollarSign, ShoppingCart, Users, Package } from 'lucide-react'

interface FinancialSummary {
  revenue: {
    today: number
    month: number
    year: number
    growth_rate: number
  }
  orders: {
    orders_today: number
    orders_month: number
    pending_orders: number
    average_order_value: number
  }
  customers: {
    total_customers: number
    new_customers_month: number
    customers_with_orders: number
    active_customers_30d: number
    customer_conversion_rate: number
  }
  inventory: {
    total_products: number
    low_stock_products: number
    out_of_stock_products: number
    total_inventory_value: number
  }
  conversion: {
    cart_abandonment_rate: number
  }
}

interface RealtimeMetrics {
  current_revenue_today: number
  orders_today: number
  pending_orders: number
  active_carts: number
  low_stock_alerts: number
  timestamp: string
}

const AnalyticsDashboard: React.FC = () => {
  const [financialData, setFinancialData] = useState<FinancialSummary | null>(null)
  const [realtimeData, setRealtimeData] = useState<RealtimeMetrics | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const toast = useToast()

  // Format currency
  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0
    }).format(amount)
  }

  // Format percentage
  const formatPercentage = (value: number) => {
    return `${value.toFixed(1)}%`
  }

  // Fetch financial summary
  const fetchFinancialSummary = async () => {
    try {
      const response = await fetch('/api/analytics/financial-summary', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`
        }
      })
      
      if (!response.ok) {
        throw new Error('Failed to fetch financial summary')
      }
      
      const data = await response.json()
      setFinancialData(data)
    } catch (err) {
      setError('Failed to load financial data')
      toast({
        title: 'Error',
        description: 'Failed to load financial summary',
        status: 'error',
        duration: 5000,
        isClosable: true
      })
    }
  }

  // Fetch realtime metrics
  const fetchRealtimeMetrics = async () => {
    try {
      const response = await fetch('/api/analytics/realtime-metrics', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`
        }
      })
      
      if (!response.ok) {
        throw new Error('Failed to fetch realtime metrics')
      }
      
      const data = await response.json()
      setRealtimeData(data)
    } catch (err) {
      console.error('Failed to load realtime data:', err)
    }
  }

  // Initial data load
  useEffect(() => {
    const loadData = async () => {
      setLoading(true)
      await Promise.all([
        fetchFinancialSummary(),
        fetchRealtimeMetrics()
      ])
      setLoading(false)
    }

    loadData()
  }, [])

  // Refresh realtime data every 30 seconds
  useEffect(() => {
    const interval = setInterval(fetchRealtimeMetrics, 30000)
    return () => clearInterval(interval)
  }, [])

  if (loading) {
    return (
      <Box p={8} textAlign="center">
        <Spinner size="xl" />
        <Text mt={4}>Loading analytics dashboard...</Text>
      </Box>
    )
  }

  if (error) {
    return (
      <Alert status="error">
        <AlertIcon />
        <AlertTitle>Error!</AlertTitle>
        <AlertDescription>{error}</AlertDescription>
      </Alert>
    )
  }

  return (
    <Box p={6}>
      <VStack spacing={6} align="stretch">
        {/* Header */}
        <Box>
          <Heading size="lg" mb={2}>Analytics Dashboard</Heading>
          <Text color="gray.600">
            Real-time business metrics and insights
            {realtimeData && (
              <Text as="span" fontSize="sm" ml={2} color="gray.500">
                Last updated: {new Date(realtimeData.timestamp).toLocaleTimeString()}
              </Text>
            )}
          </Text>
        </Box>

        {/* Alerts */}
        {financialData?.inventory.low_stock_products > 0 && (
          <Alert status="warning">
            <AlertIcon />
            <AlertTitle>Inventory Alert!</AlertTitle>
            <AlertDescription>
              {financialData.inventory.low_stock_products} products are running low on stock.
            </AlertDescription>
          </Alert>
        )}

        {financialData?.inventory.out_of_stock_products > 0 && (
          <Alert status="error">
            <AlertIcon />
            <AlertTitle>Stock Alert!</AlertTitle>
            <AlertDescription>
              {financialData.inventory.out_of_stock_products} products are out of stock.
            </AlertDescription>
          </Alert>
        )}

        {/* Revenue Overview */}
        <Box>
          <Heading size="md" mb={4}>Revenue Overview</Heading>
          <Grid templateColumns="repeat(auto-fit, minmax(250px, 1fr))" gap={4}>
            <Card>
              <CardBody>
                <Stat>
                  <StatLabel>
                    <HStack>
                      <DollarSign size={16} />
                      <Text>Today's Revenue</Text>
                    </HStack>
                  </StatLabel>
                  <StatNumber>{formatCurrency(financialData?.revenue.today || 0)}</StatNumber>
                  <StatHelpText>
                    Real-time: {formatCurrency(realtimeData?.current_revenue_today || 0)}
                  </StatHelpText>
                </Stat>
              </CardBody>
            </Card>

            <Card>
              <CardBody>
                <Stat>
                  <StatLabel>
                    <HStack>
                      <DollarSign size={16} />
                      <Text>Monthly Revenue</Text>
                    </HStack>
                  </StatLabel>
                  <StatNumber>{formatCurrency(financialData?.revenue.month || 0)}</StatNumber>
                  <StatHelpText>
                    <StatArrow 
                      type={financialData?.revenue.growth_rate >= 0 ? 'increase' : 'decrease'} 
                    />
                    {formatPercentage(Math.abs(financialData?.revenue.growth_rate || 0))} growth
                  </StatHelpText>
                </Stat>
              </CardBody>
            </Card>

            <Card>
              <CardBody>
                <Stat>
                  <StatLabel>
                    <HStack>
                      <DollarSign size={16} />
                      <Text>Yearly Revenue</Text>
                    </HStack>
                  </StatLabel>
                  <StatNumber>{formatCurrency(financialData?.revenue.year || 0)}</StatNumber>
                  <StatHelpText>Year to date</StatHelpText>
                </Stat>
              </CardBody>
            </Card>

            <Card>
              <CardBody>
                <Stat>
                  <StatLabel>
                    <HStack>
                      <ShoppingCart size={16} />
                      <Text>Average Order Value</Text>
                    </HStack>
                  </StatLabel>
                  <StatNumber>{formatCurrency(financialData?.orders.average_order_value || 0)}</StatNumber>
                  <StatHelpText>Per completed order</StatHelpText>
                </Stat>
              </CardBody>
            </Card>
          </Grid>
        </Box>

        {/* Orders & Customers */}
        <Grid templateColumns="repeat(auto-fit, minmax(300px, 1fr))" gap={6}>
          {/* Orders */}
          <Card>
            <CardBody>
              <VStack align="stretch" spacing={4}>
                <Heading size="sm">Orders</Heading>
                
                <HStack justify="space-between">
                  <Text>Today's Orders</Text>
                  <Badge colorScheme="blue" fontSize="md" px={2}>
                    {financialData?.orders.orders_today || 0}
                  </Badge>
                </HStack>

                <HStack justify="space-between">
                  <Text>Monthly Orders</Text>
                  <Badge colorScheme="green" fontSize="md" px={2}>
                    {financialData?.orders.orders_month || 0}
                  </Badge>
                </HStack>

                <HStack justify="space-between">
                  <Text>Pending Orders</Text>
                  <Badge 
                    colorScheme={financialData?.orders.pending_orders > 10 ? "orange" : "gray"} 
                    fontSize="md" 
                    px={2}
                  >
                    {financialData?.orders.pending_orders || 0}
                  </Badge>
                </HStack>

                <HStack justify="space-between">
                  <Text>Active Carts</Text>
                  <Badge colorScheme="purple" fontSize="md" px={2}>
                    {realtimeData?.active_carts || 0}
                  </Badge>
                </HStack>
              </VStack>
            </CardBody>
          </Card>

          {/* Customers */}
          <Card>
            <CardBody>
              <VStack align="stretch" spacing={4}>
                <Heading size="sm">Customers</Heading>
                
                <HStack justify="space-between">
                  <Text>Total Customers</Text>
                  <Badge colorScheme="blue" fontSize="md" px={2}>
                    {financialData?.customers.total_customers || 0}
                  </Badge>
                </HStack>

                <HStack justify="space-between">
                  <Text>New This Month</Text>
                  <Badge colorScheme="green" fontSize="md" px={2}>
                    {financialData?.customers.new_customers_month || 0}
                  </Badge>
                </HStack>

                <HStack justify="space-between">
                  <Text>Active (30 days)</Text>
                  <Badge colorScheme="orange" fontSize="md" px={2}>
                    {financialData?.customers.active_customers_30d || 0}
                  </Badge>
                </HStack>

                <HStack justify="space-between">
                  <Text>Conversion Rate</Text>
                  <Badge 
                    colorScheme={
                      financialData?.customers.customer_conversion_rate > 50 ? "green" : 
                      financialData?.customers.customer_conversion_rate > 25 ? "yellow" : "red"
                    } 
                    fontSize="md" 
                    px={2}
                  >
                    {formatPercentage(financialData?.customers.customer_conversion_rate || 0)}
                  </Badge>
                </HStack>
              </VStack>
            </CardBody>
          </Card>
        </Grid>

        {/* Inventory & Conversion */}
        <Grid templateColumns="repeat(auto-fit, minmax(300px, 1fr))" gap={6}>
          {/* Inventory */}
          <Card>
            <CardBody>
              <VStack align="stretch" spacing={4}>
                <Heading size="sm">Inventory</Heading>
                
                <HStack justify="space-between">
                  <Text>Total Products</Text>
                  <Badge colorScheme="blue" fontSize="md" px={2}>
                    {financialData?.inventory.total_products || 0}
                  </Badge>
                </HStack>

                <HStack justify="space-between">
                  <Text>Low Stock Items</Text>
                  <Badge 
                    colorScheme={financialData?.inventory.low_stock_products > 0 ? "orange" : "green"} 
                    fontSize="md" 
                    px={2}
                  >
                    {financialData?.inventory.low_stock_products || 0}
                  </Badge>
                </HStack>

                <HStack justify="space-between">
                  <Text>Out of Stock</Text>
                  <Badge 
                    colorScheme={financialData?.inventory.out_of_stock_products > 0 ? "red" : "green"} 
                    fontSize="md" 
                    px={2}
                  >
                    {financialData?.inventory.out_of_stock_products || 0}
                  </Badge>
                </HStack>

                <HStack justify="space-between">
                  <Text>Inventory Value</Text>
                  <Text fontWeight="bold">
                    {formatCurrency(financialData?.inventory.total_inventory_value || 0)}
                  </Text>
                </HStack>
              </VStack>
            </CardBody>
          </Card>

          {/* Conversion Metrics */}
          <Card>
            <CardBody>
              <VStack align="stretch" spacing={4}>
                <Heading size="sm">Conversion Metrics</Heading>
                
                <VStack align="stretch" spacing={3}>
                  <Box>
                    <HStack justify="space-between" mb={1}>
                      <Text fontSize="sm">Cart Abandonment Rate</Text>
                      <Text fontSize="sm" fontWeight="bold">
                        {formatPercentage(financialData?.conversion.cart_abandonment_rate || 0)}
                      </Text>
                    </HStack>
                    <Box 
                      w="full" 
                      h="8px" 
                      bg="gray.200" 
                      borderRadius="md" 
                      overflow="hidden"
                    >
                      <Box 
                        h="full" 
                        bg={
                          financialData?.conversion.cart_abandonment_rate > 70 ? "red.400" :
                          financialData?.conversion.cart_abandonment_rate > 50 ? "orange.400" : "green.400"
                        }
                        w={`${financialData?.conversion.cart_abandonment_rate || 0}%`}
                      />
                    </Box>
                  </Box>

                  <Box>
                    <HStack justify="space-between" mb={1}>
                      <Text fontSize="sm">Completion Rate</Text>
                      <Text fontSize="sm" fontWeight="bold">
                        {formatPercentage(100 - (financialData?.conversion.cart_abandonment_rate || 0))}
                      </Text>
                    </HStack>
                    <Box 
                      w="full" 
                      h="8px" 
                      bg="gray.200" 
                      borderRadius="md" 
                      overflow="hidden"
                    >
                      <Box 
                        h="full" 
                        bg="green.400"
                        w={`${100 - (financialData?.conversion.cart_abandonment_rate || 0)}%`}
                      />
                    </Box>
                  </Box>
                </VStack>
              </VStack>
            </CardBody>
          </Card>
        </Grid>
      </VStack>
    </Box>
  )
}

export default AnalyticsDashboard