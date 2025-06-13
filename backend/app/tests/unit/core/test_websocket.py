"""
Unit tests for WebSocket ConnectionManager
"""
import pytest
from unittest.mock import AsyncMock, MagicMock
import json
from datetime import datetime

from app.core.websocket import ConnectionManager


class TestConnectionManager:
    """Test cases for WebSocket ConnectionManager"""
    
    @pytest.fixture
    def manager(self):
        """Create fresh ConnectionManager instance"""
        return ConnectionManager()
    
    @pytest.fixture
    def mock_websocket(self):
        """Mock WebSocket connection"""
        websocket = AsyncMock()
        websocket.accept = AsyncMock()
        websocket.send_text = AsyncMock()
        websocket.close = AsyncMock()
        return websocket
    
    @pytest.mark.asyncio
    async def test_connect_new_user(self, manager, mock_websocket):
        """Test connecting a new user"""
        user_id = "user123"
        role = "user"
        
        await manager.connect(mock_websocket, user_id, role)
        
        assert user_id in manager.active_connections
        assert manager.active_connections[user_id] == mock_websocket
        assert user_id in manager.role_connections[role]
        mock_websocket.accept.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_connect_existing_user_closes_old_connection(self, manager, mock_websocket):
        """Test that connecting existing user closes old connection"""
        user_id = "user123"
        old_websocket = AsyncMock()
        old_websocket.close = AsyncMock()
        
        # Add existing connection
        manager.active_connections[user_id] = old_websocket
        
        # Connect with new websocket
        await manager.connect(mock_websocket, user_id, "user")
        
        # Verify old connection was closed
        old_websocket.close.assert_called_once()
        assert manager.active_connections[user_id] == mock_websocket
    
    def test_disconnect_user(self, manager, mock_websocket):
        """Test disconnecting a user"""
        user_id = "user123"
        role = "admin"
        
        # Setup connection
        manager.active_connections[user_id] = mock_websocket
        manager.role_connections[role] = [user_id]
        
        # Disconnect
        manager.disconnect(user_id)
        
        assert user_id not in manager.active_connections
        assert user_id not in manager.role_connections[role]
    
    @pytest.mark.asyncio
    async def test_send_personal_message_success(self, manager, mock_websocket):
        """Test sending personal message successfully"""
        user_id = "user123"
        message = "Hello user!"
        
        manager.active_connections[user_id] = mock_websocket
        
        await manager.send_personal_message(message, user_id, "info")
        
        mock_websocket.send_text.assert_called_once()
        call_args = mock_websocket.send_text.call_args[0][0]
        sent_data = json.loads(call_args)
        
        assert sent_data["message"] == message
        assert sent_data["type"] == "info"
        assert sent_data["user_id"] == user_id
        assert "timestamp" in sent_data
    
    @pytest.mark.asyncio
    async def test_send_personal_message_user_not_connected(self, manager):
        """Test sending message to non-connected user"""
        user_id = "user123"
        message = "Hello user!"
        
        # Should not raise exception
        await manager.send_personal_message(message, user_id, "info")
        
        # Nothing should happen since user is not connected
        assert user_id not in manager.active_connections
    
    @pytest.mark.asyncio
    async def test_send_personal_message_websocket_error(self, manager, mock_websocket):
        """Test handling WebSocket error when sending personal message"""
        user_id = "user123"
        message = "Hello user!"
        
        manager.active_connections[user_id] = mock_websocket
        mock_websocket.send_text.side_effect = Exception("WebSocket error")
        
        await manager.send_personal_message(message, user_id, "info")
        
        # User should be disconnected on error
        assert user_id not in manager.active_connections
    
    @pytest.mark.asyncio
    async def test_broadcast_to_role(self, manager):
        """Test broadcasting message to role"""
        role = "admin"
        message = "System alert!"
        
        # Setup multiple users with same role
        websocket1 = AsyncMock()
        websocket2 = AsyncMock()
        
        manager.active_connections["admin1"] = websocket1
        manager.active_connections["admin2"] = websocket2
        manager.role_connections[role] = ["admin1", "admin2"]
        
        await manager.broadcast_to_role(message, role, "warning")
        
        # Both websockets should receive the message
        websocket1.send_text.assert_called_once()
        websocket2.send_text.assert_called_once()
        
        # Check message content
        call_args = websocket1.send_text.call_args[0][0]
        sent_data = json.loads(call_args)
        
        assert sent_data["message"] == message
        assert sent_data["type"] == "warning"
        assert sent_data["role"] == role
    
    @pytest.mark.asyncio
    async def test_broadcast_to_role_nonexistent(self, manager):
        """Test broadcasting to non-existent role"""
        role = "nonexistent"
        message = "Test message"
        
        # Should not raise exception
        await manager.broadcast_to_role(message, role, "info")
        
        # No connections should be affected
        assert len(manager.active_connections) == 0
    
    @pytest.mark.asyncio
    async def test_broadcast_to_all(self, manager):
        """Test broadcasting to all connected users"""
        message = "Global announcement"
        
        # Setup multiple users
        websocket1 = AsyncMock()
        websocket2 = AsyncMock()
        websocket3 = AsyncMock()
        
        manager.active_connections["user1"] = websocket1
        manager.active_connections["user2"] = websocket2
        manager.active_connections["user3"] = websocket3
        
        await manager.broadcast_to_all(message, "announcement")
        
        # All websockets should receive the message
        websocket1.send_text.assert_called_once()
        websocket2.send_text.assert_called_once()
        websocket3.send_text.assert_called_once()
    
    def test_get_active_connections_count(self, manager, mock_websocket):
        """Test getting active connections count"""
        assert manager.get_active_connections_count() == 0
        
        manager.active_connections["user1"] = mock_websocket
        manager.active_connections["user2"] = mock_websocket
        
        assert manager.get_active_connections_count() == 2
    
    def test_get_role_connections_count(self, manager):
        """Test getting role connections count"""
        role = "admin"
        
        assert manager.get_role_connections_count(role) == 0
        
        manager.role_connections[role] = ["admin1", "admin2", "admin3"]
        
        assert manager.get_role_connections_count(role) == 3
    
    def test_get_timestamp(self, manager):
        """Test timestamp generation"""
        timestamp = manager._get_timestamp()
        
        assert isinstance(timestamp, str)
        # Should be valid ISO format
        datetime.fromisoformat(timestamp.replace('Z', '+00:00') if timestamp.endswith('Z') else timestamp)
    
    @pytest.mark.asyncio
    async def test_multiple_roles_for_same_user(self, manager, mock_websocket):
        """Test user being added to multiple role groups"""
        user_id = "user123"
        
        # Connect as user
        await manager.connect(mock_websocket, user_id, "user")
        assert user_id in manager.role_connections["user"]
        
        # Reconnect as admin (simulate role update)
        await manager.connect(mock_websocket, user_id, "admin")
        assert user_id in manager.role_connections["admin"]
        # Should be removed from user role when disconnected and reconnected
        
        # Disconnect
        manager.disconnect(user_id)
        assert user_id not in manager.role_connections.get("user", [])
        assert user_id not in manager.role_connections.get("admin", [])