# Real-Time Data Architecture Standard

**Version:** 1.0
**Status:** Proposed
**Last Updated:** 2025-12-17
**Owner:** Architecture Team

---

## Table of Contents

1. [Core Principle](#core-principle)
2. [Architecture Overview](#architecture-overview)
3. [Standard Patterns](#standard-patterns)
4. [Event Detection Methods](#event-detection-methods)
5. [Implementation Templates](#implementation-templates)
6. [Decision Trees](#decision-trees)
7. [Exception Cases](#exception-cases)
8. [Migration Checklist](#migration-checklist)
9. [Performance Standards](#performance-standards)
10. [Testing Requirements](#testing-requirements)
11. [Monitoring & Debugging](#monitoring--debugging)
12. [Examples & References](#examples--references)

---

## Core Principle

### The Standard

**All real-time data in the main tac-webbuilder application MUST use event-driven WebSocket updates.**

Polling is:
- ❌ **Prohibited** in the main application UI
- ❌ **Prohibited** in backend periodic watchers
- ✅ **Only acceptable** for external development tools
- ⚠️ **Only acceptable** as emergency fallback (with logging)

### Why Event-Driven?

| Metric | Polling (Old) | Event-Driven (Standard) | Improvement |
|--------|---------------|------------------------|-------------|
| **Latency** | 2-30 seconds | <100ms | **20-300x faster** |
| **Backend CPU** | Continuous loops | Event callbacks only | **-50% load** |
| **Database Load** | Query every N seconds | Query on change only | **-80% queries** |
| **Network Traffic** | Constant updates | Change-based only | **-70% traffic** |
| **Scalability** | Poor (N clients × M queries/sec) | Excellent (broadcast to N clients) | **Linear → Constant** |

### Philosophy

> "Data should push to clients when it changes, not clients pulling to check if it changed."

This inverts the traditional request-response model:
- **Pull (Polling):** "Has anything changed?" every N seconds → Wasteful
- **Push (Event-Driven):** "This changed!" only when needed → Efficient

---

## Architecture Overview

### High-Level Flow

```
┌─────────────────┐
│  Data Source    │ (Database table, file, API action)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Event Detection │ (NOTIFY, file watcher, direct call)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Event Broadcast │ (EventBroadcastManager)
│    Manager      │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   WebSocket     │ (Active connections only)
│   Broadcast     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Frontend Hook   │ (useXWebSocket)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  UI Component   │ (Real-time updates)
└─────────────────┘
```

### Component Responsibilities

| Component | Responsibility | File Location |
|-----------|----------------|---------------|
| **Data Source** | Database table, file, or API | `app/server/db/`, workflows/, etc. |
| **Event Detection** | Detect changes, trigger callbacks | Triggers (SQL), watchers (Python) |
| **Event Broadcast Manager** | Coordinate broadcasts, manage listeners | `app/server/services/event_broadcast_manager.py` |
| **WebSocket Manager** | Manage connections, send messages | `app/server/services/websocket_manager.py` |
| **WebSocket Endpoint** | Accept connections, send initial data | `app/server/routes/websocket_routes.py` |
| **WebSocket Hook** | Subscribe, handle messages, manage state | `app/client/src/hooks/useWebSocket.ts` |
| **UI Component** | Display data, handle user interactions | `app/client/src/components/` |

---

## Standard Patterns

### Pattern 1: Database-Driven Updates

**Use Case:** Data stored in PostgreSQL tables (most common)

**Example:** Planned features, pattern reviews, queue items, workflow history

**Flow:**
```
User Action → Database Mutation → Trigger → NOTIFY → Listener → Broadcast → Frontend
```

**Components:**
1. PostgreSQL trigger function (fires on INSERT/UPDATE/DELETE)
2. PostgreSQL NOTIFY sends event to channel
3. Python listener (asyncpg) receives notification
4. EventBroadcastManager callback fetches fresh data
5. WebSocket broadcast to all connected clients
6. Frontend hook updates React state

**Latency:** <100ms (database commit to frontend update)

---

### Pattern 2: File-Driven Updates

**Use Case:** Data stored in file system (configuration files)

**Example:** Workflow definitions, route configurations

**Flow:**
```
File Change → File Watcher → Callback → Broadcast → Frontend
```

**Components:**
1. Python watchdog observer monitors directory
2. FileSystemEventHandler triggers on file change
3. EventBroadcastManager callback fetches fresh data (debounced)
4. WebSocket broadcast to all connected clients
5. Frontend hook updates React state

**Latency:** <500ms (includes debouncing to avoid rapid-fire updates)

---

### Pattern 3: Action-Driven Updates

**Use Case:** Changes triggered by API actions or external events

**Example:** ADW phase updates, admin actions, webhook events

**Flow:**
```
API Call/Webhook → Action Handler → Direct Broadcast → Frontend
```

**Components:**
1. API endpoint or webhook handler
2. Business logic performs action
3. Direct call to EventBroadcastManager.broadcast_X()
4. WebSocket broadcast to all connected clients
5. Frontend hook updates React state

**Latency:** <50ms (synchronous broadcast after action)

---

## Event Detection Methods

### Method 1: PostgreSQL NOTIFY/LISTEN

**When to Use:**
- ✅ Data in PostgreSQL tables
- ✅ Need transactional guarantees
- ✅ Standard CRUD operations

**Advantages:**
- Transactional (notification only sent on commit)
- Reliable (built into PostgreSQL)
- Efficient (no polling overhead)
- Automatic (triggers fire on any change)

**Disadvantages:**
- PostgreSQL-specific (not portable to other databases)
- Requires migration for triggers
- Payload limited to 8000 bytes (use IDs, not full data)

**Implementation:**

```sql
-- Step 1: Create trigger function
CREATE OR REPLACE FUNCTION notify_table_change()
RETURNS TRIGGER AS $$
BEGIN
  PERFORM pg_notify('table_changed', json_build_object(
    'operation', TG_OP,
    'id', COALESCE(NEW.id, OLD.id),
    'timestamp', now()
  )::text);
  RETURN COALESCE(NEW, OLD);
END;
$$ LANGUAGE plpgsql;

-- Step 2: Create trigger
CREATE TRIGGER table_notify
AFTER INSERT OR UPDATE OR DELETE ON table_name
FOR EACH ROW EXECUTE FUNCTION notify_table_change();
```

```python
# Step 3: Register listener callback
db_listener.register_callback(
    'table_changed',
    event_broadcast_manager._on_table_change
)

# Step 4: Implement callback
async def _on_table_change(self, event_data: dict):
    if len(self.websocket_manager.active_connections) == 0:
        return

    # Fetch fresh data
    data = await fetch_table_data()

    # Broadcast to all clients
    await self.websocket_manager.broadcast({
        "type": "table_update",
        "data": data
    })
```

---

### Method 2: File System Watchers

**When to Use:**
- ✅ Data stored in files (YAML, JSON, etc.)
- ✅ Configuration files
- ✅ Not in database

**Advantages:**
- Works with any file format
- Detects external changes (not just app changes)
- Platform-independent (watchdog library)

**Disadvantages:**
- Can fire multiple events for single change (need debouncing)
- No transactional guarantees
- Higher latency than database triggers

**Implementation:**

```python
# Step 1: Create file watcher
file_watcher = FileWatcher()

# Step 2: Register directory to watch
file_watcher.watch_directory(
    path="/path/to/workflows",
    callback=event_broadcast_manager._on_workflow_file_change
)

# Step 3: Implement callback with debouncing
async def _on_workflow_file_change(self, event):
    # Debounce: wait 500ms to collect multiple rapid changes
    await asyncio.sleep(0.5)

    if len(self.websocket_manager.active_connections) == 0:
        return

    # Fetch fresh data
    workflows = self.workflow_service.get_workflows()

    # Broadcast to all clients
    await self.websocket_manager.broadcast({
        "type": "workflows_update",
        "data": [w.model_dump() for w in workflows]
    })
```

---

### Method 3: Direct Broadcast Calls

**When to Use:**
- ✅ API actions (admin operations)
- ✅ External webhooks
- ✅ Immediate feedback required
- ✅ Data changes not detectable by triggers/watchers

**Advantages:**
- Lowest latency (<50ms)
- Synchronous with action
- Full control over broadcast

**Disadvantages:**
- Must remember to call in every relevant endpoint
- Tightly coupled to business logic
- No automatic detection

**Implementation:**

```python
# In API endpoint
@router.post("/admin/restart-service")
async def restart_service():
    # Perform action
    result = await service_manager.restart()

    # Broadcast updated status IMMEDIATELY
    await event_broadcast_manager.broadcast_system_status()

    return {"status": "restarted", "result": result}

# In EventBroadcastManager
async def broadcast_system_status(self):
    """Public method for direct broadcast calls"""
    if len(self.websocket_manager.active_connections) == 0:
        return

    status = await get_system_status()

    await self.websocket_manager.broadcast({
        "type": "system_status_update",
        "data": status
    })

    logger.info("[EVENT_BROADCAST] Broadcasted system status")
```

---

## Implementation Templates

### Template 1: Database Table Notification

**File:** `app/server/migrations/templates/notify_trigger_template.sql`

```sql
-- ============================================================================
-- Template: Database Notification Trigger
-- ============================================================================
-- Usage:
--   1. Replace [TABLE_NAME] with your table name (e.g., planned_features)
--   2. Replace [CHANNEL_NAME] with notification channel (e.g., planned_features_changed)
--   3. Adjust payload fields as needed
--   4. Add to migration file
-- ============================================================================

CREATE OR REPLACE FUNCTION notify_[TABLE_NAME]_change()
RETURNS TRIGGER AS $$
BEGIN
  -- Send notification with minimal payload (IDs only, not full data)
  PERFORM pg_notify('[CHANNEL_NAME]', json_build_object(
    'operation', TG_OP,              -- INSERT, UPDATE, or DELETE
    'id', COALESCE(NEW.id, OLD.id),  -- Primary key
    'timestamp', now()                -- When it happened
  )::text);
  RETURN COALESCE(NEW, OLD);
END;
$$ LANGUAGE plpgsql;

-- Create trigger (fires after every row change)
CREATE TRIGGER [TABLE_NAME]_notify
AFTER INSERT OR UPDATE OR DELETE ON [TABLE_NAME]
FOR EACH ROW EXECUTE FUNCTION notify_[TABLE_NAME]_change();

-- Test the trigger
-- INSERT INTO [TABLE_NAME] (column1, column2) VALUES ('test', 'data');
-- LISTEN [CHANNEL_NAME];  -- In psql, should see notification
```

---

### Template 2: Backend Event Handler

**File:** `app/server/services/event_broadcast_manager.py`

```python
# ============================================================================
# Template: Event Handler Callback
# ============================================================================
# Usage:
#   1. Replace [DATA_TYPE] with your data type (e.g., PlannedFeature)
#   2. Replace [data_type] with snake_case name (e.g., planned_features)
#   3. Implement data fetching logic
#   4. Register callback in start() method
# ============================================================================

async def _on_[data_type]_change(self, event_data: dict):
    """
    Handle [data_type] database change event.

    Args:
        event_data: Notification payload with operation, id, timestamp
    """
    # Skip if no active WebSocket connections
    if len(self.websocket_manager.active_connections) == 0:
        logger.debug(f"[EVENT_BROADCAST] Skipping [data_type] broadcast - no active connections")
        return

    try:
        # Fetch fresh data from database/service
        # TODO: Replace with actual data fetching logic
        data = await self.[data_type]_service.get_all()

        # Broadcast to all connected clients
        await self.websocket_manager.broadcast({
            "type": "[data_type]_update",
            "data": [item.model_dump() for item in data]
        })

        logger.info(
            f"[EVENT_BROADCAST] Broadcasted [data_type] update to "
            f"{len(self.websocket_manager.active_connections)} clients "
            f"(operation={event_data.get('operation')}, id={event_data.get('id')})"
        )

    except Exception as e:
        logger.error(f"[EVENT_BROADCAST] Error broadcasting [data_type] update: {e}")

# Register callback in start() method:
# self.db_listener.register_callback(
#     '[data_type]_changed',
#     self._on_[data_type]_change
# )
```

---

### Template 3: WebSocket Endpoint

**File:** `app/server/routes/websocket_routes.py`

```python
# ============================================================================
# Template: WebSocket Endpoint
# ============================================================================
# Usage:
#   1. Replace [data_type] with snake_case name (e.g., planned_features)
#   2. Replace [DataType] with PascalCase name (e.g., PlannedFeature)
#   3. Implement initial data fetching
#   4. Add to init_websocket_routes()
# ============================================================================

@router.websocket("/ws/[data-type]")
async def websocket_[data_type](websocket: WebSocket) -> None:
    """
    WebSocket endpoint for real-time [data_type] updates.

    Protocol:
        - Client connects
        - Server sends initial data
        - Server broadcasts updates when data changes
        - Client receives real-time updates
    """
    # Fetch initial data to send on connection
    # TODO: Replace with actual data fetching logic
    data = get_[data_type]_data()

    initial_data = {
        "type": "[data_type]_update",
        "data": data  # Format according to your data structure
    }

    # Handle connection lifecycle
    await _handle_websocket_connection(
        websocket,
        manager,
        initial_data,
        "[data_type]"  # Context for logging
    )
```

---

### Template 4: Frontend WebSocket Hook

**File:** `app/client/src/hooks/useWebSocket.ts`

```typescript
// ============================================================================
// Template: Frontend WebSocket Hook
// ============================================================================
// Usage:
//   1. Replace [DataType] with your TypeScript type (e.g., PlannedFeature)
//   2. Replace [data-type] with kebab-case name (e.g., planned-features)
//   3. Implement message handling logic
//   4. Export and use in components
// ============================================================================

interface [DataType]WebSocketMessage {
  type: '[data_type]_update';
  data: {
    // TODO: Define your data structure
    items: [DataType][];
    // ... other fields
  };
}

export function use[DataType]WebSocket() {
  const [data, setData] = useState<[DataType][]>([]);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);

  const wsUrl = apiConfig.websocket.[dataType]();

  const connectionState = useReliableWebSocket<
    { items: [DataType][] },
    [DataType]WebSocketMessage
  >({
    url: wsUrl,
    queryKey: ['[data-type]'],
    queryFn: async () => {
      // Fallback HTTP fetch for initial connection
      // TODO: Replace with actual API client call
      const response = await fetch[DataType]();
      return { items: response };
    },
    onMessage: (message: any) => {
      // Handle WebSocket message
      if (message.type === '[data_type]_update') {
        setData(message.data.items);
        setLastUpdated(new Date());
        if (DEBUG_WS) {
          console.log('[WS] Received [data_type] update:', message.data.items.length, 'items');
        }
      }
    },
  });

  return {
    data,
    lastUpdated,
    isConnected: connectionState.isConnected,
    connectionQuality: connectionState.connectionQuality,
    reconnectAttempts: connectionState.reconnectAttempts,
  };
}
```

---

### Template 5: Component Usage

**File:** `app/client/src/components/[DataType]Panel.tsx`

```typescript
// ============================================================================
// Template: Component Using WebSocket Hook
// ============================================================================
// Usage:
//   1. Import WebSocket hook
//   2. Remove React Query polling
//   3. Use WebSocket data directly
// ============================================================================

import { use[DataType]WebSocket } from '../hooks/useWebSocket';

export function [DataType]Panel() {
  // ✅ CORRECT: Use WebSocket hook
  const {
    data,
    isConnected,
    connectionQuality,
    lastUpdated,
  } = use[DataType]WebSocket();

  // ❌ INCORRECT: Do NOT use React Query polling
  // const { data } = useQuery({
  //   queryKey: ['data'],
  //   queryFn: fetchData,
  //   refetchInterval: 30000,  // ❌ NO POLLING!
  // });

  // Loading state
  const isLoading = !data || data.length === 0;

  // Connection status indicator (optional)
  const connectionStatus = isConnected ? '🟢 Live' : '🔴 Disconnected';

  if (isLoading) {
    return <LoadingState message="Loading data..." />;
  }

  return (
    <div>
      <div className="connection-status">{connectionStatus}</div>
      {data.map(item => (
        <ItemCard key={item.id} item={item} />
      ))}
    </div>
  );
}
```

---

## Decision Trees

### Decision Tree 1: Choosing Event Detection Method

```
Adding Real-Time Data to Frontend?
│
├─ Where is the data stored?
│  │
│  ├─ PostgreSQL Database
│  │  └─ Use: PostgreSQL NOTIFY/LISTEN (Method 1)
│  │     Files: migrations/*.sql, event_broadcast_manager.py
│  │
│  ├─ File System (YAML, JSON, etc.)
│  │  └─ Use: File System Watcher (Method 2)
│  │     Files: file_watcher.py, event_broadcast_manager.py
│  │
│  └─ API Action / External Event
│     └─ Use: Direct Broadcast Call (Method 3)
│        Files: route handler → event_broadcast_manager.broadcast_X()
│
└─ Not sure / Multiple sources?
   └─ Consult: Architecture team or review existing patterns
```

### Decision Tree 2: Is Polling Acceptable?

```
Want to Add Polling?
│
├─ Is this part of the main application UI?
│  │
│  ├─ YES (main app, dashboard, panels)
│  │  └─ ❌ REJECTED - Use event-driven WebSocket instead
│  │
│  └─ NO (external tool, script, automation)
│     │
│     ├─ Is it a development/monitoring tool?
│     │  └─ ✅ ACCEPTABLE - Document as external tool
│     │
│     ├─ Is it an automation trigger?
│     │  │
│     │  ├─ Can webhooks be used instead?
│     │  │  ├─ YES → Use webhooks (better)
│     │  │  └─ NO → ✅ ACCEPTABLE - Document reasoning
│     │  │
│     │  └─ Is it emergency fallback?
│     │     └─ ✅ ACCEPTABLE - Log as warning, monitor frequency
│     │
│     └─ Other use case?
│        └─ ⚠️ REVIEW REQUIRED - Consult architecture team
│
└─ Data changes infrequently (>1 hour)?
   └─ Consider: Manual refresh button instead of polling
```

### Decision Tree 3: Broadcast Optimization

```
Implementing Event Broadcast?
│
├─ How often does this data change?
│  │
│  ├─ Very Frequently (>10/sec)
│  │  └─ Add: Debouncing (500ms) + state comparison
│  │     Reason: Avoid overwhelming clients
│  │
│  ├─ Moderately (1-10/sec)
│  │  └─ Add: State comparison only
│  │     Reason: Only broadcast actual changes
│  │
│  └─ Infrequently (<1/sec)
│     └─ Add: Nothing - broadcast all changes
│        Reason: Overhead negligible
│
├─ How large is the data payload?
│  │
│  ├─ Large (>100KB)
│  │  └─ Consider: Incremental updates or pagination
│  │     Warning: Large broadcasts can cause latency
│  │
│  └─ Small (<100KB)
│     └─ OK: Broadcast full data
│
└─ How many clients will subscribe?
   │
   ├─ Many (>50 concurrent)
   │  └─ Add: Connection count check, broadcast batching
   │     Reason: Reduce broadcast overhead
   │
   └─ Few (<50 concurrent)
      └─ OK: Standard broadcast pattern
```

---

## Exception Cases

### Exception 1: External Development Tools

**Examples:**
- `adws/monitor_adw_tokens.py` - Token usage monitoring
- Custom scripts for debugging or analysis
- One-off administrative utilities

**Ruling:** ✅ **Polling ACCEPTABLE**

**Requirements:**
- Must NOT be part of main application
- Must be in `/adws/` or `/scripts/` directories
- Must document that it's a development tool
- Should have `--watch` flag (opt-in polling)

**Example:**
```python
# adws/monitor_something.py
"""
Development tool for monitoring X in real-time.
NOT part of main application - uses polling.
"""

if args.watch:
    while True:
        display_data()
        time.sleep(10)  # Polling acceptable here
```

---

### Exception 2: External Automation Triggers

**Examples:**
- `adws/adw_triggers/trigger_cron.py` - GitHub issue polling
- CI/CD pipeline triggers
- External service monitoring

**Ruling:** ⚠️ **Polling ACCEPTABLE** (if webhooks not viable)

**Requirements:**
- Must document why webhooks aren't used
- Must be in `/adws/adw_triggers/` or similar
- Should have configurable interval (env var)
- Must log polling activity

**Justification Needed:**
```markdown
# Why Polling Instead of Webhooks?

**Service:** GitHub Issues
**Polling Interval:** 20 seconds
**Reason:** GitHub webhooks require public endpoint + ngrok setup.
          For development simplicity, polling is easier.
**Future:** Could migrate to webhooks for production deployment.
```

---

### Exception 3: Emergency Fallback

**Examples:**
- WebSocket connection fails after max retries
- Database NOTIFY/LISTEN connection lost
- Temporary degraded mode during incidents

**Ruling:** ⚠️ **Polling ACCEPTABLE** (with logging)

**Requirements:**
- Must log as WARNING when fallback activated
- Must attempt to restore event-driven connection
- Must have max fallback duration (5 minutes)
- Should alert monitoring system

**Example:**
```typescript
const connectionState = useReliableWebSocket({
  url: wsUrl,
  maxReconnectAttempts: 10,
  onFallback: () => {
    console.warn('[WS] Fallback to polling - WebSocket failed');
    // Alert monitoring
    sendAlert('websocket_fallback_activated');
  }
});

// After 5 minutes, force page reload to restore WebSocket
if (connectionState.inFallbackMode && fallbackDuration > 5 * 60 * 1000) {
  window.location.reload();
}
```

---

### Exception 4: Data Changes Infrequently

**Examples:**
- System configuration (changed monthly)
- User preferences (changed per session)
- Static reference data (rarely updated)

**Ruling:** ✅ **Manual Refresh ACCEPTABLE** (better than polling)

**Requirements:**
- Provide clear "Refresh" button
- Show last updated timestamp
- Optional: WebSocket for live updates (preferred)

**Example:**
```typescript
// ACCEPTABLE: Manual refresh for infrequent data
const { data, refetch } = useQuery({
  queryKey: ['config'],
  queryFn: fetchConfig,
  staleTime: Infinity,  // Never auto-refetch
});

return (
  <div>
    <button onClick={() => refetch()}>Refresh Config</button>
    <div>Last updated: {data.timestamp}</div>
  </div>
);
```

**Better (if viable):**
```typescript
// PREFERRED: Still use WebSocket even for infrequent changes
const { config, lastUpdated } = useConfigWebSocket();

return (
  <div>
    <div>Last updated: {lastUpdated}</div>
    {/* Automatically updates when config changes */}
  </div>
);
```

---

## Migration Checklist

### For Adding New Real-Time Data

Use this checklist when adding new real-time data to the application:

#### Backend Setup

- [ ] **Choose event detection method** (database trigger / file watcher / direct call)
- [ ] **Create database trigger** (if using PostgreSQL NOTIFY)
  - [ ] Create trigger function (SQL)
  - [ ] Create trigger (SQL)
  - [ ] Add to migration file
  - [ ] Test trigger fires on INSERT/UPDATE/DELETE
- [ ] **Register event listener** (in EventBroadcastManager)
  - [ ] Add callback method `_on_[data_type]_change()`
  - [ ] Fetch fresh data in callback
  - [ ] Broadcast to WebSocket clients
  - [ ] Add logging
  - [ ] Register callback in `start()` method
- [ ] **Create WebSocket endpoint** (in websocket_routes.py)
  - [ ] Add `@router.websocket("/ws/[data-type]")` endpoint
  - [ ] Fetch and send initial data
  - [ ] Use `_handle_websocket_connection` helper
- [ ] **Update websocket route initialization** (in server.py)
  - [ ] Add data fetcher function parameter
  - [ ] Wire up endpoint in `init_websocket_routes()`

#### Frontend Setup

- [ ] **Create WebSocket hook** (in useWebSocket.ts)
  - [ ] Define message type interface
  - [ ] Implement `use[DataType]WebSocket()` hook
  - [ ] Add state management (useState)
  - [ ] Configure useReliableWebSocket
  - [ ] Handle incoming messages
  - [ ] Return data + connection state
- [ ] **Add WebSocket URL config** (in config/api.ts)
  - [ ] Add `[dataType]: () => string` to apiConfig.websocket
- [ ] **Update component** (in components/)
  - [ ] Import and use WebSocket hook
  - [ ] Remove React Query polling (if exists)
  - [ ] Add connection status indicator (optional)
  - [ ] Handle loading/error states

#### Testing

- [ ] **Unit tests**
  - [ ] Test database trigger (insert/update/delete)
  - [ ] Test event listener callback
  - [ ] Test WebSocket message format
- [ ] **Integration tests**
  - [ ] Test end-to-end flow (data change → frontend update)
  - [ ] Test WebSocket reconnection
  - [ ] Test multiple concurrent clients
- [ ] **Performance tests**
  - [ ] Measure latency (target: <100ms for database, <500ms for files)
  - [ ] Test with 10+ concurrent connections
  - [ ] Verify no memory leaks

#### Documentation

- [ ] **Update this document**
  - [ ] Add to "Examples & References" section
  - [ ] Document any unique patterns or edge cases
- [ ] **Add code comments**
  - [ ] Document trigger purpose
  - [ ] Document callback logic
  - [ ] Document message format
- [ ] **Update API docs** (if using OpenAPI/Swagger)

---

### For Migrating from Polling to Event-Driven

Use this checklist when migrating existing polling code:

#### Analysis

- [ ] **Identify polling instances**
  - [ ] Frontend: Search for `refetchInterval` in components
  - [ ] Backend: Search for `while True: sleep()` patterns
  - [ ] Document current polling intervals
  - [ ] Measure current latency

#### Backend Migration

- [ ] **Determine event detection method**
  - [ ] Database table? → Use PostgreSQL NOTIFY
  - [ ] File-based? → Use file watcher
  - [ ] API action? → Use direct broadcast
- [ ] **Implement event detection** (see "Backend Setup" above)
- [ ] **Test event-driven broadcasting**
  - [ ] Verify events fire on data changes
  - [ ] Verify broadcasts reach clients
  - [ ] Compare latency (should be <100ms vs seconds)
- [ ] **Remove old polling code**
  - [ ] Remove periodic watcher methods
  - [ ] Remove from BackgroundTaskManager (if exists)
  - [ ] Remove unused imports

#### Frontend Migration

- [ ] **Create or use existing WebSocket hook**
- [ ] **Update component**
  - [ ] Replace `useQuery` with `use[DataType]WebSocket`
  - [ ] Remove `refetchInterval` configuration
  - [ ] Test real-time updates work
- [ ] **Remove old polling code**
  - [ ] Remove React Query polling config
  - [ ] Remove unused interval constants
  - [ ] Clean up imports

#### Verification

- [ ] **Functional testing**
  - [ ] Verify data updates in real-time
  - [ ] Test edge cases (no connections, rapid changes)
  - [ ] Test error scenarios (connection loss)
- [ ] **Performance testing**
  - [ ] Measure new latency (should be <100ms)
  - [ ] Compare before/after metrics
  - [ ] Monitor resource usage (CPU, memory)
- [ ] **User acceptance**
  - [ ] Verify UI responsiveness improved
  - [ ] Check for any regression bugs

#### Cleanup

- [ ] **Remove deprecated code**
  - [ ] Delete unused polling utilities
  - [ ] Remove polling configuration constants
  - [ ] Clean up unused dependencies
- [ ] **Update documentation**
  - [ ] Mark migration complete
  - [ ] Document performance improvements
  - [ ] Update architecture diagrams

---

## Performance Standards

### Latency Targets

| Event Source | Target Latency | Acceptable Latency | Failing |
|--------------|----------------|-------------------|---------|
| **Database Change** | <50ms | <100ms | >500ms |
| **File Change** | <200ms | <500ms | >2s |
| **Direct Broadcast** | <20ms | <50ms | >100ms |
| **End-to-End** | <100ms | <500ms | >2s |

**How to Measure:**

```python
# Backend logging
start = time.time()
await websocket_manager.broadcast(message)
latency_ms = (time.time() - start) * 1000
logger.info(f"Broadcast latency: {latency_ms:.2f}ms")
```

```typescript
// Frontend logging
const handleMessage = (message) => {
  const receivedAt = Date.now();
  const sentAt = new Date(message.timestamp).getTime();
  const latency = receivedAt - sentAt;
  console.log(`WebSocket latency: ${latency}ms`);
};
```

### Resource Usage Targets

| Metric | Target | Warning | Critical |
|--------|--------|---------|----------|
| **Backend CPU** | <20% avg | <50% avg | >80% avg |
| **Backend Memory** | <500MB | <1GB | >2GB |
| **Database Connections** | <5 | <10 | >20 |
| **WebSocket Connections** | <100 | <200 | >500 |
| **Broadcast Frequency** | <10/sec per channel | <50/sec | >100/sec |

### Scalability Targets

| Concurrent Users | Max Latency | Broadcast Efficiency |
|------------------|-------------|---------------------|
| 1-10 | <50ms | 100% (all receive) |
| 10-50 | <100ms | >99% |
| 50-100 | <200ms | >95% |
| 100+ | <500ms | >90% |

**If targets not met:**
1. Add broadcast batching (group updates)
2. Implement selective broadcasting (subscriptions)
3. Add edge caching for static data
4. Consider horizontal scaling (multiple servers)

---

## Testing Requirements

### Unit Tests

**Required for Each Implementation:**

```python
# Test: Database trigger fires on INSERT/UPDATE/DELETE
def test_trigger_fires_on_insert():
    # Insert data
    db.execute("INSERT INTO table (col) VALUES ('test')")

    # Assert notification sent
    assert notification_received('table_changed')

# Test: Event callback fetches and broadcasts
async def test_event_callback_broadcasts():
    # Trigger event
    await event_manager._on_table_change({'id': 1})

    # Assert broadcast called
    assert websocket_manager.broadcast.called
    assert websocket_manager.broadcast.call_args[0][0]['type'] == 'table_update'

# Test: WebSocket endpoint sends initial data
async def test_websocket_endpoint_initial_data():
    # Connect to WebSocket
    async with websocket_client('/ws/data') as ws:
        message = await ws.receive_json()

    # Assert initial data sent
    assert message['type'] == 'data_update'
    assert 'data' in message
```

```typescript
// Test: WebSocket hook updates state
test('WebSocket hook updates on message', async () => {
  const { result } = renderHook(() => useDataWebSocket());

  // Send mock message
  await act(async () => {
    mockWebSocket.sendMessage({
      type: 'data_update',
      data: [{ id: 1, name: 'test' }]
    });
  });

  // Assert state updated
  expect(result.current.data).toHaveLength(1);
  expect(result.current.data[0].name).toBe('test');
});
```

### Integration Tests

**End-to-End Flow:**

```python
# Test: Database change triggers frontend update
async def test_end_to_end_update():
    # Connect WebSocket client
    async with websocket_client('/ws/data') as ws:
        # Get initial data
        initial = await ws.receive_json()

        # Make database change
        db.execute("INSERT INTO table (name) VALUES ('new')")

        # Wait for broadcast
        update = await ws.receive_json(timeout=1.0)

        # Assert update received
        assert update['type'] == 'data_update'
        assert any(item['name'] == 'new' for item in update['data'])
```

### Performance Tests

**Latency Measurement:**

```python
# Test: Latency under load
async def test_broadcast_latency():
    # Connect 10 clients
    clients = [websocket_client('/ws/data') for _ in range(10)]

    # Trigger event
    start = time.time()
    db.execute("INSERT INTO table (name) VALUES ('test')")

    # Wait for all clients to receive
    await asyncio.gather(*[
        client.receive_json(timeout=1.0)
        for client in clients
    ])

    latency = (time.time() - start) * 1000

    # Assert latency acceptable
    assert latency < 100, f"Latency {latency}ms exceeds 100ms target"
```

---

## Monitoring & Debugging

### Logging Standards

**All event-driven components MUST log:**

```python
# Event detection
logger.info(f"[EVENT_DETECTION] {channel} event received: {payload}")

# Broadcasting
logger.info(
    f"[EVENT_BROADCAST] Broadcasted {data_type} update to "
    f"{num_clients} clients (operation={op}, id={id})"
)

# WebSocket connections
logger.info(f"[WS] Client connected: {client_id} ({total_clients} total)")
logger.info(f"[WS] Client disconnected: {client_id} ({total_clients} remaining)")
```

### Metrics to Track

**Backend Metrics:**
- Event detection rate (events/sec by channel)
- Broadcast rate (broadcasts/sec by type)
- Active WebSocket connections (count)
- Broadcast latency (ms, p50/p95/p99)
- Error rate (errors/min)

**Frontend Metrics:**
- WebSocket connection status (connected/disconnected)
- Message receive rate (messages/sec)
- Reconnection attempts (count)
- UI update latency (ms from message to render)

### Debug Tools

**PostgreSQL NOTIFY Testing:**

```bash
# Listen for notifications in psql
psql -d tac_webbuilder
LISTEN table_changed;

# In another terminal, trigger change
psql -d tac_webbuilder -c "INSERT INTO table (name) VALUES ('test');"

# First terminal should show: Asynchronous notification "table_changed" received
```

**WebSocket Testing:**

```bash
# Connect to WebSocket endpoint
websocat ws://localhost:8002/ws/data

# Should receive initial data and live updates
```

**Frontend Debug Mode:**

```typescript
// Enable WebSocket debug logging
const DEBUG_WS = true;  // In useWebSocket.ts

// View logs in browser console
// [WS] Received data_update: 10 items
```

### Common Issues & Solutions

| Issue | Symptom | Solution |
|-------|---------|----------|
| **Trigger not firing** | No broadcasts after DB change | Check trigger exists: `\dft` in psql |
| **Notification not received** | Trigger fires but callback not called | Check listener registered for correct channel |
| **Broadcast not sent** | Callback executes but clients don't update | Check active connections count |
| **Frontend not updating** | Broadcast sent but UI stale | Check message type matches hook |
| **High latency** | Updates delayed >1 second | Check for debouncing, large payloads, connection count |
| **Connection drops** | Frequent reconnections | Check WebSocket timeout settings, network stability |

---

## Examples & References

### Successful Implementations

#### Example 1: ADW Monitor (Event-Driven via HTTP POST)

**Status:** ✅ Production (Session 19)
**Pattern:** Action-Driven Updates (Method 3)
**Latency:** <50ms (was 500ms with polling)

**Implementation:**
- ADW orchestrator POSTs to `/api/v1/adw-phase-update` after each phase
- Endpoint calls `event_broadcast_manager.broadcast_adw_monitor()`
- WebSocket broadcasts to all clients
- Frontend updates instantly

**Files:**
- Backend: `app/server/routes/adw_routes.py` (POST endpoint)
- Broadcasting: `app/server/services/event_broadcast_manager.py`
- Frontend: `app/client/src/hooks/useWebSocket.ts` (useADWMonitorWebSocket)

**Lesson Learned:** Direct broadcasts are fastest but require discipline (easy to forget to call).

---

#### Example 2: Workflow History (WebSocket Migration)

**Status:** ✅ Production (Sessions 15-16)
**Pattern:** Currently polling (10s), will migrate to database triggers
**Current Latency:** ~5 seconds (10s poll interval ÷ 2)
**Target Latency:** <100ms with triggers

**Current Implementation (to be replaced):**
```python
# CURRENT (polling)
async def watch_workflow_history(self):
    while True:
        history_data, did_sync = workflow_service.get_workflow_history_with_cache()
        if did_sync:
            await websocket_manager.broadcast(...)
        await asyncio.sleep(10)  # ❌ Polling
```

**Target Implementation (event-driven):**
```sql
-- Add trigger to workflow_history table
CREATE TRIGGER workflow_history_notify
AFTER INSERT OR UPDATE ON workflow_history
FOR EACH ROW EXECUTE FUNCTION notify_workflow_history_change();
```

```python
# Event-driven callback
async def _on_workflow_history_change(self, event_data):
    history_data = workflow_service.get_workflow_history()
    await websocket_manager.broadcast({
        "type": "workflow_history_update",
        "data": history_data
    })  # ✅ Event-driven
```

---

#### Example 3: Planned Features (WebSocket Migration)

**Status:** 🟡 Partial (WebSocket infrastructure exists, but still using React Query polling)
**Pattern:** Database-Driven Updates (Method 1)
**Current:** Frontend polls every 5-10 minutes
**Target:** PostgreSQL triggers + WebSocket

**Files to Change:**
- Add trigger: `app/server/migrations/add_planned_features_trigger.sql`
- Backend: `app/server/services/event_broadcast_manager.py` (callback exists in `/ws/planned-features` endpoint)
- Frontend: `app/client/src/components/PlansPanel.tsx` (remove lines 509-525, keep WebSocket hook)

**Current Code (to remove):**
```typescript
// ❌ Remove this polling code
const { data: features } = useQuery({
  queryKey: ['planned-features'],
  queryFn: () => plannedFeaturesClient.getAll({ limit: 200 }),
  refetchInterval: 5 * 60 * 1000,  // ❌ Polling every 5 minutes
});
```

**Keep this WebSocket code:**
```typescript
// ✅ Already exists, just remove the polling above
const { features, stats, isConnected } = usePlannedFeaturesWebSocket();
```

---

### Anti-Patterns to Avoid

#### Anti-Pattern 1: Polling in Component

```typescript
// ❌ BAD: Polling with setInterval in component
useEffect(() => {
  const interval = setInterval(async () => {
    const data = await fetchData();
    setData(data);
  }, 30000);

  return () => clearInterval(interval);
}, []);
```

**Why Bad:**
- Duplicates backend polling (double the requests)
- No coordination (all clients poll independently)
- Continues polling even when data hasn't changed

**Correct:**
```typescript
// ✅ GOOD: Use WebSocket hook
const { data, isConnected } = useDataWebSocket();
```

---

#### Anti-Pattern 2: Polling in Backend Without State Comparison

```python
# ❌ BAD: Broadcast every N seconds regardless of changes
async def watch_data(self):
    while True:
        data = get_data()
        await websocket_manager.broadcast({
            "type": "data_update",
            "data": data
        })  # Broadcasts even if nothing changed!
        await asyncio.sleep(10)
```

**Why Bad:**
- Wastes bandwidth (broadcasting unchanged data)
- Causes unnecessary frontend re-renders
- Scales poorly (N clients × M broadcasts/sec)

**Correct (if must use polling):**
```python
# ✅ BETTER: Compare state before broadcasting
async def watch_data(self):
    last_state = None
    while True:
        data = get_data()
        current_state = json.dumps(data, sort_keys=True)

        if current_state != last_state:
            await websocket_manager.broadcast({
                "type": "data_update",
                "data": data
            })
            last_state = current_state

        await asyncio.sleep(10)
```

**Best:**
```python
# ✅ BEST: Use event-driven (no polling)
async def _on_data_change(self, event_data):
    data = get_data()
    await websocket_manager.broadcast({
        "type": "data_update",
        "data": data
    })
```

---

#### Anti-Pattern 3: Multiple Polling Sources

```python
# ❌ BAD: Component polls AND backend polls
# Backend
async def watch_data():
    while True:
        await broadcast_data()
        await asyncio.sleep(10)

# Frontend
useQuery({
  queryFn: fetchData,
  refetchInterval: 30000  # Also polling!
})
```

**Why Bad:**
- Double the database queries
- Inconsistent update frequencies
- Race conditions (which update wins?)

**Correct:**
```python
# ✅ GOOD: Backend broadcasts, frontend subscribes
# Backend
async def _on_data_change(event):
    await broadcast_data()

# Frontend
const { data } = useDataWebSocket();  // No polling!
```

---

### Migration Stories

#### Migration 1: Queue Panel (Session 16)

**Before:** HTTP polling every 3 seconds → 20 requests/minute
**After:** WebSocket with 2s backend watcher → 0 HTTP requests, ~0.5 broadcasts/sec
**Improvement:** 100% reduction in HTTP traffic

**Challenges:**
- Queue data not in database (in-memory state)
- Solution: File watcher + direct broadcast on queue mutations

**Code Change:**
```python
# Before
# Frontend polled /api/v1/queue every 3 seconds

# After
# Backend watches queue state changes → broadcasts via WebSocket
# Frontend subscribes to /ws/queue
```

---

## Approval & Review

**Document Status:** 📋 **DRAFT - Pending Approval**

**Review Checklist:**
- [ ] Architecture team review
- [ ] Performance standards validated
- [ ] Templates tested with real implementation
- [ ] Exception cases documented
- [ ] Decision trees clear and complete

**Approval:**
- [ ] Architecture Lead: ___________________
- [ ] Backend Lead: ___________________
- [ ] Frontend Lead: ___________________
- [ ] Date: ___________________

**Revision History:**
- v1.0 (2025-12-17): Initial draft

---

## Next Steps

1. **Review this document** - Gather feedback from team
2. **Pilot implementation** - Test with one data type (planned_features)
3. **Iterate on templates** - Refine based on pilot experience
4. **Approve standard** - Finalize and publish
5. **Begin migration** - Roll out to all polling instances
6. **Monitor results** - Track performance improvements

---

## Questions & Feedback

**Open Questions:**
1. Should we add automatic fallback to polling if WebSocket fails for >5 minutes?
2. What's the max broadcast frequency before we need rate limiting?
3. Should we implement selective subscriptions (clients choose which channels)?

**Feedback Wanted:**
- Are the templates clear and complete?
- Are the decision trees helpful?
- What other exception cases should we document?
- What monitoring/debugging tools would help?

---

**Document Maintainer:** Architecture Team
**Last Updated:** 2025-12-17
**Next Review:** After pilot implementation
