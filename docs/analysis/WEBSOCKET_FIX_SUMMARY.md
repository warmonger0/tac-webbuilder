# WebSocket Disconnection Fix - Quick Reference

## Problem in One Sentence

Server blocks indefinitely waiting for client messages that never arrive, causing WebSocket timeout and abnormal closure (code 1006).

---

## The Issue

### Current Code (Broken)
```python
# File: app/server/routes/websocket_routes.py:32-36

while True:
    try:
        await websocket.receive_text()  # ⚠️ BLOCKS FOREVER
    except WebSocketDisconnect:
        break
```

**Problem:**
- Waits for client to send a message
- Client never sends messages (passive listener)
- Connection times out → code 1006
- Affects all 8 WebSocket endpoints

---

## The Fix

### Replace With (Working)
```python
# File: app/server/routes/websocket_routes.py:32-36

while True:
    try:
        await asyncio.sleep(1)  # ✓ NON-BLOCKING

        # Optional: Check if still connected
        if websocket.client_state != WebSocketState.CONNECTED:
            break

    except WebSocketDisconnect:
        break
```

**Why This Works:**
- `asyncio.sleep()` yields control to event loop
- Allows broadcast messages to be sent
- Connection stays alive
- No blocking on client messages

---

## Required Imports

Add these to top of `websocket_routes.py`:

```python
import asyncio
from starlette.websockets import WebSocketState
```

---

## Complete Fixed Function

```python
async def _handle_websocket_connection(
    websocket: WebSocket,
    manager,
    initial_data: dict,
    error_context: str
):
    """
    Handle common websocket connection pattern: connect, send initial data, keep alive, disconnect.
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
                # This allows broadcast messages to be sent
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

---

## Testing Checklist

### Before Fix
- [ ] WebSocket connects then immediately disconnects (code 1006)
- [ ] Console shows continuous reconnection attempts
- [ ] Real-time updates don't work
- [ ] Network tab shows constant WS errors

### After Fix
- [ ] WebSocket stays connected (no disconnections)
- [ ] No code 1006 errors
- [ ] No reconnection attempts
- [ ] Real-time updates work within 2 seconds
- [ ] Connection stable for 5+ minutes
- [ ] All 8 endpoints working (test each panel)

---

## Affected Endpoints

All 8 endpoints use the same `_handle_websocket_connection` function:

1. `/api/v1/ws/queue` - Queue updates
2. `/api/v1/ws/adw-monitor` - ADW monitoring
3. `/api/v1/ws/system-status` - System status
4. `/api/v1/ws/workflows` - Workflow list
5. `/api/v1/ws/routes` - Route list
6. `/api/v1/ws/workflow-history` - History
7. `/api/v1/ws/planned-features` - Features
8. `/api/v1/ws/webhook-status` - Webhook status

**One fix solves all 8 endpoints.**

---

## File to Edit

```
app/server/routes/websocket_routes.py
```

**Lines:** 15-42 (the `_handle_websocket_connection` function)

---

## Impact

### Before
- 8 endpoints × 10 retries = 80 connection attempts per session
- No real-time updates
- Stale data until page refresh
- High server load from reconnections
- Poor user experience

### After
- Stable persistent connections
- Real-time updates working
- Clean disconnects (code 1000)
- Minimal server load
- Excellent user experience

---

## Deployment

1. Edit `app/server/routes/websocket_routes.py`
2. Apply the fix to `_handle_websocket_connection`
3. Restart backend server
4. Test in browser (Network → WS tab)
5. Verify all 8 endpoints stay connected
6. Verify real-time updates work

**No client-side changes needed.**

---

## Time Estimate

- **Fix:** 5 minutes
- **Test:** 10 minutes
- **Total:** 15 minutes
