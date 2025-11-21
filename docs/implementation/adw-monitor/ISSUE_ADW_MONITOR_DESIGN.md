# ADW Monitor Card - Design Document

## Overview
A real-time ADW workflow monitoring card to be placed in the "New Request" tab, positioned to the right of the "System Status" card. This provides visual feedback on all active, paused, and recent ADW workflows.

## UI/UX Design

### Card Placement
- **Location:** `RequestForm.tsx` - Right column of the 2-column grid
- **Position:** Below `ZteHopperQueueCard` (or replace it based on priority)
- **Layout:** Matches height and styling of "Create New Request" card

### Visual Components

#### 1. Card Header
```
┌─────────────────────────────────────────────────┐
│ 🤖 Active ADW Workflows              [Refresh] │
│ 3 running • 1 completed • 0 failed              │
└─────────────────────────────────────────────────┘
```

#### 2. Workflow Status Cards (Scrollable)
Each workflow displayed as a compact card:

```
┌─────────────────────────────────────────────────┐
│ Issue #66 • bug 🔴 RUNNING                      │
│ ───────────────────────────────────────────────  │
│ Fix workflow history data                       │
│                                                  │
│ Phase: Build [████████░░] 80%                   │
│ Started: 4 mins ago                             │
│ Cost: $0.23 → ~$3.50                            │
│                                                  │
│ [View Logs] [View Issue] [Cancel]               │
└─────────────────────────────────────────────────┘
```

### Status Indicators
- 🔴 **RUNNING** - Green pulse animation
- ⏸️ **PAUSED** - Yellow/orange static
- ✅ **COMPLETED** - Green checkmark
- ❌ **FAILED** - Red X with error count
- ⏱️ **QUEUED** - Gray/blue clock

### Phase Progress
Visual progress bar showing current phase with 8 segments (for complete SDLC):
1. Plan
2. Build
3. Lint
4. Test
5. Review
6. Doc
7. Ship
8. Cleanup

**Progress Calculation:**
- Each phase = 12.5% (100% / 8)
- Sub-phase progress interpolated if available

### Workflow Card Details
- **Issue Number & Classification Badge**
- **Title** (truncated at 50 chars)
- **Current Phase** with progress bar
- **Duration** (human-readable: "4 mins ago", "2 hours ago")
- **Cost** (current → estimated total)
- **Action Buttons:**
  - View Logs: Opens latest phase log in modal
  - View Issue: Opens GitHub issue in new tab
  - Cancel: Stops workflow (with confirmation)

### Empty State
```
┌─────────────────────────────────────────────────┐
│ 🤖 Active ADW Workflows              [Refresh] │
│                                                  │
│         No active workflows                     │
│                                                  │
│   Create a new request to start a workflow →    │
└─────────────────────────────────────────────────┘
```

### Error State
```
┌─────────────────────────────────────────────────┐
│ 🤖 Active ADW Workflows              [Refresh] │
│                                                  │
│  ⚠️  Unable to load workflow status             │
│      [Retry]                                     │
└─────────────────────────────────────────────────┘
```

## Backend API Design

### New Endpoint: GET /api/adw-monitor

**Purpose:** Aggregate all ADW states for real-time monitoring

#### Response Schema
```typescript
interface AdwMonitorResponse {
  summary: {
    total: number;
    running: number;
    completed: number;
    failed: number;
    paused: number;
  };
  workflows: AdwWorkflowStatus[];
  last_updated: string; // ISO timestamp
}

interface AdwWorkflowStatus {
  adw_id: string;
  issue_number: string;
  issue_class: string; // "/bug", "/feature", etc.
  title: string;
  status: "running" | "completed" | "failed" | "paused" | "queued";
  current_phase: string | null;
  phase_progress: number; // 0-100
  workflow_template: string;
  start_time: string;
  end_time: string | null;
  duration_seconds: number | null;
  github_url: string;
  worktree_path: string | null;

  // Cost tracking
  current_cost: number | null;
  estimated_cost_total: number | null;

  // Error tracking
  error_count: number;
  last_error: string | null;

  // Process tracking
  is_process_active: boolean;

  // Phase breakdown (for progress calculation)
  phases_completed: string[];
  total_phases: number;
}
```

