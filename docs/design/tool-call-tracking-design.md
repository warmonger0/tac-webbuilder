# Tool Call Tracking System Design

**Feature ID:** #128
**Created:** 2025-12-18
**Status:** Design
**Priority:** High
**Complexity:** Medium
**Estimated Effort:** 16 hours

---

## Table of Contents

1. [Overview](#overview)
2. [Goals & Requirements](#goals--requirements)
3. [Database Schema](#database-schema)
4. [Data Model](#data-model)
5. [Implementation Architecture](#implementation-architecture)
6. [API Design](#api-design)
7. [Analytics Queries](#analytics-queries)
8. [Migration Strategy](#migration-strategy)
9. [Testing Strategy](#testing-strategy)
10. [Rollout Plan](#rollout-plan)

---

## Overview

### Problem Statement

Currently, ADW workflows track high-level metrics (cost, duration, tokens) at the workflow and phase level, but lack visibility into individual tool calls (Bash, Read, Write, Edit, Grep). This prevents:

- Identifying tool usage patterns and inefficiencies
- Detecting redundant operations (e.g., reading the same file multiple times)
- Analyzing tool call sequences for pattern learning
- Attributing costs and latency to specific tool types
- Optimizing tool selection and usage strategies

### Solution

Implement comprehensive tracking of individual tool calls during ADW workflow execution by:

1. Extending `task_logs` table with a `tool_calls` JSONB field
2. Modifying `observability.py` to capture tool invocations
3. Creating analytics queries for tool usage analysis
4. Building dashboard visualizations

### Success Criteria

- ✅ Tool calls tracked in `task_logs.tool_calls` JSONB field
- ✅ Tool call data includes: name, duration_ms, success, parameters, result, context_size
- ✅ Tool sequence patterns detected and stored
- ✅ Analytics dashboard shows tool usage patterns
- ✅ API endpoints for tool call queries and analysis
- ✅ Documentation updated with tool tracking details

---

## Goals & Requirements

### Functional Requirements

1. **Capture Tool Calls**: Record every Bash, Read, Write, Edit, Grep operation during workflow execution
2. **Timing Data**: Track duration_ms for each tool call
3. **Success Tracking**: Record whether each tool call succeeded or failed
4. **Parameters**: Store tool call parameters (file paths, commands, etc.)
5. **Context Metrics**: Track context size before tool call, tokens consumed
6. **Sequence Analysis**: Detect and store tool call sequences (e.g., Read→Edit→Write)
7. **Analytics**: Query tool usage patterns, redundancy, efficiency

### Non-Functional Requirements

1. **Zero Overhead**: Tool call tracking must not slow down workflow execution
2. **Non-Blocking**: Tracking failures must not block workflow progress
3. **Backward Compatible**: Existing workflows must continue to function
4. **Scalable**: Must handle 1000s of tool calls per workflow
5. **Query Performance**: Analytics queries must return in < 2 seconds

### Constraints

1. **No New Tables**: Use existing `task_logs` table with JSONB field
2. **Minimal Code Changes**: Extend existing observability module
3. **No Breaking Changes**: Maintain existing API contracts

---

## Database Schema

### Migration: Add tool_calls Column

**File:** `app/server/db/migrations/019_add_tool_calls_tracking.sql`

```sql
-- Migration 019: Add tool call tracking to task_logs
-- Created: 2025-12-18

-- Add tool_calls JSONB column to task_logs
ALTER TABLE task_logs ADD COLUMN tool_calls JSONB DEFAULT '[]'::jsonb;

-- Add index for querying tool calls
CREATE INDEX idx_task_logs_tool_calls ON task_logs USING GIN (tool_calls);

-- Add comment
COMMENT ON COLUMN task_logs.tool_calls IS 'Array of tool call records with timing, success, parameters, and results';

-- Example tool_calls structure:
-- [
--   {
--     "tool_name": "Bash",
--     "command": "pytest tests/",
--     "duration_ms": 1250,
--     "success": true,
--     "exit_code": 0,
--     "tokens_consumed": 450,
--     "cache_hit": true,
--     "context_size_before": 45000,
--     "timestamp": "2025-12-18T10:00:00Z",
--     "error_message": null
--   },
--   {
--     "tool_name": "Read",
--     "file_path": "app/server/routes.py",
--     "duration_ms": 80,
--     "success": true,
--     "lines_read": 250,
--     "file_size_bytes": 12500,
--     "timestamp": "2025-12-18T10:00:05Z"
--   },
--   {
--     "tool_name": "Edit",
--     "file_path": "app/server/routes.py",
--     "duration_ms": 120,
--     "success": true,
--     "lines_changed": 15,
--     "old_string_length": 150,
--     "new_string_length": 200,
--     "timestamp": "2025-12-18T10:00:10Z"
--   }
-- ]
```

### PostgreSQL Schema (for reference)

```sql
-- Full task_logs schema with tool_calls
CREATE TABLE task_logs (
    id SERIAL PRIMARY KEY,
    adw_id TEXT NOT NULL,
    issue_number INTEGER,
    workflow_template TEXT,

    -- Phase Details
    phase_name TEXT NOT NULL,
    phase_number INTEGER,
    phase_status TEXT NOT NULL,

    -- Logging
    log_message TEXT,
    error_message TEXT,

    -- Timing
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    duration_seconds REAL,

    -- Cost
    tokens_used INTEGER,
    cost_usd REAL,

    -- NEW: Tool Call Tracking
    tool_calls JSONB DEFAULT '[]'::jsonb,

    -- Metadata
    captured_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX idx_task_logs_adw_id ON task_logs(adw_id);
CREATE INDEX idx_task_logs_issue_number ON task_logs(issue_number);
CREATE INDEX idx_task_logs_phase_status ON task_logs(phase_status);
CREATE INDEX idx_task_logs_tool_calls ON task_logs USING GIN (tool_calls);
```

---

## Data Model

### Tool Call Record Structure

```typescript
interface ToolCallRecord {
  // Core fields (all tools)
  tool_name: "Bash" | "Read" | "Write" | "Edit" | "Grep" | "WebFetch" | "Task";
  duration_ms: number;
  success: boolean;
  timestamp: string; // ISO 8601
  error_message?: string;

  // Context metrics (all tools)
  tokens_consumed?: number;
  cache_hit?: boolean;
  context_size_before?: number;

  // Tool-specific fields

  // Bash
  command?: string;
  exit_code?: number;
  stdout_lines?: number;
  stderr_lines?: number;

  // Read
  file_path?: string;
  lines_read?: number;
  file_size_bytes?: number;
  offset?: number;
  limit?: number;

  // Write
  // file_path (from above)
  bytes_written?: number;
  created_new_file?: boolean;

  // Edit
  // file_path (from above)
  lines_changed?: number;
  old_string_length?: number;
  new_string_length?: number;
  replace_all?: boolean;

  // Grep
  pattern?: string;
  files_matched?: number;
  total_matches?: number;
  // file_path (from above) for path filter

  // WebFetch
  url?: string;
  http_status?: number;
  response_size_bytes?: number;

  // Task (sub-agent)
  subagent_type?: string;
  agent_result?: string; // "success" | "failure"
}
```

### Pydantic Models

**File:** `app/server/core/models/observability.py`

```python
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, Literal


class ToolCallRecord(BaseModel):
    """Individual tool call record."""

    # Core fields
    tool_name: Literal["Bash", "Read", "Write", "Edit", "Grep", "WebFetch", "Task"]
    duration_ms: int
    success: bool
    timestamp: datetime
    error_message: Optional[str] = None

    # Context metrics
    tokens_consumed: Optional[int] = None
    cache_hit: Optional[bool] = None
    context_size_before: Optional[int] = None

    # Tool-specific fields
    # Bash
    command: Optional[str] = None
    exit_code: Optional[int] = None
    stdout_lines: Optional[int] = None
    stderr_lines: Optional[int] = None

    # Read
    file_path: Optional[str] = None
    lines_read: Optional[int] = None
    file_size_bytes: Optional[int] = None
    offset: Optional[int] = None
    limit: Optional[int] = None

    # Write
    bytes_written: Optional[int] = None
    created_new_file: Optional[bool] = None

    # Edit
    lines_changed: Optional[int] = None
    old_string_length: Optional[int] = None
    new_string_length: Optional[int] = None
    replace_all: Optional[bool] = None

    # Grep
    pattern: Optional[str] = None
    files_matched: Optional[int] = None
    total_matches: Optional[int] = None

    # WebFetch
    url: Optional[str] = None
    http_status: Optional[int] = None
    response_size_bytes: Optional[int] = None

    # Task
    subagent_type: Optional[str] = None
    agent_result: Optional[Literal["success", "failure"]] = None


class TaskLogWithToolCalls(BaseModel):
    """Task log with tool calls."""

    id: int
    adw_id: str
    issue_number: Optional[int] = None
    workflow_template: Optional[str] = None

    phase_name: str
    phase_number: Optional[int] = None
    phase_status: str

    log_message: Optional[str] = None
    error_message: Optional[str] = None

    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration_seconds: Optional[float] = None

    tokens_used: Optional[int] = None
    cost_usd: Optional[float] = None

    tool_calls: list[ToolCallRecord] = Field(default_factory=list)

    captured_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
```

---

## Implementation Architecture

### Phase 1: Data Capture (observability.py)

**File:** `adws/adw_modules/observability.py`

#### Modified Function Signature

```python
def log_task_completion(
    adw_id: str,
    issue_number: int,
    phase_name: str,
    phase_number: int,
    success: bool,
    log_message: str,
    error_message: str | None = None,
    tool_calls: list[dict] | None = None,  # NEW PARAMETER
) -> None:
    """
    Log task completion with optional tool call tracking.

    Args:
        adw_id: Workflow ID
        issue_number: GitHub issue number
        phase_name: Name of phase (Plan, Build, Test, etc.)
        phase_number: Phase number (1-based)
        success: Whether phase succeeded
        log_message: Human-readable status message
        error_message: Error message if failed
        tool_calls: List of tool call records (NEW)
    """
    payload = {
        "adw_id": adw_id,
        "issue_number": issue_number,
        "phase_name": phase_name,
        "phase_number": phase_number,
        "phase_status": "completed" if success else "failed",
        "log_message": log_message,
        "error_message": error_message,
        "tool_calls": tool_calls or [],  # NEW
    }

    # Send to backend API
    try:
        response = requests.post(
            f"{BACKEND_URL}/api/v1/observability/task-logs",
            json=payload,
            timeout=5,
        )
        response.raise_for_status()
    except Exception as e:
        logger.warning(f"Failed to log task completion: {e}")
        # Fallback: Write to JSONL
        structured_logger.log_phase(phase_name, "completed", payload)
```

#### ADW Phase Wrapper

```python
# In ADW workflow execution code
import time
from typing import Any


class ToolCallTracker:
    """Context manager for tracking tool calls during phase execution."""

    def __init__(self):
        self.tool_calls = []

    def record_tool_call(
        self,
        tool_name: str,
        duration_ms: int,
        success: bool,
        **kwargs,
    ) -> None:
        """Record a tool call."""
        record = {
            "tool_name": tool_name,
            "duration_ms": duration_ms,
            "success": success,
            "timestamp": datetime.now().isoformat(),
            **kwargs,
        }
        self.tool_calls.append(record)

    def get_tool_calls(self) -> list[dict]:
        """Get all recorded tool calls."""
        return self.tool_calls


# Usage in ADW phase
def execute_build_phase(adw_id: str, issue_number: int):
    """Execute build phase with tool call tracking."""
    tracker = ToolCallTracker()
    started_at = time.time()

    try:
        # Example: Run tests with Bash
        test_start = time.time()
        result = subprocess.run(
            ["pytest", "tests/"],
            capture_output=True,
            text=True,
        )
        test_duration = int((time.time() - test_start) * 1000)

        tracker.record_tool_call(
            tool_name="Bash",
            command="pytest tests/",
            duration_ms=test_duration,
            success=result.returncode == 0,
            exit_code=result.returncode,
            stdout_lines=len(result.stdout.splitlines()),
            stderr_lines=len(result.stderr.splitlines()),
        )

        # Example: Read file
        read_start = time.time()
        with open("app/server/routes.py", "r") as f:
            content = f.read()
        read_duration = int((time.time() - read_start) * 1000)

        tracker.record_tool_call(
            tool_name="Read",
            file_path="app/server/routes.py",
            duration_ms=read_duration,
            success=True,
            lines_read=len(content.splitlines()),
            file_size_bytes=len(content.encode()),
        )

        # Log phase completion with tool calls
        log_task_completion(
            adw_id=adw_id,
            issue_number=issue_number,
            phase_name="Build",
            phase_number=3,
            success=True,
            log_message="Build phase completed successfully",
            tool_calls=tracker.get_tool_calls(),  # Pass tool calls
        )

    except Exception as e:
        log_task_completion(
            adw_id=adw_id,
            issue_number=issue_number,
            phase_name="Build",
            phase_number=3,
            success=False,
            log_message=f"Build phase failed: {e}",
            error_message=str(e),
            tool_calls=tracker.get_tool_calls(),  # Still log tool calls
        )
```

### Phase 2: Storage (Backend API)

**File:** `app/server/routes/observability_routes.py`

```python
from core.models.observability import TaskLogCreate, ToolCallRecord
from repositories.task_log_repository import TaskLogRepository


@router.post("/task-logs", status_code=201)
async def create_task_log(task_log: TaskLogCreate):
    """
    Create a new task log entry with optional tool calls.

    Request Body:
        {
            "adw_id": "abc123",
            "phase_name": "Build",
            "phase_status": "completed",
            "tool_calls": [
                {
                    "tool_name": "Bash",
                    "command": "pytest tests/",
                    "duration_ms": 1250,
                    "success": true,
                    "exit_code": 0
                }
            ]
        }
    """
    repo = TaskLogRepository()
    task_log_id = repo.create(task_log)
    return {"id": task_log_id, "status": "created"}
```

**File:** `app/server/repositories/task_log_repository.py`

```python
import json
from database import get_database_adapter


class TaskLogRepository:
    """Repository for task log operations."""

    def create(self, task_log: TaskLogCreate) -> int:
        """Create a new task log with tool calls."""
        adapter = get_database_adapter()

        # Convert tool_calls to JSON
        tool_calls_json = json.dumps([tc.dict() for tc in task_log.tool_calls])

        query = """
            INSERT INTO task_logs (
                adw_id,
                issue_number,
                workflow_template,
                phase_name,
                phase_number,
                phase_status,
                log_message,
                error_message,
                started_at,
                completed_at,
                duration_seconds,
                tokens_used,
                cost_usd,
                tool_calls
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            RETURNING id
        """

        result = adapter.execute(
            query,
            (
                task_log.adw_id,
                task_log.issue_number,
                task_log.workflow_template,
                task_log.phase_name,
                task_log.phase_number,
                task_log.phase_status,
                task_log.log_message,
                task_log.error_message,
                task_log.started_at,
                task_log.completed_at,
                task_log.duration_seconds,
                task_log.tokens_used,
                task_log.cost_usd,
                tool_calls_json,
            ),
        )

        return result[0]["id"]
```

### Phase 3: Analytics Queries

**File:** `app/server/services/tool_analytics_service.py`

```python
from database import get_database_adapter
from typing import Any


class ToolAnalyticsService:
    """Service for analyzing tool call patterns and usage."""

    def __init__(self):
        self.adapter = get_database_adapter()

    def get_tool_usage_summary(self, days: int = 30) -> dict[str, Any]:
        """
        Get summary of tool usage across all workflows.

        Returns:
            {
                "total_tool_calls": 12500,
                "by_tool": {
                    "Bash": {"count": 5000, "avg_duration_ms": 850, "success_rate": 0.92},
                    "Read": {"count": 4000, "avg_duration_ms": 120, "success_rate": 0.99},
                    "Edit": {"count": 2000, "avg_duration_ms": 150, "success_rate": 0.95},
                    "Write": {"count": 1500, "avg_duration_ms": 100, "success_rate": 0.98}
                },
                "top_commands": [
                    {"command": "pytest tests/", "count": 450, "avg_duration_ms": 1200},
                    {"command": "npm run build", "count": 320, "avg_duration_ms": 3500}
                ]
            }
        """
        query = """
            SELECT
                COUNT(*) as total_tool_calls,
                jsonb_agg(tool_call) as all_tool_calls
            FROM task_logs,
                 jsonb_array_elements(tool_calls) as tool_call
            WHERE created_at >= NOW() - INTERVAL '{days} days'
        """

        # Process results and aggregate by tool_name
        # ...implementation...

    def detect_redundant_operations(self, adw_id: str) -> list[dict]:
        """
        Detect redundant tool calls within a workflow.

        Examples:
        - Same file read multiple times
        - Same command run repeatedly
        - Consecutive Edit operations on same file

        Returns:
            [
                {
                    "pattern": "Multiple reads of same file",
                    "file_path": "app/server/routes.py",
                    "count": 5,
                    "total_duration_ms": 400,
                    "suggestion": "Cache file content in memory"
                }
            ]
        """
        # ...implementation...

    def analyze_tool_sequences(self, days: int = 30) -> list[dict]:
        """
        Analyze common tool call sequences.

        Returns:
            [
                {
                    "sequence": "Read→Edit→Write",
                    "count": 450,
                    "avg_duration_ms": 350,
                    "success_rate": 0.95,
                    "workflows": ["adw-123", "adw-456"]
                }
            ]
        """
        # ...implementation...
```

---

## API Design

### Endpoints

#### 1. Create Task Log with Tool Calls

```
POST /api/v1/observability/task-logs
```

**Request Body:**
```json
{
  "adw_id": "abc123",
  "issue_number": 42,
  "phase_name": "Build",
  "phase_number": 3,
  "phase_status": "completed",
  "log_message": "Build phase completed",
  "tool_calls": [
    {
      "tool_name": "Bash",
      "command": "pytest tests/",
      "duration_ms": 1250,
      "success": true,
      "exit_code": 0,
      "timestamp": "2025-12-18T10:00:00Z"
    }
  ]
}
```

**Response:**
```json
{
  "id": 123,
  "status": "created"
}
```

#### 2. Get Tool Usage Summary

```
GET /api/v1/tool-analytics/summary?days=30
```

**Response:**
```json
{
  "total_tool_calls": 12500,
  "by_tool": {
    "Bash": {
      "count": 5000,
      "avg_duration_ms": 850,
      "success_rate": 0.92
    },
    "Read": {
      "count": 4000,
      "avg_duration_ms": 120,
      "success_rate": 0.99
    }
  }
}
```

#### 3. Detect Redundant Operations

```
GET /api/v1/tool-analytics/redundancy/{adw_id}
```

**Response:**
```json
{
  "redundancies": [
    {
      "pattern": "Multiple reads of same file",
      "file_path": "app/server/routes.py",
      "count": 5,
      "total_duration_ms": 400,
      "suggestion": "Cache file content in memory"
    }
  ]
}
```

#### 4. Analyze Tool Sequences

```
GET /api/v1/tool-analytics/sequences?days=30&min_count=10
```

**Response:**
```json
{
  "sequences": [
    {
      "sequence": "Read→Edit→Write",
      "count": 450,
      "avg_duration_ms": 350,
      "success_rate": 0.95
    }
  ]
}
```

---

## Analytics Queries

### Common Queries

#### 1. Tool Usage by Workflow Template

```sql
SELECT
    workflow_template,
    jsonb_array_elements(tool_calls)->>'tool_name' as tool_name,
    COUNT(*) as usage_count,
    AVG((jsonb_array_elements(tool_calls)->>'duration_ms')::int) as avg_duration_ms
FROM task_logs
WHERE created_at >= NOW() - INTERVAL '30 days'
GROUP BY workflow_template, tool_name
ORDER BY usage_count DESC;
```

#### 2. Failed Tool Calls

```sql
SELECT
    adw_id,
    phase_name,
    tool_call->>'tool_name' as tool_name,
    tool_call->>'error_message' as error_message,
    created_at
FROM task_logs,
     jsonb_array_elements(tool_calls) as tool_call
WHERE (tool_call->>'success')::boolean = false
ORDER BY created_at DESC
LIMIT 100;
```

#### 3. Most Time-Consuming Tools

```sql
SELECT
    tool_call->>'tool_name' as tool_name,
    COUNT(*) as call_count,
    SUM((tool_call->>'duration_ms')::int) as total_duration_ms,
    AVG((tool_call->>'duration_ms')::int) as avg_duration_ms,
    MAX((tool_call->>'duration_ms')::int) as max_duration_ms
FROM task_logs,
     jsonb_array_elements(tool_calls) as tool_call
WHERE created_at >= NOW() - INTERVAL '7 days'
GROUP BY tool_call->>'tool_name'
ORDER BY total_duration_ms DESC;
```

---

## Migration Strategy

### Step 1: Database Migration

1. Run migration `019_add_tool_calls_tracking.sql`
2. Verify column added: `SELECT column_name FROM information_schema.columns WHERE table_name = 'task_logs' AND column_name = 'tool_calls';`
3. Test JSONB operations: `SELECT tool_calls FROM task_logs LIMIT 1;`

### Step 2: Backend API Update

1. Add `ToolCallRecord` model to `core/models/observability.py`
2. Update `TaskLogCreate` to include `tool_calls` field
3. Modify `TaskLogRepository.create()` to handle tool_calls
4. Test with sample data

### Step 3: Observability Module Update

1. Add `tool_calls` parameter to `log_task_completion()`
2. Update JSONL structured logger to include tool_calls
3. Test logging with sample tool calls

### Step 4: ADW Phase Integration

1. Create `ToolCallTracker` helper class
2. Update 1-2 phases as pilot (e.g., Build, Test)
3. Verify tool calls are being captured
4. Roll out to all phases

### Step 5: Analytics Implementation

1. Create `ToolAnalyticsService`
2. Implement analytics queries
3. Add API endpoints
4. Test with real workflow data

### Step 6: Dashboard Integration

1. Add tool call metrics to workflow details page
2. Create tool usage analytics panel
3. Add redundancy detection alerts

---

## Testing Strategy

### Unit Tests

**File:** `tests/services/test_tool_analytics_service.py`

```python
import pytest
from services.tool_analytics_service import ToolAnalyticsService


def test_get_tool_usage_summary():
    """Test tool usage summary calculation."""
    service = ToolAnalyticsService()
    summary = service.get_tool_usage_summary(days=30)

    assert "total_tool_calls" in summary
    assert "by_tool" in summary
    assert all(key in summary["by_tool"]["Bash"] for key in ["count", "avg_duration_ms", "success_rate"])


def test_detect_redundant_operations():
    """Test redundant operation detection."""
    service = ToolAnalyticsService()
    redundancies = service.detect_redundant_operations("test-adw-id")

    assert isinstance(redundancies, list)
    if redundancies:
        assert "pattern" in redundancies[0]
        assert "suggestion" in redundancies[0]
```

### Integration Tests

**File:** `tests/integration/test_tool_call_tracking.py`

```python
import pytest
from services.planned_features_service import PlannedFeaturesService
from repositories.task_log_repository import TaskLogRepository
from core.models.observability import TaskLogCreate, ToolCallRecord


def test_end_to_end_tool_call_tracking():
    """Test complete flow of tool call tracking."""
    # 1. Create task log with tool calls
    repo = TaskLogRepository()
    task_log = TaskLogCreate(
        adw_id="test-123",
        phase_name="Build",
        phase_status="completed",
        tool_calls=[
            ToolCallRecord(
                tool_name="Bash",
                command="pytest tests/",
                duration_ms=1250,
                success=True,
                exit_code=0,
                timestamp=datetime.now(),
            )
        ],
    )

    task_log_id = repo.create(task_log)
    assert task_log_id > 0

    # 2. Retrieve and verify
    retrieved = repo.get_by_id(task_log_id)
    assert len(retrieved.tool_calls) == 1
    assert retrieved.tool_calls[0].tool_name == "Bash"

    # 3. Query analytics
    service = ToolAnalyticsService()
    summary = service.get_tool_usage_summary(days=1)
    assert summary["total_tool_calls"] >= 1
```

---

## Rollout Plan

### Week 1: Foundation

**Days 1-2:**
- [ ] Create database migration
- [ ] Run migration on dev database
- [ ] Add Pydantic models
- [ ] Update TaskLogRepository

**Days 3-4:**
- [ ] Update observability.py
- [ ] Create ToolCallTracker helper
- [ ] Write unit tests
- [ ] Test in isolated environment

### Week 2: Integration

**Days 5-6:**
- [ ] Integrate with 2 pilot phases (Build, Test)
- [ ] Verify data capture
- [ ] Fix any issues

**Days 7-8:**
- [ ] Roll out to all ADW phases
- [ ] Monitor for errors
- [ ] Validate data quality

### Week 3: Analytics

**Days 9-10:**
- [ ] Implement ToolAnalyticsService
- [ ] Create API endpoints
- [ ] Write integration tests

**Days 11-12:**
- [ ] Build dashboard components
- [ ] Add visualizations
- [ ] User acceptance testing

---

## Success Metrics

- **Coverage**: 95%+ of ADW workflows have tool call data
- **Performance**: < 5ms overhead per tool call
- **Reliability**: < 0.1% tracking failure rate
- **Analytics**: Queries return in < 2 seconds
- **Adoption**: 5+ optimization recommendations implemented based on insights

---

## Future Enhancements

1. **Real-time Tool Call Monitoring**: WebSocket stream of tool calls
2. **Anomaly Detection**: Alert on unusual tool usage patterns
3. **Cost Attribution**: Attribute token costs to specific tool calls
4. **Tool Call Replay**: Ability to replay tool call sequences for debugging
5. **Pattern-Based Automation**: Automatically suggest tool for common patterns
6. **Tool Performance Benchmarking**: Compare tool performance across workflows

---

## References

- ADW Tracking Architecture: `docs/architecture/adw-tracking-architecture.md`
- Task Logs Schema: `app/server/repositories/task_log_repository.py`
- Observability Module: `adws/adw_modules/observability.py`
- Planned Feature: `planned_features` table, ID #128
