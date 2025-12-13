# Observability Implementation Guide

## Overview

This guide documents the observability system for capturing user prompts and task logs in the tac-webbuilder project.

## System Components

### 1. Database Tables

- **`user_prompts`** - Captures user request submissions
- **`task_logs`** - Captures ADW phase execution logs

See: `migration/015_add_task_logs_and_user_prompts_sqlite.sql`

### 2. Backend Infrastructure

#### Models (`core/models/observability.py`)
- `UserPrompt`, `UserPromptCreate`, `UserPromptWithProgress`
- `TaskLog`, `TaskLogCreate`, `IssueProgress`

#### Repositories
- `repositories/user_prompt_repository.py`
- `repositories/task_log_repository.py`

#### API Routes (`routes/observability_routes.py`)
- `POST /api/v1/observability/user-prompts` - Log user prompt
- `GET /api/v1/observability/user-prompts` - List prompts
- `POST /api/v1/observability/task-logs` - Log task completion
- `GET /api/v1/observability/task-logs/issue/{n}` - Get logs by issue

### 3. Capture Hooks

#### User Prompt Capture (Backend)
Location: `services/github_issue_service.py`

**When:** After processing user's NL input
**Data:** Request ID, NL input, issue title/body, cost estimate, complexity

```python
# Line ~223-245
user_prompt = UserPromptCreate(
    request_id=request_id,
    nl_input=request.nl_input,
    issue_title=github_issue.title,
    # ... other fields
)
self.user_prompt_repo.create(user_prompt)
```

**Update:** When GitHub issue is posted (line ~462-473)

#### Task Log Capture (ADW Workflows)
Location: Each `adw_*_iso.py` phase script

**Module:** `adw_modules/observability.py`
**Functions:**
- `log_phase_completion()` - Log when phase completes
- `log_phase_start()` - Log when phase starts (optional)
- `get_phase_number()` - Get phase number from name

## Implementation Pattern for ADW Phases

### Step 1: Add Import

At the top of each phase script:

```python
from adw_modules.observability import log_phase_completion, get_phase_number
```

### Step 2: Add Logging Call

At the completion point (after "phase completed successfully" log):

```python
# OBSERVABILITY: Log phase completion
from datetime import datetime
start_time = datetime.fromisoformat(state.get("start_time")) if state.get("start_time") else None
log_phase_completion(
    adw_id=adw_id,
    issue_number=int(issue_number),
    phase_name="PhaseNameHere",  # e.g., "Validate", "Lint", "Review", etc.
    phase_number=get_phase_number("PhaseNameHere"),
    success=True,  # or False if phase failed
    workflow_template="adw_phase_iso",  # e.g., "adw_validate_iso", "adw_lint_iso"
    error_message=None,  # or error string if failed
    started_at=start_time,
)
```

### Step 3: Test

The logging is **zero-overhead** - if the API is unavailable, it logs a debug message and continues.

## Completed Phases

✅ **adw_plan_iso.py** - Line ~368-378
✅ **adw_build_iso.py** - Line ~415-426
✅ **adw_test_iso.py** - Line ~1455-1467

## Remaining Phases to Implement

Apply the same pattern to:

| Phase | File | Phase Name | Phase Number |
|-------|------|------------|--------------|
| Validate | `adw_validate_iso.py` | "Validate" | 2 |
| Lint | `adw_lint_iso.py` | "Lint" | 4 |
| Review | `adw_review_iso.py` | "Review" | 6 |
| Document | `adw_document_iso.py` | "Document" | 7 |
| Ship | `adw_ship_iso.py` | "Ship" | 8 |
| Cleanup | `adw_cleanup_iso.py` | "Cleanup" | 9 |

### Example: adw_validate_iso.py

Find the completion point (search for "completed successfully"):

```python
logger.info("Validation phase completed successfully")
```

Add after it:

```python
# OBSERVABILITY: Log phase completion
from datetime import datetime
start_time = datetime.fromisoformat(state.get("start_time")) if state.get("start_time") else None
log_phase_completion(
    adw_id=adw_id,
    issue_number=int(issue_number),
    phase_name="Validate",
    phase_number=get_phase_number("Validate"),
    success=True,
    workflow_template="adw_validate_iso",
    started_at=start_time,
)
```

And add the import at the top:

```python
from adw_modules.observability import log_phase_completion, get_phase_number
```

## Frontend Integration (Pending)

### Panel 10 UI Structure

```
┌─────────────────────────────────────────┐
│         10. Log Panel                    │
├─────────────────────────────────────────┤
│  [Work Logs] [Task Logs] [User Prompts] │ <-- Tabs
├─────────────────────────────────────────┤
│                                          │
│  Content based on selected tab           │
│                                          │
└─────────────────────────────────────────┘
```

### API Client (To Create)

`app/client/src/api/observabilityClient.ts`

```typescript
export const observabilityClient = {
  // User Prompts
  getUserPrompts: (filters) =>
    apiClient.get('/observability/user-prompts', { params: filters }),

  // Task Logs
  getTaskLogs: (filters) =>
    apiClient.get('/observability/task-logs', { params: filters }),
  getTaskLogsByIssue: (issueNumber) =>
    apiClient.get(`/observability/task-logs/issue/${issueNumber}`),

  // Progress
  getIssueProgress: (issueNumber) =>
    apiClient.get(`/observability/progress/issue/${issueNumber}`),
};
```

## Testing

### Test User Prompt Capture

1. Start backend: `cd app/server && uv run python server.py`
2. Submit a request via the UI
3. Check database:
   ```sql
   SELECT * FROM user_prompts ORDER BY created_at DESC LIMIT 1;
   ```

### Test Task Log Capture

1. Run a workflow: `cd adws && uv run adw_plan_iso.py 123`
2. Check database:
   ```sql
   SELECT * FROM task_logs WHERE issue_number = 123 ORDER BY created_at DESC;
   ```

### Check API Endpoints

```bash
# List user prompts
curl http://localhost:8000/api/v1/observability/user-prompts?limit=10

# List task logs for issue #42
curl http://localhost:8000/api/v1/observability/task-logs/issue/42

# Get progress for issue #42
curl http://localhost:8000/api/v1/observability/progress/issue/42
```

## Architecture Decisions

### Why Zero-Overhead?

The observability system is designed to **never block** the main workflows:

1. **Non-blocking API calls** - Uses `urllib` with timeout
2. **Error handling** - Failures logged as debug, never raised
3. **Optional data** - Missing fields don't cause failures

### Why Two Tables?

- **`user_prompts`** - Captures the "input" (what user requested)
- **`task_logs`** - Captures the "execution" (how system processed it)

This separation allows:
- Tracking conversion rate (requests → completions)
- Identifying bottlenecks (where workflows fail)
- Cost analysis (estimated vs actual)

## Next Steps

1. ✅ Complete remaining phase implementations
2. ⏳ Build frontend UI (LogPanel tabs)
3. ⏳ Create TypeScript API client
4. ⏳ End-to-end testing
5. ⏳ Documentation for Panel 10 usage

## Support

For questions or issues:
- Check logs: `tail -f /tmp/backend_startup.log`
- Verify database: `sqlite3 tac_webbuilder.db ".tables"`
- Test API: `curl http://localhost:8000/api/v1/observability/user-prompts`