#### Implementation Details
```python
# app/server/server.py

@app.get("/api/adw-monitor", response_model=AdwMonitorResponse)
async def get_adw_monitor_status() -> AdwMonitorResponse:
    """
    Aggregate ADW workflow status from:
    1. agents/*/adw_state.json files
    2. Running process checks (ps aux)
    3. Worktree existence checks
    4. Recent activity timestamps
    """
    pass
```

**Data Sources:**
1. **ADW State Files:** `agents/*/adw_state.json`
2. **Process List:** `ps aux | grep adw` to check if actively running
3. **Worktree Status:** Check if `trees/{adw_id}/` exists
4. **Phase Logs:** Parse `agents/{adw_id}/*/raw_output.jsonl` for latest status
5. **Cost Data:** From state file's `estimated_cost_total` and phase costs

**Status Determination Logic:**
```python
def determine_status(adw_id: str, state: dict) -> str:
    # Check if process is running
    if is_process_running(adw_id):
        return "running"

    # Check state file status
    if state.get("status") == "failed":
        return "failed"

    if state.get("status") == "completed":
        return "completed"

    # Check if worktree exists but no process
    if worktree_exists(adw_id) and not is_process_running(adw_id):
        # Check last activity timestamp
        last_activity = get_last_activity_timestamp(adw_id)
        if (datetime.now() - last_activity).seconds > 600:  # 10 mins
            return "paused"

    return "queued"
```

**Phase Progress Calculation:**
```python
def calculate_phase_progress(adw_id: str, state: dict) -> tuple[str, float]:
    phases = ["plan", "build", "lint", "test", "review", "doc", "ship", "cleanup"]
    total_phases = len(phases)

    # Get completed phases
    completed_dirs = os.listdir(f"agents/{adw_id}")
    completed_phases = [p for p in phases if any(p in d for d in completed_dirs)]

    # Calculate progress
    base_progress = (len(completed_phases) / total_phases) * 100

    # If currently in a phase, add partial progress
    current_phase = state.get("current_phase")
    if current_phase:
        # Could parse logs for sub-phase progress
        base_progress += (100 / total_phases) * 0.5  # Add 50% of phase

    return current_phase, base_progress
```

## Frontend Implementation

### New Component: `AdwMonitorCard.tsx`

**Location:** `app/client/src/components/AdwMonitorCard.tsx`

**Dependencies:**
- TanStack Query for data fetching
- Tailwind for styling
- React hooks for state management

**Key Features:**
1. **Auto-refresh:** Poll every 10 seconds when workflows are active
2. **Real-time updates:** Use existing WebSocket if available
3. **Responsive:** Collapses gracefully on smaller screens
4. **Accessible:** Keyboard navigation, screen reader support

### API Client Addition
```typescript
// app/client/src/api/client.ts

export interface AdwMonitorResponse {
  // ... (see above)
}

export async function getAdwMonitorStatus(): Promise<AdwMonitorResponse> {
  const response = await fetch(`${API_BASE_URL}/api/adw-monitor`);
  if (!response.ok) {
    throw new Error('Failed to fetch ADW monitor status');
  }
  return response.json();
}
```

### Integration in RequestForm

**Update:** `app/client/src/components/RequestForm.tsx`

```tsx
// Add after line 387 (inside the grid)
<div className="space-y-6">
  <ZteHopperQueueCard />
  <AdwMonitorCard />
</div>
```

## Real-Time Updates

### Polling Strategy
```typescript
// Auto-refresh based on activity
const refreshInterval = workflows.some(w => w.status === 'running')
  ? 10000  // 10 seconds if any running
  : 30000; // 30 seconds if all idle

useQuery({
  queryKey: ['adw-monitor'],
  queryFn: getAdwMonitorStatus,
  refetchInterval: refreshInterval,
});
```

### WebSocket Enhancement (Optional)
Could extend existing WebSocket to broadcast ADW state changes:
```python
# When ADW state changes
await manager.broadcast_to_namespace({
    "type": "adw_status_update",
    "adw_id": adw_id,
    "status": status,
    "phase": current_phase
}, namespace="/adw-monitor")
```

## User Interactions

### 1. View Logs
- Opens modal with latest phase log
- Formatted with syntax highlighting
- Auto-scroll to bottom
- Refresh button

