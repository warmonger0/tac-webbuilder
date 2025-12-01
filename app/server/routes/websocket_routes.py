"""
WebSocket endpoints for real-time updates.
"""
import logging

from core.data_models import WorkflowHistoryFilters
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

logger = logging.getLogger(__name__)

# Router will be created with dependencies injected from server.py
router = APIRouter(prefix="", tags=["WebSockets"])


async def _handle_websocket_connection(websocket: WebSocket, manager, initial_data: dict, error_context: str):
    """
    Handle common websocket connection pattern: connect, send initial data, keep alive, disconnect.

    Args:
        websocket: WebSocket connection
        manager: WebSocket connection manager
        initial_data: Initial data to send to client
        error_context: Context string for error logging
    """
    await manager.connect(websocket)

    try:
        # Send initial data
        await websocket.send_json(initial_data)

        # Keep connection alive and handle incoming messages
        while True:
            try:
                # Wait for any client messages (ping/pong, etc.)
                await websocket.receive_text()
            except WebSocketDisconnect:
                break
    except Exception as e:
        logger.error(f"[WS] Error in {error_context} WebSocket connection: {e}")
    finally:
        manager.disconnect(websocket)


def init_websocket_routes(manager, get_workflows_data_func, get_routes_data_func, get_workflow_history_data_func, get_adw_state_func):
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
