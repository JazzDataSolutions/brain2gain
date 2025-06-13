class NotificationService {
  private ws: WebSocket | null = null;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectInterval = 1000;
  private listeners: Map<string, Function[]> = new Map();
  private userId: string | null = null;
  private userRole: string = 'user';

  constructor() {
    this.setupEventListeners();
  }

  connect(userId: string, role: string = 'user') {
    this.userId = userId;
    this.userRole = role;
    
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.disconnect();
    }

    const wsUrl = `ws://localhost:8000/api/v1/ws/notifications/${userId}`;
    console.log('Connecting to WebSocket:', wsUrl);
    
    this.ws = new WebSocket(wsUrl);
    
    this.ws.onopen = () => {
      console.log('WebSocket connected');
      this.reconnectAttempts = 0;
      
      // Update role if not default
      if (role !== 'user') {
        this.updateRole(role);
      }
      
      this.emit('connected', { userId, role });
    };
    
    this.ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        console.log('WebSocket message received:', data);
        
        // Emit specific event type
        this.emit(data.type || 'message', data);
        
        // Emit general notification event
        this.emit('notification', data);
        
        // Show browser notification if supported
        this.showBrowserNotification(data);
        
      } catch (error) {
        console.error('Error parsing WebSocket message:', error);
      }
    };
    
    this.ws.onclose = (event) => {
      console.log('WebSocket disconnected:', event.code, event.reason);
      this.emit('disconnected', { code: event.code, reason: event.reason });
      
      // Attempt to reconnect
      if (this.reconnectAttempts < this.maxReconnectAttempts) {
        setTimeout(() => {
          this.reconnectAttempts++;
          console.log(`Reconnecting attempt ${this.reconnectAttempts}...`);
          this.connect(userId, role);
        }, this.reconnectInterval * Math.pow(2, this.reconnectAttempts));
      }
    };
    
    this.ws.onerror = (error) => {
      console.error('WebSocket error:', error);
      this.emit('error', error);
    };
  }

  disconnect() {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }

  updateRole(role: string) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.userRole = role;
      this.send({
        type: 'role_update',
        role: role
      });
    }
  }

  send(data: any) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(data));
    }
  }

  ping() {
    this.send({ type: 'ping' });
  }

  // Event listener management
  on(event: string, callback: Function) {
    if (!this.listeners.has(event)) {
      this.listeners.set(event, []);
    }
    this.listeners.get(event)!.push(callback);
  }

  off(event: string, callback: Function) {
    const callbacks = this.listeners.get(event);
    if (callbacks) {
      const index = callbacks.indexOf(callback);
      if (index > -1) {
        callbacks.splice(index, 1);
      }
    }
  }

  private emit(event: string, data: any) {
    const callbacks = this.listeners.get(event);
    if (callbacks) {
      callbacks.forEach(callback => {
        try {
          callback(data);
        } catch (error) {
          console.error('Error in notification callback:', error);
        }
      });
    }
  }

  private setupEventListeners() {
    // Keep connection alive with periodic ping
    setInterval(() => {
      if (this.ws && this.ws.readyState === WebSocket.OPEN) {
        this.ping();
      }
    }, 30000); // Ping every 30 seconds
  }

  private async showBrowserNotification(data: any) {
    // Request notification permission if not granted
    if (Notification.permission === 'default') {
      await Notification.requestPermission();
    }

    // Show notification if permission granted
    if (Notification.permission === 'granted') {
      const notificationTypes = {
        'order_update': '🛍️',
        'low_stock': '⚠️',
        'new_order': '🛒',
        'connection': '🔗',
        'test': '🧪'
      };

      const icon = notificationTypes[data.type as keyof typeof notificationTypes] || '🔔';
      
      new Notification(`${icon} Brain2Gain`, {
        body: data.message,
        icon: '/assets/images/favicon.png',
        tag: data.type,
        requireInteraction: data.type === 'low_stock' || data.type === 'new_order'
      });
    }
  }

  // Utility methods for checking connection status
  isConnected(): boolean {
    return this.ws?.readyState === WebSocket.OPEN;
  }

  getConnectionState(): string {
    if (!this.ws) return 'disconnected';
    
    switch (this.ws.readyState) {
      case WebSocket.CONNECTING: return 'connecting';
      case WebSocket.OPEN: return 'connected';
      case WebSocket.CLOSING: return 'closing';
      case WebSocket.CLOSED: return 'disconnected';
      default: return 'unknown';
    }
  }

  getUserInfo() {
    return {
      userId: this.userId,
      role: this.userRole,
      connected: this.isConnected(),
      state: this.getConnectionState()
    };
  }
}

// Export singleton instance
export const notificationService = new NotificationService();
export default notificationService;