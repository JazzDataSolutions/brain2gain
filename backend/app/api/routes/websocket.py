import json
import logging

from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect

from app.core.websocket import manager

logger = logging.getLogger(__name__)
router = APIRouter()


@router.websocket("/notifications/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    """WebSocket endpoint for real-time notifications"""
    try:
        # Accept connection first
        await websocket.accept()

        # Basic authentication via query params (in production, use proper JWT validation)
        # For now, we'll accept any user_id and assume role is "user"
        # TODO: Implement proper WebSocket authentication
        role = "user"  # Default role

        # Connect to manager
        await manager.connect(websocket, user_id, role)

        # Send welcome message
        await manager.send_personal_message(
            "Conectado a notificaciones en tiempo real",
            user_id,
            "connection"
        )

        # Keep connection alive and handle incoming messages
        while True:
            try:
                # Receive message from client
                data = await websocket.receive_text()
                message_data = json.loads(data)

                # Handle different message types
                if message_data.get("type") == "ping":
                    await websocket.send_text(json.dumps({
                        "type": "pong",
                        "timestamp": manager._get_timestamp()
                    }))
                elif message_data.get("type") == "role_update":
                    # Update user role (for admin/manager connections)
                    new_role = message_data.get("role", "user")
                    if new_role in ["admin", "manager", "seller", "accountant"]:
                        manager.disconnect(user_id)
                        await manager.connect(websocket, user_id, new_role)
                        await manager.send_personal_message(
                            f"Rol actualizado a {new_role}",
                            user_id,
                            "role_update"
                        )

            except WebSocketDisconnect:
                break
            except json.JSONDecodeError:
                logger.warning(f"Invalid JSON received from user {user_id}")
            except Exception as e:
                logger.error(f"Error handling WebSocket message: {e}")
                break

    except Exception as e:
        logger.error(f"WebSocket connection error for user {user_id}: {e}")
    finally:
        manager.disconnect(user_id)


@router.get("/notifications/stats")
async def get_notification_stats():
    """Get WebSocket connection statistics"""
    return {
        "active_connections": manager.get_active_connections_count(),
        "admin_connections": manager.get_role_connections_count("admin"),
        "manager_connections": manager.get_role_connections_count("manager"),
        "user_connections": manager.get_role_connections_count("user"),
        "seller_connections": manager.get_role_connections_count("seller")
    }


@router.post("/notifications/test")
async def test_notification(message: str, target_user: str | None = None, role: str | None = None):
    """Test endpoint for sending notifications"""
    try:
        if target_user:
            await manager.send_personal_message(
                f"Test message: {message}",
                target_user,
                "test"
            )
            return {"success": True, "message": f"Test notification sent to user {target_user}"}
        elif role:
            await manager.broadcast_to_role(
                f"Test broadcast: {message}",
                role,
                "test"
            )
            return {"success": True, "message": f"Test notification broadcast to role {role}"}
        else:
            await manager.broadcast_to_all(
                f"Global test: {message}",
                "test"
            )
            return {"success": True, "message": "Test notification sent to all users"}
    except Exception as e:
        logger.error(f"Failed to send test notification: {e}")
        raise HTTPException(status_code=500, detail=str(e))
