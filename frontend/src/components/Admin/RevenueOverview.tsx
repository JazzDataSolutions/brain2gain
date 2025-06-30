import {
  Box,
  Card,
  CardBody,
  Grid,
  HStack,
  Heading,
  Icon,
  Stat,
  StatArrow,
  StatHelpText,
  StatLabel,
  StatNumber,
  Text,
} from "@chakra-ui/react"
import type React from "react"
import {
  FiDollarSign,
  FiShoppingCart,
  FiTrendingUp,
  FiUsers,
} from "react-icons/fi"
import type {
  FinancialSummary,
  RealtimeMetrics,
} from "../../services/AnalyticsService"

interface RevenueOverviewProps {
  financialData: FinancialSummary | null
  realtimeData: RealtimeMetrics | null
  formatCurrency: (amount: number) => string
  formatPercentage: (value: number) => string
}

const RevenueOverview: React.FC<RevenueOverviewProps> = ({
  financialData,
  realtimeData,
  formatCurrency,
  formatPercentage,
}) => (
  <Box>
    <Heading size="md" mb={4}>
      Revenue Overview
    </Heading>
    <Grid templateColumns="repeat(auto-fit, minmax(250px, 1fr))" gap={4}>
      <Card>
        <CardBody>
          <Stat>
            <StatLabel>
              <HStack>
                <Icon as={FiDollarSign} boxSize={4} />
                <Text>Today's Revenue</Text>
              </HStack>
            </StatLabel>
            <StatNumber>
              {formatCurrency(financialData?.revenue.today || 0)}
            </StatNumber>
            <StatHelpText>
              Real-time:{" "}
              {formatCurrency(realtimeData?.current_revenue_today || 0)}
            </StatHelpText>
          </Stat>
        </CardBody>
      </Card>

      <Card>
        <CardBody>
          <Stat>
            <StatLabel>
              <HStack>
                <Icon as={FiDollarSign} boxSize={4} />
                <Text>Monthly Revenue</Text>
              </HStack>
            </StatLabel>
            <StatNumber>
              {formatCurrency(financialData?.revenue.month || 0)}
            </StatNumber>
            <StatHelpText>
              <StatArrow
                type={
                  financialData?.revenue?.growth_rate &&
                  financialData.revenue.growth_rate >= 0
                    ? "increase"
                    : "decrease"
                }
              />
              {formatPercentage(
                Math.abs(financialData?.revenue?.growth_rate || 0),
              )}{" "}
              growth
            </StatHelpText>
          </Stat>
        </CardBody>
      </Card>

      <Card>
        <CardBody>
          <Stat>
            <StatLabel>
              <HStack>
                <Icon as={FiTrendingUp} boxSize={4} />
                <Text>MRR</Text>
              </HStack>
            </StatLabel>
            <StatNumber>
              {formatCurrency(financialData?.revenue.mrr || 0)}
            </StatNumber>
            <StatHelpText>Monthly Recurring Revenue</StatHelpText>
          </Stat>
        </CardBody>
      </Card>

      <Card>
        <CardBody>
          <Stat>
            <StatLabel>
              <HStack>
                <Icon as={FiTrendingUp} boxSize={4} />
                <Text>ARR</Text>
              </HStack>
            </StatLabel>
            <StatNumber>
              {formatCurrency(financialData?.revenue.arr || 0)}
            </StatNumber>
            <StatHelpText>Annual Recurring Revenue</StatHelpText>
          </Stat>
        </CardBody>
      </Card>

      <Card>
        <CardBody>
          <Stat>
            <StatLabel>
              <HStack>
                <Icon as={FiShoppingCart} boxSize={4} />
                <Text>Average Order Value</Text>
              </HStack>
            </StatLabel>
            <StatNumber>
              {formatCurrency(financialData?.orders.average_order_value || 0)}
            </StatNumber>
            <StatHelpText>Per completed order</StatHelpText>
          </Stat>
        </CardBody>
      </Card>

      <Card>
        <CardBody>
          <Stat>
            <StatLabel>
              <HStack>
                <Icon as={FiUsers} boxSize={4} />
                <Text>Revenue Per Visitor</Text>
              </HStack>
            </StatLabel>
            <StatNumber>
              {formatCurrency(financialData?.revenue.revenue_per_visitor || 0)}
            </StatNumber>
            <StatHelpText>RPV (30 days)</StatHelpText>
          </Stat>
        </CardBody>
      </Card>
    </Grid>
  </Box>
)

export default RevenueOverview
