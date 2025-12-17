# Implementation Plan: Eliminate Polling - Move to Event-Driven Architecture

**Goal:** Replace ALL polling with event-driven, live WebSocket updates for real-time information only.

**Status:** Planning Phase
**Created:** 2025-12-17

---

## Executive Summary

Currently, the application uses a mix of:
- **Frontend polling** (React Query: 30s-10min intervals)
- **Backend periodic watchers** (2-10s intervals that poll then broadcast via WebSocket)
- **Partial WebSocket usage** (infrastructure exists but not fully utilized)

**Target Architecture:**
- **Zero frontend polling** - WebSocket subscriptions only
- **Zero backend periodic watchers** - Event-driven broadcasts only
- **PostgreSQL NOTIFY/LISTEN** - Database change detection triggers broadcasts
- **True real-time updates** - Sub-second latency for all data changes

---

## Current State Analysis

### Frontend Polling (React Query)

| Component | Data | Interval | Status | WebSocket Hook Exists? |
|-----------|------|----------|--------|------------------------|
| PlansPanel | Features/Stats | 5-10 min | ❌ Polling | ✅ Yes (`usePlannedFeaturesWebSocket`) |
| ReviewPanel | Pattern Reviews | 30s | ❌ Polling | ❌ No |
| ContextReviewPanel | Analysis Status | 3s (conditional) | ❌ Polling | ❌ No |

### Backend Periodic Watchers

| Watcher | Interval | Broadcasts To | Event-Driven? |
|---------|----------|---------------|---------------|
| `watch_workflows()` | 10s | `/ws/workflows` | ❌ No |
| `watch_routes()` | 10s | `/ws/routes` | ❌ No |
| `watch_workflow_history()` | 10s | `/ws/workflow-history` | ❌ No |
| `watch_queue()` | 2s | `/ws/queue` | ❌ No |
| ~~`watch_adw_monitor()`~~ | REMOVED | `/ws/adw-monitor` | ✅ Yes (Event-driven via HTTP POST) |

**Note:** ADW monitor was successfully converted to event-driven in Session 19 - serves as reference implementation.

### WebSocket Endpoints (Existing)

| Endpoint | Broadcasting? | Frontend Hook | Usage |
|----------|---------------|---------------|-------|
| `/ws/workflows` | ✅ Yes (10s poll) | ✅ `useWorkflowsWebSocket` | ✅ Active |
| `/ws/routes` | ✅ Yes (10s poll) | ✅ `useRoutesWebSocket` | ✅ Active |
| `/ws/workflow-history` | ✅ Yes (10s poll) | ✅ `useWorkflowHistoryWebSocket` | ✅ Active |
| `/ws/queue` | ✅ Yes (2s poll) | ✅ `useQueueWebSocket` | ✅ Active |
| `/ws/adw-monitor` | ✅ Yes (event-driven) | ✅ `useADWMonitorWebSocket` | ✅ Active |
| `/ws/adw-state/{id}` | ✅ Yes (event-driven) | ✅ `useADWStateWebSocket` | ✅ Active |
| `/ws/system-status` | ❌ No | ✅ `useSystemStatusWebSocket` | ⚠️ Partial |
| `/ws/webhook-status` | ❌ No | ✅ `useWebhookStatusWebSocket` | ⚠️ Partial |
| `/ws/planned-features` | ❌ No | ✅ `usePlannedFeaturesWebSocket` | ❌ Not used |

---

## Architecture Design: Event-Driven System

### Core Principle

**Replace periodic polling with event-driven broadcasts:**

```
OLD (Polling):
Database → Backend polls every 2-10s → WebSocket broadcast → Frontend

NEW (Event-Driven):
Database → PostgreSQL NOTIFY → Backend listens → WebSocket broadcast → Frontend
```

### Key Technologies

1. **PostgreSQL NOTIFY/LISTEN**
   - Database-level event notification system
   - Triggers send notifications on INSERT/UPDATE/DELETE
   - Backend listens for notifications and broadcasts via WebSocket

2. **Event-Driven Broadcasting**
   - Replace `while True: sleep(N)` loops
   - Use event callbacks: when data changes → broadcast immediately
   - Zero latency between change and notification

