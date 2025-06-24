import { renderHook, act } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { useNotifications } from '../../../hooks/useNotifications';
import { notificationService } from '../../../services/NotificationService';

// Mock the notification service
vi.mock('../../../services/NotificationService');
const mockNotificationService = notificationService as any;

// Mock useAuth hook
vi.mock('../../../hooks/useAuth', () => ({
  useAuth: () => ({
    user: {
      id: 'user123',
      role: { name: 'admin' },
      email: 'test@example.com'
    }
  })
}));

describe('useNotifications', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    
    // Reset notification service mocks
    mockNotificationService.connect = vi.fn();
    mockNotificationService.disconnect = vi.fn();
    mockNotificationService.on = vi.fn();
    mockNotificationService.off = vi.fn();
    mockNotificationService.isConnected = vi.fn().mockReturnValue(true);
    mockNotificationService.getConnectionState = vi.fn().mockReturnValue('connected');
  });

  it('should initialize with empty notifications', () => {
    const { result } = renderHook(() => useNotifications());

    expect(result.current.notifications).toEqual([]);
    expect(result.current.unreadCount).toBe(0);
    expect(result.current.isConnected).toBe(true);
  });

  it('should auto-connect when user is available', () => {
    renderHook(() => useNotifications());

    expect(mockNotificationService.connect).toHaveBeenCalledWith('user123', 'admin');
  });

  it('should add notification and update unread count', () => {
    const { result } = renderHook(() => useNotifications());

    act(() => {
      result.current.addNotification({
        type: 'order_update',
        message: 'Your order has been shipped',
        timestamp: new Date().toISOString()
      });
    });

    expect(result.current.notifications).toHaveLength(1);
    expect(result.current.unreadCount).toBe(1);
    expect(result.current.notifications[0].message).toBe('Your order has been shipped');
    expect(result.current.notifications[0].read).toBe(false);
  });

  it('should mark notification as read', () => {
    const { result } = renderHook(() => useNotifications());

    // Add a notification first
    act(() => {
      result.current.addNotification({
        type: 'info',
        message: 'Test notification',
        timestamp: new Date().toISOString()
      });
    });

    const notificationId = result.current.notifications[0].id;

    // Mark as read
    act(() => {
      result.current.markAsRead(notificationId);
    });

    expect(result.current.notifications[0].read).toBe(true);
    expect(result.current.unreadCount).toBe(0);
  });

  it('should mark all notifications as read', () => {
    const { result } = renderHook(() => useNotifications());

    // Add multiple notifications
    act(() => {
      result.current.addNotification({
        type: 'info',
        message: 'Notification 1',
        timestamp: new Date().toISOString()
      });
      result.current.addNotification({
        type: 'warning',
        message: 'Notification 2',
        timestamp: new Date().toISOString()
      });
    });

    expect(result.current.unreadCount).toBe(2);

    // Mark all as read
    act(() => {
      result.current.markAllAsRead();
    });

    expect(result.current.unreadCount).toBe(0);
    result.current.notifications.forEach(notification => {
      expect(notification.read).toBe(true);
    });
  });

  it('should remove notification', () => {
    const { result } = renderHook(() => useNotifications());

    // Add a notification
    act(() => {
      result.current.addNotification({
        type: 'info',
        message: 'Test notification',
        timestamp: new Date().toISOString()
      });
    });

    const notificationId = result.current.notifications[0].id;
    expect(result.current.notifications).toHaveLength(1);
    expect(result.current.unreadCount).toBe(1);

    // Remove notification
    act(() => {
      result.current.removeNotification(notificationId);
    });

    expect(result.current.notifications).toHaveLength(0);
    expect(result.current.unreadCount).toBe(0);
  });

  it('should clear all notifications', () => {
    const { result } = renderHook(() => useNotifications());

    // Add multiple notifications
    act(() => {
      result.current.addNotification({
        type: 'info',
        message: 'Notification 1',
        timestamp: new Date().toISOString()
      });
      result.current.addNotification({
        type: 'warning',
        message: 'Notification 2',
        timestamp: new Date().toISOString()
      });
    });

    expect(result.current.notifications).toHaveLength(2);
    expect(result.current.unreadCount).toBe(2);

    // Clear all
    act(() => {
      result.current.clearAll();
    });

    expect(result.current.notifications).toHaveLength(0);
    expect(result.current.unreadCount).toBe(0);
  });

  it('should limit notifications to 50', () => {
    const { result } = renderHook(() => useNotifications());

    // Add 52 notifications
    act(() => {
      for (let i = 0; i < 52; i++) {
        result.current.addNotification({
          type: 'info',
          message: `Notification ${i}`,
          timestamp: new Date().toISOString()
        });
      }
    });

    // Should only keep the latest 50
    expect(result.current.notifications).toHaveLength(50);
    expect(result.current.notifications[0].message).toBe('Notification 51'); // Latest first
  });

  it('should disconnect when user becomes unavailable', () => {
    const { rerender } = renderHook(() => useNotifications());

    // Simulate user logout by mocking useAuth to return null user
    vi.doMock('../../../hooks/useAuth', () => ({
      useAuth: () => ({
        user: null
      })
    }));

    rerender();

    expect(mockNotificationService.disconnect).toHaveBeenCalled();
  });

  it('should update connection state periodically', async () => {
    const { result } = renderHook(() => useNotifications());

    // Mock connection state changes
    mockNotificationService.getConnectionState
      .mockReturnValueOnce('connected')
      .mockReturnValueOnce('disconnected');

    mockNotificationService.isConnected
      .mockReturnValueOnce(true)
      .mockReturnValueOnce(false);

    // Wait for the interval to run
    await act(async () => {
      await new Promise(resolve => setTimeout(resolve, 1100)); // Wait for interval
    });

    expect(mockNotificationService.getConnectionState).toHaveBeenCalled();
  });

  it('should handle WebSocket event listeners', () => {
    renderHook(() => useNotifications());

    // Verify event listeners are registered
    expect(mockNotificationService.on).toHaveBeenCalledWith('connected', expect.any(Function));
    expect(mockNotificationService.on).toHaveBeenCalledWith('disconnected', expect.any(Function));
    expect(mockNotificationService.on).toHaveBeenCalledWith('error', expect.any(Function));
    expect(mockNotificationService.on).toHaveBeenCalledWith('notification', expect.any(Function));
  });

  it('should not add connection/pong messages to notification list', () => {
    const { result } = renderHook(() => useNotifications());

    // Simulate receiving a connection message
    act(() => {
      result.current.addNotification({
        type: 'connection',
        message: 'Connected to notifications',
        timestamp: new Date().toISOString()
      });
    });

    // Should not be added to notifications list based on the hook logic
    expect(result.current.notifications).toHaveLength(0);
    expect(result.current.unreadCount).toBe(0);
  });

  it('should properly handle different notification types', () => {
    const { result } = renderHook(() => useNotifications());

    const notificationTypes = [
      { type: 'order_update', priority: 'high' },
      { type: 'low_stock', priority: 'medium' },
      { type: 'new_order', priority: 'high' },
      { type: 'info', priority: 'low' }
    ];

    act(() => {
      notificationTypes.forEach((notif, index) => {
        result.current.addNotification({
          type: notif.type,
          message: `Test notification ${index}`,
          timestamp: new Date().toISOString(),
          priority: notif.priority
        });
      });
    });

    expect(result.current.notifications).toHaveLength(4);
    expect(result.current.unreadCount).toBe(4);

    // Check that priorities are preserved
    result.current.notifications.forEach((notification, index) => {
      expect(notification.priority).toBe(notificationTypes[3 - index].priority); // Reverse order (latest first)
    });
  });
});