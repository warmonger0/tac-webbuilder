# WebSocket Architecture

## Overview

TAC WebBuilder uses WebSockets for real-time bidirectional communication between the frontend and backend. This document describes the architecture, implementation patterns, and critical requirements for all WebSocket functionality.

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                         Frontend                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Component (e.g., CurrentWorkflowCard)                          │
│         │                                                        │
│         ├─> useWebSocket hook (e.g., useADWMonitorWebSocket)   │
│                  │                                               │
│                  ├─> useReliableWebSocket (core hook)           │
│                           │                                      │
│                           ├─> WebSocket connection              │
│                           ├─> Exponential backoff reconnection  │
│                           └─> NO HTTP FALLBACK (disabled)       │
│                                                                  │
└──────────────────────────────┬──────────────────────────────────┘
                               │
                    WebSocket Connection
                     ws://host:port/api/v1/ws/*
                               │
┌──────────────────────────────▼──────────────────────────────────┐
│                         Backend                                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  WebSocket Endpoint (/api/v1/ws/adw-monitor)                   │
│         │                                                        │
│         ├─> init_websocket_routes() (routes/websocket_routes.py)│
│         │         │                                              │
│         │         ├─> _handle_websocket_connection()            │
│         │         │      ├─> Accept connection                  │
│         │         │      ├─> Send initial data                  │
│         │         │      └─> Keep-alive loop                    │
│         │         │                                              │
│         │         └─> Data function (get_adw_monitor_data)      │
│         │                                                        │
│         └─> ConnectionManager (manager)                         │
│                  │                                               │
│                  ├─> Maintains active connections               │
│                  └─> broadcast() - Push updates to clients      │
│                                                                  │
│  Broadcasting Sources:                                          │
│         ├─> BackgroundTasks (background_tasks.py)              │
│         ├─> PhaseCoordinator (phase_coordinator.py)            │
│         └─> Event handlers (hooks, webhooks)                   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Core Components

### Frontend

#### 1. useReliableWebSocket (Core Hook)
**Location:** `app/client/src/hooks/useReliableWebSocket.ts`

The foundation hook that manages WebSocket connections with:
- Automatic reconnection with exponential backoff
- Visibility API integration (pause when tab hidden)
- Connection quality monitoring
- **NO HTTP fallback** (disabled since commit 8d254cb)

```typescript
interface ReliableWebSocketOptions<T, M = any> {
  url: string;                    // WebSocket URL
  queryKey: string[];             // React Query key (unused now)
  queryFn: () => Promise<T>;      // Fallback function (unused now)
  onMessage: (data: M) => void;   // Message handler
  enabled?: boolean;              // Enable/disable connection
  pollingInterval?: number;       // UNUSED (kept for compat)
  maxReconnectDelay?: number;     // Max backoff delay (default: 30s)
  maxReconnectAttempts?: number;  // Max reconnect attempts (default: 10)
}
```

**Key Behavior:**
- Connects on mount
- Sends/receives JSON messages
- Reconnects automatically with exponential backoff (1s → 2s → 4s → ... → 30s max)
- Pauses when tab hidden (via Visibility API)
- **NEVER falls back to HTTP polling** (this is intentional)

#### 2. Specific WebSocket Hooks
**Location:** `app/client/src/hooks/useWebSocket.ts`

Each WebSocket endpoint has a dedicated hook:

```typescript
// Example: ADW Monitor WebSocket
export function useADWMonitorWebSocket() {
  const [workflows, setWorkflows] = useState<AdwWorkflowStatus[]>([]);
  const wsUrl = apiConfig.websocket.adwMonitor();

  const connectionState = useReliableWebSocket({
    url: wsUrl,
    queryKey: ['adw-monitor'],
    queryFn: getAdwMonitor, // Unused (no fallback)
    onMessage: (message) => {
      if (message.type === 'adw_monitor_update') {
        setWorkflows(message.data.workflows);
      }
    },
  });

  return { workflows, isConnected, ... };
}
```