3. **WebSocket-Only Frontend**
   - Remove all React Query polling (`refetchInterval`)
   - Use WebSocket hooks exclusively
   - Automatic reconnection and error handling

---

## Implementation Plan

### Phase 1: Database Event Notification System

**Goal:** Create PostgreSQL NOTIFY/LISTEN infrastructure for change detection

#### 1.1 Create Database Triggers

```sql
-- File: app/server/migrations/add_notify_triggers.sql

-- Planned Features Table
CREATE OR REPLACE FUNCTION notify_planned_features_change()
RETURNS TRIGGER AS $$
BEGIN
  PERFORM pg_notify('planned_features_changed', json_build_object(
    'operation', TG_OP,
    'id', COALESCE(NEW.id, OLD.id),
    'timestamp', now()
  )::text);
  RETURN COALESCE(NEW, OLD);
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER planned_features_notify
AFTER INSERT OR UPDATE OR DELETE ON planned_features
FOR EACH ROW EXECUTE FUNCTION notify_planned_features_change();

-- Pattern Review Table
CREATE OR REPLACE FUNCTION notify_pattern_review_change()
RETURNS TRIGGER AS $$
BEGIN
  PERFORM pg_notify('pattern_review_changed', json_build_object(
    'operation', TG_OP,
    'pattern_id', COALESCE(NEW.pattern_id, OLD.pattern_id),
    'timestamp', now()
  )::text);
  RETURN COALESCE(NEW, OLD);
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER pattern_review_notify
AFTER INSERT OR UPDATE OR DELETE ON pattern_review
FOR EACH ROW EXECUTE FUNCTION notify_pattern_review_change();

-- Workflow History Table
CREATE OR REPLACE FUNCTION notify_workflow_history_change()
RETURNS TRIGGER AS $$
BEGIN
  PERFORM pg_notify('workflow_history_changed', json_build_object(
    'operation', TG_OP,
    'workflow_id', COALESCE(NEW.workflow_id, OLD.workflow_id),
    'timestamp', now()
  )::text);
  RETURN COALESCE(NEW, OLD);
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER workflow_history_notify
AFTER INSERT OR UPDATE OR DELETE ON workflow_history
FOR EACH ROW EXECUTE FUNCTION notify_workflow_history_change();

-- Phase Queue Table
CREATE OR REPLACE FUNCTION notify_phase_queue_change()
RETURNS TRIGGER AS $$
BEGIN
  PERFORM pg_notify('phase_queue_changed', json_build_object(
    'operation', TG_OP,
    'queue_id', COALESCE(NEW.queue_id, OLD.queue_id),
    'timestamp', now()
  )::text);
  RETURN COALESCE(NEW, OLD);
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER phase_queue_notify
AFTER INSERT OR UPDATE OR DELETE ON phase_queue
FOR EACH ROW EXECUTE FUNCTION notify_phase_queue_change();

-- Context Analysis Table (for ContextReviewPanel)
CREATE OR REPLACE FUNCTION notify_context_analysis_change()
RETURNS TRIGGER AS $$
BEGIN
  PERFORM pg_notify('context_analysis_changed', json_build_object(
    'operation', TG_OP,
    'review_id', COALESCE(NEW.id, OLD.id),
    'status', NEW.status,
    'timestamp', now()
  )::text);
  RETURN COALESCE(NEW, OLD);
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER context_analysis_notify
AFTER INSERT OR UPDATE ON context_analysis
FOR EACH ROW EXECUTE FUNCTION notify_context_analysis_change();
```

#### 1.2 Create Python Database Listener Service

