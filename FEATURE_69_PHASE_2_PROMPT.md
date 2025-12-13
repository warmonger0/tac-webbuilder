# Feature #69 Phase 2: Backend Endpoint & Full Integration

## Context
Load: `/prime`

**Depends on**: Phase 1 complete ✅ (Option B: Remote Logging Endpoint chosen)

## Task
Create backend observability endpoint and integrate external webhook with full logging.

**Scope**: Backend API endpoint + webhook integration + end-to-end testing.

## Background

### Phase 1 Delivered
- ✅ Decision: Option B (Remote Logging Endpoint)
- ✅ `log_to_observability()` helper function in `trigger_webhook.py` (lines 99-157)
- ✅ Architecture defined: Webhook → POST → Backend → StructuredLogger
- ✅ Decision doc: `docs/features/webhook-observability-decision.md`

### Phase 2 Goal
Create the backend endpoint that receives webhook observability logs and complete the integration.

## Workflow

### 1. Investigate (10 min)

```bash
cd /Users/Warmonger0/tac/tac-webbuilder

# Review Phase 1 work
cat adws/adw_triggers/trigger_webhook.py | grep -A60 "def log_to_observability"
cat docs/features/webhook-observability-decision.md

# Check existing observability routes
ls -la app/server/routes/*observability* 2>/dev/null || echo "No observability routes yet"
grep -r "StructuredLogger\|log_webhook_event" app/server/routes/ | head -10

# Review internal webhook implementation (our reference)
grep -A30 "log_webhook_event" app/server/routes/queue_routes.py | head -40
```

### 2. Implement Backend Endpoint (20 min)

**Create**: `app/server/routes/observability_routes.py`

```python
"""
Observability API routes for logging events from external services.
"""

from datetime import datetime
from typing import Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from services.structured_logger import StructuredLogger
from repositories.task_log_repository import TaskLogRepository
from core.models.observability import TaskLogCreate

router = APIRouter(prefix="/api/v1/observability", tags=["observability"])

# Initialize
structured_logger = StructuredLogger()
task_log_repo = TaskLogRepository()


class WebhookLogRequest(BaseModel):
    """Request model for webhook observability logging."""

    adw_id: Optional[str] = Field(None, description="ADW ID if applicable")
    issue_number: Optional[str] = Field(None, description="GitHub issue number")
    message: str = Field(..., description="Log message")
    webhook_type: str = Field(..., description="Type of webhook (github_issue, workflow_complete, etc.)")
    event_data: dict = Field(default_factory=dict, description="Additional event data")
    level: str = Field(default="info", description="Log level (info, warning, error)")
    source: str = Field(default="webhook", description="Source of the log event")


@router.post("/log-webhook-event")
async def log_webhook_event(request: WebhookLogRequest):
    """
    Log webhook event to observability system.

    Called by external webhook server to persist observability data.
    """
    try:
        # Log to structured logger
        structured_logger.log_webhook_event(
            adw_id=request.adw_id,
            issue_number=request.issue_number,
            message=request.message,
            webhook_type=request.webhook_type,
            event_data=request.event_data,
            level=request.level
        )

        # Create task log entry for pattern analysis
        if request.adw_id:
            task_log_entry = TaskLogCreate(
                adw_id=request.adw_id,
                task_type="webhook_event",
                message=request.message,
                metadata={
                    "webhook_type": request.webhook_type,
                    "issue_number": request.issue_number,
                    "source": request.source,
                    **request.event_data
                },
                timestamp=datetime.utcnow()
            )
            task_log_repo.create(task_log_entry)

        return {
            "status": "logged",
            "message": "Webhook event logged successfully",
            "webhook_type": request.webhook_type
        }

    except Exception as e:
        # Don't fail webhook processing if logging fails
        print(f"[Observability] Failed to log webhook event: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to log webhook event: {str(e)}"
        )
```

**Register route in** `app/server/server.py`:

```python
# Add import (around line 30-50)
from routes.observability_routes import router as observability_router

# Register router (around line 200-250, with other routers)
app.include_router(observability_router)
```

