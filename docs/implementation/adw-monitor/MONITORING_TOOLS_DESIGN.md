# ADW Monitor: Enhanced Monitoring and Debugging Tools Design

**Date:** 2025-11-24
**Version:** 1.0
**Status:** Design Phase
**Related:** [ADW_PIPELINE_ANALYSIS.md](./ADW_PIPELINE_ANALYSIS.md)

---

## Executive Summary

This document outlines the design for enhanced monitoring and debugging tools for the ADW Current Workflow visualization. The goal is to make it easy to diagnose why a workflow failed or is stuck, and provide actionable information to fix it.

### Key Features

1. **Phase Log Viewer** - Real-time and historical log viewing for each phase
2. **Enhanced Status Indicators** - Visual health checks and early warning system
3. **Detailed Phase Information** - Expandable phase cards with diagnostic data
4. **Diagnostic Dashboard** - System-wide health overview and metrics
5. **Quick Actions** - One-click troubleshooting and recovery tools

### Implementation Priority

- **P0 (Critical):** Phase Log Viewer, Enhanced Status Indicators
- **P1 (High):** Detailed Phase Information, Quick Actions
- **P2 (Medium):** Diagnostic Dashboard

---

## 1. Phase Log Viewer

### 1.1 Overview

Provides real-time and historical access to phase execution logs stored in `agents/{adw_id}/{phase_name}/raw_output.jsonl`.

### 1.2 UI/UX Design

```
┌─────────────────────────────────────────────────────────────────┐
│ Phase: Build                                    [X] Close       │
├─────────────────────────────────────────────────────────────────┤
│ Filters: [All ▼] [Errors Only] [Search logs...]     [↻ Refresh]│
├─────────────────────────────────────────────────────────────────┤
│ ┌───────────────────────────────────────────────────────────┐ │
│ │ 12:34:56  INFO   Starting build phase                     │ │
│ │ 12:35:02  INFO   Running: npm install                     │ │
│ │ 12:35:45  WARN   Peer dependency conflict detected        │ │
│ │ 12:36:12  INFO   Running: npm run build                   │ │
│ │ 12:37:30  ERROR  TypeScript compilation failed            │ │
│ │           ├─ src/components/Foo.tsx:15:3                  │ │
│ │           └─ Property 'bar' does not exist on type 'Baz'  │ │
│ │ 12:37:31  INFO   Build phase failed with exit code 1      │ │
│ └───────────────────────────────────────────────────────────┘ │
│                                                                 │
│ Actions: [📥 Download Full Log] [🔍 View in Editor]            │
└─────────────────────────────────────────────────────────────────┘
```

### 1.3 Features

#### Real-time Log Streaming
- **WebSocket connection** for live log updates during active phases
- **Auto-scroll** to follow new entries (with pause option)
- **Update indicator** shows when new logs arrive

#### Historical Log Viewing
- **Parse JSONL format** from `raw_output.jsonl` files
- **Structured display** with timestamps, log levels, and messages
- **Lazy loading** for large log files (load first 100 lines, paginate rest)

#### Error Highlighting
- **Auto-detect error patterns:**
  - Lines containing "ERROR", "FAILED", "Exception"
  - Exit codes != 0
  - Stack traces
- **Color coding:**
  - ERROR: Red background
  - WARN: Yellow background
  - INFO: Normal
- **Error summary** at top showing count and first occurrence

#### Filtering
- **By log level:** All, Error, Warn, Info, Debug
- **By timestamp:** Last 5 min, Last hour, All time
- **Text search:** Filter lines matching search term
- **Regex support** for advanced filtering

### 1.4 API Endpoints

#### GET /api/adw-monitor/{adw_id}/logs/{phase_name}
```typescript
// Request
GET /api/adw-monitor/adw-3af4a34d/logs/build?limit=100&offset=0&level=error

// Response
{
  "phase": "build",
  "adw_id": "adw-3af4a34d",
  "logs": [
    {
      "timestamp": "2025-11-24T12:37:30Z",
      "level": "ERROR",
      "message": "TypeScript compilation failed",
      "source": "build_external.py",
      "metadata": {
        "exit_code": 1,
        "file": "src/components/Foo.tsx",
        "line": 15
      }
    }
  ],
  "total_lines": 1523,
  "has_more": true,
  "log_file_path": "agents/adw-3af4a34d/build/raw_output.jsonl"
}
```

#### WebSocket /ws/adw-monitor/{adw_id}/logs/{phase_name}
```typescript
// Subscribe to live log updates
ws://localhost:8000/ws/adw-monitor/adw-3af4a34d/logs/build

// Message format
{
  "type": "log_entry",
  "data": {
    "timestamp": "2025-11-24T12:37:30Z",
    "level": "ERROR",
    "message": "TypeScript compilation failed"
  }
}
```

### 1.5 Implementation Details

#### Backend (Python)

**File:** `app/server/core/log_viewer.py`