**Available Hooks:**
- `useWorkflowsWebSocket()` - Workflow list
- `useRoutesWebSocket()` - Route configuration
- `useWorkflowHistoryWebSocket()` - Workflow history
- `useADWStateWebSocket(adwId)` - Individual ADW state
- `useADWMonitorWebSocket()` - All ADW workflows
- `useQueueWebSocket()` - Phase queue
- `useSystemStatusWebSocket()` - System status (no broadcasting)
- `useWebhookStatusWebSocket()` - Webhook status (no broadcasting)

#### 3. Component Usage

```typescript
export function CurrentWorkflowCard() {
  // Use WebSocket hook
  const { workflows, isConnected } = useADWMonitorWebSocket();

  // workflows updates automatically when backend broadcasts
  const workflow = useMemo(() => {
    return workflows.find(w => w.status === 'failed')
      || workflows.find(w => w.status === 'running')
      || workflows.find(w => w.status === 'paused')
      || null;
  }, [workflows]);

  // Show connection status
  if (!isConnected) {
    return <div>Disconnected</div>;
  }

  return <div>{workflow?.title}</div>;
}
```

### Backend

#### 1. WebSocket Endpoints
**Location:** `app/server/routes/websocket_routes.py`

WebSocket endpoints follow a standard pattern:

```python
@router.websocket("/ws/adw-monitor")
async def websocket_adw_monitor(websocket: WebSocket) -> None:
    """WebSocket endpoint for real-time ADW monitor updates"""
    # 1. Get initial data
    monitor_data = get_adw_monitor_data_func()

    # 2. Format as WebSocket message
    initial_data = {
        "type": "adw_monitor_update",
        "data": monitor_data
    }

    # 3. Handle connection (connect, send initial, keep-alive)
    await _handle_websocket_connection(
        websocket, manager, initial_data, "ADW monitor"
    )
```

**Standard Handler:**
```python
async def _handle_websocket_connection(
    websocket: WebSocket,
    manager: ConnectionManager,
    initial_data: dict,
    error_context: str
):
    # Accept and register connection
    await manager.connect(websocket)

    try:
        # Send initial data to client
        await websocket.send_json(initial_data)

        # Keep connection alive
        while True:
            await websocket.receive_text()  # Wait for ping/pong
    except WebSocketDisconnect:
        pass
    except Exception as e:
        logger.error(f"[WS] Error in {error_context}: {e}")
    finally:
        manager.disconnect(websocket)
```

#### 2. ConnectionManager
**Location:** `app/server/services/websocket_manager.py`

Manages all active WebSocket connections and broadcasts updates:

```python
class ConnectionManager:
    def __init__(self):
        self.active_connections: set[WebSocket] = set()

    async def connect(self, websocket: WebSocket):
        """Accept and register new connection"""
        await websocket.accept()
        self.active_connections.add(websocket)

    def disconnect(self, websocket: WebSocket):
        """Remove connection"""
        self.active_connections.discard(websocket)

    async def broadcast(self, message: dict):
        """Send message to all connected clients"""
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Broadcast error: {e}")
```

**Key Point:** `broadcast()` is **global** - it sends to ALL connected clients regardless of which endpoint they're connected to. This is intentional for simplicity.

#### 3. Broadcasting Sources

WebSocket updates are triggered from multiple sources:

##### A. Background Tasks
**Location:** `app/server/services/background_tasks.py`

Periodically scans for changes and broadcasts updates:

```python
async def _broadcast_updates(self):
    """Periodically broadcast state changes to WebSocket clients"""
    while True:
        try:
            # Scan for changes
            current_state = self._get_current_state()

            # Broadcast if changed
            if current_state != self.last_state:
                await self.websocket_manager.broadcast({
                    "type": "adw_monitor_update",
                    "data": current_state
                })
                self.last_state = current_state

            await asyncio.sleep(5)  # Check every 5 seconds
        except Exception as e:
            logger.error(f"Broadcast error: {e}")
```

