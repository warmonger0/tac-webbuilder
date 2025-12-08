# WebSocket Broadcasting Template

## Quick Reference

Copy-paste templates for adding WebSocket broadcasting logic. Use these when implementing Phase 2 of the WebSocket implementation checklist.

---

## Template 1: Background Polling Broadcast

Use this for data that changes periodically and needs polling.

**When to use:**
- System status
- Configuration that changes occasionally
- Aggregated statistics
- Any data without specific change events

### Backend Code

```python
# Location: app/server/services/background_tasks.py

class BackgroundTasks:
    def __init__(self, websocket_manager):
        self.websocket_manager = websocket_manager
        # Add state tracking variable
        self.last_FEATURE_state = None  # Replace FEATURE with your feature name

    async def _broadcast_FEATURE_updates(self):  # Replace FEATURE
        """
        Broadcast FEATURE updates to WebSocket clients.

        Frequency: Every N seconds (if state changed)
        Trigger: Background polling
        Message type: FEATURE_update
        """
        while True:
            try:
                # 1. Fetch current state
                current_state = get_FEATURE_data()  # Replace with your data function

                # 2. Compare with last state (prevents unnecessary broadcasts)
                if current_state != self.last_FEATURE_state:
                    # 3. Broadcast to all clients
                    await self.websocket_manager.broadcast({
                        "type": "FEATURE_update",  # Replace FEATURE (snake_case)
                        "data": current_state
                    })

                    # 4. Update last state
                    self.last_FEATURE_state = current_state
                    logger.debug(f"[WS] Broadcast FEATURE update")

                # 5. Wait before next check
                await asyncio.sleep(5)  # Adjust interval (5-60 seconds)

            except Exception as e:
                logger.error(f"[WS] Error broadcasting FEATURE updates: {e}")
                await asyncio.sleep(5)  # Wait before retry

    async def start(self):
        """Start all background tasks"""
        # Add your task here
        asyncio.create_task(self._broadcast_FEATURE_updates())

        # Existing tasks...
        asyncio.create_task(self._broadcast_workflows())
        asyncio.create_task(self._broadcast_routes())
        # ... etc
```

### Interval Guidelines

| Interval | Use Case | Example |
|----------|----------|---------|
| 1-5s | Critical real-time data | Workflow status, queue state |
| 5-15s | Important updates | ADW monitor, system metrics |
| 15-30s | Moderate updates | System status, health checks |
| 30-60s | Slow-changing data | Configuration, statistics |

---

## Template 2: Event-Driven Broadcast

Use this for data that changes on specific events.

**When to use:**
- Phase completion/failure
- Workflow status changes
- Queue state changes
- User actions
- External webhook events

### Backend Code

```python
# Location: Wherever the event occurs (e.g., phase_coordinator.py, routes)

async def handle_FEATURE_event(self, event_data):
    """
    Handle FEATURE event and broadcast to WebSocket clients.

    Args:
        event_data: Event payload
    """
    try:
        # 1. Process the event
        result = await process_FEATURE_event(event_data)

        # 2. Broadcast immediately to all clients
        await self.websocket_manager.broadcast({
            "type": "FEATURE_update",  # Replace FEATURE (snake_case)
            "data": result
        })

        logger.info(f"[WS] Broadcast FEATURE event: {event_data}")

    except Exception as e:
        logger.error(f"[WS] Error handling FEATURE event: {e}")
        # Don't re-raise - prevent event handler from crashing
```

### Common Event Sources

#### In Service Methods
```python
class YourService:
    def __init__(self, websocket_manager):
        self.websocket_manager = websocket_manager

    async def update_something(self, item_id: str):
        # Update database
        item = self.repository.update(item_id)

        # Broadcast update
        await self.websocket_manager.broadcast({
            "type": "FEATURE_update",
            "data": item.to_dict()
        })

        return item
```

#### In API Routes
```python
@router.post("/api/v1/your-endpoint")
async def create_item(data: dict):
    # Create item
    item = service.create(data)

    # Broadcast to WebSocket clients
    await websocket_manager.broadcast({
        "type": "FEATURE_update",
        "data": item
    })

    return item
```