```python
# File: app/server/services/db_event_listener.py

import asyncio
import json
import logging
from typing import Callable, Dict
import asyncpg

logger = logging.getLogger(__name__)


class DatabaseEventListener:
    """
    Listens for PostgreSQL NOTIFY events and triggers callbacks.

    Replaces periodic polling with event-driven architecture.
    """

    def __init__(self, database_url: str):
        self.database_url = database_url
        self.connection: asyncpg.Connection | None = None
        self.callbacks: Dict[str, list[Callable]] = {}
        self._running = False

    async def connect(self):
        """Establish connection to PostgreSQL for LISTEN"""
        self.connection = await asyncpg.connect(self.database_url)
        logger.info("[DB_LISTENER] Connected to PostgreSQL for event listening")

    async def disconnect(self):
        """Close connection"""
        if self.connection:
            await self.connection.close()
            logger.info("[DB_LISTENER] Disconnected from PostgreSQL")

    def register_callback(self, channel: str, callback: Callable):
        """
        Register a callback for a specific notification channel.

        Args:
            channel: PostgreSQL notification channel name
            callback: Async function to call when notification received
        """
        if channel not in self.callbacks:
            self.callbacks[channel] = []
        self.callbacks[channel].append(callback)
        logger.info(f"[DB_LISTENER] Registered callback for channel: {channel}")

    async def start_listening(self, channels: list[str]):
        """
        Start listening for notifications on specified channels.

        Args:
            channels: List of PostgreSQL notification channel names
        """
        if not self.connection:
            await self.connect()

        # Register listener for each channel
        for channel in channels:
            await self.connection.add_listener(channel, self._handle_notification)
            logger.info(f"[DB_LISTENER] Listening on channel: {channel}")

        self._running = True

        # Keep connection alive
        while self._running:
            await asyncio.sleep(1)

    async def stop_listening(self):
        """Stop listening for notifications"""
        self._running = False
        await self.disconnect()

    async def _handle_notification(self, connection, pid, channel, payload):
        """
        Handle incoming notification from PostgreSQL.

        Args:
            connection: Database connection
            pid: Process ID that sent notification
            channel: Notification channel
            payload: JSON payload with event data
        """
        try:
            # Parse JSON payload
            data = json.loads(payload)
            logger.info(f"[DB_LISTENER] Received {channel} event: {data}")

            # Call all registered callbacks for this channel
            if channel in self.callbacks:
                for callback in self.callbacks[channel]:
                    try:
                        await callback(data)
                    except Exception as e:
                        logger.error(f"[DB_LISTENER] Error in callback for {channel}: {e}")

        except Exception as e:
            logger.error(f"[DB_LISTENER] Error handling notification from {channel}: {e}")
```

#### 1.3 Create Event-Driven Broadcast Manager

