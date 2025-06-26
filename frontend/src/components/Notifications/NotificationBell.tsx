import React, { useState } from 'react';
import {
  Box,
  IconButton,
  Badge,
  Popover,
  PopoverTrigger,
  PopoverContent,
  PopoverHeader,
  PopoverBody,
  VStack,
  Text,
  Button,
  HStack,
  Divider,
  useColorModeValue,
  Circle
} from '@chakra-ui/react';
import { FiBell, FiCheck, FiX, FiTrash2 } from 'react-icons/fi';
import { useNotifications } from '../../hooks/useNotifications';

export function NotificationBell() {
  const [isOpen, setIsOpen] = useState(false);
  const {
    notifications,
    unreadCount,
    isConnected,
    markAsRead,
    markAllAsRead,
    clearAll,
    removeNotification
  } = useNotifications();

  const bellColor = useColorModeValue('gray.600', 'gray.300');
  const bgColor = useColorModeValue('white', 'gray.800');
  const borderColor = useColorModeValue('gray.200', 'gray.600');

  const getNotificationIcon = (type: string) => {
    const icons = {
      'order_update': '🛍️',
      'low_stock': '⚠️',
      'new_order': '🛒',
      'connection': '🔗',
      'test': '🧪',
      'info': '💡',
      'success': '✅',
      'warning': '⚠️',
      'error': '❌'
    };
    return icons[type as keyof typeof icons] || '🔔';
  };

  const getNotificationColor = (type: string) => {
    const colors = {
      'order_update': 'blue.500',
      'low_stock': 'orange.500',
      'new_order': 'green.500',
      'connection': 'gray.500',
      'test': 'purple.500',
      'info': 'blue.500',
      'success': 'green.500',
      'warning': 'orange.500',
      'error': 'red.500'
    };
    return colors[type as keyof typeof colors] || 'gray.500';
  };

  return (
    <Popover isOpen={isOpen} onClose={() => setIsOpen(false)}>
      <PopoverTrigger>
        <IconButton
          aria-label="Notificaciones"
          icon={
            <Badge
              colorScheme={unreadCount > 0 ? 'red' : 'gray'}
              variant={unreadCount > 0 ? 'solid' : 'subtle'}
              fontSize="xs"
              position="absolute"
              top="-1"
              right="-1"
              display={unreadCount > 0 ? 'flex' : 'none'}
            >
              {unreadCount > 99 ? '99+' : unreadCount}
            </Badge>
          }
          variant="ghost"
          color={bellColor}
          position="relative"
          onClick={() => setIsOpen(!isOpen)}
        >
          <FiBell size={20} />
          {!isConnected && (
            <Circle
              size="8px"
              bg="red.500"
              position="absolute"
              bottom="0"
              right="0"
            />
          )}
        </IconButton>
      </PopoverTrigger>

      <PopoverContent w="400px" maxW="90vw" bg={bgColor} borderColor={borderColor}>
        <PopoverHeader>
          <HStack justify="space-between" align="center">
            <Text fontWeight="bold" fontSize="lg">
              Notificaciones
            </Text>
            <HStack spacing={1}>
              <Text fontSize="xs" color={isConnected ? 'green.500' : 'red.500'}>
                {isConnected ? '🟢 Conectado' : '🔴 Desconectado'}
              </Text>
              {unreadCount > 0 && (
                <Button
                  size="xs"
                  variant="ghost"
                  onClick={markAllAsRead}
                  leftIcon={<FiCheck size={12} />}
                >
                  Marcar todo
                </Button>
              )}
              <IconButton
                size="xs"
                variant="ghost"
                aria-label="Limpiar todo"
                icon={<FiTrash2 size={12} />}
                onClick={clearAll}
              />
            </HStack>
          </HStack>
        </PopoverHeader>

        <PopoverBody p={0} maxH="400px" overflowY="auto">
          {notifications.length === 0 ? (
            <Box p={4} textAlign="center" color="gray.500">
              <FiBell size={32} style={{ margin: '0 auto 8px' }} />
              <Text fontSize="sm">No hay notificaciones</Text>
            </Box>
          ) : (
            <VStack spacing={0} align="stretch">
              {notifications.map((notification, index) => (
                <React.Fragment key={notification.id}>
                  <Box
                    p={3}
                    cursor="pointer"
                    bg={notification.read ? 'transparent' : useColorModeValue('blue.50', 'blue.900')}
                    _hover={{ bg: useColorModeValue('gray.50', 'gray.700') }}
                    onClick={() => markAsRead(notification.id)}
                    position="relative"
                  >
                    <HStack align="start" spacing={3}>
                      <Text fontSize="lg" minW="24px">
                        {getNotificationIcon(notification.type)}
                      </Text>
                      
                      <VStack align="start" spacing={1} flex={1} minW={0}>
                        <Text
                          fontSize="sm"
                          fontWeight={notification.read ? 'normal' : 'semibold'}
                          color={useColorModeValue('gray.800', 'gray.200')}
                          noOfLines={2}
                        >
                          {notification.message}
                        </Text>
                        
                        <HStack spacing={2}>
                          <Text fontSize="xs" color="gray.500">
                            {new Date(notification.timestamp).toLocaleTimeString()}
                          </Text>
                          
                          {!notification.read && (
                            <Circle size="6px" bg={getNotificationColor(notification.type)} />
                          )}
                        </HStack>
                      </VStack>

                      <IconButton
                        size="xs"
                        variant="ghost"
                        aria-label="Eliminar notificación"
                        icon={<FiX size={12} />}
                        onClick={(e) => {
                          e.stopPropagation();
                          removeNotification(notification.id);
                        }}
                        opacity={0.5}
                        _hover={{ opacity: 1 }}
                      />
                    </HStack>
                  </Box>
                  
                  {index < notifications.length - 1 && <Divider />}
                </React.Fragment>
              ))}
              
              {notifications.length >= 50 && (
                <Box p={2} textAlign="center">
                  <Text fontSize="xs" color="gray.500">
                    Mostrando las últimas 50 notificaciones
                  </Text>
                </Box>
              )}
            </VStack>
          )}
        </PopoverBody>
      </PopoverContent>
    </Popover>
  );
}