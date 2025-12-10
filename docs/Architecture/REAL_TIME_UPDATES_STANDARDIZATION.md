# Real-Time Updates Standardization Plan

**Date**: 2025-12-10
**Status**: Proposed Architecture
**Related Issues**: Plans Panel #64, #65, #66, #67

## Executive Summary

This document proposes a **standardized real-time update architecture** to resolve 4 critical issues identified in the tac-webbuilder system:

1. **System Status Panel shows stale data** - Missing WebSocket broadcasting
2. **CurrentWorkflowCard shows $0.00 cost** - No real-time cost tracking
3. **Branch name missing from workflow state** - Database sync gap
4. **Failed workflows disappear from UI** - Visibility issue

Rather than implementing piecemeal fixes, this plan establishes **consistent architectural patterns** for real-time data flow across the entire application.

---

## Current State Analysis

### WebSocket Architecture Status

| Component | WebSocket Endpoint | Broadcasting | Status | Latency |
|-----------|-------------------|--------------|--------|---------|
| ADW Monitor | `/ws/adw-monitor` | ✅ Event-driven (HTTP POST) | Working | <100ms |
| Queue | `/ws/queue` | ✅ Polling (2s) + Events | Working | <2s |
| Workflows | `/ws/workflows` | ✅ Polling (10s) | Working | <10s |
| Routes | `/ws/routes` | ✅ Polling (10s) | Working | <10s |
| History | `/ws/workflow-history` | ✅ Polling (10s) | Working | <10s |
| **System Status** | `/ws/system-status` | ❌ **NONE** | **Broken** | **Never** |
| **Webhook Status** | `/ws/webhook-status` | ❌ **NONE** | **Broken** | **Never** |

### Data Flow Patterns (Current)

**Pattern A: Event-Driven (Best - 0ms latency)**
```
Orchestrator → HTTP POST /api/v1/adw-phase-update → Backend updates state → WebSocket broadcast
```
- Used by: ADW Monitor
- Latency: <100ms
- Efficiency: Excellent (only broadcasts on real changes)

**Pattern B: Polling with Change Detection (Good - 2-10s latency)**
```
Background task polls every Xs → Detect changes → WebSocket broadcast if changed
```
- Used by: Queue (2s), Workflows/Routes/History (10s)
- Latency: 2-10 seconds
- Efficiency: Good (only broadcasts when state changes)

**Pattern C: Initial Data Only (Broken - infinite latency)**
```
WebSocket connects → Send initial data → No further updates
```
- Used by: System Status, Webhook Status
- Latency: ∞ (never updates)
- Efficiency: N/A (incomplete implementation)

**Pattern D: Manual HTTP Polling (Acceptable for on-demand operations)**
```
User action → HTTP GET → Display result → No auto-refresh
```
- Used by: Preflight checks
- Latency: N/A (user-triggered)
- Efficiency: Excellent (zero overhead when not in use)

---

## Proposed Standardized Architecture

### 1. Real-Time Update Classification

All data updates should be classified into one of 4 tiers:

#### **Tier 1: Critical Real-Time (Event-Driven WebSocket)**
- **Latency requirement**: <100ms
- **Pattern**: HTTP POST event → Backend handler → WebSocket broadcast
- **Use cases**:
  - Workflow phase transitions
  - **NEW: Cost updates** (after each phase)
  - Queue state changes
  - Critical errors/alerts

**Standard Implementation:**
```python
# Orchestrator or service emits event
broadcast_event(
    event_type="workflow_update",
    adw_id=adw_id,
    data={"current_cost": 1.25, "current_phase": "Build"}
)

# Backend route handler
@app.post("/api/v1/event/{event_type}")
async def handle_event(event_type: str, data: dict):
    # Update state
    update_state(data)

    # Immediate WebSocket broadcast
    await websocket_manager.broadcast({
        "type": f"{event_type}_update",
        "data": data
    })
```

#### **Tier 2: Near Real-Time (Polling with Change Detection)**
- **Latency requirement**: 10-30s
- **Pattern**: Background task polls → Detect changes → Broadcast
- **Use cases**:
  - **NEW: System status** (service health)
  - **NEW: Webhook status**
  - Routes configuration
  - Workflow list

**Standard Implementation:**
```python
async def watch_{component}(self):
    """Poll {component} every {interval}s and broadcast if changed"""
    while True:
        if len(self.websocket_manager.active_connections) > 0:
            data = await get_{component}_data()
            current_state = json.dumps(data, sort_keys=True)

            if current_state != self.last_{component}_state:
                self.last_{component}_state = current_state
                await self.websocket_manager.broadcast({
                    "type": "{component}_update",
                    "data": data
                })
                logger.debug(f"[BACKGROUND] Broadcasted {component} update")

        await asyncio.sleep({interval})
```