#### In Webhook Handlers
```python
@router.post("/webhook")
async def handle_github_webhook(payload: dict):
    # Process webhook
    result = await process_webhook(payload)

    # Broadcast immediately
    await websocket_manager.broadcast({
        "type": "FEATURE_update",
        "data": result
    })

    return {"status": "ok"}
```

---

## Template 3: Hybrid (Polling + Events)

Use this for critical data that needs both immediate updates AND periodic verification.

**When to use:**
- Phase queue (events can be missed)
- Critical workflows (backup polling)
- High-reliability requirements

### Backend Code

```python
# Combine both templates above

class BackgroundTasks:
    def __init__(self, websocket_manager):
        self.websocket_manager = websocket_manager
        self.last_FEATURE_state = None

    # Periodic backup polling
    async def _broadcast_FEATURE_updates(self):
        """Background polling as backup (every 5-10s)"""
        while True:
            try:
                current_state = get_FEATURE_data()
                if current_state != self.last_FEATURE_state:
                    await self.websocket_manager.broadcast({
                        "type": "FEATURE_update",
                        "data": current_state
                    })
                    self.last_FEATURE_state = current_state
                    logger.debug(f"[WS] Broadcast FEATURE update (polling)")
                await asyncio.sleep(5)
            except Exception as e:
                logger.error(f"[WS] Error broadcasting FEATURE: {e}")
                await asyncio.sleep(5)

# Event handler for immediate updates
async def on_FEATURE_event(self, event_data):
    """Immediate broadcast on event"""
    await self.websocket_manager.broadcast({
        "type": "FEATURE_update",
        "data": event_data
    })
    logger.info(f"[WS] Broadcast FEATURE event (immediate)")
```

**Result:** Updates within <1s on events, with 5-10s backup polling if event is missed.

---

## Template 4: Conditional Broadcasting

Use this to reduce unnecessary broadcasts based on conditions.

**When to use:**
- High-frequency data
- Large payloads
- Rate-limited APIs

### Backend Code

```python
async def _broadcast_FEATURE_updates(self):
    """Broadcast with conditions"""
    while True:
        try:
            current_state = get_FEATURE_data()

            # Condition 1: Only broadcast if changed
            if current_state == self.last_FEATURE_state:
                await asyncio.sleep(5)
                continue

            # Condition 2: Only broadcast if clients connected
            if not self.websocket_manager.active_connections:
                logger.debug("[WS] No clients connected, skipping broadcast")
                await asyncio.sleep(5)
                continue

            # Condition 3: Only broadcast significant changes
            if not self._is_significant_change(current_state, self.last_FEATURE_state):
                await asyncio.sleep(5)
                continue

            # All conditions passed - broadcast
            await self.websocket_manager.broadcast({
                "type": "FEATURE_update",
                "data": current_state
            })

            self.last_FEATURE_state = current_state
            logger.debug(f"[WS] Broadcast FEATURE update")
            await asyncio.sleep(5)

        except Exception as e:
            logger.error(f"[WS] Error broadcasting FEATURE: {e}")
            await asyncio.sleep(5)

    def _is_significant_change(self, new_state, old_state):
        """Check if change is worth broadcasting"""
        # Example: Only broadcast if count changed by >10%
        if old_state is None:
            return True
        old_count = old_state.get('count', 0)
        new_count = new_state.get('count', 0)
        return abs(new_count - old_count) / max(old_count, 1) > 0.1
```

---

## Testing Your Broadcasting

### 1. Check Broadcast is Called

```bash
# Watch backend logs
tail -f logs/backend.log | grep "Broadcast FEATURE"

# Expected output:
[WS] Broadcast FEATURE update
[WS] Broadcast FEATURE update
```

### 2. Check Clients Receive Updates

```javascript
// Browser console
// Should see:
[WS] Received FEATURE update
[WS] Received FEATURE update
```

### 3. Verify Multiple Clients

1. Open app in 2+ browser tabs
2. Trigger update
3. All tabs should update simultaneously

### 4. Verify No HTTP Polling

```bash
# Browser DevTools → Network tab → Filter by "Fetch/XHR"
# Should see: ZERO requests to /api/v1/FEATURE
```

---

## Common Mistakes