```python
# File: app/server/services/event_broadcast_manager.py

import logging
from typing import TYPE_CHECKING
from services.db_event_listener import DatabaseEventListener

if TYPE_CHECKING:
    from services.websocket_manager import ConnectionManager
    from services.workflow_service import WorkflowService

logger = logging.getLogger(__name__)


class EventBroadcastManager:
    """
    Manages event-driven WebSocket broadcasting.

    Replaces periodic polling watchers with database event listeners.
    """

    def __init__(
        self,
        websocket_manager: "ConnectionManager",
        workflow_service: "WorkflowService",
        db_listener: DatabaseEventListener,
    ):
        self.websocket_manager = websocket_manager
        self.workflow_service = workflow_service
        self.db_listener = db_listener
        self._app = None

    def set_app(self, app):
        """Set FastAPI app instance for route introspection"""
        self._app = app

    async def start(self):
        """
        Start event-driven broadcasting system.

        Registers callbacks for database events and starts listening.
        """
        logger.info("[EVENT_BROADCAST] Starting event-driven broadcast system...")

        # Register callbacks for each data type
        self.db_listener.register_callback(
            'planned_features_changed',
            self._on_planned_features_change
        )

        self.db_listener.register_callback(
            'pattern_review_changed',
            self._on_pattern_review_change
        )

        self.db_listener.register_callback(
            'workflow_history_changed',
            self._on_workflow_history_change
        )

        self.db_listener.register_callback(
            'phase_queue_changed',
            self._on_phase_queue_change
        )

        self.db_listener.register_callback(
            'context_analysis_changed',
            self._on_context_analysis_change
        )

        # Start listening
        await self.db_listener.start_listening([
            'planned_features_changed',
            'pattern_review_changed',
            'workflow_history_changed',
            'phase_queue_changed',
            'context_analysis_changed',
        ])

        logger.info("[EVENT_BROADCAST] Event-driven broadcast system started")

    async def stop(self):
        """Stop event-driven broadcasting system"""
        logger.info("[EVENT_BROADCAST] Stopping event-driven broadcast system...")
        await self.db_listener.stop_listening()
        logger.info("[EVENT_BROADCAST] Event-driven broadcast system stopped")

    # Event Handlers

    async def _on_planned_features_change(self, event_data: dict):
        """Handle planned features database change"""
        if len(self.websocket_manager.active_connections) == 0:
            return

        # Fetch fresh data
        from api.plannedFeaturesClient import plannedFeaturesClient
        features = await plannedFeaturesClient.getAll(limit=200)
        stats = await plannedFeaturesClient.getStats()

        # Broadcast update
        await self.websocket_manager.broadcast({
            "type": "planned_features_update",
            "data": {
                "features": [f.model_dump() for f in features],
                "stats": stats.model_dump()
            }
        })

        logger.info(f"[EVENT_BROADCAST] Broadcasted planned features update to "
                   f"{len(self.websocket_manager.active_connections)} clients")

    async def _on_pattern_review_change(self, event_data: dict):
        """Handle pattern review database change"""
        if len(self.websocket_manager.active_connections) == 0:
            return

        # Fetch fresh data
        from services.pattern_review_service import PatternReviewService
        service = PatternReviewService()

        patterns = service.get_pending_patterns(limit=20)
        stats = service.get_review_statistics()

        # Broadcast update
        await self.websocket_manager.broadcast({
            "type": "pattern_review_update",
            "data": {
                "patterns": [p.model_dump() for p in patterns],
                "stats": stats
            }
        })

        logger.info(f"[EVENT_BROADCAST] Broadcasted pattern review update to "
                   f"{len(self.websocket_manager.active_connections)} clients")

    async def _on_workflow_history_change(self, event_data: dict):
        """Handle workflow history database change"""
        if len(self.websocket_manager.active_connections) == 0:
            return

        # Fetch fresh data
        from core.data_models import WorkflowHistoryFilters
        history_data, _ = self.workflow_service.get_workflow_history_with_cache(
            WorkflowHistoryFilters(limit=50, offset=0)
        )

        # Broadcast update
        await self.websocket_manager.broadcast({
            "type": "workflow_history_update",
            "data": history_data.model_dump()
        })

        logger.info(f"[EVENT_BROADCAST] Broadcasted workflow history update to "
                   f"{len(self.websocket_manager.active_connections)} clients")

    async def _on_phase_queue_change(self, event_data: dict):
        """Handle phase queue database change"""
        if len(self.websocket_manager.active_connections) == 0:
            return

        # Fetch fresh data
        from server import get_queue_data
        queue_data = get_queue_data()

        # Broadcast update
        await self.websocket_manager.broadcast({
            "type": "queue_update",
            "data": queue_data
        })

        logger.info(f"[EVENT_BROADCAST] Broadcasted queue update to "
                   f"{len(self.websocket_manager.active_connections)} clients")

    async def _on_context_analysis_change(self, event_data: dict):
        """Handle context analysis status change"""
        if len(self.websocket_manager.active_connections) == 0:
            return

        # Broadcast status update with review_id
        review_id = event_data.get('review_id')
        status = event_data.get('status')

        await self.websocket_manager.broadcast({
            "type": "context_analysis_update",
            "data": {
                "review_id": review_id,
                "status": status,
                "timestamp": event_data.get('timestamp')
            }
        })

        logger.info(f"[EVENT_BROADCAST] Broadcasted context analysis update "
                   f"(review_id={review_id}, status={status})")
```

---

### Phase 2: File-Based Event Detection

**For data sources NOT in PostgreSQL (workflows, routes):**

#### 2.1 File Watcher Service