#### **Tier 3: Eventual Consistency (Periodic Sync)**
- **Latency requirement**: 1-5 minutes
- **Pattern**: Cron-like periodic sync to database
- **Use cases**:
  - Workflow history sync (filesystem → database)
  - Cost aggregation (raw_output.jsonl → database)
  - Analytics data updates

**Standard Implementation:**
```python
async def sync_{component}_background(self):
    """Sync {component} every {interval} minutes"""
    while True:
        try:
            synced_count = sync_{component}()
            if synced_count > 0:
                logger.info(f"[SYNC] {component}: {synced_count} items")
        except Exception as e:
            logger.error(f"[SYNC] {component} failed: {e}")

        await asyncio.sleep({interval} * 60)
```

#### **Tier 4: On-Demand (Manual Trigger)**
- **Latency requirement**: N/A (user-triggered)
- **Pattern**: User action → HTTP request → Display result
- **Use cases**:
  - Preflight checks (expensive, 5-35s runtime)
  - One-time validations
  - Manual diagnostics

**Standard Implementation:**
```python
# No automatic updates - user must trigger explicitly
const { data, refetch } = useQuery({
  queryKey: ['component'],
  queryFn: fetchData,
  refetchInterval: false,
  refetchOnWindowFocus: false,
});
```

---

### 2. Database Sync Standardization

**Problem**: Incomplete field extraction causes missing data in database and WebSocket broadcasts.

**Current Flow**:
```
State File (adw_state.json) → Filesystem Scanner → Database → WebSocket → Frontend
         ✅ Complete                ❌ Incomplete      ❌ Missing    ✅ Works
```

**Standardized Solution**: **Schema-Driven Extraction**

```python
# Define authoritative state schema
STATE_CORE_FIELDS = {
    # Workflow identity
    "adw_id", "issue_number", "github_url",

    # Planning outputs
    "branch_name", "plan_file", "issue_class", "integration_checklist",

    # Build outputs
    "external_build_results",

    # Test outputs
    "external_test_results",

    # Review outputs
    "review_results",

    # Execution state
    "status", "current_phase", "start_time", "end_time",

    # Cost tracking
    "current_cost", "estimated_cost_total", "estimated_cost_breakdown",

    # Infrastructure
    "worktree_path", "backend_port", "frontend_port", "model_used",
}

def _extract_workflow_metadata(adw_id: str, adw_dir: Path, state_data: dict) -> dict:
    """Extract ALL defined fields from state data."""
    metadata = {"adw_id": adw_id}

    # Extract all core fields present in state
    for field in STATE_CORE_FIELDS:
        if field in state_data:
            metadata[field] = state_data[field]

    # Special handling for computed fields
    metadata["worktree_path"] = str(adw_dir)

    return metadata
```

**Benefits**:
- ✅ **Single source of truth** - Schema defines what gets extracted
- ✅ **No missing fields** - All state data flows to database
- ✅ **Easy to extend** - Add field to schema, automatically extracted
- ✅ **Type-safe** - Pydantic validates against schema

---

### 3. WebSocket Broadcasting Standardization

**Standard Message Format**:
```typescript
interface WebSocketMessage {
  type: string;          // e.g., "adw_monitor_update", "system_status_update"
  data: any;             // Payload specific to type
  timestamp: string;     // ISO 8601 timestamp
  source?: string;       // Optional: "event" | "poll" | "sync"
}
```

**Standard Broadcasting Function**:
```python
async def broadcast_update(
    manager: WebSocketManager,
    update_type: str,
    data: dict,
    source: str = "poll"
) -> int:
    """
    Standardized WebSocket broadcasting.

    Args:
        manager: WebSocket connection manager
        update_type: Message type (e.g., "system_status_update")
        data: Payload to broadcast
        source: Update source ("event", "poll", "sync")

    Returns:
        Number of clients that received the broadcast
    """
    if not manager or not manager.active_connections:
        return 0

    message = {
        "type": update_type,
        "data": data,
        "timestamp": datetime.now().isoformat(),
        "source": source
    }

    await manager.broadcast(message)

    logger.debug(
        f"[WS_BROADCAST] {update_type} → {len(manager.active_connections)} clients"
    )

    return len(manager.active_connections)
```

---

### 4. Frontend WebSocket Hook Standardization