```python
def parse_jsonl_logs(adw_id: str, phase_name: str,
                     limit: int = 100, offset: int = 0,
                     level_filter: str | None = None) -> dict[str, Any]:
    """Parse JSONL log file with filtering and pagination."""
    log_path = Path(f"agents/{adw_id}/{phase_name}/raw_output.jsonl")

    if not log_path.exists():
        return {"logs": [], "total_lines": 0, "has_more": False}

    logs = []
    total_lines = 0

    with open(log_path, 'r') as f:
        for line_num, line in enumerate(f):
            total_lines += 1

            # Skip to offset
            if line_num < offset:
                continue

            # Stop at limit
            if len(logs) >= limit:
                break

            try:
                entry = json.loads(line)

                # Apply level filter
                if level_filter and entry.get("type") != level_filter:
                    continue

                logs.append({
                    "timestamp": entry.get("timestamp"),
                    "level": entry.get("type", "INFO").upper(),
                    "message": entry.get("content", ""),
                    "metadata": entry.get("metadata", {})
                })
            except json.JSONDecodeError:
                # Handle malformed lines
                logs.append({
                    "timestamp": None,
                    "level": "WARN",
                    "message": f"Malformed log entry: {line[:100]}"
                })

    return {
        "logs": logs,
        "total_lines": total_lines,
        "has_more": total_lines > (offset + limit)
    }
```

#### Frontend (TypeScript/React)

**File:** `app/client/src/components/PhaseLogViewer.tsx`