```python
# File: app/server/services/file_watcher.py

import asyncio
import logging
from pathlib import Path
from typing import Callable
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileSystemEvent

logger = logging.getLogger(__name__)


class AsyncFileChangeHandler(FileSystemEventHandler):
    """Handles file system events and triggers async callbacks"""

    def __init__(self, callback: Callable):
        self.callback = callback
        self.loop = asyncio.get_event_loop()

    def on_any_event(self, event: FileSystemEvent):
        """Handle any file system event"""
        if not event.is_directory:
            # Schedule callback in async event loop
            asyncio.run_coroutine_threadsafe(
                self.callback(event),
                self.loop
            )


class FileWatcher:
    """
    Watches file system for changes and triggers callbacks.

    Used for non-database data sources (workflows, routes).
    """

    def __init__(self):
        self.observer = Observer()
        self.watches = []

    def watch_directory(self, path: str, callback: Callable):
        """
        Watch a directory for changes.

        Args:
            path: Directory path to watch
            callback: Async function to call on change
        """
        handler = AsyncFileChangeHandler(callback)
        watch = self.observer.schedule(handler, path, recursive=True)
        self.watches.append((path, watch))
        logger.info(f"[FILE_WATCHER] Watching directory: {path}")

    def start(self):
        """Start watching"""
        self.observer.start()
        logger.info("[FILE_WATCHER] File watching started")

    def stop(self):
        """Stop watching"""
        self.observer.stop()
        self.observer.join()
        logger.info("[FILE_WATCHER] File watching stopped")
```

#### 2.2 Integrate File Watcher into Event Broadcast Manager

```python
# Add to EventBroadcastManager

async def _on_workflow_file_change(self, event):
    """Handle workflow file change"""
    if len(self.websocket_manager.active_connections) == 0:
        return

    # Small debounce to avoid multiple rapid updates
    await asyncio.sleep(0.5)

    # Fetch fresh workflow data
    workflows = self.workflow_service.get_workflows()

    # Broadcast update
    await self.websocket_manager.broadcast({
        "type": "workflows_update",
        "data": [w.model_dump() for w in workflows]
    })

    logger.info(f"[EVENT_BROADCAST] Broadcasted workflow update "
               f"(file change: {event.src_path})")

async def _on_routes_change(self):
    """Handle routes change (triggered by app startup/reload)"""
    if len(self.websocket_manager.active_connections) == 0:
        return

    routes = self.workflow_service.get_routes(self._app)

    await self.websocket_manager.broadcast({
        "type": "routes_update",
        "data": [r.model_dump() for r in routes]
    })

    logger.info("[EVENT_BROADCAST] Broadcasted routes update")
```

---

### Phase 3: Frontend WebSocket Migration

#### 3.1 Fix PlansPanel - Use WebSocket Only

**File:** `app/client/src/components/PlansPanel.tsx`

**Current (Lines 500-525):** Uses `usePlannedFeaturesWebSocket()` but still has React Query code

**Action:** Remove React Query code, use WebSocket hook exclusively

```typescript
// REMOVE these lines (509-525):
// const { data: features, isLoading: featuresLoading } = useQuery({
//   queryKey: ['planned-features'],
//   queryFn: () => plannedFeaturesClient.getAll({ limit: 200 }),
//   refetchInterval: 5 * 60 * 1000,
//   ...
// });

// KEEP only WebSocket hook (already exists at 503-509):
const {
  features,
  stats,
  isConnected,
  connectionQuality,
  lastUpdated: wsLastUpdated,
} = usePlannedFeaturesWebSocket();

// Update loading state to use WebSocket data
const isLoading = !features || features.length === 0;
```

#### 3.2 Create Pattern Review WebSocket Hook

**File:** `app/client/src/hooks/useWebSocket.ts`

**Add new hook:**

```typescript
interface PatternReviewWebSocketMessage {
  type: 'pattern_review_update';
  data: {
    patterns: PatternReview[];
    stats: ReviewStatistics;
  };
}

export function usePatternReviewWebSocket() {
  const [patterns, setPatterns] = useState<PatternReview[]>([]);
  const [stats, setStats] = useState<ReviewStatistics | null>(null);

  const wsUrl = apiConfig.websocket.patternReview();

  const connectionState = useReliableWebSocket<
    { patterns: PatternReview[]; stats: ReviewStatistics },
    PatternReviewWebSocketMessage
  >({
    url: wsUrl,
    queryKey: ['pattern-review'],
    queryFn: async () => {
      const patterns = await patternReviewClient.getPendingPatterns(20);
      const stats = await patternReviewClient.getReviewStatistics();
      return { patterns, stats };
    },
    onMessage: (message: any) => {
      if (message.type === 'pattern_review_update') {
        setPatterns(message.data.patterns);
        setStats(message.data.stats);
        if (DEBUG_WS) console.log('[WS] Received pattern review update:', message.data.patterns.length, 'patterns');
      }
    },
  });

  return {
    patterns,
    stats,
    isConnected: connectionState.isConnected,
    connectionQuality: connectionState.connectionQuality,
    lastUpdated: connectionState.lastUpdated,
    reconnectAttempts: connectionState.reconnectAttempts,
  };
}
```

