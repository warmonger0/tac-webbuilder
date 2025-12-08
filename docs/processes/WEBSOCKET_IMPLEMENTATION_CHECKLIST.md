# WebSocket Implementation Checklist

## Purpose

This checklist ensures that ALL WebSocket endpoints are implemented correctly with proper broadcasting logic. **Following this checklist prevents the #1 WebSocket mistake: creating endpoints that connect but never update.**

## When to Use This Checklist

Use this checklist whenever you:
- Create a new WebSocket endpoint
- Add real-time functionality to a component
- Migrate from HTTP polling to WebSocket
- Debug WebSocket connection issues

## The #1 Mistake to Avoid

```
❌ WRONG: Creating WebSocket endpoint without broadcasting

Result:
1. WebSocket connects ✅
2. Sends initial data ✅
3. Sits idle forever ❌
4. Client never gets updates ❌
5. Falls back to HTTP polling ❌
```

```
✅ CORRECT: WebSocket endpoint + broadcasting logic

Result:
1. WebSocket connects ✅
2. Sends initial data ✅
3. Backend broadcasts updates ✅
4. Client receives real-time updates ✅
5. Zero HTTP polling ✅
```

---

## Implementation Checklist

### Phase 1: Backend - WebSocket Endpoint

#### ☐ 1.1 Create data function in `server.py`

```python
# Location: app/server/server.py

def get_your_feature_data() -> dict:
    """
    Get data for WebSocket broadcast.

    Returns:
        dict: Data payload for WebSocket message
    """
    # Fetch data from service/repository
    data = your_service.get_data()

    # Convert to dict if needed
    if hasattr(data, 'model_dump'):
        return data.model_dump()
    elif hasattr(data, 'to_dict'):
        return data.to_dict()
    else:
        return data
```

**Example:**
```python
def get_system_status_data() -> dict:
    from routes.system_routes import _get_system_status_handler
    status = await _get_system_status_handler(health_service)
    return status.model_dump()
```

#### ☐ 1.2 Add data function to `init_websocket_routes()` parameters

```python
# Location: app/server/server.py

websocket_routes.init_websocket_routes(
    manager,
    get_workflows_data,
    get_routes_data,
    # ... existing functions ...
    get_your_feature_data,  # ← Add your function here
)
```

#### ☐ 1.3 Create WebSocket endpoint in `websocket_routes.py`

```python
# Location: app/server/routes/websocket_routes.py

# 1. Update function signature
def init_websocket_routes(
    manager,
    # ... existing parameters ...
    get_your_feature_data_func,  # ← Add parameter
):

# 2. Add WebSocket endpoint
@router.websocket("/ws/your-feature")
async def websocket_your_feature(websocket: WebSocket) -> None:
    """WebSocket endpoint for real-time your-feature updates"""
    # Get initial data
    feature_data = get_your_feature_data_func()

    # Format as WebSocket message
    initial_data = {
        "type": "your_feature_update",  # Must match frontend expectation
        "data": feature_data
    }

    # Handle connection
    await _handle_websocket_connection(
        websocket, manager, initial_data, "your feature"
    )
```

**Naming Convention:**
- Endpoint: `/ws/your-feature` (kebab-case)
- Message type: `your_feature_update` (snake_case)
- Function name: `websocket_your_feature` (snake_case)

#### ☐ 1.4 Test endpoint manually

```bash
# Test WebSocket connection
curl -i -N \
  -H "Connection: Upgrade" \
  -H "Upgrade: websocket" \
  -H "Sec-WebSocket-Version: 13" \
  -H "Sec-WebSocket-Key: $(base64 <<< 'test')" \
  http://localhost:8002/api/v1/ws/your-feature
```

Expected result:
- `HTTP/1.1 101 Switching Protocols`
- Initial data sent as JSON

---

### Phase 2: Backend - Broadcasting Logic

**⚠️ CRITICAL:** This is where most mistakes happen. DO NOT SKIP THIS PHASE.

#### ☐ 2.1 Decide broadcasting strategy

Choose ONE of the following:

**Option A: Background Polling** (for data that changes periodically)
```python
# Example: System status, ADW monitor
# Updates every 5-30 seconds if changed
```

**Option B: Event-Driven** (for data that changes on specific events)
```python
# Example: Phase queue, workflow status
# Updates immediately when event occurs
```

**Option C: Hybrid** (both polling AND events)
```python
# Example: Queue (event-driven + 5s polling backup)
# Updates on events + periodic check
```