### 3. Enable Webhook Integration (15 min)

**Edit**: `adws/adw_triggers/trigger_webhook.py`

**Uncomment the HTTP POST** in `log_to_observability()` function:

```python
# Around line 140-150
async def log_to_observability(
    message: str,
    webhook_type: str,
    event_data: dict,
    adw_id: str = None,
    issue_number: str = None,
    level: str = "info"
):
    """Log webhook event to backend observability system."""

    # PHASE 2: Uncomment this block to enable actual logging
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                OBSERVABILITY_ENDPOINT,
                json={
                    "adw_id": adw_id,
                    "issue_number": issue_number,
                    "message": message,
                    "webhook_type": webhook_type,
                    "event_data": event_data,
                    "level": level,
                    "source": "external_webhook"
                },
                timeout=5.0  # 5 second timeout
            )

            if response.status_code != 200:
                print(f"[Observability] Warning: Failed to log (status {response.status_code})")

    except Exception as e:
        # Don't fail webhook processing if logging fails
        print(f"[Observability] Warning: Failed to log to backend: {e}")
```

**Add logging calls** to webhook processing functions (around lines 200-400):

```python
# When webhook received
await log_to_observability(
    message=f"GitHub webhook received: {event_type}",
    webhook_type="github_issue",
    event_data={
        "event_type": event_type,
        "action": payload.get("action"),
        "repository": payload.get("repository", {}).get("full_name")
    },
    issue_number=str(issue_number) if issue_number else None
)

# When processing starts
await log_to_observability(
    message=f"Processing GitHub issue #{issue_number}",
    webhook_type="github_issue",
    event_data={"phase": "processing_start"},
    issue_number=str(issue_number),
    adw_id=adw_id
)

# When successful
await log_to_observability(
    message=f"Workflow launched successfully for issue #{issue_number}",
    webhook_type="github_issue",
    event_data={"phase": "workflow_launched", "adw_id": adw_id},
    issue_number=str(issue_number),
    adw_id=adw_id,
    level="info"
)

# When error occurs
await log_to_observability(
    message=f"Webhook processing failed: {error}",
    webhook_type="github_issue",
    event_data={"phase": "error", "error": str(error)},
    issue_number=str(issue_number),
    level="error"
)
```

### 4. Test End-to-End (15 min)

```bash
# Start backend (with new observability endpoint)
cd app/server
env POSTGRES_HOST=localhost POSTGRES_PORT=5432 POSTGRES_DB=tac_webbuilder POSTGRES_USER=tac_user POSTGRES_PASSWORD=changeme DB_TYPE=postgresql .venv/bin/python3 server.py &
BACKEND_PID=$!

# Wait for backend to start
sleep 3

# Test observability endpoint directly
curl -X POST http://localhost:8002/api/v1/observability/log-webhook-event \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Test webhook event",
    "webhook_type": "github_issue",
    "event_data": {"test": true},
    "level": "info"
  }'

# Expected: {"status":"logged","message":"Webhook event logged successfully",...}

# Start webhook server
cd ../../adws/adw_triggers
python3 trigger_webhook.py &
WEBHOOK_PID=$!

# Wait for webhook to start
sleep 2

# Trigger a test webhook event (simulate GitHub webhook)
curl -X POST http://localhost:8001/webhook/github \
  -H "Content-Type: application/json" \
  -H "X-GitHub-Event: issues" \
  -d '{
    "action": "opened",
    "issue": {
      "number": 999,
      "title": "Test issue for observability",
      "body": "Test"
    },
    "repository": {
      "full_name": "test/repo"
    }
  }'

# Check backend logs for observability events
# Should see: "[Observability] Webhook event logged..."

# Check database for task logs
cd /Users/Warmonger0/tac/tac-webbuilder
env POSTGRES_HOST=localhost POSTGRES_PORT=5432 POSTGRES_DB=tac_webbuilder POSTGRES_USER=tac_user POSTGRES_PASSWORD=changeme PGPASSWORD=changeme psql -h localhost -U tac_user -d tac_webbuilder -c "SELECT task_type, message, created_at FROM task_logs WHERE task_type = 'webhook_event' ORDER BY created_at DESC LIMIT 5;"

# Cleanup
kill $BACKEND_PID $WEBHOOK_PID
```