#### 3.3 Update ReviewPanel - Use WebSocket

**File:** `app/client/src/components/ReviewPanel.tsx`

```typescript
// REPLACE React Query polling (lines 34-45) with WebSocket:
const {
  patterns,
  stats,
  isConnected,
  connectionQuality,
} = usePatternReviewWebSocket();

const isLoading = !patterns || patterns.length === 0;
const error = null; // WebSocket handles errors internally
```

#### 3.4 Create Context Analysis WebSocket Hook

**File:** `app/client/src/hooks/useWebSocket.ts`

```typescript
interface ContextAnalysisWebSocketMessage {
  type: 'context_analysis_update';
  data: {
    review_id: string;
    status: 'pending' | 'analyzing' | 'completed' | 'failed';
    timestamp: string;
  };
}

export function useContextAnalysisWebSocket(reviewId: string | null) {
  const [analysisStatus, setAnalysisStatus] = useState<string>('pending');

  const wsUrl = reviewId ? apiConfig.websocket.contextAnalysis(reviewId) : '';

  const connectionState = useReliableWebSocket<
    { review_id: string; status: string },
    ContextAnalysisWebSocketMessage
  >({
    url: wsUrl,
    queryKey: ['context-analysis', reviewId || ''],
    queryFn: async () => {
      // No HTTP fallback - WebSocket only
      throw new Error('Context analysis only available via WebSocket');
    },
    onMessage: (message) => {
      if (message.type === 'context_analysis_update' && message.data.review_id === reviewId) {
        setAnalysisStatus(message.data.status);
        if (DEBUG_WS) console.log('[WS] Context analysis status:', message.data.status);
      }
    },
    enabled: !!reviewId,
  });

  return {
    status: analysisStatus,
    isConnected: connectionState.isConnected,
    lastUpdated: connectionState.lastUpdated,
  };
}
```

#### 3.5 Update ContextReviewPanel - Use WebSocket

**File:** `app/client/src/components/context-review/ContextReviewPanel.tsx`

```typescript
// REPLACE conditional polling (lines 74-90) with WebSocket:
const { status: analysisStatus, isConnected } = useContextAnalysisWebSocket(reviewId);

// Keep the main data fetch but remove refetchInterval
const {
  data: analysis,
  isLoading: isLoadingAnalysis,
  error: analysisError,
} = useQuery({
  queryKey: ['context-review', reviewId],
  queryFn: () => fetchContextAnalysis(reviewId!),
  enabled: !!reviewId,
  staleTime: 0,
  // REMOVED: refetchInterval - now using WebSocket for status updates
});
```

---

### Phase 4: Backend WebSocket Endpoints

#### 4.1 Add Pattern Review WebSocket Endpoint

**File:** `app/server/routes/websocket_routes.py`

```python
@router.websocket("/ws/pattern-review")
async def websocket_pattern_review(websocket: WebSocket) -> None:
    """WebSocket endpoint for real-time pattern review updates"""
    from services.pattern_review_service import PatternReviewService

    service = PatternReviewService()
    patterns = service.get_pending_patterns(limit=20)
    stats = service.get_review_statistics()

    initial_data = {
        "type": "pattern_review_update",
        "data": {
            "patterns": [p.model_dump() for p in patterns],
            "stats": stats
        }
    }
    await _handle_websocket_connection(websocket, manager, initial_data, "pattern review")
```

#### 4.2 Add Context Analysis WebSocket Endpoint

**File:** `app/server/routes/websocket_routes.py`