**What it broadcasts:**
- ADW monitor updates (every 5s if changed)
- Queue updates (every 5s if changed)
- Workflow history (every 10s if changed)
- Routes (every 10s if changed)

##### B. Event Handlers
**Location:** `app/server/services/phase_coordination/phase_coordinator.py`

Broadcasts immediately when events occur:

```python
async def _on_phase_complete(self, phase_id: str):
    """Handle phase completion event"""
    # Update state
    phase = self.phase_queue_service.get_by_id(phase_id)
    phase.status = 'completed'

    # Broadcast immediately
    await self.websocket_manager.broadcast({
        "type": "queue_update",
        "data": {
            "phases": self._get_all_phases(),
            "total": len(phases),
            "paused": self.is_paused()
        }
    })
```

**Events that trigger broadcasts:**
- Phase completion
- Phase failure
- Queue state changes
- Workflow status changes

##### C. Webhook Handlers
**Location:** `app/server/routes/queue_routes.py`, `adws/adw_triggers/trigger_webhook.py`

External events (GitHub webhooks) trigger broadcasts:

```python
@router.post("/webhook")
async def handle_webhook(payload: dict):
    """Handle GitHub webhook"""
    # Process webhook
    result = await process_github_webhook(payload)

    # Broadcast workflow update
    await websocket_manager.broadcast({
        "type": "workflow_update",
        "data": result
    })

    return {"status": "ok"}
```

## Message Format

All WebSocket messages follow a standard format:

```typescript
interface WebSocketMessage {
  type: string;        // Message type (e.g., "adw_monitor_update")
  data: any;           // Payload (varies by type)
  timestamp?: string;  // Optional timestamp
}
```

### Message Types

| Type | Source | Frequency | Description |
|------|--------|-----------|-------------|
| `workflows_update` | BackgroundTasks | 5s (if changed) | Workflow list updates |
| `routes_update` | BackgroundTasks | 10s (if changed) | Route configuration |
| `workflow_history_update` | BackgroundTasks | 10s (if changed) | History updates |
| `adw_state_update` | BackgroundTasks | 5s (if changed) | Individual ADW state |
| `adw_monitor_update` | BackgroundTasks | 5s (if changed) | All ADW workflows |
| `queue_update` | PhaseCoordinator + BackgroundTasks | Event + 5s | Phase queue changes |
| `system_status_update` | **NONE** | Never | System status (no broadcasting) |
| `webhook_status_update` | **NONE** | Never | Webhook status (no broadcasting) |

## Critical Requirements

### ⚠️ EVERY WebSocket endpoint MUST have broadcasting logic

This is the #1 mistake that causes issues. WebSocket endpoints without broadcasting:
1. Connect successfully ✅
2. Send initial data ✅
3. Sit idle forever ❌
4. Client sees no updates ❌
5. Connection eventually times out ❌

**Example of BROKEN WebSocket** (system-status, webhook-status):
```python
# Endpoint exists ✅
@router.websocket("/ws/system-status")
async def websocket_system_status(websocket: WebSocket):
    initial_data = await get_system_status_data_func()
    await _handle_websocket_connection(...)

# But NO broadcasting logic ❌
# These connections get initial data then receive nothing
```

**How to fix:** Add broadcasting in `background_tasks.py` or event handlers:

```python
# In background_tasks.py
async def _broadcast_system_status(self):
    while True:
        current_status = await get_system_status()
        if current_status != self.last_system_status:
            await self.websocket_manager.broadcast({
                "type": "system_status_update",
                "data": current_status
            })
            self.last_system_status = current_status
        await asyncio.sleep(30)  # Check every 30s
```

## Current Status

### Working WebSockets (with broadcasting)
- ✅ `/ws/workflows` - Background polling (5s)
- ✅ `/ws/routes` - Background polling (10s)
- ✅ `/ws/workflow-history` - Background polling (10s)
- ✅ `/ws/adw-monitor` - Background polling (5s)
- ✅ `/ws/queue` - Event-driven + background polling (5s)
- ✅ `/ws/adw-state/{adw_id}` - Background polling (5s)