#### ☐ 2.2A If background polling: Add to `background_tasks.py`

```python
# Location: app/server/services/background_tasks.py

class BackgroundTasks:
    def __init__(self, websocket_manager):
        self.websocket_manager = websocket_manager
        self.last_your_feature_state = None  # Track last state

    async def _broadcast_your_feature_updates(self):
        """Broadcast your-feature updates every N seconds"""
        while True:
            try:
                # Fetch current state
                current_state = get_your_feature_data()

                # Only broadcast if changed
                if current_state != self.last_your_feature_state:
                    await self.websocket_manager.broadcast({
                        "type": "your_feature_update",
                        "data": current_state
                    })
                    self.last_your_feature_state = current_state
                    logger.debug(f"[WS] Broadcast your-feature update")

                # Wait before next check
                await asyncio.sleep(5)  # Adjust interval as needed
            except Exception as e:
                logger.error(f"[WS] Error broadcasting your-feature: {e}")
                await asyncio.sleep(5)

    async def start(self):
        """Start all background tasks"""
        asyncio.create_task(self._broadcast_workflows())
        # ... existing tasks ...
        asyncio.create_task(self._broadcast_your_feature_updates())  # ← Add task
```

**Interval guidelines:**
- Fast updates (1-5s): Critical data (workflows, queue)
- Medium updates (5-15s): Important data (system status)
- Slow updates (15-60s): Stable data (configuration)

#### ☐ 2.2B If event-driven: Add to event handlers

```python
# Location: Wherever events occur (e.g., phase_coordinator.py, routes)

async def handle_your_event(self, event_data):
    """Handle event that requires WebSocket update"""
    # Process event
    result = await process_event(event_data)

    # Broadcast immediately
    await self.websocket_manager.broadcast({
        "type": "your_feature_update",
        "data": result
    })

    logger.info(f"[WS] Broadcast your-feature event: {event_data}")
```

**Common event sources:**
- Phase completion/failure
- Workflow status changes
- Queue state changes
- Configuration updates
- External webhooks

#### ☐ 2.3 Verify broadcasting is working

```bash
# Check backend logs for broadcast messages
tail -f logs/backend.log | grep "Broadcast your-feature"
```

Expected result:
- `[WS] Broadcast your-feature update` messages appear
- Messages appear on state changes (polling) or events

---

### Phase 3: Frontend - WebSocket Hook

#### ☐ 3.1 Add WebSocket URL helper in `api.ts`

```typescript
// Location: app/client/src/config/api.ts

export const apiConfig = {
  websocket: {
    workflows: () => apiConfig.websocket.getUrl('/ws/workflows'),
    // ... existing helpers ...
    yourFeature: () => apiConfig.websocket.getUrl('/ws/your-feature'),  // ← Add
  },
}
```

#### ☐ 3.2 Create WebSocket hook in `useWebSocket.ts`

```typescript
// Location: app/client/src/hooks/useWebSocket.ts

// 1. Define message type interface
interface YourFeatureWebSocketMessage {
  type: 'your_feature_update';
  data: YourFeatureData;  // Define your data type
}

// 2. Create hook
export function useYourFeatureWebSocket() {
  const [data, setData] = useState<YourFeatureData | null>(null);

  const wsUrl = apiConfig.websocket.yourFeature();

  const connectionState = useReliableWebSocket<
    YourFeatureData,
    YourFeatureWebSocketMessage
  >({
    url: wsUrl,
    queryKey: ['your-feature'],
    queryFn: async () => {
      const { getYourFeature } = await import('../api/client');
      return getYourFeature();
    },
    onMessage: (message: any) => {
      // Handle both WebSocket format and HTTP fallback format
      if (message.type === 'your_feature_update') {
        // WebSocket message
        setData(message.data);
        if (DEBUG_WS) console.log('[WS] Received your-feature update');
      } else if (message.someField) {
        // HTTP fallback (detect by presence of expected field)
        setData(message);
        if (DEBUG_WS) console.log('[HTTP] Received your-feature update');
      }
    },
  });

  return {
    data,
    isConnected: connectionState.isConnected,
    connectionQuality: connectionState.connectionQuality,
    lastUpdated: connectionState.lastUpdated,
    reconnectAttempts: connectionState.reconnectAttempts,
  };
}
```

#### ☐ 3.3 Test hook in isolation

Create a test component to verify the hook works:

