# Phase 1: Backend API Implementation

## Overview
This document tracks the implementation of the ADW Monitor backend API (Phase 1).

## Objective
Create a `/api/adw-monitor` endpoint that aggregates and returns the status of all ADW workflows in the system.

## API Specification

### Endpoint
```
GET /api/adw-monitor
```

### Response Schema
See the complete schema in [ISSUE_ADW_MONITOR_DESIGN.md](./ISSUE_ADW_MONITOR_DESIGN.md#response-schema)

Key response fields:
- `summary`: Aggregate statistics (total, running, completed, failed, paused)
- `workflows`: Array of workflow status objects
- `last_updated`: ISO timestamp of data collection

### Status Determination Logic
1. **Running:** Process is active (checked via process list)
2. **Completed:** State file status = "completed"
3. **Failed:** State file status = "failed"
4. **Paused:** Worktree exists, no process, no activity >10 minutes
5. **Queued:** State file exists but no active process

### Phase Progress Calculation
- 8 standard SDLC phases: plan, build, lint, test, review, doc, ship, cleanup
- Each phase = 12.5% of total progress
- Progress calculated by counting completed phase directories

## Implementation

### Core Module: `app/server/core/adw_monitor.py`

**Functions:**
- `scan_adw_states()` - Scan agents/ directory for state files
- `is_process_running(adw_id: str) -> bool` - Check process status
- `worktree_exists(adw_id: str) -> bool` - Verify worktree directory
- `determine_status(adw_id: str, state: dict) -> str` - Calculate workflow status
- `calculate_phase_progress(adw_id: str, state: dict) -> tuple[str, float]` - Calculate progress
- `get_last_activity_timestamp(adw_id: str) -> datetime` - Get last activity time
- `aggregate_adw_monitor_data() -> dict` - Main aggregation function

### Data Models
Pydantic models added to `app/server/core/data_models.py`:
- `AdwWorkflowStatus` - Individual workflow status
- `AdwMonitorSummary` - Summary statistics
- `AdwMonitorResponse` - Complete API response

### API Endpoint
Added to `app/server/server.py`:
- Route: `/api/adw-monitor`
- Method: GET
- Response caching: 5 seconds
- Error handling: Graceful degradation for corrupt state files

## Testing

### Unit Tests: `app/server/tests/test_adw_monitor.py`
Tests for all core functions with mocked data

### Integration Tests: `app/server/tests/test_adw_monitor_endpoint.py`
End-to-end tests for the API endpoint

### E2E Tests: `.claude/commands/e2e/test_adw_monitor.md`
User story-based validation tests

## Validation

### Performance
- Response time: <200ms (target)
- Tested with 15+ concurrent workflows

### Quality
- Code coverage: >80%
- Linting: ruff check passes
- File length: <800 lines (hard limit)
- Function length: <300 lines (hard limit)

## Data Sources
1. **ADW State Files:** `agents/*/adw_state.json`
2. **Process List:** Check for running processes
3. **Worktree Status:** Check `trees/{adw_id}/` directory
4. **Phase Directories:** Check `agents/{adw_id}/*/` for completed phases
5. **Cost Data:** Extract from state file

## Security Considerations
- Path validation to prevent directory traversal
- Error messages sanitized to avoid information disclosure
- No user input (endpoint takes no parameters)

## Performance Optimizations
- 5-second response caching
- Batch file reads
- Limit to most recent 20 workflows (if needed)
- Async I/O for file operations (if performance issues occur)

## Known Limitations
- Does not include historical data from completed workflows
- No WebSocket support (added in Phase 3)
- Basic error tracking (could be enhanced)

## Next Steps (Phase 2)
- Create `AdwMonitorCard.tsx` React component
- Add API client function
- Implement polling logic
- Add visual styling and animations

## References
- [Complete Design Document](./ISSUE_ADW_MONITOR_DESIGN.md)
- [Implementation Overview](./ADW_MONITOR_IMPLEMENTATION_OVERVIEW.md)