```python
@router.websocket("/ws/context-analysis/{review_id}")
async def websocket_context_analysis(websocket: WebSocket, review_id: str) -> None:
    """WebSocket endpoint for real-time context analysis status updates"""
    # Get initial status
    from services.context_review_service import get_analysis_status

    status_data = get_analysis_status(review_id)

    initial_data = {
        "type": "context_analysis_update",
        "data": {
            "review_id": review_id,
            "status": status_data.get("status", "pending"),
            "timestamp": status_data.get("timestamp", "")
        }
    }
    await _handle_websocket_connection(websocket, manager, initial_data, "context analysis")
```

---

### Phase 5: Replace Backend Periodic Watchers

#### 5.1 Update server.py Startup

**File:** `app/server/server.py`

```python
# REMOVE BackgroundTaskManager initialization
# OLD:
# background_tasks = BackgroundTaskManager(
#     websocket_manager,
#     workflow_service,
#     workflow_watch_interval=10.0,
#     ...
# )

# ADD EventBroadcastManager initialization
from services.db_event_listener import DatabaseEventListener
from services.event_broadcast_manager import EventBroadcastManager
from services.file_watcher import FileWatcher

# Initialize database listener
db_listener = DatabaseEventListener(
    database_url=os.getenv("DATABASE_URL")
)

# Initialize file watcher
file_watcher = FileWatcher()

# Initialize event broadcast manager
event_broadcast_manager = EventBroadcastManager(
    websocket_manager=websocket_manager,
    workflow_service=workflow_service,
    db_listener=db_listener,
    file_watcher=file_watcher,
)

@app.on_event("startup")
async def startup_event():
    """Application startup - start event-driven broadcasting"""
    logger.info("[SERVER] Starting event-driven broadcast system...")

    # Set app reference for routes introspection
    event_broadcast_manager.set_app(app)

    # Start event-driven broadcasting (replaces periodic watchers)
    await event_broadcast_manager.start()

    logger.info("[SERVER] Event-driven broadcast system started")

@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown - stop event-driven broadcasting"""
    logger.info("[SERVER] Stopping event-driven broadcast system...")
    await event_broadcast_manager.stop()
    logger.info("[SERVER] Event-driven broadcast system stopped")
```

#### 5.2 Add System Status & Webhook Status Broadcasting

**Add to EventBroadcastManager:**

```python
async def broadcast_system_status(self):
    """Broadcast system status update (called by admin actions)"""
    if len(self.websocket_manager.active_connections) == 0:
        return

    from api.client import getSystemStatus
    status_data = await getSystemStatus()

    await self.websocket_manager.broadcast({
        "type": "system_status_update",
        "data": status_data
    })

    logger.info("[EVENT_BROADCAST] Broadcasted system status update")

async def broadcast_webhook_status(self):
    """Broadcast webhook status update (called by webhook events)"""
    if len(self.websocket_manager.active_connections) == 0:
        return

    from api.client import getWebhookStatus
    status_data = getWebhookStatus()

    await self.websocket_manager.broadcast({
        "type": "webhook_status_update",
        "data": status_data
    })

    logger.info("[EVENT_BROADCAST] Broadcasted webhook status update")
```

**Call from relevant endpoints:**

```python
# In system admin endpoints:
@router.post("/admin/restart")
async def restart_service():
    # ... restart logic ...

    # Broadcast updated status
    await event_broadcast_manager.broadcast_system_status()

    return {"status": "restarted"}

# In webhook endpoints:
@router.post("/webhooks/github")
async def handle_github_webhook():
    # ... webhook logic ...

    # Broadcast updated webhook status
    await event_broadcast_manager.broadcast_webhook_status()

    return {"status": "processed"}
```

---

### Phase 6: Cleanup

#### 6.1 Remove Deprecated Code

Files to clean up:
- `app/server/services/background_tasks.py` - Delete (replaced by `event_broadcast_manager.py`)
- `app/client/src/hooks/useReliablePolling.ts` - Delete (not used)
- `app/client/src/config/intervals.ts` - Remove polling config values

#### 6.2 Update Configuration

**File:** `app/client/src/config/intervals.ts`