```typescript
function TestYourFeatureWebSocket() {
  const { data, isConnected } = useYourFeatureWebSocket();

  return (
    <div>
      <p>Connected: {isConnected ? 'Yes' : 'No'}</p>
      <pre>{JSON.stringify(data, null, 2)}</pre>
    </div>
  );
}
```

---

### Phase 4: Frontend - Component Integration

#### ☐ 4.1 Update component to use WebSocket hook

```typescript
// Before (HTTP polling)
export function YourComponent() {
  const { data } = useQuery({
    queryKey: ['your-feature'],
    queryFn: getYourFeature,
    refetchInterval: 5000  // ❌ HTTP polling
  });

  return <div>{data?.value}</div>;
}

// After (WebSocket)
export function YourComponent() {
  const { data, isConnected } = useYourFeatureWebSocket();  // ✅ WebSocket

  // Handle disconnected state
  if (!isConnected && !data) {
    return <div>Connecting...</div>;
  }

  return <div>{data?.value}</div>;
}
```

#### ☐ 4.2 Add connection status indicator

```typescript
<ConnectionStatusIndicator
  isConnected={isConnected}
  connectionQuality={connectionQuality}
  lastUpdated={lastUpdated}
  consecutiveErrors={0}
  onRetry={() => window.location.reload()}
  variant="compact"
/>
```

#### ☐ 4.3 Handle loading and error states

```typescript
const { data, isConnected } = useYourFeatureWebSocket();

// Loading state
if (!isConnected && !data) {
  return <LoadingSpinner />;
}

// Disconnected with stale data
if (!isConnected && data) {
  return (
    <div>
      <Warning>Connection lost. Showing last known data.</Warning>
      <YourContent data={data} />
    </div>
  );
}

// Connected and ready
return <YourContent data={data} />;
```

---

### Phase 5: Testing

#### ☐ 5.1 Test WebSocket connection

1. Open browser DevTools → Network tab
2. Filter by "WS" (WebSocket)
3. Verify connection to `ws://localhost:8002/api/v1/ws/your-feature`
4. Check connection status: `101 Switching Protocols`

#### ☐ 5.2 Test initial data

1. Verify initial data is received immediately after connection
2. Check browser console for `[WS] Received your-feature update`
3. Verify data is displayed in UI

#### ☐ 5.3 Test real-time updates

**For background polling:**
1. Wait for next broadcast interval (5-30s)
2. Change backend state (e.g., update database)
3. Verify frontend updates automatically
4. Check console for `[WS] Received your-feature update`

**For event-driven:**
1. Trigger event (e.g., create workflow, complete phase)
2. Verify frontend updates immediately (<1s)
3. Check console for `[WS] Received your-feature update`

#### ☐ 5.4 Test reconnection

1. Stop backend (Ctrl+C)
2. Verify frontend shows "Reconnecting..." status
3. Restart backend
4. Verify frontend reconnects automatically
5. Verify data syncs after reconnection

#### ☐ 5.5 Test with multiple clients

1. Open application in 2+ browser tabs
2. Trigger update in one tab
3. Verify ALL tabs receive update simultaneously
4. This confirms broadcasting works globally

#### ☐ 5.6 Verify zero HTTP polling

1. Open DevTools → Network tab
2. Filter by "Fetch/XHR"
3. Verify NO polling requests to `/api/v1/your-feature`
4. Only WebSocket connection should be present

**Expected log output:**
```
INFO: WebSocket /api/v1/ws/your-feature [accepted]
INFO: connection open
[WS] Broadcast your-feature update
[WS] Broadcast your-feature update
(no GET /api/v1/your-feature requests)
```

---

### Phase 6: Documentation

#### ☐ 6.1 Update WebSocket architecture doc

Add your endpoint to the "Available Hooks" and "Message Types" sections:

```markdown
## Available Hooks
- `useYourFeatureWebSocket()` - Your feature description
```

#### ☐ 6.2 Add inline documentation

```typescript
/**
 * WebSocket hook for real-time your-feature updates.
 *
 * Subscribes to your-feature state changes via WebSocket connection.
 * Updates are pushed from backend when [trigger condition].
 *
 * @returns Object containing:
 *   - data: Current your-feature data (null if not loaded)
 *   - isConnected: WebSocket connection status
 *   - connectionQuality: Connection quality indicator
 *   - lastUpdated: Timestamp of last update
 */
export function useYourFeatureWebSocket() {
  // ...
}
```

