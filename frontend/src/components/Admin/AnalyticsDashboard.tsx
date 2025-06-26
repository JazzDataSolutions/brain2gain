// frontend/src/components/Admin/AnalyticsDashboard.tsx

import React, { useState, useEffect } from 'react'
import {
  Box,
  Grid,
  Card,
  CardBody,
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
  useToast,
  Button,
} from '@chakra-ui/react'
import { Icon } from '@chakra-ui/react'
import RevenueOverview from './RevenueOverview'
import { 
  FiRefreshCw, 
  FiAlertTriangle
} from 'react-icons/fi'
import AnalyticsService, { 
  type FinancialSummary, 
  type RealtimeMetrics, 
  type AlertSummary 
} from '../../services/AnalyticsService'

const AnalyticsDashboard: React.FC = () => {
  const [financialData, setFinancialData] = useState<FinancialSummary | null>(null)
  const [realtimeData, setRealtimeData] = useState<RealtimeMetrics | null>(null)
  const [alertsData, setAlertsData] = useState<AlertSummary | null>(null)
  
  const [loading, setLoading] = useState(true)
  const [refreshing, setRefreshing] = useState(false)
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
      const data = await AnalyticsService.getFinancialSummaryWithFallback()
      setFinancialData(data)
      setError(null) // Clear any previous errors
    } catch (err) {
      const errorMessage = 'Failed to load financial data'
      setError(errorMessage)
      toast({
        title: 'Error',
        description: errorMessage,
        status: 'error',
        duration: 5000,
        isClosable: true
      })
    }
  }

  // Fetch realtime metrics
  const fetchRealtimeMetrics = async () => {
    try {
      const data = await AnalyticsService.getRealtimeMetricsWithFallback()
      setRealtimeData(data)
    } catch (err) {
      console.error('Failed to load realtime data:', err)
    }
  }

  // Fetch alerts
  const fetchAlerts = async () => {
    try {
      const data = await AnalyticsService.getAlertSummaryWithFallback()
      setAlertsData(data)
    } catch (err) {
      console.error('Failed to load alerts:', err)
    }
  }

  // Phase 2: Fetch RFM Segmentation Data
  const fetchRFMData = async () => {
    try {
      const response = await fetch('/api/v1/analytics/segmentation/rfm', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      })
      if (response.ok) {
        await response.json()
      }
    } catch (err) {
      console.error('Failed to load RFM data:', err)
    }
  }

  // Phase 2: Fetch Cohort Analysis Data
  const fetchCohortData = async () => {
    try {
      const response = await fetch('/api/v1/analytics/cohorts/retention?months_back=6', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      })
      if (response.ok) {
        await response.json()
      }
    } catch (err) {
      console.error('Failed to load cohort data:', err)
    }
  }

  // Phase 2: Fetch Conversion Funnel Data
  const fetchFunnelData = async () => {
    try {
      const response = await fetch('/api/v1/analytics/funnel/conversion?days=30', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      })
      if (response.ok) {
        await response.json()
      }
    } catch (err) {
      console.error('Failed to load funnel data:', err)
    }
  }

  // Refresh all data
  const refreshAllData = async () => {
    setRefreshing(true)
    try {
      await Promise.all([
        fetchFinancialSummary(),
        fetchRealtimeMetrics(),
        fetchAlerts(),
        fetchRFMData(),
        fetchCohortData(),
        fetchFunnelData()
      ])
      
      toast({
        title: 'Success',
        description: 'Dashboard data refreshed successfully',
        status: 'success',
        duration: 3000,
        isClosable: true
      })
    } catch (err) {
      toast({
        title: 'Error',
        description: 'Failed to refresh some data',
        status: 'warning',
        duration: 5000,
        isClosable: true
      })
    } finally {
      setRefreshing(false)
    }
  }

  // Initial data load
  useEffect(() => {
    const loadData = async () => {
      setLoading(true)
      await Promise.all([
        fetchFinancialSummary(),
        fetchRealtimeMetrics(),
        fetchAlerts(),
        fetchRFMData(),
        fetchCohortData(),
        fetchFunnelData()
      ])
      setLoading(false)
    }

    loadData()
  }, [])

  // Refresh realtime data every 30 seconds
  useEffect(() => {
    const interval = setInterval(() => {
      fetchRealtimeMetrics()
      fetchAlerts() // Also refresh alerts periodically
    }, 30000)
    return () => clearInterval(interval)
  }, [])

  if (loading) {
    return (
      <Box p={8} textAlign="center">
        <Spinner size="xl" data-testid="loading-spinner" />
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
          <HStack justify="space-between" align="center" mb={4}>
            <Box>
              <Heading size="lg" mb={2}>Analytics Dashboard</Heading>
              <HStack spacing={4} align="center">
                <Text color="gray.600">
                  Real-time business metrics and advanced analytics
                </Text>
                {alertsData && alertsData.total_alerts > 0 && (
                  <Badge 
                    colorScheme={alertsData.critical_alerts > 0 ? "red" : "orange"} 
                    variant="solid"
                    display="flex"
                    alignItems="center"
                    gap={1}
                  >
                    <Icon as={FiAlertTriangle} boxSize={3} />
                    {alertsData.total_alerts} Alert{alertsData.total_alerts > 1 ? 's' : ''}
                  </Badge>
                )}
              </HStack>
            </Box>
            
            <VStack align="end" spacing={1}>
              <Button
                size="sm"
                colorScheme="blue"
                variant="outline"
                leftIcon={<Icon as={FiRefreshCw} boxSize={3.5} />}
                onClick={refreshAllData}
                isLoading={refreshing}
                loadingText="Refreshing"
              >
                Refresh
              </Button>
              {realtimeData && (
                <Text fontSize="xs" color="gray.500">
                  Last updated: {new Date(realtimeData.timestamp).toLocaleTimeString()}
                </Text>
              )}
            </VStack>
          </HStack>
        </Box>

        {/* Dynamic Alerts from API */}
        {alertsData && alertsData.alerts.length > 0 && (
          <VStack spacing={3} align="stretch">
            {alertsData.alerts.slice(0, 3).map((alert) => (
              <Alert 
                key={alert.id}
                status={
                  alert.severity === 'critical' ? 'error' : 
                  alert.severity === 'warning' ? 'warning' : 'info'
                }
              >
                <AlertIcon />
                <Box flex="1">
                  <AlertTitle fontSize="sm">{alert.title}</AlertTitle>
                  <AlertDescription fontSize="sm">
                    {alert.description}
                  </AlertDescription>
                </Box>
                <Badge 
                  colorScheme={
                    alert.severity === 'critical' ? 'red' : 
                    alert.severity === 'warning' ? 'orange' : 'blue'
                  }
                  size="sm"
                >
                  {alert.severity.toUpperCase()}
                </Badge>
              </Alert>
            ))}
            {alertsData.alerts.length > 3 && (
              <Text fontSize="sm" color="gray.500" textAlign="center">
                + {alertsData.alerts.length - 3} more alerts
              </Text>
            )}
          </VStack>
        )}

        {/* Fallback inventory alerts */}
                {(!alertsData || alertsData.alerts.length === 0) && financialData?.inventory?.low_stock_products && financialData.inventory.low_stock_products > 0 && (
          <Alert status="warning">
            <AlertIcon />
            <AlertTitle>Inventory Alert!</AlertTitle>
            <AlertDescription>
              {financialData?.inventory?.low_stock_products} products are running low on stock.
            </AlertDescription>
          </Alert>
        )}

        {(!alertsData || alertsData.alerts.length === 0) && financialData?.inventory?.out_of_stock_products && financialData.inventory.out_of_stock_products > 0 && (
          <Alert status="error">
            <AlertIcon />
            <AlertTitle>Stock Alert!</AlertTitle>
            <AlertDescription>
              {financialData?.inventory?.out_of_stock_products} products are out of stock.
            </AlertDescription>
          </Alert>
        )}

        {/* Revenue Overview */}
        <RevenueOverview
          financialData={financialData}
          realtimeData={realtimeData}
          formatCurrency={formatCurrency}
          formatPercentage={formatPercentage}
        />

        {/* KPI Summary Cards */}
        <Box>
          <Heading size="md" mb={4}>Key Performance Indicators</Heading>
          <Grid templateColumns="repeat(auto-fit, minmax(280px, 1fr))" gap={4}>
            {/* MRR Growth Card */}
            <Card>
              <CardBody>
                <VStack align="stretch" spacing={3}>
                  <HStack justify="space-between">
                    <Text fontSize="sm" fontWeight="medium">MRR Growth</Text>
                    <Badge colorScheme="green" size="sm">
                      +{formatPercentage(Math.abs(financialData?.revenue.growth_rate || 0))}
                    </Badge>
                  </HStack>
                  <Text fontSize="2xl" fontWeight="bold">
                    {formatCurrency(financialData?.revenue.mrr || 0)}
                  </Text>
                  <Box>
                    <Text fontSize="xs" color="gray.500" mb={1}>
                      Projected ARR: {formatCurrency(financialData?.revenue.arr || 0)}
                    </Text>
                    <Box w="full" h="2" bg="gray.200" borderRadius="full" overflow="hidden">
                      <Box 
                        h="full" 
                        bg="green.400" 
                        w={`${Math.min((financialData?.revenue.mrr || 0) / 50000 * 100, 100)}%`}
                        borderRadius="full"
                      />
                    </Box>
                  </Box>
                </VStack>
              </CardBody>
            </Card>

            {/* Customer Health Card */}
            <Card>
              <CardBody>
                <VStack align="stretch" spacing={3}>
                  <HStack justify="space-between">
                    <Text fontSize="sm" fontWeight="medium">Customer Health</Text>
                    <Badge 
                      colorScheme={
                        (financialData?.conversion.churn_rate || 0) < 10 ? "green" : 
                        (financialData?.conversion.churn_rate || 0) < 15 ? "orange" : "red"
                      } 
                      size="sm"
                    >
                      {(financialData?.conversion.churn_rate || 0) < 10 ? "Healthy" : 
                       (financialData?.conversion.churn_rate || 0) < 15 ? "Warning" : "Critical"}
                    </Badge>
                  </HStack>
                  <HStack spacing={4}>
                    <VStack align="start" spacing={1} flex={1}>
                      <Text fontSize="xs" color="gray.500">Churn Rate</Text>
                      <Text fontSize="lg" fontWeight="bold" color="red.500">
                        {formatPercentage(financialData?.conversion.churn_rate || 0)}
                      </Text>
                    </VStack>
                    <VStack align="start" spacing={1} flex={1}>
                      <Text fontSize="xs" color="gray.500">Repeat Rate</Text>
                      <Text fontSize="lg" fontWeight="bold" color="green.500">
                        {formatPercentage(financialData?.conversion.repeat_customer_rate || 0)}
                      </Text>
                    </VStack>
                  </HStack>
                  <Box>
                    <Text fontSize="xs" color="gray.500" mb={1}>Retention Score</Text>
                    <Box w="full" h="2" bg="gray.200" borderRadius="full" overflow="hidden">
                      <Box 
                        h="full" 
                        bg={
                          (financialData?.conversion.churn_rate || 0) < 10 ? "green.400" : 
                          (financialData?.conversion.churn_rate || 0) < 15 ? "orange.400" : "red.400"
                        }
                        w={`${Math.max(100 - (financialData?.conversion.churn_rate || 0), 0)}%`}
                        borderRadius="full"
                      />
                    </Box>
                  </Box>
                </VStack>
              </CardBody>
            </Card>

            {/* Conversion Funnel Card */}
            <Card>
              <CardBody>
                <VStack align="stretch" spacing={3}>
                  <HStack justify="space-between">
                    <Text fontSize="sm" fontWeight="medium">Conversion Funnel</Text>
                    <Badge 
                      colorScheme={
                        (financialData?.conversion.conversion_rate || 0) > 5 ? "green" : 
                        (financialData?.conversion.conversion_rate || 0) > 2 ? "orange" : "red"
                      } 
                      size="sm"
                    >
                      {formatPercentage(financialData?.conversion.conversion_rate || 0)}
                    </Badge>
                  </HStack>
                  
                  <VStack align="stretch" spacing={2}>
                    {/* Funnel Steps */}
                    <Box>
                      <HStack justify="space-between" mb={1}>
                        <Text fontSize="xs">Visitors</Text>
                        <Text fontSize="xs">100%</Text>
                      </HStack>
                      <Box w="full" h="2" bg="blue.100" borderRadius="full" />
                    </Box>
                    
                    <Box>
                      <HStack justify="space-between" mb={1}>
                        <Text fontSize="xs">Add to Cart</Text>
                        <Text fontSize="xs">
                          {formatPercentage(100 - (financialData?.conversion.cart_abandonment_rate || 0))}
                        </Text>
                      </HStack>
                      <Box w="full" h="2" bg="gray.200" borderRadius="full" overflow="hidden">
                        <Box 
                          h="full" 
                          bg="blue.300" 
                          w={`${100 - (financialData?.conversion.cart_abandonment_rate || 0)}%`}
                          borderRadius="full"
                        />
                      </Box>
                    </Box>
                    
                    <Box>
                      <HStack justify="space-between" mb={1}>
                        <Text fontSize="xs">Purchase</Text>
                        <Text fontSize="xs">
                          {formatPercentage(financialData?.conversion.conversion_rate || 0)}
                        </Text>
                      </HStack>
                      <Box w="full" h="2" bg="gray.200" borderRadius="full" overflow="hidden">
                        <Box 
                          h="full" 
                          bg="green.400" 
                          w={`${Math.min(financialData?.conversion.conversion_rate || 0, 100)}%`}
                          borderRadius="full"
                        />
                      </Box>
                    </Box>
                  </VStack>
                </VStack>
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
                    colorScheme={financialData?.orders?.pending_orders && financialData.orders.pending_orders > 10 ? "orange" : "gray"} 
                    fontSize="md" 
                    px={2}
                  >
                    {financialData?.orders?.pending_orders || 0}
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
                      financialData?.customers?.customer_conversion_rate && financialData.customers.customer_conversion_rate > 50 ? "green" : 
                      financialData?.customers?.customer_conversion_rate && financialData.customers.customer_conversion_rate > 25 ? "yellow" : "red"
                    } 
                    fontSize="md" 
                    px={2}
                  >
                    {formatPercentage(financialData?.customers?.customer_conversion_rate || 0)}
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
                    colorScheme={financialData?.inventory?.low_stock_products && financialData.inventory.low_stock_products > 0 ? "orange" : "green"} 
                    fontSize="md" 
                    px={2}
                  >
                    {financialData?.inventory?.low_stock_products || 0}
                  </Badge>
                </HStack>

                <HStack justify="space-between">
                  <Text>Out of Stock</Text>
                  <Badge 
                    colorScheme={financialData?.inventory?.out_of_stock_products && financialData.inventory.out_of_stock_products > 0 ? "red" : "green"} 
                    fontSize="md" 
                    px={2}
                  >
                    {financialData?.inventory?.out_of_stock_products || 0}
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
                      <Text fontSize="sm">Conversion Rate</Text>
                      <Text fontSize="sm" fontWeight="bold">
                        {formatPercentage(financialData?.conversion?.conversion_rate || 0)}
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
                          financialData?.conversion?.conversion_rate && financialData.conversion.conversion_rate > 5 ? "green.400" :
                          financialData?.conversion?.conversion_rate && financialData.conversion.conversion_rate > 2 ? "orange.400" : "red.400"
                        }
                        w={`${Math.min(financialData?.conversion?.conversion_rate || 0, 100)}%`}
                      />
                    </Box>
                  </Box>

                  <Box>
                    <HStack justify="space-between" mb={1}>
                      <Text fontSize="sm">Cart Abandonment Rate</Text>
                      <Text fontSize="sm" fontWeight="bold">
                        {formatPercentage(financialData?.conversion?.cart_abandonment_rate || 0)}
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
                          financialData?.conversion?.cart_abandonment_rate && financialData.conversion.cart_abandonment_rate > 70 ? "red.400" :
                          financialData?.conversion?.cart_abandonment_rate && financialData.conversion.cart_abandonment_rate > 50 ? "orange.400" : "green.400"
                        }
                        w={`${financialData?.conversion?.cart_abandonment_rate || 0}%`}
                      />
                    </Box>
                  </Box>

                  <Box>
                    <HStack justify="space-between" mb={1}>
                      <Text fontSize="sm">Repeat Customer Rate</Text>
                      <Text fontSize="sm" fontWeight="bold">
                        {formatPercentage(financialData?.conversion?.repeat_customer_rate || 0)}
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
                          financialData?.conversion?.repeat_customer_rate && financialData.conversion.repeat_customer_rate > 30 ? "green.400" :
                          financialData?.conversion?.repeat_customer_rate && financialData.conversion.repeat_customer_rate > 15 ? "orange.400" : "red.400"
                        }
                        w={`${Math.min(financialData?.conversion?.repeat_customer_rate || 0, 100)}%`}
                      />
                    </Box>
                  </Box>

                  <Box>
                    <HStack justify="space-between" mb={1}>
                      <Text fontSize="sm">Churn Rate</Text>
                      <Text fontSize="sm" fontWeight="bold" color={
                        financialData?.conversion?.churn_rate && financialData.conversion.churn_rate > 15 ? "red.500" :
                        financialData?.conversion?.churn_rate && financialData.conversion.churn_rate > 10 ? "orange.500" : "green.500"
                      }>
                        {formatPercentage(financialData?.conversion?.churn_rate || 0)}
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
                          financialData?.conversion?.churn_rate && financialData.conversion.churn_rate > 15 ? "red.400" :
                          financialData?.conversion?.churn_rate && financialData.conversion.churn_rate > 10 ? "orange.400" : "green.400"
                        }
                        w={`${Math.min(financialData?.conversion?.churn_rate || 0, 100)}%`}
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