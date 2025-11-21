"""
WebSocket endpoints for real-time updates.
"""
import logging

from core.data_models import WorkflowHistoryFilters
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

logger = logging.getLogger(__name__)

# Router will be created with dependencies injected from server.py
router = APIRouter(prefix="", tags=["WebSockets"])


def init_websocket_routes(manager, get_workflows_data_func, get_routes_data_func, get_workflow_history_data_func):
    """
    Initialize WebSocket routes with service dependencies.

    This function is called from server.py to inject service dependencies.
    """

    @router.websocket("/ws/workflows")
    async def websocket_workflows(websocket: WebSocket) -> None:
        """WebSocket endpoint for real-time workflow updates"""
        await manager.connect(websocket)

        try:
            # Send initial data
            workflows = get_workflows_data_func()
            await websocket.send_json({
                "type": "workflows_update",
                "data": [w.model_dump() for w in workflows]
            })

            # Keep connection alive and handle incoming messages
            while True:
                try:
                    # Wait for any client messages (ping/pong, etc.)
                    await websocket.receive_text()
                except WebSocketDisconnect:
                    break
        except Exception as e:
            logger.error(f"[WS] Error in WebSocket connection: {e}")
        finally:
            manager.disconnect(websocket)

    @router.websocket("/ws/routes")
    async def websocket_routes(websocket: WebSocket) -> None:
        """WebSocket endpoint for real-time route updates"""
        await manager.connect(websocket)

        try:
            # Send initial data
            routes = get_routes_data_func()
            await websocket.send_json({
                "type": "routes_update",
                "data": [r.model_dump() for r in routes]
            })

            # Keep connection alive and handle incoming messages
            while True:
                try:
                    # Wait for any client messages (ping/pong, etc.)
                    await websocket.receive_text()
                except WebSocketDisconnect:
                    break
        except Exception as e:
            logger.error(f"[WS] Error in WebSocket connection: {e}")
        finally:
            manager.disconnect(websocket)

    @router.websocket("/ws/workflow-history")
    async def websocket_workflow_history(websocket: WebSocket) -> None:
        """WebSocket endpoint for real-time workflow history updates"""
        await manager.connect(websocket)

        try:
            # Send initial data (ignore did_sync flag for initial connection)
            history_data, _ = get_workflow_history_data_func(WorkflowHistoryFilters(limit=50, offset=0))
            await websocket.send_json({
                "type": "workflow_history_update",
                "data": {
                    "workflows": [w.model_dump() for w in history_data.workflows],
                    "total_count": history_data.total_count,
                    "analytics": history_data.analytics.model_dump()
                }
            })

            # Keep connection alive and handle incoming messages
            while True:
                try:
                    # Wait for any client messages (ping/pong, etc.)
                    await websocket.receive_text()
                except WebSocketDisconnect:
                    break
        except Exception as e:
            logger.error(f"[WS] Error in workflow history WebSocket connection: {e}")
        finally:
            manager.disconnect(websocket)