```typescript
// REMOVE polling config
export const intervals = {
  websocket: {
    maxReconnectDelay: 30000,
    maxReconnectAttempts: 10,
  },

  // REMOVED: polling config (no longer used)

  components: {
    systemStatus: {
      refreshDelayAfterAction: 2000, // KEEP - UI timing, not polling
    },
    workflowHistory: {
      defaultLimit: 50, // KEEP - data limit, not polling
    },
  },
};
```

---

## Migration Strategy

### Recommended Order

1. **Phase 1 (Database Events)** - 2-3 hours
   - Create triggers and listener service
   - Test with one table first (planned_features)

2. **Phase 2 (File Watchers)** - 1-2 hours
   - Implement file watching for workflows
   - Add debouncing to avoid spam

3. **Phase 3 (Frontend Migration)** - 2-3 hours
   - Start with PlansPanel (easiest - hook exists)
   - Then ReviewPanel and ContextReviewPanel

4. **Phase 4 (Backend Endpoints)** - 1 hour
   - Add missing WebSocket endpoints
   - Wire up to event system

5. **Phase 5 (Replace Watchers)** - 2-3 hours
   - Replace BackgroundTaskManager with EventBroadcastManager
   - Test thoroughly

6. **Phase 6 (Cleanup)** - 1 hour
   - Remove deprecated code
   - Update documentation

**Total Estimated Time:** 9-13 hours

### Testing Strategy

1. **Unit Tests**
   - Test database trigger functions
   - Test event listener callbacks
   - Test WebSocket message formats

2. **Integration Tests**
   - Test end-to-end: DB change → NOTIFY → Listener → Broadcast → Frontend
   - Test reconnection scenarios
   - Test multiple concurrent connections

3. **Performance Tests**
   - Measure latency: DB change to frontend update
   - Target: <100ms for event-driven (vs 2-10s for polling)
   - Test with 10+ concurrent WebSocket clients

---

## Success Metrics

### Latency Improvements

| Data Source | Old (Polling) | New (Event-Driven) | Improvement |
|-------------|---------------|-------------------|-------------|
| Planned Features | 5-10 min | <100ms | 3000-6000x faster |
| Pattern Reviews | 30s | <100ms | 300x faster |
| Context Analysis | 3s | <100ms | 30x faster |
| Workflows | 10s | <100ms | 100x faster |
| Queue | 2s | <100ms | 20x faster |

### Resource Improvements

- **Backend CPU:** -50% (no periodic polling loops)
- **Database Load:** -80% (queries only on change, not every N seconds)
- **Network Traffic:** -70% (broadcasts only on change)

### Code Quality

- **Backend:** Remove ~400 lines of polling code
- **Frontend:** Remove ~100 lines of React Query polling config
- **Maintainability:** Clearer event-driven architecture

---

## Risk Mitigation

### Risk 1: PostgreSQL NOTIFY Reliability

**Mitigation:**
- NOTIFY is transactional - guaranteed delivery on commit
- Add heartbeat mechanism to detect connection loss
- Fallback to periodic sync every 5 minutes if no events

### Risk 2: File Watcher Performance

**Mitigation:**
- Add debouncing (500ms) to avoid rapid-fire updates
- Filter events to only relevant file types
- Use inotify on Linux for efficiency

### Risk 3: WebSocket Connection Stability

**Mitigation:**
- Already have robust reconnection logic in `useReliableWebSocket`
- Add connection quality indicators
- Log connection issues for monitoring

---

## Next Steps

1. **Review this plan** - Confirm approach and priorities
2. **Start with Phase 1** - Implement database triggers for one table (planned_features)
3. **Test proof-of-concept** - Verify NOTIFY → Broadcast → Frontend flow
4. **Iterate through phases** - Complete one phase at a time with testing
5. **Deploy incrementally** - Feature flag for gradual rollout

---

## References

- **ADW Monitor Migration:** Session 19 - Event-driven HTTP POST (0ms latency)
- **WebSocket Implementation:** Sessions 15-16, Dec 8 2025 postmortem
- **PostgreSQL NOTIFY:** https://www.postgresql.org/docs/current/sql-notify.html
- **watchdog (Python):** https://python-watchdog.readthedocs.io/

---

**Status:** ✅ Ready for implementation
**Next:** Start Phase 1 - Database event notification system