### ❌ Mistake 1: Forgot to Call broadcast()
```python
async def _broadcast_FEATURE_updates(self):
    current_state = get_FEATURE_data()
    # Missing: await self.websocket_manager.broadcast(...)
    await asyncio.sleep(5)
```
**Fix:** Always call `broadcast()` in your loop.

### ❌ Mistake 2: Not Handling Exceptions
```python
async def _broadcast_FEATURE_updates(self):
    while True:
        current_state = get_FEATURE_data()  # Might throw exception
        # If exception, loop exits forever
```
**Fix:** Wrap in try-except.

### ❌ Mistake 3: Broadcasting Too Frequently
```python
async def _broadcast_FEATURE_updates(self):
    while True:
        await self.websocket_manager.broadcast(...)
        await asyncio.sleep(0.1)  # ❌ Every 100ms is too fast!
```
**Fix:** Use 5-60 second intervals.

### ❌ Mistake 4: Not Comparing State
```python
async def _broadcast_FEATURE_updates(self):
    while True:
        current_state = get_FEATURE_data()
        # Missing: if current_state != self.last_FEATURE_state
        await self.websocket_manager.broadcast(...)  # Broadcasts even if unchanged
```
**Fix:** Always compare with last state before broadcasting.

### ❌ Mistake 5: Forgot to Add Task to start()
```python
async def _broadcast_FEATURE_updates(self):
    # Function defined ✅
    while True:
        await self.websocket_manager.broadcast(...)

async def start(self):
    asyncio.create_task(self._broadcast_workflows())
    # Missing: asyncio.create_task(self._broadcast_FEATURE_updates()) ❌
```
**Fix:** Add task in `start()` method.

---

## Quick Checklist

Before committing broadcasting code:

- ☐ Function defined (`_broadcast_FEATURE_updates`)
- ☐ Added to `start()` method
- ☐ Has try-except error handling
- ☐ Compares state before broadcasting
- ☐ Uses reasonable interval (5-60s)
- ☐ Logs broadcasts (`logger.debug`)
- ☐ Tested with backend logs (see broadcast messages)
- ☐ Tested with frontend (see updates)
- ☐ Tested with Network tab (no HTTP polling)

---

## Real Examples

### Example 1: ADW Monitor (Background Polling)
**File:** `app/server/services/background_tasks.py`
**Pattern:** Background polling every 5 seconds

```python
async def _broadcast_adw_monitor_updates(self):
    """Broadcast ADW monitor updates"""
    while True:
        try:
            from core.adw_monitor import aggregate_adw_monitor_data
            current_data = aggregate_adw_monitor_data()
            current_state = json.dumps(current_data, sort_keys=True)

            if current_state != self.last_adw_monitor_state:
                await self.websocket_manager.broadcast({
                    "type": "adw_monitor_update",
                    "data": current_data
                })
                self.last_adw_monitor_state = current_state
                logger.debug("[WS] Broadcast ADW monitor update")

            await asyncio.sleep(5)
        except Exception as e:
            logger.error(f"[WS] Error broadcasting ADW monitor: {e}")
            await asyncio.sleep(5)
```

### Example 2: Phase Queue (Event-Driven)
**File:** `app/server/services/phase_coordination/phase_coordinator.py`
**Pattern:** Immediate broadcast on phase events

```python
async def _on_phase_complete(self, queue_id: str):
    """Handle phase completion and broadcast"""
    try:
        # Update state
        phase = self.phase_queue_service.get_by_id(queue_id)
        phase.status = 'completed'
        self.phase_queue_service.update(phase)

        # Broadcast immediately
        event = {
            "type": "queue_update",
            "queue_id": queue_id,
            "status": "completed",
            "parent_issue": phase.parent_issue
        }
        await self.websocket_manager.broadcast(event)
        logger.info(f"[WS] Broadcast phase complete: {queue_id}")

    except Exception as e:
        logger.error(f"[WS] Error in phase completion: {e}")
```

---

## Summary

**Key Points:**
1. **Always add broadcasting logic** when creating WebSocket endpoints
2. **Choose the right pattern** (polling, events, or hybrid)
3. **Compare state** before broadcasting (avoid redundant updates)
4. **Handle exceptions** to prevent task crashes
5. **Test thoroughly** (logs, frontend, Network tab)

**Remember:** A WebSocket endpoint without broadcasting is like a radio station that never transmits - the connection exists but nothing happens.