### 2. View Issue
- Opens GitHub issue in new tab
- Uses `github_url` from state

### 3. Cancel Workflow
- Shows confirmation dialog
- Calls new endpoint: `POST /api/adw/{adw_id}/cancel`
- Kills process, marks state as cancelled
- Cleans up worktree (optional)

### 4. Refresh
- Manual refresh button
- Shows loading spinner
- Refetches all data

## Visual Design Specs

### Colors
- **Running:** `bg-green-100 text-green-800 border-green-300` with pulse
- **Completed:** `bg-green-50 text-green-700 border-green-200`
- **Failed:** `bg-red-100 text-red-800 border-red-300`
- **Paused:** `bg-yellow-100 text-yellow-800 border-yellow-300`
- **Queued:** `bg-gray-100 text-gray-700 border-gray-300`

### Progress Bar
```tsx
<div className="w-full bg-gray-200 rounded-full h-2">
  <div
    className="bg-blue-600 h-2 rounded-full transition-all duration-500"
    style={{ width: `${progress}%` }}
  />
</div>
```

### Card Spacing
- Card padding: `p-6`
- Section spacing: `space-y-4`
- Button spacing: `gap-2`
- Max height: `max-h-96 overflow-y-auto` for scrolling

## Error Handling

### Backend Errors
- Graceful degradation if state files are corrupt
- Skip ADWs with missing critical data
- Log errors but don't fail entire request

### Frontend Errors
- Show error state with retry button
- Display last successful data if available
- Toast notifications for transient errors

## Performance Considerations

### Backend Optimization
- Cache ADW states for 5 seconds
- Batch file reads
- Limit to most recent 20 workflows
- Use async I/O for file operations

### Frontend Optimization
- Virtualize list if >10 workflows
- Debounce refresh clicks
- Memoize expensive calculations
- Lazy load log viewer component

## Testing Strategy

### Backend Tests
1. Test ADW state aggregation
2. Test status determination logic
3. Test phase progress calculation
4. Test error handling for corrupt states
5. Test performance with 15+ concurrent ADWs

### Frontend Tests
1. Test component rendering
2. Test polling behavior
3. Test user interactions (view logs, cancel)
4. Test error states
5. Test responsive layout

### Integration Tests
1. End-to-end workflow monitoring
2. Real-time updates accuracy
3. Cross-tab synchronization
4. WebSocket integration

## Implementation Phases

### Phase 1: Backend API (Day 1)
- [ ] Create `/api/adw-monitor` endpoint
- [ ] Implement state aggregation logic
- [ ] Add status determination
- [ ] Add phase progress calculation
- [ ] Write backend tests

### Phase 2: Frontend Component (Day 2)
- [ ] Create `AdwMonitorCard` component
- [ ] Add API client function
- [ ] Implement polling logic
- [ ] Add basic styling
- [ ] Write frontend tests

### Phase 3: Polish & Integration (Day 3)
- [ ] Add visual polish (animations, colors)
- [ ] Implement user interactions (logs, cancel)
- [ ] Add WebSocket support (optional)
- [ ] Performance optimization
- [ ] Documentation

## Success Metrics

### Functionality
- ✅ Accurately shows all ADW workflows
- ✅ Updates within 10 seconds of status change
- ✅ Shows correct phase progress
- ✅ All user interactions work reliably

### Performance
- ✅ API responds in <200ms
- ✅ Frontend renders in <100ms
- ✅ No jank with 15 concurrent workflows
- ✅ Polling doesn't impact other operations

### UX
- ✅ Clear visual hierarchy
- ✅ Intuitive status indicators
- ✅ Helpful error messages
- ✅ Responsive design works on all screens

## Future Enhancements

1. **Filtering:** Filter by status, classification
2. **Sorting:** Sort by start time, duration, cost
3. **History:** Show completed workflows from last 24h
4. **Notifications:** Browser notifications for failures
5. **Detailed View:** Expandable cards with full details
6. **Logs Streaming:** Real-time log streaming
7. **Cost Breakdown:** Detailed cost per phase
8. **Performance Graphs:** Visual timeline of workflow

---

**Document Version:** 1.0
**Created:** 2025-11-20
**Author:** Claude Code
**Status:** Ready for Implementation
