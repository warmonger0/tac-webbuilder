# Session 19 - Phase 1, Part 4: Observability Integration

## Context
**Project**: tac-webbuilder - AI-powered GitHub automation platform
**Database**: PostgreSQL (production)
**Main Ports**: Backend 8002, Frontend 5173
**Issue**: Webhooks exist but don't log to observability system - cannot analyze patterns, costs, or failures.

## Objective
Integrate both webhook implementations with the observability system using StructuredLogger and TaskLog entries.

## Background
- **Files**:
  - `adws/adw_triggers/trigger_webhook.py` (external webhook)
  - `app/server/routes/queue_routes.py` (internal webhook)
- **Current State**: Webhooks have in-memory stats that are lost on restart
- **Target**: Full observability integration for pattern analysis, cost tracking, and failure monitoring
- **Time**: 4 hours
- **Risk**: Low (logging is additive, doesn't affect workflow)

## Current Problem

**External Webhook** (`trigger_webhook.py`):
- Uses in-memory stats dictionary (lines 74-81)
- Stats lost on server restart
- No integration with observability dashboard
- Cannot analyze webhook patterns over time

**Internal Webhook** (`queue_routes.py`):
- No logging to observability system
- Cannot track completion patterns
- No cost attribution for webhook-triggered work
- Missing audit trail

**Impact**: Cannot answer questions like:
- How many webhooks per day?
- What percentage fail?
- Which workflows are most common?
- What's the average processing time?

## Target Solution

- Use StructuredLogger for all webhook events
- Create TaskLog entries for webhook received, processed, and failed
- Enable pattern analysis via CLI tools
- Maintain complete audit trail
- Track processing time and metadata

## Implementation Steps

### Step 1: Review Existing Observability System

```bash
cd app/server

# Check StructuredLogger
grep -n "class StructuredLogger" services/structured_logger.py

# Check log_webhook_event method
grep -A20 "def log_webhook_event" services/structured_logger.py

# Check TaskLog model
grep -n "class TaskLog" core/models/observability.py

# Check repository
ls -la repositories/task_log_repository.py
```

**If `log_webhook_event` doesn't exist**, add to StructuredLogger:

```python
def log_webhook_event(
    self,
    adw_id: Optional[str],
    issue_number: int,
    message: str,
    webhook_type: str,
    event_data: Optional[dict] = None
) -> None:
    """Log webhook event to structured log.

    Args:
        adw_id: ADW ID (may be None for initial webhook)
        issue_number: GitHub issue number
        message: Descriptive message
        webhook_type: Type of webhook ('github_issue', 'workflow_complete')
        event_data: Additional event metadata
    """
    self.logger.info(
        message,
        extra={
            "adw_id": adw_id,
            "issue_number": issue_number,
            "webhook_type": webhook_type,
            "event_data": event_data or {},
            "event_type": "webhook"
        }
    )
```

### Step 2: Update External Webhook (trigger_webhook.py)

**Add imports** at top:
```python
import sys
import time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../app/server"))
from services.structured_logger import StructuredLogger
from repositories.task_log_repository import TaskLogRepository
from core.models.observability import TaskLogCreate
```

**Initialize loggers**:
```python
# Add near top of file (after existing logger setup)
structured_logger = StructuredLogger()
task_log_repo = TaskLogRepository()
```

**Update webhook processing function**:
```python
async def process_webhook_background(
    payload: dict,
    issue_number: int,
    workflow: str,
    trigger_source: str,
    event_type: str
):
    """Process webhook in background with observability logging."""

    adw_id = None
    start_time = time.time()

    try:
        # Log webhook received
        structured_logger.log_webhook_event(
            adw_id=None,  # Don't have it yet
            issue_number=issue_number,
            message=f"Webhook received from {trigger_source}",
            webhook_type="github_issue",
            event_data={
                "event_type": event_type,
                "workflow": workflow,
                "trigger_source": trigger_source
            }
        )

        # ... existing extraction logic ...

        # After ADW ID is generated
        adw_id = f"adw-{random_id}"

        # ... existing preflight and launch logic ...

        # Log successful processing
        elapsed_time = time.time() - start_time

        structured_logger.log_webhook_event(
            adw_id=adw_id,
            issue_number=issue_number,
            message=f"Webhook processed successfully - workflow launched",
            webhook_type="github_issue",
            event_data={
                "workflow": workflow,
                "elapsed_seconds": elapsed_time,
                "trigger_source": trigger_source
            }
        )

        # Create TaskLog entry
        task_log_repo.create(TaskLogCreate(
            adw_id=adw_id,
            issue_number=issue_number,
            workflow_template=workflow,
            phase_name="webhook_received",
            phase_status="completed",
            log_message=f"Webhook received and processed from {trigger_source}",
            duration_seconds=elapsed_time,
            metadata={
                "event_type": event_type,
                "workflow": workflow,
                "trigger_source": trigger_source
            }
        ))

        # Update stats
        webhook_stats["successful"] += 1
        webhook_stats["last_successful"] = {
            "issue": issue_number,
            "adw_id": adw_id,
            "workflow": workflow,
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        # Log failure
        elapsed_time = time.time() - start_time

        structured_logger.log_webhook_event(
            adw_id=adw_id,
            issue_number=issue_number,
            message=f"Webhook processing failed: {str(e)}",
            webhook_type="github_issue",
            event_data={
                "error": str(e),
                "workflow": workflow,
                "elapsed_seconds": elapsed_time
            }
        )

        # Create TaskLog for failure
        if adw_id:
            task_log_repo.create(TaskLogCreate(
                adw_id=adw_id,
                issue_number=issue_number,
                workflow_template=workflow,
                phase_name="webhook_received",
                phase_status="failed",
                log_message=f"Webhook processing failed: {str(e)}",
                duration_seconds=elapsed_time,
                metadata={"error": str(e)}
            ))

        # Update stats
        webhook_stats["failed"] += 1
        webhook_stats["recent_failures"].append({
            "issue": issue_number,
            "timestamp": datetime.now().isoformat(),
            "error": str(e)
        })

        # ... existing error handling (issue comment, etc.) ...
```

### Step 3: Update Internal Webhook (queue_routes.py)

**Add imports**:
```python
from services.structured_logger import StructuredLogger
from repositories.task_log_repository import TaskLogRepository
from core.models.observability import TaskLogCreate
import time
```

**Update endpoint** (around line 594-720):
```python
@router.post("/workflow-complete")
async def workflow_complete(
    request: Request,
    workflow_request: WorkflowCompleteRequest,
    background_tasks: BackgroundTasks
) -> WorkflowCompleteResponse:
    """Handle workflow completion webhook with observability."""

    structured_logger = StructuredLogger()
    task_log_repo = TaskLogRepository()
    start_time = time.time()

    # Log webhook received
    structured_logger.log_webhook_event(
        adw_id=workflow_request.adw_id,
        issue_number=workflow_request.parent_issue,
        message=f"Workflow complete webhook received (status={workflow_request.status})",
        webhook_type="workflow_complete",
        event_data={
            "status": workflow_request.status,
            "queue_id": workflow_request.queue_id,
            "phase_number": workflow_request.phase_number,
            "trigger_next": workflow_request.trigger_next
        }
    )

    # ... existing validation, idempotency, and processing logic ...

    try:
        # ... process webhook ...

        # Construct response
        response = WorkflowCompleteResponse(
            success=True,
            message="Workflow complete processed",
            phase_updated=True,  # Set based on actual logic
            next_phase_triggered=workflow_request.trigger_next
        )

        # Log successful processing
        elapsed_time = time.time() - start_time

        structured_logger.log_webhook_event(
            adw_id=workflow_request.adw_id,
            issue_number=workflow_request.parent_issue,
            message=f"Workflow complete webhook processed successfully",
            webhook_type="workflow_complete",
            event_data={
                "phase_updated": response.phase_updated,
                "next_phase_triggered": response.next_phase_triggered,
                "elapsed_seconds": elapsed_time
            }
        )

        # Create TaskLog entry
        task_log_repo.create(TaskLogCreate(
            adw_id=workflow_request.adw_id,
            issue_number=workflow_request.parent_issue,
            workflow_template="unknown",  # Could extract from metadata
            phase_name=f"phase_{workflow_request.phase_number}_complete",
            phase_status=workflow_request.status,
            log_message=f"Phase {workflow_request.phase_number} marked {workflow_request.status}",
            duration_seconds=elapsed_time,
            metadata={
                "trigger_next": workflow_request.trigger_next,
                "next_phase_triggered": response.next_phase_triggered
            }
        ))

        return response

    except Exception as e:
        # Log failure
        elapsed_time = time.time() - start_time

        structured_logger.log_webhook_event(
            adw_id=workflow_request.adw_id,
            issue_number=workflow_request.parent_issue,
            message=f"Workflow complete webhook failed: {str(e)}",
            webhook_type="workflow_complete",
            event_data={
                "error": str(e),
                "elapsed_seconds": elapsed_time
            }
        )

        raise
```

### Step 4: Verify Observability Integration

**Check TaskLog entries**:
```bash
cd app/server

POSTGRES_HOST=localhost POSTGRES_PORT=5432 POSTGRES_DB=tac_webbuilder \
POSTGRES_USER=tac_user POSTGRES_PASSWORD=changeme \
PGPASSWORD=changeme psql -h localhost -U tac_user -d tac_webbuilder \
-c "SELECT * FROM task_logs WHERE phase_name LIKE '%webhook%' ORDER BY created_at DESC LIMIT 10;"
```

**Check structured logs**:
```bash
tail -f logs/structured.jsonl | grep webhook
```

**Expected output**: JSON log entries with `event_type: "webhook"`

### Step 5: Test Pattern Analysis

**Trigger a webhook** and then run pattern analysis:
```bash
cd app/server

# Run pattern analysis (should now show webhook events)
./scripts/run_analytics.sh analyze_daily_patterns.py --report

# Check for webhook patterns in output
```

**Query webhook analytics**:
```bash
POSTGRES_HOST=localhost POSTGRES_PORT=5432 POSTGRES_DB=tac_webbuilder \
POSTGRES_USER=tac_user POSTGRES_PASSWORD=changeme \
PGPASSWORD=changeme psql -h localhost -U tac_user -d tac_webbuilder \
-c "SELECT
    phase_name,
    phase_status,
    COUNT(*) as count,
    AVG(duration_seconds) as avg_duration,
    MIN(created_at) as first_seen,
    MAX(created_at) as last_seen
FROM task_logs
WHERE phase_name LIKE '%webhook%'
GROUP BY phase_name, phase_status
ORDER BY count DESC;"
```

### Step 6: Create Observability Dashboard Query

**Optional**: Create a view for webhook analytics

**Create**: `app/server/database/views/webhook_analytics.sql`

```sql
CREATE OR REPLACE VIEW webhook_analytics AS
SELECT
    DATE(created_at) as date,
    CASE
        WHEN phase_name = 'webhook_received' THEN 'github_webhook'
        WHEN phase_name LIKE 'phase_%_complete' THEN 'workflow_complete'
        ELSE 'other'
    END as webhook_type,
    phase_status,
    COUNT(*) as event_count,
    AVG(duration_seconds) as avg_duration_seconds,
    MIN(duration_seconds) as min_duration_seconds,
    MAX(duration_seconds) as max_duration_seconds
FROM task_logs
WHERE phase_name LIKE '%webhook%' OR phase_name LIKE '%_complete'
GROUP BY DATE(created_at), webhook_type, phase_status
ORDER BY date DESC, event_count DESC;
```

**Apply view**:
```bash
POSTGRES_HOST=localhost POSTGRES_PORT=5432 POSTGRES_DB=tac_webbuilder \
POSTGRES_USER=tac_user POSTGRES_PASSWORD=changeme \
PGPASSWORD=changeme psql -h localhost -U tac_user -d tac_webbuilder \
-f database/views/webhook_analytics.sql
```

**Query view**:
```bash
POSTGRES_HOST=localhost POSTGRES_PORT=5432 POSTGRES_DB=tac_webbuilder \
POSTGRES_USER=tac_user POSTGRES_PASSWORD=changeme \
PGPASSWORD=changeme psql -h localhost -U tac_user -d tac_webbuilder \
-c "SELECT * FROM webhook_analytics LIMIT 20;"
```

### Step 7: Test End-to-End

**Manual test**:
1. Trigger a GitHub webhook (create/update issue)
2. Check structured.jsonl for log entries
3. Check task_logs table for entries
4. Run pattern analysis
5. Verify webhook appears in analytics

**Automated test** (optional):
```bash
cd app/server

# Run observability tests
POSTGRES_HOST=localhost POSTGRES_PORT=5432 POSTGRES_DB=tac_webbuilder \
POSTGRES_USER=tac_user POSTGRES_PASSWORD=changeme DB_TYPE=postgresql \
.venv/bin/pytest tests/services/test_structured_logger.py -v -k webhook
```

### Step 8: Commit Changes

```bash
git add adws/adw_triggers/trigger_webhook.py
git add app/server/routes/queue_routes.py
git add app/server/services/structured_logger.py  # if modified
git add app/server/database/views/webhook_analytics.sql  # if created

git commit -m "feat: Integrate webhooks with observability system

Add comprehensive logging to both webhook implementations for pattern
analysis, cost tracking, and failure monitoring.

Changes:
- Added StructuredLogger integration to external webhook
- Added StructuredLogger integration to internal webhook
- Create TaskLog entries for all webhook events
- Log received, processed, and failed events separately
- Include elapsed time, metadata, and error details
- Created webhook_analytics view for reporting

Observability Impact:
- Webhooks now visible in observability dashboard
- Pattern analysis can track webhook frequency and types
- Cost attribution for webhook-triggered workflows
- Error analytics for webhook failures
- Complete audit trail of all webhook events

Data Captured:
- Webhook type (github_issue, workflow_complete)
- Event metadata (issue number, ADW ID, status)
- Processing time (duration_seconds)
- Success/failure status
- Error details (if failed)

Session 19 - Phase 1, Part 4/4"
```

## Success Criteria

- ✅ StructuredLogger used for all webhook events
- ✅ TaskLog entries created for received/processed/failed events
- ✅ External webhook logs to observability system
- ✅ Internal webhook logs to observability system
- ✅ Pattern analysis can query webhook events
- ✅ Structured logs contain webhook event data
- ✅ Webhook analytics queryable in database

## Observability Metrics Captured

**For Each Webhook Event**:
- Event type (webhook)
- Webhook type (github_issue, workflow_complete)
- ADW ID
- Issue number
- Processing time (duration_seconds)
- Status (completed, failed)
- Metadata (workflow, trigger_source, error details)
- Timestamp

**Analytics Enabled**:
- Webhook frequency by type
- Success/failure rates
- Average processing time
- Error patterns
- Cost attribution (via workflow tracking)

## Summary Template

After completing, provide this summary:

```
# Part 4 Complete: Observability Integration

## Changes Made
- Modified: adws/adw_triggers/trigger_webhook.py
- Modified: app/server/routes/queue_routes.py
- [Modified: app/server/services/structured_logger.py (if log_webhook_event added)]
- [Created: app/server/database/views/webhook_analytics.sql (if created)]

## Observability Features Added
- StructuredLogger integration: ✅
- TaskLog entries created: ✅
- External webhook logging: ✅
- Internal webhook logging: ✅
- Pattern analysis support: ✅
- Webhook analytics view: [YES/NO]

## Test Results
- Webhook events in task_logs: X events found
- Structured logs contain webhook data: [VERIFIED/NOT VERIFIED]
- Pattern analysis shows webhooks: [VERIFIED/NOT VERIFIED]
- All existing tests: [PASS/FAIL]

## Analytics Verification
```bash
# Sample query result
SELECT * FROM webhook_analytics LIMIT 5;

# [Paste output showing webhook analytics]
```

## Performance Impact
- Logging overhead: ~5-10ms per webhook (acceptable)
- Database writes: 1 TaskLog entry per webhook
- No impact on webhook processing logic

## Issues Encountered
- [List any issues OR "None"]

## Files Modified
- adws/adw_triggers/trigger_webhook.py
- app/server/routes/queue_routes.py
- [Any others]

## Commit Hash
- [Paste commit hash]

## Phase 1 Complete
✅ All 4 parts of Phase 1 complete:
  1. N+1 Query Fix - DONE
  2. Webhook Signature Validation - DONE
  3. Webhook Idempotency Protection - DONE
  4. Observability Integration - DONE

Ready to report back to architectural review tracking.
```

---

**Estimated Time**: 4 hours
**Dependencies**: Parts 1-3 should be complete first
**Next**: Return to Session 19 main tracking with complete Phase 1 summary

## Return to Main Tracking

After all 4 parts are complete, compile a comprehensive summary using summaries from each part and report back to the architectural review tracking prompt.