**Standard Hook Pattern**:
```typescript
export function use{Component}WebSocket() {
  const [data, setData] = useState<{Component}Data | null>(null);
  const wsUrl = apiConfig.websocket.{component}();

  const connectionState = useReliableWebSocket({
    url: wsUrl,
    queryKey: ['{component}'],
    queryFn: get{Component},  // Fallback HTTP endpoint
    onMessage: (message: WebSocketMessage) => {
      if (message.type === '{component}_update') {
        setData(message.data);

        // Optional: Log source for debugging
        if (process.env.NODE_ENV === 'development') {
          console.log(`[WS] {Component} update from ${message.source}`);
        }
      }
    },
  });

  return {
    data,
    isConnected: connectionState.isConnected,
    connectionQuality: connectionState.connectionQuality,
    lastUpdated: connectionState.lastUpdated,
  };
}
```

**Benefits**:
- ✅ Consistent API across all components
- ✅ Built-in connection quality monitoring
- ✅ Automatic reconnection handling
- ✅ TypeScript type safety

---

## Implementation Roadmap

### Phase 1: Critical Fixes (Week 1)

**Priority 1A: System Status Broadcasting (1 hour)**
- File: `app/server/services/background_tasks.py`
- Add: `watch_system_status()` function
- Interval: 30 seconds
- Tier: 2 (Near Real-Time)

```python
async def watch_system_status(self) -> None:
    """Watch system status and broadcast changes every 30s"""
    try:
        while True:
            if len(self.websocket_manager.active_connections) > 0:
                from routes.system_routes import _get_system_status_handler
                from server import health_service

                system_status = await _get_system_status_handler(health_service)
                current_state = json.dumps(system_status.model_dump(), sort_keys=True)

                if current_state != getattr(self.websocket_manager, 'last_system_status_state', None):
                    self.websocket_manager.last_system_status_state = current_state
                    await self.websocket_manager.broadcast({
                        "type": "system_status_update",
                        "data": system_status.model_dump(),
                        "timestamp": datetime.now().isoformat(),
                        "source": "poll"
                    })
                    logger.debug("[BACKGROUND_TASKS] Broadcasted system status update")

            await asyncio.sleep(30)

    except asyncio.CancelledError:
        logger.info("[BACKGROUND_TASKS] System status watcher cancelled")
        raise
```

**Priority 1B: Branch Name Extraction (30 minutes)**
- File: `app/server/core/workflow_history_utils/filesystem.py`
- Change: Add 3 lines to `_extract_workflow_metadata()` return dict
- Tier: N/A (data extraction fix)

```python
def _extract_workflow_metadata(adw_id: str, adw_dir: Path, state_data: dict) -> dict:
    return {
        # ... existing fields ...

        # FIX: Add phase outputs
        "branch_name": state_data.get("branch_name"),
        "plan_file": state_data.get("plan_file"),
        "issue_class": state_data.get("issue_class"),
    }
```

**Priority 1C: Database Migration (15 minutes)**
```sql
-- Add missing columns to workflow_history
ALTER TABLE workflow_history
  ADD COLUMN IF NOT EXISTS branch_name TEXT,
  ADD COLUMN IF NOT EXISTS plan_file TEXT,
  ADD COLUMN IF NOT EXISTS issue_class TEXT,
  ADD COLUMN IF NOT EXISTS current_cost NUMERIC(10, 4);

-- Index for faster branch lookups
CREATE INDEX IF NOT EXISTS idx_workflow_history_branch_name
  ON workflow_history(branch_name)
  WHERE branch_name IS NOT NULL;
```

**Priority 1D: Failed Workflow Visibility Investigation (2 hours)**
- Files: `app/client/src/components/CurrentWorkflowCard.tsx`, `app/server/core/adw_monitor.py`
- Investigate: Why failed workflows disappear
- Fix: Ensure failed workflows remain visible with clear failure indication

---

### Phase 2: Real-Time Cost Tracking (Week 2)

**Step 2A: Add current_cost to State Schema (30 minutes)**
- File: `adws/adw_modules/state.py`
- Add: `current_cost` to core fields
- Update: `ADWStateData` Pydantic model

**Step 2B: Progressive Cost Tracking in Orchestrators (2 hours)**
- Files: `adws/adw_sdlc_complete_iso.py`, `adws/adw_sdlc_complete_zte.py`
- Add: Cost calculation after each phase
- Pattern: Read raw_output.jsonl → Calculate delta → Update state → Broadcast

