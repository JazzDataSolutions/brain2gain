import {
  Box,
  CloseButton,
  HStack,
  Text,
  VStack,
  useColorModeValue,
  useToast,
} from "@chakra-ui/react"
import { useEffect } from "react"
import { useNotifications } from "../../hooks/useNotifications"

interface ToastNotificationProps {
  id: string
  type: string
  message: string
  timestamp: string
  onClose: () => void
}

function ToastNotification({
  type,
  message,
  timestamp,
  onClose,
}: ToastNotificationProps) {
  const bgColor = useColorModeValue("white", "gray.800")
  const borderColor = useColorModeValue("gray.200", "gray.600")

  const getNotificationIcon = (type: string) => {
    const icons = {
      order_update: "🛍️",
      low_stock: "⚠️",
      new_order: "🛒",
      connection: "🔗",
      test: "🧪",
      info: "💡",
      success: "✅",
      warning: "⚠️",
      error: "❌",
    }
    return icons[type as keyof typeof icons] || "🔔"
  }

  return (
    <Box
      bg={bgColor}
      borderWidth="1px"
      borderColor={borderColor}
      borderRadius="md"
      p={4}
      boxShadow="lg"
      maxW="400px"
      minW="300px"
    >
      <HStack align="start" spacing={3}>
        <Text fontSize="xl" mt={1}>
          {getNotificationIcon(type)}
        </Text>

        <VStack align="start" spacing={1} flex={1} minW={0}>
          <Text fontSize="sm" fontWeight="medium" noOfLines={3}>
            {message}
          </Text>

          <Text fontSize="xs" color="gray.500">
            {new Date(timestamp).toLocaleTimeString("es-ES", {
              hour: "2-digit",
              minute: "2-digit",
            })}
          </Text>
        </VStack>

        <CloseButton size="sm" onClick={onClose} />
      </HStack>
    </Box>
  )
}

export function NotificationToastManager() {
  const toast = useToast()
  const { notifications } = useNotifications()

  useEffect(() => {
    // Show toast for new unread notifications
    const latestNotification = notifications[0]

    if (latestNotification && !latestNotification.read) {
      // Only show toast for important notification types
      const shouldShowToast = [
        "low_stock",
        "new_order",
        "order_update",
        "error",
        "warning",
      ].includes(latestNotification.type)

      if (shouldShowToast) {
        toast({
          duration: latestNotification.type === "low_stock" ? 10000 : 5000,
          isClosable: true,
          position: "top-right",
          render: ({ onClose }) => (
            <ToastNotification
              id={latestNotification.id}
              type={latestNotification.type}
              message={latestNotification.message}
              timestamp={latestNotification.timestamp}
              onClose={onClose}
            />
          ),
        })
      }
    }
  }, [notifications, toast])

  return null // This component only manages toasts, doesn't render anything itself
}
