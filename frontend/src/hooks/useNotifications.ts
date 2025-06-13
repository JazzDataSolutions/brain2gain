import { useState, useEffect, useCallback } from 'react';
import { notificationService } from '../services/NotificationService';
import { useAuth } from './useAuth';

export interface Notification {
  id: string;
  type: string;
  message: string;
  timestamp: string;
  read: boolean;
  priority?: 'low' | 'medium' | 'high';
}

export function useNotifications() {
  const { user } = useAuth();
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [isConnected, setIsConnected] = useState(false);
  const [connectionState, setConnectionState] = useState('disconnected');
  const [unreadCount, setUnreadCount] = useState(0);

  // Add notification to list
  const addNotification = useCallback((data: any) => {
    const notification: Notification = {
      id: Date.now().toString(),
      type: data.type || 'info',
      message: data.message || 'New notification',
      timestamp: data.timestamp || new Date().toISOString(),
      read: false,
      priority: data.priority || 'medium'
    };

    setNotifications(prev => [notification, ...prev.slice(0, 49)]); // Keep last 50
    setUnreadCount(prev => prev + 1);
  }, []);

  // Mark notification as read
  const markAsRead = useCallback((notificationId: string) => {
    setNotifications(prev => 
      prev.map(notif => 
        notif.id === notificationId 
          ? { ...notif, read: true }
          : notif
      )
    );
    setUnreadCount(prev => Math.max(0, prev - 1));
  }, []);

  // Mark all notifications as read
  const markAllAsRead = useCallback(() => {
    setNotifications(prev => 
      prev.map(notif => ({ ...notif, read: true }))
    );
    setUnreadCount(0);
  }, []);

  // Clear all notifications
  const clearAll = useCallback(() => {
    setNotifications([]);
    setUnreadCount(0);
  }, []);

  // Remove specific notification
  const removeNotification = useCallback((notificationId: string) => {
    setNotifications(prev => {
      const notification = prev.find(n => n.id === notificationId);
      if (notification && !notification.read) {
        setUnreadCount(count => Math.max(0, count - 1));
      }
      return prev.filter(n => n.id !== notificationId);
    });
  }, []);

  // Connection management
  const connect = useCallback(() => {
    if (user?.id) {
      const role = user.role?.name || 'user';
      notificationService.connect(user.id, role);
    }
  }, [user]);

  const disconnect = useCallback(() => {
    notificationService.disconnect();
  }, []);

  // Setup WebSocket event listeners
  useEffect(() => {
    const handleConnection = () => {
      setIsConnected(true);
      setConnectionState('connected');
    };

    const handleDisconnection = () => {
      setIsConnected(false);
      setConnectionState('disconnected');
    };

    const handleError = (error: any) => {
      console.error('Notification service error:', error);
      setConnectionState('error');
    };

    const handleNotification = (data: any) => {
      // Skip connection/ping messages from being added to notification list
      if (data.type === 'connection' || data.type === 'pong') {
        return;
      }
      addNotification(data);
    };

    // Register event listeners
    notificationService.on('connected', handleConnection);
    notificationService.on('disconnected', handleDisconnection);
    notificationService.on('error', handleError);
    notificationService.on('notification', handleNotification);

    // Auto-connect if user is available
    if (user?.id) {
      connect();
    }

    // Cleanup on unmount
    return () => {
      notificationService.off('connected', handleConnection);
      notificationService.off('disconnected', handleDisconnection);
      notificationService.off('error', handleError);
      notificationService.off('notification', handleNotification);
    };
  }, [user, connect, addNotification]);

  // Update connection state periodically
  useEffect(() => {
    const interval = setInterval(() => {
      const state = notificationService.getConnectionState();
      setConnectionState(state);
      setIsConnected(state === 'connected');
    }, 1000);

    return () => clearInterval(interval);
  }, []);

  // Auto-reconnect when user changes
  useEffect(() => {
    if (user?.id && !isConnected) {
      connect();
    } else if (!user?.id && isConnected) {
      disconnect();
    }
  }, [user, isConnected, connect, disconnect]);

  return {
    notifications,
    isConnected,
    connectionState,
    unreadCount,
    connect,
    disconnect,
    markAsRead,
    markAllAsRead,
    clearAll,
    removeNotification,
    addNotification
  };
}