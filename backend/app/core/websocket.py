from typing import Dict, List
from fastapi import WebSocket, WebSocketDisconnect
import json
import logging

logger = logging.getLogger(__name__)


class ConnectionManager:
    def __init__(self):
        # Store active connections by user_id
        self.active_connections: Dict[str, WebSocket] = {}
        # Store connections by role for broadcasting
        self.role_connections: Dict[str, List[str]] = {}

    async def connect(self, websocket: WebSocket, user_id: str, role: str = "user"):
        """Accept and store WebSocket connection"""
        await websocket.accept()
        
        # Close existing connection for same user
        if user_id in self.active_connections:
            try:
                await self.active_connections[user_id].close()
            except:
                pass
        
        self.active_connections[user_id] = websocket
        
        # Add to role group
        if role not in self.role_connections:
            self.role_connections[role] = []
        if user_id not in self.role_connections[role]:
            self.role_connections[role].append(user_id)
        
        logger.info(f"User {user_id} connected with role {role}")

    def disconnect(self, user_id: str):
        """Remove WebSocket connection"""
        if user_id in self.active_connections:
            del self.active_connections[user_id]
        
        # Remove from all role groups
        for role, users in self.role_connections.items():
            if user_id in users:
                users.remove(user_id)
        
        logger.info(f"User {user_id} disconnected")

    async def send_personal_message(self, message: str, user_id: str, notification_type: str = "info"):
        """Send message to specific user"""
        if user_id in self.active_connections:
            websocket = self.active_connections[user_id]
            try:
                await websocket.send_text(json.dumps({
                    "type": notification_type,
                    "message": message,
                    "timestamp": self._get_timestamp(),
                    "user_id": user_id
                }))
            except WebSocketDisconnect:
                self.disconnect(user_id)
            except Exception as e:
                logger.error(f"Error sending message to user {user_id}: {e}")
                self.disconnect(user_id)

    async def broadcast_to_role(self, message: str, role: str, notification_type: str = "info"):
        """Send message to all users with specific role"""
        if role not in self.role_connections:
            return
        
        disconnected_users = []
        for user_id in self.role_connections[role]:
            if user_id in self.active_connections:
                websocket = self.active_connections[user_id]
                try:
                    await websocket.send_text(json.dumps({
                        "type": notification_type,
                        "message": message,
                        "timestamp": self._get_timestamp(),
                        "role": role
                    }))
                except WebSocketDisconnect:
                    disconnected_users.append(user_id)
                except Exception as e:
                    logger.error(f"Error broadcasting to user {user_id}: {e}")
                    disconnected_users.append(user_id)
        
        # Clean up disconnected users
        for user_id in disconnected_users:
            self.disconnect(user_id)

    async def broadcast_to_all(self, message: str, notification_type: str = "info"):
        """Send message to all connected users"""
        disconnected_users = []
        for user_id, websocket in self.active_connections.items():
            try:
                await websocket.send_text(json.dumps({
                    "type": notification_type,
                    "message": message,
                    "timestamp": self._get_timestamp()
                }))
            except WebSocketDisconnect:
                disconnected_users.append(user_id)
            except Exception as e:
                logger.error(f"Error broadcasting to user {user_id}: {e}")
                disconnected_users.append(user_id)
        
        # Clean up disconnected users
        for user_id in disconnected_users:
            self.disconnect(user_id)

    def get_active_connections_count(self) -> int:
        """Get count of active connections"""
        return len(self.active_connections)

    def get_role_connections_count(self, role: str) -> int:
        """Get count of connections for specific role"""
        return len(self.role_connections.get(role, []))

    def _get_timestamp(self) -> str:
        """Get current timestamp in ISO format"""
        from datetime import datetime
        return datetime.utcnow().isoformat()


# Global connection manager instance
manager = ConnectionManager()