```python
def run_phase_with_cost_tracking(phase_name: str, phase_function: callable, adw_id: str):
    """Run phase and track cost incrementally"""
    # Get cost before phase
    cost_before = read_current_cost(adw_id)

    # Run phase
    logger.info(f"Starting {phase_name} phase...")
    result = phase_function()

    # Calculate cost delta
    cost_after = read_current_cost(adw_id)
    phase_cost = cost_after - cost_before

    # Update state
    state = ADWState.load(adw_id)
    state.update(current_cost=cost_after)
    state.save()

    # Broadcast cost update
    broadcast_phase_update(
        adw_id=adw_id,
        current_phase=phase_name,
        status="completed",
        metadata={"current_cost": cost_after, "phase_cost": phase_cost}
    )

    logger.info(f"{phase_name} phase cost: ${phase_cost:.4f} (total: ${cost_after:.4f})")

    return result
```

**Step 2C: Update ADW Monitor to Extract Cost (15 minutes)**
- File: `app/server/core/adw_monitor.py`
- Update: `extract_cost_data()` to read from state files
- Frontend: Already supports cost display (no changes needed)

---

### Phase 3: Standardization & Cleanup (Week 3)

**Step 3A: Implement Schema-Driven Extraction (1 hour)**
- File: `app/server/core/workflow_history_utils/filesystem.py`
- Replace: Hardcoded field list with `STATE_CORE_FIELDS` schema
- Benefit: All future state fields automatically extracted

**Step 3B: Add Standard Broadcasting Helper (30 minutes)**
- File: `app/server/services/websocket_manager.py`
- Add: `broadcast_update()` standardized function
- Update: All broadcasting code to use standard function

**Step 3C: Documentation (2 hours)**
- Create: WebSocket architecture guide
- Document: Tier classification system
- Create: Adding new real-time components guide

---

## Success Metrics

### Before Standardization
- ❌ System Status: Stale data, manual refresh required
- ❌ Cost Tracking: Always $0.00 for active workflows
- ❌ Branch Names: Missing from UI
- ❌ Failed Workflows: Disappear after refresh
- ⚠️ Inconsistent patterns: 3 different WebSocket implementations

### After Standardization
- ✅ System Status: Auto-updates every 30s
- ✅ Cost Tracking: Real-time updates after each phase
- ✅ Branch Names: Visible with PR links
- ✅ Failed Workflows: Persistent with clear failure indication
- ✅ Consistent patterns: Single tier-based architecture

### Performance Improvements
- **System Status Latency**: ∞ → 30s
- **Cost Update Latency**: ∞ → <100ms
- **Branch Name Availability**: Never → Immediate
- **Failure Visibility**: Transient → Persistent

---

## Architecture Principles

### 1. **Separation of Concerns**
- State files = Source of truth
- Database = Queryable cache
- WebSocket = Real-time broadcast layer
- Frontend = Display layer

### 2. **Progressive Enhancement**
- Start with cheapest checks (Tier 4 → Tier 1)
- Only add real-time updates where needed
- Graceful degradation on WebSocket failure

### 3. **Schema-Driven Design**
- Single source of truth for field definitions
- Automatic propagation of new fields
- Type safety via Pydantic validation

### 4. **Event-Driven First**
- Prefer events over polling where possible
- Only poll when events aren't feasible
- Always detect changes before broadcasting

### 5. **Observability Built-In**
- Log all broadcasts with timestamp and recipient count
- Track connection quality in frontend
- Monitor WebSocket health via metrics

---

## Risk Mitigation

### Risk 1: Background Tasks Overload
**Mitigation**:
- Only poll when clients are connected
- Detect changes before broadcasting
- Use exponential backoff on errors

### Risk 2: Database Migration Failures
**Mitigation**:
- Use `IF NOT EXISTS` for all schema changes
- Test migrations on dev database first
- Add rollback scripts

### Risk 3: WebSocket Connection Storms
**Mitigation**:
- Connection pooling with max limits
- Rate limiting on reconnection attempts
- Heartbeat keep-alive to detect dead connections

### Risk 4: Frontend State Inconsistencies
**Mitigation**:
- Include timestamp in all messages
- Client-side deduplication
- Optimistic UI updates with rollback

---

## Conclusion

This standardized architecture provides:

1. **Consistency**: All real-time updates follow tier-based patterns
2. **Completeness**: All state fields flow from files → database → frontend
3. **Performance**: Sub-second latency for critical updates
4. **Maintainability**: Schema-driven design makes adding features easy
5. **Reliability**: Built-in observability and error handling

**Estimated Total Implementation Time**: 12-15 hours across 3 weeks

**Benefits**:
- ✅ Resolves all 4 identified critical issues
- ✅ Establishes patterns for future real-time features
- ✅ Improves overall system observability
- ✅ Enhances user experience with live updates
