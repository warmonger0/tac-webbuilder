"""
WebSocket endpoints for real-time updates.
"""
import asyncio
import json
import logging

from core.data_models import WorkflowHistoryFilters
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from starlette.websockets import WebSocketState

logger = logging.getLogger(__name__)

# Router will be created with dependencies injected from server.py
router = APIRouter(prefix="", tags=["WebSockets"])


async def _handle_websocket_connection(websocket: WebSocket, manager, initial_data: dict, error_context: str):
    """
    Handle common websocket connection pattern: connect, send initial data, keep alive, disconnect.

    CRITICAL FIX: This implementation uses non-blocking asyncio.sleep() instead of blocking
    on receive_text(). The client is a passive listener that never sends messages (except
    for optional ping/pong), so blocking on receive_text() causes connections to timeout.

    Args:
        websocket: WebSocket connection
        manager: WebSocket connection manager
        initial_data: Initial data to send to client
        error_context: Context string for error logging
    """
    await manager.connect(websocket)

    try:
        # OPTIONAL: Wait for client_ready signal with timeout
        # This prevents race condition where client isn't ready to receive data
        try:
            ready_msg = await asyncio.wait_for(websocket.receive_text(), timeout=2.0)
            client_msg = json.loads(ready_msg)

            if client_msg.get('type') != 'client_ready':
                logger.debug(f"[WS] {error_context}: Received {client_msg.get('type')} instead of client_ready, continuing anyway")
        except asyncio.TimeoutError:
            # Client didn't send ready signal - that's OK, proceed anyway for backwards compatibility
            logger.debug(f"[WS] {error_context}: No client_ready signal within 2s, proceeding with initial data send")
        except json.JSONDecodeError:
            logger.debug(f"[WS] {error_context}: Invalid JSON in client message, proceeding anyway")

        # Send initial data
        await websocket.send_json(initial_data)
        logger.debug(f"[WS] {error_context}: Sent initial data to client")

        # CRITICAL FIX: Non-blocking keep-alive loop
        # Instead of blocking on receive_text(), we use asyncio.sleep() to yield control
        # This allows the connection to stay open while remaining responsive to:
        # 1. Background task broadcasts (via manager.broadcast())
        # 2. Client disconnections
        # 3. Optional ping/pong messages
        while True:
            # Check if connection is still open
            if websocket.client_state != WebSocketState.CONNECTED:
                logger.debug(f"[WS] {error_context}: Connection no longer in CONNECTED state, exiting")
                break

            # Try to receive messages with timeout (non-blocking)
            try:
                # Wait up to 1 second for a message, then loop again
                msg_text = await asyncio.wait_for(websocket.receive_text(), timeout=1.0)

                # Parse and handle the message
                try:
                    msg = json.loads(msg_text)
                    msg_type = msg.get('type')

                    if msg_type == 'ping':
                        # Respond to ping with pong
                        await websocket.send_json({
                            'type': 'pong',
                            'timestamp': msg.get('timestamp', None)
                        })
                        logger.debug(f"[WS] {error_context}: Responded to ping with pong")
                    elif msg_type == 'client_ready':
                        # Client ready signal (can be sent multiple times, ignore)
                        logger.debug(f"[WS] {error_context}: Received client_ready signal")
                    else:
                        # Unknown message type, log but don't crash
                        logger.debug(f"[WS] {error_context}: Received unknown message type: {msg_type}")

                except json.JSONDecodeError as e:
                    logger.warning(f"[WS] {error_context}: Failed to parse JSON message: {e}")

            except asyncio.TimeoutError:
                # No message received in 1s - that's expected and normal
                # Connection is still alive, just waiting for broadcasts from background tasks
                pass
            except WebSocketDisconnect:
                # Client disconnected normally
                logger.debug(f"[WS] {error_context}: Client disconnected")
                break

    except WebSocketDisconnect:
        # Client disconnected (can happen at any point)
        logger.debug(f"[WS] {error_context}: WebSocket disconnected")
    except Exception as e:
        logger.error(f"[WS] Error in {error_context} WebSocket connection: {e}", exc_info=True)
    finally:
        manager.disconnect(websocket)
        logger.debug(f"[WS] {error_context}: Connection cleaned up")


