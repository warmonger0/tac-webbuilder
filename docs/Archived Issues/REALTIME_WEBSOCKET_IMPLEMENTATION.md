# Real-Time WebSocket Implementation

## Overview
This document describes the WebSocket implementation for real-time updates in the tac-webbuilder application. Both API Routes and Workflows use WebSocket connections for live updates with automatic fallback to REST polling.

## Architecture Pattern

### Backend Structure (FastAPI)
1. **Helper Function** - Extracts data logic for reuse
2. **Background Watcher** - Monitors changes every 2 seconds
3. **WebSocket Endpoint** - Handles real-time connections
4. **REST Endpoint** - Serves as fallback when WebSocket fails
5. **Connection Manager** - Manages active WebSocket connections

### Frontend Structure (React + TypeScript)
1. **WebSocket Hook** - Manages connection lifecycle
2. **TanStack Query Fallback** - Polls REST API when disconnected
3. **Visual Indicators** - Shows connection status to user
4. **Auto-reconnect** - Attempts reconnection every 5 seconds

## Implementation Details

### Backend Components

#### 1. Connection Manager (server.py:83-110)
```python
class ConnectionManager:
    def __init__(self):
        self.active_connections: Set[WebSocket] = set()
        self.last_workflow_state = None
        self.last_routes_state = None
```

Manages all active WebSocket connections and tracks last known state to avoid redundant broadcasts.

#### 2. Data Helper Functions
- **get_workflows_data()** (server.py:113-164) - Scans `agents/` directory for workflow state
- **get_routes_data()** (server.py:166-204) - Introspects FastAPI routes

#### 3. Background Watchers
- **watch_workflows()** (server.py:206-231) - Monitors workflow changes
- **watch_routes()** (server.py:233-255) - Monitors route changes

Both watchers:
- Run continuously in background
- Check for changes every 2 seconds
- Only broadcast when state actually changes
- Only active when clients are connected

#### 4. WebSocket Endpoints
- **POST /ws/workflows** (server.py:478-501) - Workflow updates
- **POST /ws/routes** (server.py:503-526) - Route updates

Both endpoints:
- Send initial data on connection
- Keep connection alive
- Handle graceful disconnection

#### 5. REST Fallback Endpoints
- **GET /api/workflows** (server.py:528-538) - Workflow list
- **GET /api/routes** (server.py:457-469) - Route list

### Frontend Components

#### 1. WebSocket Hooks (useWebSocket.ts)

**useWorkflowsWebSocket()** (lines 16-96)
- Connects to ws://localhost:8000/ws/workflows
- Manages workflows state
- Auto-reconnects on disconnect
- Falls back to polling every 3s when disconnected

**useRoutesWebSocket()** (lines 98-178)
- Connects to ws://localhost:8000/ws/routes
- Manages routes state
- Auto-reconnects on disconnect
- Falls back to polling every 3s when disconnected

#### 2. Visual Components

**WorkflowDashboard.tsx**
- Green pulsing dot = Live WebSocket connection
- Yellow dot = Polling fallback mode
- Gray dot = Reconnecting
- Timestamp shows "Updated X ago"

**RoutesView.tsx**
- Same visual indicators as workflows
- Connection status in header
- Real-time route table updates

## Data Flow

### WebSocket Connected (Normal Operation)
```
Backend watch_routes() → Detects change → Broadcasts via ConnectionManager
                                                     ↓
Frontend useRoutesWebSocket() → Receives update → Updates state → UI re-renders
```

### WebSocket Disconnected (Fallback Mode)
```
Frontend detects disconnect → Enables TanStack Query polling (3s interval)
                                              ↓
                                    Polls /api/routes REST endpoint
                                              ↓
                                    Updates state → UI shows yellow indicator
```

### Reconnection Flow
```
Frontend disconnect → Wait 5s → Attempt reconnect → On success: Disable polling, enable WS
```

## Configuration

### Backend Dependencies (pyproject.toml)
```toml
dependencies = [
    "fastapi==0.115.13",
    "uvicorn==0.34.3",
    "websockets==15.0.1",    # WebSocket protocol support
    "wsproto==1.3.1",        # Low-level WebSocket protocol
]
```

### Frontend Dependencies (package.json)
```json
{
  "dependencies": {
    "@tanstack/react-query": "^5.0.0",  // REST fallback polling
    "react": "^18.3.1"
  }
}
```

### Environment Variables (.ports.env)
```bash
BACKEND_PORT=8000
FRONTEND_PORT=5173
VITE_BACKEND_URL=http://localhost:8000
```

### Vite Configuration (vite.config.ts)
```typescript
server: {
  port: 5173,
  proxy: {
    '/api': { target: 'http://localhost:8000' },
    '/ws': { target: 'ws://localhost:8000', ws: true }
  }
}
```

## Visual Indicators

### Connection States
| Indicator | Status | Meaning |
|-----------|--------|---------|
| 🟢 Green pulsing | Live updates | WebSocket connected and active |
| 🟡 Yellow | Polling fallback | WebSocket failed, using REST API |
| ⚪ Gray | Reconnecting... | Attempting to reconnect |

### Timestamp Display
- "Just now" - Updated < 5 seconds ago
- "Xs ago" - Updated X seconds ago
- "Xm ago" - Updated X minutes ago
- "Xh ago" - Updated X hours ago

## Troubleshooting

### WebSocket Not Connecting

**Symptom**: Yellow "Polling fallback" indicator persists

**Check**:
1. Backend logs for WebSocket library errors
2. Browser console for connection errors
3. Verify `websockets` and `wsproto` installed: `uv pip list | grep websocket`

**Solution**:
```bash
cd app/server
uv pip install websockets wsproto
# Restart backend server
```

### Routes/Workflows Not Updating

**Check**:
1. Backend logs show "[STARTUP] Workflow and routes watchers started"
2. Backend logs show "[WS] Broadcasted X update to Y clients"
3. Browser console shows "[WS] Received X update: Y items"

**Solution**: Check background watchers are running in startup event

### High CPU Usage

**Issue**: Background watchers check every 2 seconds

**Optimization**: Adjust `asyncio.sleep(2)` in watch functions to longer intervals

## Git Commits

### Session 1: API Routes WebSocket Implementation
- **f53b7d0** - feat: Add real-time WebSocket updates for API routes
- **ebd1c7c** - chore: Add WebSocket dependencies for real-time updates

## Testing

### Manual Testing
1. Open http://localhost:5173
2. Navigate to API Routes or Workflows tab
3. Verify green "Live updates" indicator appears
4. Kill backend server: `pkill -f uvicorn`
5. Verify indicator changes to yellow "Polling fallback"
6. Restart backend
7. Verify indicator returns to green within 5 seconds

### Browser Console Verification
```javascript
// Should see these logs:
[WS] Connecting to: ws://localhost:8000/ws/routes
[WS] Connected to routes updates
[WS] Received routes update: 11 routes
```

## Performance Characteristics

- **Update Latency**: < 2 seconds (watcher polling interval)
- **Reconnect Time**: 5 seconds after disconnect
- **Polling Fallback**: Every 3 seconds when disconnected
- **Broadcast Overhead**: Only when state changes (diff-based)
- **Memory**: Minimal (stores last state as JSON string for comparison)

## Future Enhancements

1. **Delta Updates**: Send only changed items instead of full list
2. **Heartbeat/Ping-Pong**: Detect stale connections faster
3. **Configurable Intervals**: Allow user to adjust update frequency
4. **Connection Quality Indicator**: Show latency/packet loss
5. **Batch Updates**: Combine multiple rapid changes into single broadcast