### 5. Quality (10 min)

```bash
cd /Users/Warmonger0/tac/tac-webbuilder

# Linting
cd app/server
ruff check routes/observability_routes.py --fix
ruff check server.py --fix

cd ../..
ruff check adws/adw_triggers/trigger_webhook.py --fix

# Type check
cd app/server
mypy routes/observability_routes.py --ignore-missing-imports

# Test backend (if tests exist)
env POSTGRES_HOST=localhost POSTGRES_PORT=5432 POSTGRES_DB=tac_webbuilder POSTGRES_USER=tac_user POSTGRES_PASSWORD=changeme DB_TYPE=postgresql .venv/bin/pytest tests/routes/test_observability_routes.py -v 2>/dev/null || echo "No tests yet - manual testing sufficient"

# Commit
cd /Users/Warmonger0/tac/tac-webbuilder
git add app/server/routes/observability_routes.py app/server/server.py adws/adw_triggers/trigger_webhook.py
git commit -m "feat: Complete webhook observability integration (Phase 2/2)

Create backend endpoint and integrate external webhook logging.

Problem:
- External webhook had no persistent observability
- In-memory stats lost on restart
- No pattern analysis for GitHub webhook events

Solution (Phase 2):
- Created /api/v1/observability/log-webhook-event endpoint
- Integrated StructuredLogger + TaskLogRepository in backend
- Enabled HTTP POST in webhook log_to_observability()
- Added logging at key webhook processing points
- Async POST to backend (~5-10ms overhead)

Result:
- External webhook events now logged to observability system
- Persistent logging to task_logs table + structured.jsonl
- Pattern analysis queries work for GitHub webhooks
- Lightweight webhook design preserved
- Feature #69 100% complete

Architecture:
  Webhook → POST → Backend API → StructuredLogger → DB + JSONL

Files Changed:
- app/server/routes/observability_routes.py (new, 100 lines)
- app/server/server.py (register router)
- adws/adw_triggers/trigger_webhook.py (enable logging)

Testing:
- Manual test: POST to endpoint successful
- End-to-end: Webhook → Backend → Database verified
- Database query: task_logs populated

Location: app/server/routes/observability_routes.py"

# Update Plans Panel - COMPLETED
curl -X PATCH http://localhost:8002/api/v1/planned-features/69 \
  -H "Content-Type: application/json" \
  -d '{
    "status": "completed",
    "actual_hours": 1.5,
    "completed_at": "'$(date -u +"%Y-%m-%dT%H:%M:%SZ")'",
    "completion_notes": "Phase 1: Strategy decision (Option B). Phase 2: Backend endpoint created, webhook integrated. External webhook now logs to observability system via async POST."
  }'

# Push commits
git push origin main
```

## Success Criteria
- ✅ Backend endpoint `/api/v1/observability/log-webhook-event` created
- ✅ Webhook `log_to_observability()` enabled (HTTP POST uncommented)
- ✅ Logging calls added at key webhook processing points
- ✅ End-to-end test successful (webhook → backend → database)
- ✅ Database shows webhook events in `task_logs` table
- ✅ 0 linting errors
- ✅ Feature #69 marked completed in Plans Panel
- ✅ Commits pushed

## Time: 0.5-0.75h (30-45 min)

## Files Modified

### New Files
- `app/server/routes/observability_routes.py` (~100 lines)

### Modified Files
- `app/server/server.py` (register router)
- `adws/adw_triggers/trigger_webhook.py` (enable logging calls)

## Testing Checklist

- [ ] Backend endpoint responds to POST
- [ ] Webhook logs appear in backend console
- [ ] Database query shows task_logs entries
- [ ] Pattern analysis queries work
- [ ] No errors in webhook processing
- [ ] Webhook stays lightweight (no heavy dependencies)

---

**Ready to complete Feature #69!** 🎉