def init_websocket_routes(manager, get_workflows_data_func, get_routes_data_func, get_workflow_history_data_func, get_adw_state_func, get_adw_monitor_data_func, get_queue_data_func, get_system_status_data_func, get_webhook_status_data_func, get_planned_features_data_func):
    """
    Initialize WebSocket routes with service dependencies.

    This function is called from server.py to inject service dependencies.
    """

    @router.websocket("/ws/workflows")
    async def websocket_workflows(websocket: WebSocket) -> None:
        """WebSocket endpoint for real-time workflow updates"""
        workflows = get_workflows_data_func()
        initial_data = {
            "type": "workflows_update",
            "data": [w.model_dump() for w in workflows]
        }
        await _handle_websocket_connection(websocket, manager, initial_data, "workflows")

    @router.websocket("/ws/routes")
    async def websocket_routes(websocket: WebSocket) -> None:
        """WebSocket endpoint for real-time route updates"""
        routes = get_routes_data_func()
        initial_data = {
            "type": "routes_update",
            "data": [r.model_dump() for r in routes]
        }
        await _handle_websocket_connection(websocket, manager, initial_data, "routes")

    @router.websocket("/ws/workflow-history")
    async def websocket_workflow_history(websocket: WebSocket) -> None:
        """WebSocket endpoint for real-time workflow history updates"""
        # Send initial data (ignore did_sync flag for initial connection)
        history_data, _ = get_workflow_history_data_func(WorkflowHistoryFilters(limit=50, offset=0))
        initial_data = {
            "type": "workflow_history_update",
            "data": {
                "workflows": [w.model_dump() for w in history_data.workflows],
                "total_count": history_data.total_count,
                "analytics": history_data.analytics.model_dump()
            }
        }
        await _handle_websocket_connection(websocket, manager, initial_data, "workflow history")

    @router.websocket("/ws/adw-state/{adw_id}")
    async def websocket_adw_state(websocket: WebSocket, adw_id: str) -> None:
        """WebSocket endpoint for real-time ADW workflow state updates"""
        state_data = get_adw_state_func(adw_id)
        initial_data = {
            "type": "adw_state_update",
            "adw_id": adw_id,
            "data": state_data
        }
        await _handle_websocket_connection(websocket, manager, initial_data, "ADW state")

    @router.websocket("/ws/adw-monitor")
    async def websocket_adw_monitor(websocket: WebSocket) -> None:
        """WebSocket endpoint for real-time ADW monitor updates"""
        monitor_data = get_adw_monitor_data_func()
        initial_data = {
            "type": "adw_monitor_update",
            "data": monitor_data
        }
        await _handle_websocket_connection(websocket, manager, initial_data, "ADW monitor")

    @router.websocket("/ws/queue")
    async def websocket_queue(websocket: WebSocket) -> None:
        """WebSocket endpoint for real-time queue updates"""
        queue_data = get_queue_data_func()
        initial_data = {
            "type": "queue_update",
            "data": queue_data
        }
        await _handle_websocket_connection(websocket, manager, initial_data, "queue")

    @router.websocket("/ws/system-status")
    async def websocket_system_status(websocket: WebSocket) -> None:
        """WebSocket endpoint for real-time system status updates"""
        system_status_data = await get_system_status_data_func()
        initial_data = {
            "type": "system_status_update",
            "data": system_status_data
        }
        await _handle_websocket_connection(websocket, manager, initial_data, "system status")

    @router.websocket("/ws/webhook-status")
    async def websocket_webhook_status(websocket: WebSocket) -> None:
        """WebSocket endpoint for real-time webhook status updates"""
        webhook_status_data = get_webhook_status_data_func()
        initial_data = {
            "type": "webhook_status_update",
            "data": webhook_status_data
        }
        await _handle_websocket_connection(websocket, manager, initial_data, "webhook status")

    @router.websocket("/ws/planned-features")
    async def websocket_planned_features(websocket: WebSocket) -> None:
        """WebSocket endpoint for real-time planned features updates"""
        planned_features_data = get_planned_features_data_func()
        initial_data = {
            "type": "planned_features_update",
            "data": planned_features_data
        }
        await _handle_websocket_connection(websocket, manager, initial_data, "planned features")