#### ☐ 6.3 Document broadcasting logic

```python
async def _broadcast_your_feature_updates(self):
    """
    Broadcast your-feature updates to WebSocket clients.

    Frequency: Every 5 seconds (if state changed)
    Trigger: Background polling
    Clients: All connected to /ws/your-feature

    Message format:
        {
            "type": "your_feature_update",
            "data": {
                "field1": "value1",
                "field2": "value2"
            }
        }
    """
```

---

### Phase 7: Cleanup

#### ☐ 7.1 Remove HTTP polling code

Search for and remove old polling logic:

```bash
# Find HTTP polling code
grep -r "refetchInterval" --include="*.tsx" --include="*.ts"
grep -r "useQuery.*your.feature" --include="*.tsx"
```

#### ☐ 7.2 Remove unused HTTP endpoints

If WebSocket completely replaces HTTP endpoint, consider deprecating:

```python
@app.get("/api/v1/your-feature")
@deprecated("Use WebSocket /ws/your-feature instead")
async def get_your_feature():
    """DEPRECATED: Use WebSocket instead"""
    pass
```

#### ☐ 7.3 Build and test

```bash
cd app/client
bun run build
```

Verify no TypeScript errors.

---

## Verification Checklist

Use this to verify implementation is complete:

### Backend
- ☐ Data function exists in `server.py`
- ☐ Data function added to `init_websocket_routes()` call
- ☐ WebSocket endpoint created in `websocket_routes.py`
- ☐ **Broadcasting logic added to `background_tasks.py` OR event handlers**
- ☐ Backend logs show broadcast messages

### Frontend
- ☐ WebSocket URL helper added to `api.ts`
- ☐ WebSocket hook created in `useWebSocket.ts`
- ☐ Component uses WebSocket hook (not HTTP polling)
- ☐ Connection status indicator added
- ☐ Loading/error states handled

### Testing
- ☐ WebSocket connects successfully
- ☐ Initial data received
- ☐ Real-time updates working
- ☐ Reconnection works
- ☐ Multiple clients receive broadcasts
- ☐ **Zero HTTP polling in Network tab**

### Documentation
- ☐ Architecture doc updated
- ☐ Inline docs added
- ☐ Broadcasting logic documented

---

## Common Mistakes

### Mistake #1: No Broadcasting Logic
**Symptom:** WebSocket connects but never updates
**Fix:** Add broadcasting in Phase 2

### Mistake #2: Wrong Message Type
**Symptom:** Frontend receives messages but doesn't process them
**Fix:** Verify message type matches exactly in backend and frontend

### Mistake #3: Broadcasting Too Frequently
**Symptom:** High CPU/network usage, logs flooded
**Fix:** Add state comparison to only broadcast when changed

### Mistake #4: Not Handling Disconnection
**Symptom:** UI shows errors when backend restarts
**Fix:** Add loading/error states in Phase 4

### Mistake #5: Forgetting to Remove HTTP Polling
**Symptom:** Both WebSocket AND HTTP polling active
**Fix:** Complete Phase 7 cleanup

---

## Quick Reference

### Backend Files to Modify
1. `app/server/server.py` - Data function
2. `app/server/routes/websocket_routes.py` - WebSocket endpoint
3. `app/server/services/background_tasks.py` - Broadcasting logic

### Frontend Files to Modify
1. `app/client/src/config/api.ts` - WebSocket URL
2. `app/client/src/hooks/useWebSocket.ts` - WebSocket hook
3. `app/client/src/components/YourComponent.tsx` - Use hook

### Key Commands
```bash
# Test WebSocket
curl -i -N -H "Connection: Upgrade" -H "Upgrade: websocket" http://localhost:8002/api/v1/ws/your-feature

# Check broadcasts
tail -f logs/backend.log | grep "Broadcast"

# Verify no polling
# Open DevTools → Network → Filter by "Fetch/XHR"
```

---

## Template Repository

For a complete working example, see:
- Backend: `app/server/routes/websocket_routes.py` - `/ws/adw-monitor` endpoint
- Broadcasting: `app/server/services/background_tasks.py` - `_broadcast_adw_monitor_updates()`
- Frontend: `app/client/src/hooks/useWebSocket.ts` - `useADWMonitorWebSocket()`
- Component: `app/client/src/components/CurrentWorkflowCard.tsx`

This is the gold standard implementation with all phases complete.
