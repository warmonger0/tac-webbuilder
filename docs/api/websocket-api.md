# WebSocket API Reference

Complete reference for all WebSocket endpoints and hooks in the tac-webbuilder project.

## Table of Contents

1. [Overview](#overview)
2. [Connection URLs](#connection-urls)
3. [Frontend Hooks](#frontend-hooks)
4. [Backend Endpoints](#backend-endpoints)
5. [Message Formats](#message-formats)
6. [Connection Management](#connection-management)
7. [Error Handling](#error-handling)
8. [Best Practices](#best-practices)

---

## Overview

The WebSocket API provides real-time updates for dashboard data, eliminating the need for HTTP polling and reducing latency to <2 seconds.

### Architecture

```
┌─────────────┐         WebSocket          ┌──────────────┐
│   Frontend  │◄─────────────────────────►│   Backend    │
│   (React)   │    wss://localhost:8002    │   (FastAPI)  │
└─────────────┘                            └──────────────┘
      │                                            │
      │ useWebSocket hooks                        │ Broadcast
      │                                            │
      ▼                                            ▼
  Auto-update UI                        State changes
```

### Benefits

- **Low Latency:** <2s updates vs 3-30s polling
- **Reduced Traffic:** 80% less network usage
- **Real-Time:** Instant updates across all clients
- **Auto-Reconnect:** Handles disconnections automatically
- **Connection Quality:** Monitors and reports connection health

---

## Connection URLs

All WebSocket connections use the `wss://` protocol and connect to the backend server.

**Base URL:** `wss://localhost:8002` (or port from `.ports.env`)

| Endpoint | URL | Purpose |
|----------|-----|---------|
| Workflows | `/ws/workflows` | Active workflow updates |
| Routes | `/ws/routes` | Route status updates |
| Workflow History | `/ws/workflow-history` | Historical workflow data |
| ADW State | `/ws/adw-state/{adw_id}` | Specific ADW state |
| ADW Monitor | `/ws/adw-monitor` | All ADW monitoring |
| Queue | `/ws/queue` | Phase queue updates |
| System Status | `/ws/system-status` | System health status |
| Webhook Status | `/ws/webhook-status` | Webhook status |

---

## Frontend Hooks

All frontend components should use these React hooks to connect to WebSocket endpoints.

### 1. useWorkflowsWebSocket()

**Purpose:** Real-time updates for active workflows

**Usage:**
```typescript
import { useWorkflowsWebSocket } from '../hooks/useWebSocket';

const MyComponent = () => {
  const {
    workflows,          // WorkflowExecution[]
    isConnected,        // boolean
    connectionQuality,  // 'good' | 'poor'
    lastUpdated,       // number (timestamp)
    reconnectAttempts  // number
  } = useWorkflowsWebSocket();

  return (
    <div>
      {workflows.map(workflow => (
        <div key={workflow.id}>{workflow.name}</div>
      ))}
    </div>
  );
};
```

**Return Values:**
```typescript
{
  workflows: WorkflowExecution[];  // Array of active workflows
  isConnected: boolean;            // Connection status
  connectionQuality: 'good' | 'poor';  // Connection health
  lastUpdated: number;             // Timestamp of last update
  reconnectAttempts: number;       // Reconnection attempt count
}
```

**When to Use:**
- Dashboard showing active workflows
- Workflow status monitoring
- Real-time workflow lists

---

### 2. useRoutesWebSocket()

**Purpose:** Real-time updates for API routes

**Usage:**
```typescript
import { useRoutesWebSocket } from '../hooks/useWebSocket';

const RoutesView = () => {
  const {
    routes,
    isConnected,
    connectionQuality,
    lastUpdated,
    reconnectAttempts
  } = useRoutesWebSocket();

  if (!isConnected) {
    return <div>Connecting...</div>;
  }

  return (
    <div>
      {routes.map(route => (
        <div key={route.path}>{route.method} {route.path}</div>
      ))}
    </div>
  );
};
```

**Return Values:**
```typescript
{
  routes: Route[];                 // Array of API routes
  isConnected: boolean;
  connectionQuality: 'good' | 'poor';
  lastUpdated: number;
  reconnectAttempts: number;
}
```

**When to Use:**
- API route monitoring
- Route status dashboards
- Development debugging

---

### 3. useWorkflowHistoryWebSocket()

**Purpose:** Real-time updates for workflow history and analytics

**Usage:**
```typescript
import { useWorkflowHistoryWebSocket } from '../hooks/useWebSocket';

const HistoryView = () => {
  const {
    workflows,          // WorkflowHistoryItem[]
    totalCount,         // number
    analytics,          // HistoryAnalytics
    isConnected,
    connectionQuality,
    lastUpdated,
    reconnectAttempts
  } = useWorkflowHistoryWebSocket();

  return (
    <div>
      <div>Total: {totalCount}</div>
      <div>Success Rate: {analytics?.success_rate}%</div>
      {workflows.map(workflow => (
        <WorkflowCard key={workflow.id} workflow={workflow} />
      ))}
    </div>
  );
};
```

**Return Values:**
```typescript
{
  workflows: WorkflowHistoryItem[];  // Historical workflow data
  totalCount: number;                // Total workflow count
  analytics: HistoryAnalytics | null;  // Analytics data
  isConnected: boolean;
  connectionQuality: 'good' | 'poor';
  lastUpdated: number;
  reconnectAttempts: number;
}
```

**HistoryAnalytics Type:**
```typescript
interface HistoryAnalytics {
  total_count: number;
  success_rate: number;
  average_duration: number;
  recent_failures: number;
  // ... other analytics fields
}
```

**When to Use:**
- Workflow history panels
- Analytics dashboards
- Performance monitoring

---

### 4. useADWStateWebSocket()

**Purpose:** Real-time updates for specific ADW state

**Usage:**
```typescript
import { useADWStateWebSocket } from '../hooks/useWebSocket';

const ADWDetailView = ({ adwId }: { adwId: string }) => {
  const {
    state,              // ADW state object or null
    isConnected,
    connectionQuality,
    lastUpdated,
    reconnectAttempts
  } = useADWStateWebSocket(adwId);

  if (!state) {
    return <div>No state data</div>;
  }

  return (
    <div>
      <div>Status: {state.status}</div>
      <div>Branch: {state.branch_name}</div>
      <div>Issue: {state.issue_number}</div>
    </div>
  );
};
```

**Parameters:**
- `adwId: string | null` - ADW ID to monitor (pass null to disconnect)

**Return Values:**
```typescript
{
  state: {
    adw_id: string;
    issue_number?: string;
    status?: string;
    branch_name?: string;
    plan_file?: string;
    issue_class?: string;
    worktree_path?: string;
    backend_port?: number;
    frontend_port?: number;
    model_set?: string;
    all_adws?: string[];
    workflow_template?: string;
    model_used?: string;
    start_time?: string;
    nl_input?: string;
    github_url?: string;
    [key: string]: any;
  } | null;
  isConnected: boolean;
  connectionQuality: 'good' | 'poor';
  lastUpdated: number;
  reconnectAttempts: number;
}
```

**When to Use:**
- ADW detail views
- Single ADW monitoring
- Debugging specific ADW workflows

**Note:** This hook only works via WebSocket (no HTTP fallback)

---

### 5. useADWMonitorWebSocket()

**Purpose:** Real-time updates for all ADW workflows

**Usage:**
```typescript
import { useADWMonitorWebSocket } from '../hooks/useWebSocket';

const ADWMonitorCard = () => {
  const {
    workflows,          // AdwWorkflowStatus[]
    summary,            // AdwMonitorSummary
    lastUpdated,        // string
    isConnected,
    connectionQuality,
    reconnectAttempts
  } = useADWMonitorWebSocket();

  return (
    <div>
      <div>Total: {summary.total}</div>
      <div>Running: {summary.running}</div>
      <div>Completed: {summary.completed}</div>
      <div>Failed: {summary.failed}</div>

      {workflows.map(workflow => (
        <div key={workflow.adw_id}>{workflow.status}</div>
      ))}
    </div>
  );
};
```

**Return Values:**
```typescript
{
  workflows: AdwWorkflowStatus[];  // All ADW workflows
  summary: AdwMonitorSummary;      // Summary statistics
  lastUpdated: string;             // Last update timestamp
  isConnected: boolean;
  connectionQuality: 'good' | 'poor';
  reconnectAttempts: number;
}
```

**AdwMonitorSummary Type:**
```typescript
interface AdwMonitorSummary {
  total: number;
  running: number;
  completed: number;
  failed: number;
  paused: number;
}
```

**When to Use:**
- ADW dashboard overview
- Multi-ADW monitoring
- ADW summary statistics

---

### 6. useQueueWebSocket()

**Purpose:** Real-time updates for phase queue

**Usage:**
```typescript
import { useQueueWebSocket } from '../hooks/useWebSocket';

const ZteHopperQueueCard = () => {
  const {
    phases,             // PhaseQueueItem[]
    paused,             // boolean
    isConnected,
    connectionQuality,
    reconnectAttempts
  } = useQueueWebSocket();

  return (
    <div>
      <div>Queue {paused ? 'Paused' : 'Active'}</div>
      {phases.map(phase => (
        <div key={phase.queue_id}>
          {phase.issue_number} - {phase.status}
        </div>
      ))}
    </div>
  );
};
```

**Return Values:**
```typescript
{
  phases: PhaseQueueItem[];        // Queue items
  paused: boolean;                 // Queue paused status
  isConnected: boolean;
  connectionQuality: 'good' | 'poor';
  reconnectAttempts: number;
}
```

**PhaseQueueItem Type:**
```typescript
interface PhaseQueueItem {
  queue_id: number;
  issue_number: string;
  parent_issue?: string;
  phase: string;
  status: string;
  priority: number;
  metadata?: any;
  created_at: string;
  updated_at: string;
}
```

**When to Use:**
- Phase queue monitoring
- Queue management dashboards
- ZTE hopper displays

---

### 7. useSystemStatusWebSocket()

**Purpose:** Real-time updates for system status

**Usage:**
```typescript
import { useSystemStatusWebSocket } from '../hooks/useWebSocket';

const SystemStatusPanel = () => {
  const {
    systemStatus,
    isConnected,
    connectionQuality,
    lastUpdated,
    reconnectAttempts
  } = useSystemStatusWebSocket();

  if (!systemStatus) {
    return <div>Loading status...</div>;
  }

  return (
    <div>
      <div>Overall: {systemStatus.overall_status}</div>
      {/* Display other status fields */}
    </div>
  );
};
```

**Return Values:**
```typescript
{
  systemStatus: any | null;        // System status object
  isConnected: boolean;
  connectionQuality: 'good' | 'poor';
  lastUpdated: number;
  reconnectAttempts: number;
}
```

**When to Use:**
- System health monitoring
- Status dashboards
- Admin panels

**Note:** System status rarely changes, so polling is acceptable here

---

### 8. useWebhookStatusWebSocket()

**Purpose:** Real-time updates for webhook status

**Usage:**
```typescript
import { useWebhookStatusWebSocket } from '../hooks/useWebSocket';

const WebhookStatusPanel = () => {
  const {
    webhookStatus,
    isConnected,
    connectionQuality,
    lastUpdated,
    reconnectAttempts
  } = useWebhookStatusWebSocket();

  if (!webhookStatus) {
    return <div>Loading webhook status...</div>;
  }

  return (
    <div>
      <div>Status: {webhookStatus.status}</div>
      {/* Display other webhook fields */}
    </div>
  );
};
```

**Return Values:**
```typescript
{
  webhookStatus: any | null;       // Webhook status object
  isConnected: boolean;
  connectionQuality: 'good' | 'poor';
  lastUpdated: number;
  reconnectAttempts: number;
}
```

**When to Use:**
- Webhook monitoring
- Integration status
- GitHub webhook health checks

---

## Backend Endpoints

All backend WebSocket endpoints follow the same pattern:

1. Accept connection
2. Send initial data
3. Keep connection alive
4. Broadcast updates when state changes
5. Handle disconnections

### Endpoint Pattern

```python
@router.websocket("/ws/example")
async def websocket_example(websocket: WebSocket) -> None:
    """WebSocket endpoint for real-time example updates"""

    # Get initial data
    initial_data = get_example_data()

    # Send to client
    await _handle_websocket_connection(
        websocket,
        manager,
        {
            "type": "example_update",
            "data": initial_data
        },
        "example"
    )
```

### Broadcasting Updates

When backend state changes, broadcast to all connected clients:

```python
# In service layer
from app.server.routes.websocket_routes import manager

async def update_workflow_status(workflow_id: int, status: str):
    """Update workflow and broadcast to clients"""

    # Update database
    workflow = repository.update_status(workflow_id, status)

    # Broadcast to WebSocket clients
    await manager.broadcast({
        "type": "workflows_update",
        "data": [workflow.model_dump()]
    })
```

### Connection Manager

The `ConnectionManager` class handles all WebSocket connections:

```python
class ConnectionManager:
    """Manages WebSocket connections and broadcasts."""

    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        """Accept new WebSocket connection."""
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        """Remove disconnected client."""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        """Broadcast message to all connected clients."""
        disconnected = []

        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                disconnected.append(connection)

        # Clean up disconnected clients
        for conn in disconnected:
            self.disconnect(conn)
```

---

## Message Formats

All WebSocket messages follow a standard format:

### Client → Server

Clients primarily listen and send keep-alive pings. No specific message format required.

### Server → Client

All server messages use this format:

```typescript
{
  type: string;      // Message type identifier
  data: any;         // Message payload
  timestamp?: string; // Optional timestamp
}
```

### Message Types

| Type | Description | Data Format |
|------|-------------|-------------|
| `workflows_update` | Active workflow updates | `WorkflowExecution[]` |
| `routes_update` | Route updates | `Route[]` |
| `workflow_history_update` | History updates | `{ workflows, total_count, analytics }` |
| `adw_state_update` | ADW state updates | `{ adw_id, ...state }` |
| `adw_monitor_update` | ADW monitor updates | `{ workflows, summary, last_updated }` |
| `queue_update` | Queue updates | `{ phases, total, paused }` |
| `system_status_update` | System status updates | System status object |
| `webhook_status_update` | Webhook status updates | Webhook status object |

### Example Messages

**Workflows Update:**
```json
{
  "type": "workflows_update",
  "data": [
    {
      "id": "123",
      "name": "Test Workflow",
      "status": "running",
      "start_time": "2025-12-11T10:00:00Z"
    }
  ]
}
```

**Workflow History Update:**
```json
{
  "type": "workflow_history_update",
  "data": {
    "workflows": [
      {
        "id": "123",
        "name": "Completed Workflow",
        "status": "success",
        "duration": 120
      }
    ],
    "total_count": 50,
    "analytics": {
      "success_rate": 95.5,
      "average_duration": 180,
      "recent_failures": 2
    }
  }
}
```

**Queue Update:**
```json
{
  "type": "queue_update",
  "data": {
    "phases": [
      {
        "queue_id": 1,
        "issue_number": "123",
        "phase": "test",
        "status": "ready",
        "priority": 1
      }
    ],
    "total": 5,
    "paused": false
  }
}
```

---

## Connection Management

### Automatic Reconnection

All hooks include automatic reconnection logic:

```typescript
// Configured in useReliableWebSocket
const config = {
  maxReconnectAttempts: 10,       // Max reconnect attempts
  reconnectInterval: 3000,        // 3s between attempts
  backoffMultiplier: 1.5,         // Exponential backoff
  connectionTimeout: 10000,       // 10s connection timeout
};
```

### Connection Quality

Connection quality is determined by message latency:

```typescript
// Good: Messages received within expected timeframe
connectionQuality: 'good'

// Poor: Delayed messages or reconnecting
connectionQuality: 'poor'
```

### Displaying Connection Status

```typescript
const { isConnected, connectionQuality } = useWorkflowsWebSocket();

<div className="connection-status">
  {isConnected ? (
    <span className={connectionQuality === 'good' ? 'text-green-500' : 'text-yellow-500'}>
      {connectionQuality === 'good' ? '●' : '◐'} Live
    </span>
  ) : (
    <span className="text-gray-500">○ Connecting...</span>
  )}
</div>
```

### Manual Reconnection

While automatic reconnection is handled internally, you can monitor reconnection attempts:

```typescript
const { reconnectAttempts, isConnected } = useWorkflowsWebSocket();

{reconnectAttempts > 0 && !isConnected && (
  <div>Reconnecting... (Attempt {reconnectAttempts})</div>
)}
```

---

## Error Handling

### Connection Errors

```typescript
const { isConnected } = useWorkflowsWebSocket();

if (!isConnected) {
  return (
    <LoadingState message="Connecting to real-time updates..." />
  );
}
```

### Message Errors

The hooks handle malformed messages gracefully:

```typescript
// Backend sends either WebSocket format or HTTP format
// Hook handles both automatically

// WebSocket format
{ type: 'workflows_update', data: [...] }

// HTTP fallback format
[...workflows...]
```

### Disconnection Handling

Disconnections are handled automatically:

1. Connection lost
2. Attempt reconnection with exponential backoff
3. Continue up to `maxReconnectAttempts`
4. Fall back to HTTP polling if WebSocket unavailable

---

## Best Practices

### DO ✅

**Use WebSocket for:**
- ✅ Dashboard data that updates frequently
- ✅ Real-time monitoring (workflows, queues, ADWs)
- ✅ Data that changes multiple times per minute
- ✅ Multi-user collaborative data

**Connection Management:**
- ✅ Show connection status indicator
- ✅ Display connection quality
- ✅ Handle `!isConnected` state
- ✅ Use loading states while connecting

**Message Handling:**
- ✅ Accept both WebSocket and HTTP formats
- ✅ Log in development mode only
- ✅ Validate message types
- ✅ Handle null/undefined data

### DON'T ❌

**Avoid WebSocket for:**
- ❌ Static data (use useQuery instead)
- ❌ Data that rarely changes
- ❌ One-time fetches
- ❌ User-specific data that doesn't update externally

**Connection Management:**
- ❌ Manually manage reconnections
- ❌ Block UI while connecting
- ❌ Ignore connection quality
- ❌ Show errors for temporary disconnections

**Broadcasting:**
- ❌ Broadcast on every database write
- ❌ Send high-frequency updates (>1/second)
- ❌ Broadcast unchanged data
- ❌ Include sensitive data in broadcasts

---

## Configuration

### Frontend Configuration

```typescript
// src/config/api.ts
export const apiConfig = {
  websocket: {
    workflows: () => `wss://${API_BASE}/ws/workflows`,
    routes: () => `wss://${API_BASE}/ws/routes`,
    workflowHistory: () => `wss://${API_BASE}/ws/workflow-history`,
    adwState: (adwId: string) => `wss://${API_BASE}/ws/adw-state/${adwId}`,
    adwMonitor: () => `wss://${API_BASE}/ws/adw-monitor`,
    queue: () => `wss://${API_BASE}/ws/queue`,
    systemStatus: () => `wss://${API_BASE}/ws/system-status`,
    webhookStatus: () => `wss://${API_BASE}/ws/webhook-status`,
  },
};
```

### Backend Configuration

```python
# server.py
from fastapi import FastAPI
from app.server.routes.websocket_routes import init_websocket_routes

app = FastAPI()
manager = ConnectionManager()

# Initialize WebSocket routes with dependencies
init_websocket_routes(
    manager,
    get_workflows_data_func,
    get_routes_data_func,
    # ... other data functions
)
```

---

## Testing

### Frontend Testing

```typescript
// Mock WebSocket hook in tests
jest.mock('../hooks/useWebSocket', () => ({
  useWorkflowsWebSocket: () => ({
    workflows: mockWorkflows,
    isConnected: true,
    connectionQuality: 'good',
    lastUpdated: Date.now(),
    reconnectAttempts: 0,
  }),
}));
```

### Backend Testing

```python
# Test WebSocket endpoint
from fastapi.testclient import TestClient

def test_websocket_workflows():
    with TestClient(app).websocket_connect("/ws/workflows") as websocket:
        # Receive initial data
        data = websocket.receive_json()

        assert data["type"] == "workflows_update"
        assert isinstance(data["data"], list)
```

---

## Troubleshooting

### Connection Issues

**Problem:** WebSocket won't connect

**Solutions:**
1. Check backend is running on correct port
2. Verify WebSocket URL in `apiConfig`
3. Check browser console for errors
4. Ensure CORS settings allow WebSocket
5. Try HTTP fallback (automatic in most hooks)

### High Reconnection Attempts

**Problem:** Frequent reconnections

**Solutions:**
1. Check backend stability
2. Verify network connection
3. Increase `reconnectInterval`
4. Check backend error logs
5. Monitor connection quality

### No Updates Received

**Problem:** Connected but not receiving updates

**Solutions:**
1. Verify backend is broadcasting changes
2. Check message type matches expected format
3. Look for errors in browser console
4. Ensure state is actually changing
5. Check WebSocket connection in Network tab

---

## Additional Resources

- **Frontend Patterns:** `docs/patterns/frontend-patterns.md`
- **Backend Patterns:** `docs/patterns/backend-patterns.md`
- **Migration Guide:** `docs/guides/migration-guide-session-19.md`
- **Architecture:** `docs/architecture/session-19-improvements.md`
- **Hook Implementation:** `app/client/src/hooks/useWebSocket.ts`
- **Backend Routes:** `app/server/routes/websocket_routes.py`

---

**WebSocket API Reference - Complete**

This reference covers all WebSocket endpoints, hooks, message formats, and best practices for real-time updates in the tac-webbuilder project.