```typescript
import { useState, useEffect, useRef } from 'react';

interface LogEntry {
  timestamp: string;
  level: 'ERROR' | 'WARN' | 'INFO' | 'DEBUG';
  message: string;
  metadata?: Record<string, any>;
}

interface PhaseLogViewerProps {
  adwId: string;
  phaseName: string;
  isLive?: boolean;
}

export function PhaseLogViewer({ adwId, phaseName, isLive = false }: PhaseLogViewerProps) {
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [filter, setFilter] = useState<'all' | 'error' | 'warn'>('all');
  const [autoScroll, setAutoScroll] = useState(true);
  const logContainerRef = useRef<HTMLDivElement>(null);

  // Fetch historical logs
  useEffect(() => {
    fetchLogs();
  }, [adwId, phaseName, filter]);

  // Connect to WebSocket for live updates
  useEffect(() => {
    if (!isLive) return;

    const ws = new WebSocket(`ws://localhost:8000/ws/adw-monitor/${adwId}/logs/${phaseName}`);

    ws.onmessage = (event) => {
      const msg = JSON.parse(event.data);
      if (msg.type === 'log_entry') {
        setLogs(prev => [...prev, msg.data]);

        if (autoScroll && logContainerRef.current) {
          logContainerRef.current.scrollTop = logContainerRef.current.scrollHeight;
        }
      }
    };

    return () => ws.close();
  }, [adwId, phaseName, isLive, autoScroll]);

  const fetchLogs = async () => {
    const response = await fetch(`/api/adw-monitor/${adwId}/logs/${phaseName}?level=${filter}`);
    const data = await response.json();
    setLogs(data.logs);
  };

  const getLogLevelColor = (level: string) => {
    switch (level) {
      case 'ERROR': return 'bg-red-100 text-red-800';
      case 'WARN': return 'bg-yellow-100 text-yellow-800';
      default: return 'bg-white text-gray-800';
    }
  };

  return (
    <div className="phase-log-viewer">
      {/* Filter controls */}
      <div className="filters">
        <select value={filter} onChange={(e) => setFilter(e.target.value as any)}>
          <option value="all">All Logs</option>
          <option value="error">Errors Only</option>
          <option value="warn">Warnings</option>
        </select>
        <label>
          <input type="checkbox" checked={autoScroll} onChange={(e) => setAutoScroll(e.target.checked)} />
          Auto-scroll
        </label>
      </div>

      {/* Log display */}
      <div ref={logContainerRef} className="log-container overflow-y-auto h-96">
        {logs.map((log, idx) => (
          <div key={idx} className={`log-entry p-2 ${getLogLevelColor(log.level)}`}>
            <span className="timestamp">{log.timestamp}</span>
            <span className="level font-bold">{log.level}</span>
            <span className="message">{log.message}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
```

---

## 2. Enhanced Status Indicators

### 2.1 Overview

Visual indicators for common issues with proactive health checks that warn before failures occur.

### 2.2 Status Indicator Types

#### Phase Status Icons

```
┌─────────────────────────────────────────────────────────┐
│ Plan    Build    Lint    Test    Review    Ship        │
│  ✓       ⚡       ⏸️       ❌       ⏳        ⏱️         │
│                                                         │
│ ✓  Completed successfully                              │
│ ⚡  Currently running (process active)                  │
│ ⏸️  Paused (worktree exists, no process)               │
│ ❌  Failed (error detected)                             │
│ ⏳  Queued (waiting to start)                           │
│ ⏱️  Timeout warning (>90% of expected duration)        │
│ ⚠️  Health check warning (port conflict, state issue)  │
└─────────────────────────────────────────────────────────┘
```

#### Health Check Indicators

**Port Health:**
```
🟢 Ports Available (9108, 9208)
🟡 Port Collision Warning (9108 in use by adw-xyz)
🔴 Port Unavailable (manual intervention required)
```

**Worktree Health:**
```
🟢 Worktree Clean (all files committed)
🟡 Worktree Modified (uncommitted changes)
🔴 Worktree Corrupted (git errors detected)
```

**State File Health:**
```
🟢 State Valid (last update 5s ago)
🟡 State Stale (no update in 10 minutes)
🔴 State Corrupted (JSON parse error)
```

**Process Health:**
```
🟢 Process Active (PID 12345, CPU 45%, MEM 2.1GB)
🟡 Process Idle (no activity in 5 minutes)
🔴 Process Zombie (exit code 1, not cleaned up)
```

### 2.3 Warning System

#### Predictive Warnings

**Timeout Warning:**
- Show when phase duration > 90% of expected duration
- "Build phase running for 8m (expected: 9m). Possible hang?"

**Resource Warning:**
- Show when only 1-2 ports remain available
- "Port pool depleting (13/15 used). Consider cleanup."

**State Inconsistency Warning:**
- Show when state contradicts reality
- "State shows 'running' but no process found. Possible crash?"

### 2.4 API Endpoints

#### GET /api/adw-monitor/{adw_id}/health
```typescript
// Response
{
  "adw_id": "adw-3af4a34d",
  "overall_health": "warning",  // ok | warning | critical
  "checks": {
    "ports": {
      "status": "ok",
      "backend_port": 9108,
      "frontend_port": 9208,
      "available": true,
      "conflicts": []
    },
    "worktree": {
      "status": "warning",
      "path": "/Users/Warmonger0/tac/tac-webbuilder/trees/adw-3af4a34d",
      "exists": true,
      "clean": false,
      "uncommitted_files": ["src/components/Foo.tsx"]
    },
    "state_file": {
      "status": "ok",
      "path": "agents/adw-3af4a34d/adw_state.json",
      "valid": true,
      "last_update": "2025-11-24T12:40:15Z",
      "age_seconds": 5
    },
    "process": {
      "status": "ok",
      "active": true,
      "pid": 12345,
      "cpu_percent": 45.2,
      "memory_mb": 2156,
      "command": "python aider.py"
    }
  },
  "warnings": [
    {
      "type": "timeout_warning",
      "severity": "medium",
      "message": "Build phase running for 8m (expected: 9m). Possible hang?",
      "phase": "build"
    }
  ]
}
```

### 2.5 Implementation

**Backend:** `app/server/core/health_checks.py`

```python
def check_port_health(adw_id: str, state: dict) -> dict:
    """Check if allocated ports are available and in use."""
    backend_port = state.get("backend_port")
    frontend_port = state.get("frontend_port")

    checks = {
        "status": "ok",
        "backend_port": backend_port,
        "frontend_port": frontend_port,
        "available": True,
        "conflicts": []
    }

    # Check if ports are actually in use
    if backend_port and not is_port_in_use(backend_port):
        checks["warnings"] = ["Backend port allocated but not in use"]
        checks["status"] = "warning"

    # Check for conflicts with other workflows
    conflicts = find_port_conflicts(adw_id, backend_port, frontend_port)
    if conflicts:
        checks["conflicts"] = conflicts
        checks["status"] = "critical"

    return checks

def check_worktree_health(adw_id: str) -> dict:
    """Check worktree status and git state."""
    worktree_path = Path(f"trees/{adw_id}")

    checks = {
        "status": "ok",
        "path": str(worktree_path),
        "exists": worktree_path.exists(),
        "clean": True,
        "uncommitted_files": []
    }

    if not worktree_path.exists():
        checks["status"] = "critical"
        return checks

    # Check for uncommitted changes
    result = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=worktree_path,
        capture_output=True,
        text=True
    )

    if result.stdout.strip():
        checks["clean"] = False
        checks["uncommitted_files"] = result.stdout.strip().split("\n")
        checks["status"] = "warning"

    return checks
```

---

## 3. Detailed Phase Information

### 3.1 Overview

Expandable phase cards showing comprehensive diagnostic data for each phase.

### 3.2 UI/UX Design

```
┌─────────────────────────────────────────────────────────────┐
│ Build Phase                                       [▼ Expand]│
├─────────────────────────────────────────────────────────────┤
│ Status: ❌ Failed                                           │
│                                                             │
│ ┌─────────────────────────────────────────────────────────┐│
│ │ Timing                                                  ││
│ │ • Started:  2025-11-24 12:35:00                         ││
│ │ • Ended:    2025-11-24 12:37:31                         ││
│ │ • Duration: 2m 31s (expected: 3-10m)                    ││
│ │                                                         ││
│ │ Exit Information                                        ││
│ │ • Exit Code: 1                                          ││
│ │ • Error: TypeScript compilation failed                  ││
│ │ • First Error: src/components/Foo.tsx:15:3              ││
│ │                                                         ││
│ │ Resource Usage                                          ││
│ │ • Backend Port:  9108 (in use)                          ││
│ │ • Frontend Port: 9208 (in use)                          ││
│ │ • Worktree: /trees/adw-3af4a34d                         ││
│ │ • State File: agents/adw-3af4a34d/adw_state.json        ││
│ │                                                         ││
│ │ Dependencies                                            ││
│ │ • Requires: Plan ✓                                      ││
│ │ • Blocks: Lint, Test, Review                            ││
│ │                                                         ││
│ │ Actions                                                 ││
│ │ [🔍 View Full Logs] [🔄 Retry Phase] [⏭️ Skip Phase]   ││
│ │ [📁 Open Worktree] [📄 View State File]                 ││
│ └─────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────┘
```

### 3.3 Data Model

```typescript
interface PhaseDetails {
  name: string;
  status: 'pending' | 'running' | 'completed' | 'failed' | 'skipped';

  timing: {
    started_at: string | null;
    ended_at: string | null;
    duration_seconds: number | null;
    expected_duration_range: [number, number]; // [min, max] in seconds
  };

  exit_info: {
    exit_code: number | null;
    error_message: string | null;
    first_error_line: string | null;
    error_count: number;
  };

  resources: {
    backend_port: number | null;
    frontend_port: number | null;
    worktree_path: string | null;
    state_file_path: string;
    log_file_path: string;
  };

  dependencies: {
    requires: string[];      // Phases that must complete first
    blocks: string[];        // Phases that depend on this
    can_skip: boolean;       // Whether this phase is optional
  };

  process_info: {
    pid: number | null;
    command: string | null;
    cpu_percent: number | null;
    memory_mb: number | null;
    is_active: boolean;
  };
}
```

### 3.4 API Endpoints

#### GET /api/adw-monitor/{adw_id}/phases/{phase_name}
```typescript
// Response
{
  "phase": {
    "name": "build",
    "status": "failed",
    "timing": {
      "started_at": "2025-11-24T12:35:00Z",
      "ended_at": "2025-11-24T12:37:31Z",
      "duration_seconds": 151,
      "expected_duration_range": [180, 600]
    },
    "exit_info": {
      "exit_code": 1,
      "error_message": "TypeScript compilation failed",
      "first_error_line": "src/components/Foo.tsx:15:3 - Property 'bar' does not exist",
      "error_count": 3
    },
    "resources": {
      "backend_port": 9108,
      "frontend_port": 9208,
      "worktree_path": "/Users/Warmonger0/tac/tac-webbuilder/trees/adw-3af4a34d",
      "state_file_path": "agents/adw-3af4a34d/adw_state.json",
      "log_file_path": "agents/adw-3af4a34d/build/raw_output.jsonl"
    },
    "dependencies": {
      "requires": ["plan"],
      "blocks": ["lint", "test", "review"],
      "can_skip": false
    }
  }
}
```

### 3.5 Quick Actions

#### Retry Phase
- **Endpoint:** `POST /api/adw-monitor/{adw_id}/phases/{phase_name}/retry`
- **Action:** Re-runs the phase script with same parameters
- **Safety:** Confirms no process is running, cleans up state

#### Skip Phase
- **Endpoint:** `POST /api/adw-monitor/{adw_id}/phases/{phase_name}/skip`
- **Action:** Marks phase as skipped, continues to next phase
- **Constraint:** Only available for optional phases (doc, validate)

#### View State
- **Action:** Opens state file in read-only JSON viewer modal
- **Features:** Syntax highlighting, collapsible sections, search

#### Open in Editor
- **Action:** Opens `code` or configured editor at worktree path
- **Platform-specific:** Uses `open` on macOS, `xdg-open` on Linux

---

## 4. Diagnostic Dashboard

### 4.1 Overview

System-wide health overview showing metrics across all workflows.

### 4.2 UI/UX Design

```
┌───────────────────────────────────────────────────────────────┐
│ ADW Diagnostic Dashboard                   Updated: 2s ago   │
├───────────────────────────────────────────────────────────────┤
│ System Health: 🟡 Warning                                     │
│                                                               │
│ ┌─────────────────┬─────────────────┬─────────────────────┐  │
│ │ Active Workflows│ Port Usage      │ Worktree Usage      │  │
│ │                 │                 │                     │  │
│ │     3 / 15      │   13 / 100      │    9 / unlimited    │  │
│ │   ████░░░░░░    │   ████████████░ │    ███░░░░░░░░░    │  │
│ └─────────────────┴─────────────────┴─────────────────────┘  │
│                                                               │
│ Active Worktrees                                              │
│ ┌─────────────────────────────────────────────────────────┐  │
│ │ adw-3af4a34d  #83  Build Failed   Ports: 9108,9208     │  │
│ │ adw-446dab5f  #83  Test Running   Ports: 9103,9203     │  │
│ │ adw-2cfe5aa9  #79  Review Done    Ports: 9105,9205     │  │
│ └─────────────────────────────────────────────────────────┘  │
│                                                               │
│ Recent Errors (Last Hour)                                     │
│ ┌─────────────────────────────────────────────────────────┐  │
│ │ 12:37 Build    adw-3af4a34d  TypeScript compilation     │  │
│ │ 11:52 Test     adw-50443844  E2E timeout (600s)         │  │
│ │ 11:23 Port     adw-d7e1040d  Port 9110 unavailable      │  │
│ └─────────────────────────────────────────────────────────┘  │
│                                                               │
│ Performance Metrics                                           │
│ ┌─────────────────────────────────────────────────────────┐  │
│ │ Phase Success Rates (Last 7 Days)                       │  │
│ │                                                         │  │
│ │ Plan     ████████████████████ 95%                       │  │
│ │ Build    ████████████████░░░░ 82%                       │  │
│ │ Lint     ███████████████████░ 93%                       │  │
│ │ Test     ████████████░░░░░░░░ 68% ⚠️                    │  │
│ │ Review   ████████████████░░░░ 88%                       │  │
│ │ Ship     ███████████████████░ 91%                       │  │
│ │                                                         │  │
│ │ Average Phase Durations                                 │  │
│ │ Plan: 3m 12s  |  Build: 7m 45s  |  Test: 12m 30s       │  │
│ └─────────────────────────────────────────────────────────┘  │
│                                                               │
│ Actions: [🧹 Cleanup All] [🔍 View Full Metrics]             │
└───────────────────────────────────────────────────────────────┘
```

### 4.3 Metrics Tracked

#### System Metrics
- Active workflows count
- Port pool usage (used/available)
- Worktree disk usage
- Average CPU/memory per workflow

#### Error Metrics
- Errors by phase (last hour, last day, last week)
- Most common error types
- Time to failure (average time before error)

#### Performance Metrics
- Phase success rates (% successful completions)
- Average phase durations
- P50, P90, P95 duration percentiles
- Workflow completion rate

### 4.4 API Endpoints

#### GET /api/adw-monitor/dashboard
```typescript
// Response
{
  "system_health": "warning",
  "active_workflows": 3,
  "total_workflows": 15,

  "port_usage": {
    "used": 13,
    "total": 100,
    "available": 87,
    "conflicts": []
  },

  "worktree_usage": {
    "count": 9,
    "total_size_mb": 4500,
    "oldest_age_days": 7
  },

  "recent_errors": [
    {
      "timestamp": "2025-11-24T12:37:00Z",
      "phase": "build",
      "adw_id": "adw-3af4a34d",
      "error": "TypeScript compilation failed"
    }
  ],

  "phase_metrics": {
    "plan": {
      "success_rate": 0.95,
      "avg_duration_seconds": 192,
      "p90_duration_seconds": 245
    },
    "test": {
      "success_rate": 0.68,
      "avg_duration_seconds": 750,
      "p90_duration_seconds": 900
    }
  }
}
```

#### POST /api/adw-monitor/actions/cleanup-all
```typescript
// Request
{
  "dry_run": false,
  "age_threshold_days": 7,
  "include_failed": true
}

// Response
{
  "cleaned_worktrees": ["adw-old123", "adw-old456"],
  "released_ports": [9100, 9101, 9200, 9201],
  "disk_space_freed_mb": 1200
}
```

---

## 5. Component Architecture

### 5.1 Component Hierarchy

```
AdwMonitorCard (existing)
├── CurrentWorkflowDisplay
│   ├── PhaseVisualization (existing pipeline)
│   └── EnhancedPhaseNode (NEW)
│       ├── PhaseStatusIndicator (NEW)
│       ├── PhaseHealthBadge (NEW)
│       └── PhaseDetailsPanel (NEW)
│           ├── PhaseTimingInfo
│           ├── PhaseResourceInfo
│           ├── PhaseErrorSummary
│           └── PhaseQuickActions
└── WorkflowHealthPanel (NEW)
    ├── PortHealthIndicator
    ├── WorktreeHealthIndicator
    ├── StateHealthIndicator
    └── ProcessHealthIndicator

DiagnosticDashboard (NEW)
├── SystemHealthOverview
│   ├── MetricCard (Workflows, Ports, Worktrees)
│   └── HealthStatusBadge
├── ActiveWorkflowsList
│   └── WorkflowSummaryCard
├── RecentErrorsList
│   └── ErrorLogEntry
└── PerformanceMetricsChart
    ├── PhaseSuccessRateChart
    └── PhaseDurationChart

PhaseLogViewerModal (NEW)
├── LogFilterControls
├── LogStreamDisplay
│   └── LogEntry
└── LogExportActions
```

### 5.2 State Management

```typescript
// Global state (app/client/src/store/adwMonitor.ts)
interface AdwMonitorState {
  workflows: AdwWorkflowStatus[];
  selectedWorkflow: string | null;
  expandedPhases: Set<string>;
  healthChecks: Record<string, HealthCheckResult>;
  dashboardMetrics: DashboardMetrics | null;
  logViewers: Record<string, LogViewerState>;
}

// Actions
- fetchWorkflows()
- selectWorkflow(adwId)
- togglePhaseExpanded(adwId, phase)
- fetchHealthChecks(adwId)
- fetchDashboardMetrics()
- openLogViewer(adwId, phase)
- closeLogViewer(adwId, phase)
```

### 5.3 File Structure

```
app/client/src/
├── components/
│   ├── adw-monitor/
│   │   ├── AdwMonitorCard.tsx (existing, enhanced)
│   │   ├── EnhancedPhaseNode.tsx (NEW)
│   │   ├── PhaseDetailsPanel.tsx (NEW)
│   │   ├── PhaseLogViewer.tsx (NEW)
│   │   ├── WorkflowHealthPanel.tsx (NEW)
│   │   └── DiagnosticDashboard.tsx (NEW)
│   └── ...
├── hooks/
│   ├── useAdwHealth.ts (NEW)
│   ├── usePhaseLogs.ts (NEW)
│   └── useWebSocket.ts (NEW)
├── api/
│   └── adwMonitor.ts (extend existing client.ts)
└── types/
    └── adwMonitor.types.ts (NEW)

app/server/
├── core/
│   ├── adw_monitor.py (existing, enhanced)
│   ├── health_checks.py (NEW)
│   ├── log_viewer.py (NEW)
│   └── phase_actions.py (NEW)
└── routes/
    └── adw_monitor_routes.py (extend existing)
```

---

## 6. Implementation Phases

### Phase 1: Foundation (Week 1)
**Goal:** Enhanced status indicators and basic health checks

- [ ] Implement health check system (ports, worktree, state, process)
- [ ] Add health check API endpoint
- [ ] Create `EnhancedPhaseNode` component with status icons
- [ ] Add warning indicators to phase pipeline
- [ ] Basic error highlighting in current UI

**Deliverable:** Current workflow shows health warnings

### Phase 2: Phase Details (Week 2)
**Goal:** Expandable phase information panels

- [ ] Design and implement `PhaseDetailsPanel` component
- [ ] Add phase timing, exit code, resource info
- [ ] Create phase details API endpoint
- [ ] Implement expand/collapse functionality
- [ ] Add quick action buttons (non-functional placeholders)

**Deliverable:** Click phase to see details

### Phase 3: Log Viewer (Week 3)
**Goal:** View phase logs in modal

- [ ] Implement JSONL log parser backend
- [ ] Create `PhaseLogViewer` modal component
- [ ] Add log filtering (level, search, time)
- [ ] Implement pagination for large logs
- [ ] Add download/export functionality

**Deliverable:** View historical logs for any phase

### Phase 4: Real-time Updates (Week 4)
**Goal:** Live log streaming and status updates

- [ ] Implement WebSocket server for log streaming
- [ ] Add WebSocket client to log viewer
- [ ] Implement real-time health check updates
- [ ] Add auto-refresh for active workflows
- [ ] Performance optimization (lazy loading, caching)

**Deliverable:** Live log updates during active phases

### Phase 5: Quick Actions (Week 5)
**Goal:** One-click troubleshooting

- [ ] Implement retry phase action
- [ ] Implement skip phase action (optional phases only)
- [ ] Add state file viewer
- [ ] Add "Open in Editor" action
- [ ] Implement safety checks and confirmations

**Deliverable:** Retry/skip phases from UI

### Phase 6: Diagnostic Dashboard (Week 6)
**Goal:** System-wide metrics and cleanup

- [ ] Create `DiagnosticDashboard` component
- [ ] Implement system health metrics API
- [ ] Add performance metrics tracking (success rates, durations)
- [ ] Create cleanup action (remove old worktrees/release ports)
- [ ] Add metrics visualization (charts, gauges)

**Deliverable:** Standalone diagnostic dashboard page

---

## 7. User Workflows for Debugging

### Workflow 1: "My workflow failed, why?"

1. **User sees workflow failed in AdwMonitorCard**
2. **Click failed phase (e.g., "Build ❌")**
   - Phase details panel expands
   - Shows: Exit code 1, error message preview
3. **Click "View Full Logs"**
   - Log viewer modal opens
   - Auto-filters to ERROR level
   - First error highlighted
4. **User reads error:** "TypeScript compilation failed - Property 'bar' does not exist"
5. **Click "Open Worktree"**
   - Opens code editor at worktree path
   - User fixes the issue
6. **Click "Retry Phase"**
   - Confirms retry, phase re-runs
   - Log viewer shows live updates
7. **Phase succeeds**, workflow continues

### Workflow 2: "My workflow is stuck"

1. **User sees workflow running for 20 minutes**
2. **Health panel shows:**
   - ⏱️ "Test phase running for 18m (expected: 5-15m)"
   - 🟢 Process active (PID 12345)
3. **Click "View Full Logs"**
   - Last log entry: "Running E2E tests..." (10 minutes ago)
   - No new output
4. **User suspects timeout**
5. **Click "View State File"**
   - Sees `current_phase: "test"`, `status: "running"`
6. **Navigate to Diagnostic Dashboard**
   - Sees Test phase has 68% success rate
   - Average duration: 12m 30s, P90: 15m
7. **User decides to wait** (still within P90)
8. **If still stuck after 15m:**
   - Kill process manually
   - Click "Retry Phase" to restart

### Workflow 3: "I need to clean up resources"

1. **User opens Diagnostic Dashboard**
2. **Sees:**
   - Port usage: 87/100 (13 used)
   - Worktree usage: 9 worktrees, 4.5GB
   - Oldest worktree: 7 days old
3. **Click "Cleanup All"**
   - Modal shows preview:
     - Will remove 3 completed worktrees (>7 days old)
     - Will release 6 ports
     - Will free ~1.2GB disk space
4. **Confirm cleanup**
5. **Dashboard updates:**
   - Port usage: 94/100 (6 used)
   - Worktree usage: 6 worktrees, 3.3GB

### Workflow 4: "Which phase fails most often?"

1. **User opens Diagnostic Dashboard**
2. **Views "Phase Success Rates" section:**
   - Test: 68% ⚠️ (lowest)
   - Build: 82%
   - Plan: 95%
3. **Clicks on "Test 68%"**
4. **Modal shows detailed Test phase metrics:**
   - Total runs: 50
   - Successes: 34
   - Failures: 16
   - Most common errors:
     - "E2E timeout (600s)": 8 occurrences
     - "Vitest assertion failed": 5 occurrences
5. **User investigates timeout issue**
   - Clicks on error to see example logs
   - Identifies long-running test
   - Plans to optimize or increase timeout

---

## 8. Future Enhancements (Post-MVP)

### 8.1 Advanced Features

**AI-Powered Error Diagnosis:**
- Send error logs to Claude API
- Get suggested fixes and explanation
- "Ask Claude about this error" button

**Workflow Comparison:**
- Compare successful vs failed workflow logs side-by-side
- Identify where they diverged
- Useful for flaky test diagnosis

**Automated Recovery:**
- Define recovery strategies per error type
- Auto-retry on transient errors (network, timeout)
- Auto-skip on known non-critical failures

**Performance Profiling:**
- CPU/memory usage graphs over time
- Identify resource bottlenecks
- Phase-by-phase resource breakdown

**Custom Alerts:**
- Email/Slack notifications on failure
- Alert on health check warnings
- Custom alert rules (e.g., "notify if test phase >20m")

### 8.2 Integration Ideas

**GitHub Integration:**
- Post error summary as PR comment
- Link to logs from GitHub UI
- Auto-update PR status based on phases

**Cost Tracking:**
- Show per-phase LLM costs
- Budget alerts
- Cost trend analysis

**Dependency Visualization:**
- Interactive phase dependency graph
- Show which phases block others
- Critical path highlighting

---

## 9. Testing Strategy

### 9.1 Unit Tests

**Backend:**
- `test_health_checks.py` - All health check functions
- `test_log_viewer.py` - JSONL parsing, filtering, pagination
- `test_phase_actions.py` - Retry, skip, cleanup actions

**Frontend:**
- `PhaseLogViewer.test.tsx` - Rendering, filtering, WebSocket
- `EnhancedPhaseNode.test.tsx` - Status icons, health badges
- `DiagnosticDashboard.test.tsx` - Metrics display, cleanup action

### 9.2 Integration Tests

- **Log streaming:** Start phase, verify logs appear in real-time
- **Health checks:** Corrupt state file, verify warning shown
- **Retry action:** Fail phase, retry, verify success
- **Cleanup action:** Create old worktrees, run cleanup, verify removal

### 9.3 E2E Tests

- **Full debugging workflow:**
  1. Trigger workflow failure
  2. Open log viewer
  3. Identify error
  4. Retry phase
  5. Verify success

---

## 10. Success Metrics

### User Experience Metrics
- **Time to Diagnose:** Average time from "workflow failed" to "identified root cause"
  - Target: <2 minutes (vs current ~10 minutes manual investigation)

- **Self-Service Rate:** % of issues resolved without manual intervention
  - Target: 80% of failures resolved via retry/skip

- **Log Viewer Usage:** % of failures where logs are viewed
  - Target: >90%

### System Health Metrics
- **Early Warning Detection:** % of failures predicted by health checks
  - Target: >60% of failures have pre-failure warnings

- **Resource Cleanup Rate:** % of completed workflows cleaned up within 24h
  - Target: >95%

### Development Velocity
- **Reduced Debug Time:** Developer time spent debugging workflows
  - Target: 50% reduction in debug time

- **Workflow Reliability:** Overall workflow success rate improvement
  - Target: +10% success rate after fixes identified via monitoring

---

## 11. Risks and Mitigations

### Risk 1: WebSocket Performance
**Issue:** 100+ concurrent log streams could overload server

**Mitigation:**
- Limit to 5 active log viewers per user
- Implement server-side rate limiting
- Use efficient JSONL streaming (line-by-line, not full file)

### Risk 2: Large Log Files
**Issue:** 100MB+ log files slow down UI

**Mitigation:**
- Lazy loading (load first 100 lines, paginate rest)
- Streaming parse (don't load entire file into memory)
- Download option for full logs

### Risk 3: State File Race Conditions
**Issue:** Reading state while it's being written

**Mitigation:**
- Implement file locking (addressed in ADW_PIPELINE_ANALYSIS.md P0)
- Add retry logic on read failures
- Cache state with short TTL (5s)

### Risk 4: Quick Actions Safety
**Issue:** User accidentally retries critical phase

**Mitigation:**
- Confirmation modal for destructive actions
- Safety checks (e.g., verify no process running)
- Audit log of all actions taken

---

## 12. Documentation

### User Documentation
- **Monitoring Guide:** How to use monitoring tools to debug
- **Health Checks Reference:** What each health check means
- **Quick Actions Guide:** When to retry vs skip vs cleanup
- **Dashboard Metrics Explained:** Understanding success rates and durations

### Developer Documentation
- **API Reference:** All new endpoints with examples
- **Component API:** Props and usage for new React components
- **WebSocket Protocol:** Message format for log streaming
- **Adding Health Checks:** How to add new health check types

---

## Appendix A: API Reference Summary

### Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/adw-monitor/{adw_id}/logs/{phase}` | GET | Fetch historical logs |
| `/ws/adw-monitor/{adw_id}/logs/{phase}` | WS | Live log streaming |
| `/api/adw-monitor/{adw_id}/health` | GET | Health check results |
| `/api/adw-monitor/{adw_id}/phases/{phase}` | GET | Detailed phase info |
| `/api/adw-monitor/{adw_id}/phases/{phase}/retry` | POST | Retry failed phase |
| `/api/adw-monitor/{adw_id}/phases/{phase}/skip` | POST | Skip optional phase |
| `/api/adw-monitor/dashboard` | GET | System-wide metrics |
| `/api/adw-monitor/actions/cleanup-all` | POST | Cleanup old resources |

---

## Appendix B: Wireframe Mockups (ASCII)

### Phase Node Expanded

```
╔═══════════════════════════════════════════════════════════════╗
║ Build Phase                                         [▲ Collapse]║
╠═══════════════════════════════════════════════════════════════╣
║ Status: ❌ Failed                           Health: 🟢 OK      ║
║                                                               ║
║ ┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓ ║
║ ┃ ⏱️  Timing                                                ┃ ║
║ ┃   Started:  12:35:00  |  Ended: 12:37:31  |  2m 31s       ┃ ║
║ ┃   Expected: 3-10 minutes                                  ┃ ║
║ ┣━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┫ ║
║ ┃ ❌ Exit Information                                       ┃ ║
║ ┃   Exit Code: 1                                            ┃ ║
║ ┃   Error: TypeScript compilation failed                    ┃ ║
║ ┃   Location: src/components/Foo.tsx:15:3                   ┃ ║
║ ┣━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┫ ║
║ ┃ 🔧 Resources                                              ┃ ║
║ ┃   Ports: 9108 (backend), 9208 (frontend)                  ┃ ║
║ ┃   Worktree: trees/adw-3af4a34d                            ┃ ║
║ ┃   Logs: agents/adw-3af4a34d/build/raw_output.jsonl        ┃ ║
║ ┣━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┫ ║
║ ┃ 🔗 Dependencies                                           ┃ ║
║ ┃   Requires: Plan ✓                                        ┃ ║
║ ┃   Blocks: Lint, Test, Review                              ┃ ║
║ ┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛ ║
║                                                               ║
║ [🔍 View Logs] [🔄 Retry] [📁 Open Worktree] [📄 View State]  ║
╚═══════════════════════════════════════════════════════════════╝
```

---

## Summary

This design provides a comprehensive monitoring and debugging solution for ADW workflows:

1. **Phase Log Viewer** enables quick access to execution logs with filtering and real-time streaming
2. **Enhanced Status Indicators** provide early warnings before failures occur
3. **Detailed Phase Information** gives developers all context needed to diagnose issues
4. **Diagnostic Dashboard** offers system-wide visibility and cleanup tools
5. **Quick Actions** enable self-service recovery without manual intervention

The phased implementation approach ensures we deliver value incrementally, starting with the highest-impact features (health checks and log viewing) before building out advanced functionality (dashboard, metrics).

**Key Success Factor:** Making debugging workflows feel like using browser DevTools - intuitive, fast, and comprehensive.
