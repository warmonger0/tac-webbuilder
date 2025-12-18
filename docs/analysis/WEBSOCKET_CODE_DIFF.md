# WebSocket Fix - Exact Code Changes

## File: `app/server/routes/websocket_routes.py`

### Add Imports (Line ~4-5)

```diff
 """
 WebSocket endpoints for real-time updates.
 """
 import logging
+import asyncio

 from core.data_models import WorkflowHistoryFilters
 from fastapi import APIRouter, WebSocket, WebSocketDisconnect
+from starlette.websockets import WebSocketState

 logger = logging.getLogger(__name__)
```

### Replace Function (Lines ~15-42)

#### BEFORE (Broken)
```python
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
                await websocket.receive_text()  # ⚠️ BLOCKS FOREVER - CLIENT NEVER SENDS
            except WebSocketDisconnect:
                break
    except Exception as e:
        logger.error(f"[WS] Error in {error_context} WebSocket connection: {e}", exc_info=True)
    finally:
        manager.disconnect(websocket)
```

#### AFTER (Fixed)
```python
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

        # Keep connection alive - non-blocking
        # The manager.broadcast() method sends updates to all active connections
        while True:
            try:
                # Yield control to event loop while keeping connection alive
                # This allows broadcast messages to be sent without blocking
                await asyncio.sleep(1)  # Check every second

                # Check if connection is still alive
                if websocket.client_state != WebSocketState.CONNECTED:
                    logger.debug(f"[WS] {error_context} client disconnected")
                    break

            except WebSocketDisconnect:
                logger.debug(f"[WS] {error_context} received disconnect signal")
                break

    except Exception as e:
        logger.error(f"[WS] Error in {error_context} WebSocket connection: {e}", exc_info=True)
    finally:
        manager.disconnect(websocket)
```

### Complete Fixed File

```python
"""
WebSocket endpoints for real-time updates.
"""
import asyncio
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

        # Keep connection alive - non-blocking
        # The manager.broadcast() method sends updates to all active connections
        while True:
            try:
                # Yield control to event loop while keeping connection alive
                # This allows broadcast messages to be sent without blocking
                await asyncio.sleep(1)  # Check every second

                # Check if connection is still alive
                if websocket.client_state != WebSocketState.CONNECTED:
                    logger.debug(f"[WS] {error_context} client disconnected")
                    break

            except WebSocketDisconnect:
                logger.debug(f"[WS] {error_context} received disconnect signal")
                break

    except Exception as e:
        logger.error(f"[WS] Error in {error_context} WebSocket connection: {e}", exc_info=True)
    finally:
        manager.disconnect(websocket)


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
```

---

## Changes Summary

### Line Changes
- **Line 4:** Add `import asyncio`
- **Line 8:** Add `from starlette.websockets import WebSocketState`
- **Lines 32-36:** Replace blocking `receive_text()` loop with non-blocking `asyncio.sleep()`

### Logic Changes
1. Import `asyncio` for non-blocking sleep
2. Import `WebSocketState` to check connection status
3. Replace infinite blocking wait with periodic sleep + status check
4. Add debug logging for disconnect events

---

## Copy-Paste Ready Code

### Just the Function (Lines 15-49)

```python
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

        # Keep connection alive - non-blocking
        # The manager.broadcast() method sends updates to all active connections
        while True:
            try:
                # Yield control to event loop while keeping connection alive
                # This allows broadcast messages to be sent without blocking
                await asyncio.sleep(1)  # Check every second

                # Check if connection is still alive
                if websocket.client_state != WebSocketState.CONNECTED:
                    logger.debug(f"[WS] {error_context} client disconnected")
                    break

            except WebSocketDisconnect:
                logger.debug(f"[WS] {error_context} received disconnect signal")
                break

    except Exception as e:
        logger.error(f"[WS] Error in {error_context} WebSocket connection: {e}", exc_info=True)
    finally:
        manager.disconnect(websocket)
```

### Just the Imports (Lines 1-9)

```python
"""
WebSocket endpoints for real-time updates.
"""
import asyncio
import logging

from core.data_models import WorkflowHistoryFilters
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from starlette.websockets import WebSocketState

logger = logging.getLogger(__name__)
```

---

## Verification Steps

1. **Before editing:** Check current behavior
   ```bash
   # Terminal 1
   cd app/server && python server.py

   # Terminal 2
   cd app/client && npm run dev

   # Browser DevTools → Network → WS
   # Observe: Immediate disconnection (code 1006)
   ```

2. **Apply changes** to `app/server/routes/websocket_routes.py`

3. **After editing:** Test the fix
   ```bash
   # Restart server (Ctrl+C, then re-run)
   cd app/server && python server.py

   # Refresh browser
   # Browser DevTools → Network → WS
   # Observe: Connection stays open, no code 1006
   ```

4. **Test real-time updates:**
   - Navigate to Queue panel
   - Trigger a workflow (add item to queue)
   - Verify UI updates within 2 seconds
   - No manual refresh needed

5. **Test all endpoints:**
   - Panel 1: Workflows → `/ws/workflows`
   - Panel 2: Routes → `/ws/routes`
   - Panel 3: History → `/ws/workflow-history`
   - Panel 4: ADW Monitor → `/ws/adw-monitor`
   - Panel 5: System Status → `/ws/system-status`
   - Panel 6: Queue → `/ws/queue`
   - Panel 7: Planned Features → `/ws/planned-features`
   - Panel 8: Webhook Status → `/ws/webhook-status`

---

## Expected Results

### Before Fix
```
WebSocket ws://localhost:8002/api/v1/ws/queue
Status: 101 Switching Protocols
↓ Receiving: { "type": "queue_update", "data": {...} }
↓ Close: Code 1006 (Abnormal Closure)
Time: ~1-2 seconds
```

### After Fix
```
WebSocket ws://localhost:8002/api/v1/ws/queue
Status: 101 Switching Protocols
↓ Receiving: { "type": "queue_update", "data": {...} }
[Connection stays open]
↓ Receiving: { "type": "queue_update", "data": {...} }  [when data changes]
↓ Receiving: { "type": "queue_update", "data": {...} }  [when data changes]
[No disconnection]
Time: Persistent (hours/days)
```

---

## Rollback Plan

If issues occur, revert to original:

```python
# Original blocking version
while True:
    try:
        await websocket.receive_text()
    except WebSocketDisconnect:
        break
```

Remove new imports if needed.

---

## No Client Changes Needed

The client code is already correct - it's a passive listener that only receives messages. No changes required to:
- `GlobalWebSocketContext.tsx`
- `api.ts`
- `intervals.ts`
- Any other client files

**Server-side fix only.**