### Incomplete WebSockets (no broadcasting)
- ⚠️ `/ws/system-status` - Gets initial data, then idle
- ⚠️ `/ws/webhook-status` - Gets initial data, then idle

**Impact:** These work for initial load but never update. Since we disabled HTTP fallback, components show stale data but no polling occurs (which is acceptable for rarely-changing status).

## Configuration

### Frontend Config
**Location:** `app/client/src/config/intervals.ts`

```typescript
export const intervals = {
  websocket: {
    pollingInterval: 60000,        // UNUSED (no fallback)
    maxReconnectDelay: 30000,      // Max reconnect delay
    maxReconnectAttempts: 10,      // Max reconnect attempts
    qualityUpdateInterval: 5000,   // Connection quality check
  }
}
```

### Backend Config
**Location:** `app/server/services/background_tasks.py`

```python
# Broadcasting intervals
BROADCAST_INTERVAL_FAST = 5    # seconds (adw-monitor, queue)
BROADCAST_INTERVAL_SLOW = 10   # seconds (routes, history)
```

## Troubleshooting

### WebSocket not updating
**Symptoms:** Connection shows "Live" but data never updates

**Causes:**
1. ❌ No broadcasting logic for this endpoint
2. ❌ Broadcasting logic exists but has bug
3. ❌ Data comparison logic prevents broadcasts (nothing changed)

**Fix:** Add/fix broadcasting in `background_tasks.py` or event handlers

### Connection keeps disconnecting
**Symptoms:** "Reconnecting..." indicator flashing

**Causes:**
1. ❌ Backend not running
2. ❌ Port mismatch (check VITE_BACKEND_PORT)
3. ❌ Network issues
4. ❌ WebSocket endpoint crashing

**Fix:** Check backend logs for errors, verify ports in `.env`

### No connection at all
**Symptoms:** Permanent "Disconnected" state

**Causes:**
1. ❌ Wrong WebSocket URL
2. ❌ CORS issues
3. ❌ Backend not exposing WebSocket endpoints

**Fix:** Check browser console, verify backend running, check CORS config

## Migration from HTTP Polling

**Old pattern (DEPRECATED):**
```typescript
const { data } = useQuery({
  queryKey: ['adw-monitor'],
  queryFn: getAdwMonitor,
  refetchInterval: 5000  // ❌ HTTP polling
});
```

**New pattern (CURRENT):**
```typescript
const { workflows, isConnected } = useADWMonitorWebSocket();
// ✅ Real-time WebSocket updates
// ✅ No HTTP polling
```

## Performance Characteristics

### HTTP Polling (Old)
- Request frequency: Every 3-60 seconds
- Network usage: ~4-180 requests/minute
- Server load: Constant database queries
- Latency: 3-60 seconds for updates
- Log noise: Constant GET requests

### WebSocket (Current)
- Request frequency: Zero (push-based)
- Network usage: ~0-10 messages/minute (only when state changes)
- Server load: Minimal (broadcast only when changed)
- Latency: <100ms for updates
- Log noise: Silent (only connection events)

## Security Considerations

1. **Authentication:** Currently no WebSocket authentication (relies on same-origin)
2. **Authorization:** No per-connection authorization
3. **Rate limiting:** No WebSocket-specific rate limiting
4. **Input validation:** All WebSocket messages should validate input (future work)

## Future Improvements

1. **Add broadcasting for system-status and webhook-status**
2. **WebSocket authentication/authorization**
3. **Per-connection message filtering** (only send relevant updates)
4. **Compression** for large payloads
5. **Binary message support** for efficiency
6. **Heartbeat/ping-pong** for connection health
7. **Metrics/monitoring** for WebSocket connections

## References

- Frontend WebSocket hooks: `app/client/src/hooks/useWebSocket.ts`
- Backend WebSocket routes: `app/server/routes/websocket_routes.py`
- Connection manager: `app/server/services/websocket_manager.py`
- Background tasks: `app/server/services/background_tasks.py`
- Configuration: `app/client/src/config/intervals.ts`
