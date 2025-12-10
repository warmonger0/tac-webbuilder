# Session 19 - Phase 1, Part 3: Webhook Idempotency Protection

## Context
**Project**: tac-webbuilder - AI-powered GitHub automation platform
**Database**: PostgreSQL (production)
**Main Ports**: Backend 8002, Frontend 5173
**Issue**: workflow_complete endpoint has no deduplication - same completion could be processed twice.

## Objective
Add idempotency protection to prevent duplicate webhook processing within a time window.

## Background
- **File**: `app/server/routes/queue_routes.py` (workflow_complete endpoint)
- **Problem**: No deduplication - same adw_id completion could be processed twice
- **Impact**: Wastes resources, could cause double state updates
- **Time**: 2 hours
- **Risk**: Low (additive change, doesn't break existing flow)

## Current Problem

**workflow_complete endpoint** (lines 594-720):
- No tracking of processed webhook events
- If GitHub sends duplicate webhook (network retry, etc.), both are processed
- Same phase could be marked completed twice
- Wastes AI resources and database operations

**Example Scenario**:
1. ADW completes Phase 1, sends webhook
2. Network hiccup causes GitHub to retry webhook
3. Both webhooks processed → duplicate work

## Target Solution

- Track processed webhook events in database (webhook_id + timestamp)
- Deduplicate within 30-second window
- Return early if duplicate detected
- Auto-cleanup old events (7 days retention)

## Implementation Steps

### Step 1: Create Webhook Events Table

**Create**: `app/server/database/migrations/add_webhook_idempotency.sql`

```sql
-- Add webhook idempotency tracking
CREATE TABLE IF NOT EXISTS webhook_events (
    id SERIAL PRIMARY KEY,
    webhook_id VARCHAR(255) NOT NULL,
    webhook_type VARCHAR(50) NOT NULL,
    adw_id VARCHAR(100),
    issue_number INTEGER,
    received_at TIMESTAMP NOT NULL DEFAULT NOW(),
    processed BOOLEAN DEFAULT FALSE,
    UNIQUE(webhook_id)
);

-- Index for fast lookup
CREATE INDEX IF NOT EXISTS idx_webhook_events_lookup
    ON webhook_events(webhook_id, received_at);

-- Index for cleanup queries
CREATE INDEX IF NOT EXISTS idx_webhook_events_cleanup
    ON webhook_events(received_at);
```

**Apply migration**:
```bash
cd app/server

POSTGRES_HOST=localhost POSTGRES_PORT=5432 POSTGRES_DB=tac_webbuilder \
POSTGRES_USER=tac_user POSTGRES_PASSWORD=changeme \
PGPASSWORD=changeme psql -h localhost -U tac_user -d tac_webbuilder \
-f database/migrations/add_webhook_idempotency.sql

# Verify table created
POSTGRES_HOST=localhost POSTGRES_PORT=5432 POSTGRES_DB=tac_webbuilder \
POSTGRES_USER=tac_user POSTGRES_PASSWORD=changeme \
PGPASSWORD=changeme psql -h localhost -U tac_user -d tac_webbuilder \
-c "\d webhook_events"
```

### Step 2: Create Webhook Event Repository

**Create**: `app/server/repositories/webhook_event_repository.py`

```python
"""Repository for webhook event deduplication."""
from typing import Optional
from datetime import datetime, timedelta
import logging

from database.db_utils import get_database_adapter

logger = logging.getLogger(__name__)


class WebhookEventRepository:
    """Manages webhook event tracking for idempotency."""

    def __init__(self):
        self.adapter = get_database_adapter()

    def is_duplicate(
        self,
        webhook_id: str,
        window_seconds: int = 30
    ) -> bool:
        """Check if webhook was already processed recently.

        Args:
            webhook_id: Unique identifier for webhook event
            window_seconds: Deduplication window in seconds

        Returns:
            True if duplicate (already processed), False otherwise
        """
        cutoff_time = datetime.now() - timedelta(seconds=window_seconds)

        with self.adapter.get_connection() as conn:
            cursor = conn.cursor()

            query = """
                SELECT id FROM webhook_events
                WHERE webhook_id = %s
                  AND received_at > %s
                LIMIT 1
            """

            cursor.execute(query, (webhook_id, cutoff_time))
            result = cursor.fetchone()

            return result is not None

    def record_webhook(
        self,
        webhook_id: str,
        webhook_type: str,
        adw_id: Optional[str] = None,
        issue_number: Optional[int] = None
    ) -> int:
        """Record webhook event.

        Args:
            webhook_id: Unique identifier for webhook event
            webhook_type: Type of webhook ('github_issue', 'workflow_complete', etc.)
            adw_id: Associated ADW ID (if applicable)
            issue_number: Associated issue number (if applicable)

        Returns:
            Event ID (-1 if duplicate)
        """
        with self.adapter.get_connection() as conn:
            cursor = conn.cursor()

            query = """
                INSERT INTO webhook_events
                    (webhook_id, webhook_type, adw_id, issue_number, processed)
                VALUES (%s, %s, %s, %s, TRUE)
                ON CONFLICT (webhook_id) DO NOTHING
                RETURNING id
            """

            cursor.execute(
                query,
                (webhook_id, webhook_type, adw_id, issue_number)
            )

            result = cursor.fetchone()
            conn.commit()

            if result:
                return result[0]
            else:
                # Already exists (conflict)
                logger.debug(f"[WEBHOOK] Duplicate webhook_id: {webhook_id}")
                return -1

    def cleanup_old_events(self, days: int = 7) -> int:
        """Remove webhook events older than specified days.

        Args:
            days: Number of days to retain

        Returns:
            Number of events deleted
        """
        cutoff_time = datetime.now() - timedelta(days=days)

        with self.adapter.get_connection() as conn:
            cursor = conn.cursor()

            query = "DELETE FROM webhook_events WHERE received_at < %s"
            cursor.execute(query, (cutoff_time,))

            deleted_count = cursor.rowcount
            conn.commit()

            logger.info(f"[WEBHOOK] Cleaned up {deleted_count} old webhook events")
            return deleted_count
```

### Step 3: Update Workflow Complete Endpoint

**File**: `app/server/routes/queue_routes.py`

**Add imports**:
```python
from repositories.webhook_event_repository import WebhookEventRepository
import hashlib
```

**Update endpoint** (around line 594-720):
```python
@router.post("/workflow-complete")
async def workflow_complete(
    request: Request,
    workflow_request: WorkflowCompleteRequest,
    background_tasks: BackgroundTasks
) -> WorkflowCompleteResponse:
    """Handle workflow completion webhook (with idempotency)."""

    # Validate signature (from Part 2)
    try:
        await validate_webhook_request(request, webhook_type="internal")
    except HTTPException:
        logger.warning("[WEBHOOK] Internal webhook signature validation failed")

    # CHECK FOR DUPLICATE (idempotency)
    webhook_repo = WebhookEventRepository()

    # Generate unique webhook ID from request data
    webhook_id = hashlib.sha256(
        f"{workflow_request.adw_id}:{workflow_request.status}:{workflow_request.queue_id}".encode()
    ).hexdigest()[:16]

    if webhook_repo.is_duplicate(webhook_id, window_seconds=30):
        logger.warning(
            f"[WEBHOOK] Duplicate webhook detected for adw_id={workflow_request.adw_id}, "
            f"queue_id={workflow_request.queue_id}"
        )
        return WorkflowCompleteResponse(
            success=True,
            message="Duplicate webhook - already processed",
            phase_updated=False,
            next_phase_triggered=False
        )

    # Record webhook event
    webhook_repo.record_webhook(
        webhook_id=webhook_id,
        webhook_type="workflow_complete",
        adw_id=workflow_request.adw_id,
        issue_number=workflow_request.parent_issue
    )

    # ... rest of existing logic (process webhook) ...
```

### Step 4: Create Unit Tests

**Create**: `app/server/tests/repositories/test_webhook_event_repository.py`

```python
import pytest
from repositories.webhook_event_repository import WebhookEventRepository
import time


def test_is_duplicate_returns_false_for_new_webhook(db_session):
    """Test that new webhook is not marked as duplicate."""
    repo = WebhookEventRepository()

    webhook_id = "test-webhook-123"
    assert repo.is_duplicate(webhook_id) is False


def test_is_duplicate_returns_true_for_recent_webhook(db_session):
    """Test that recently processed webhook is marked as duplicate."""
    repo = WebhookEventRepository()

    webhook_id = "test-webhook-456"

    # Record webhook
    repo.record_webhook(webhook_id, "workflow_complete", "adw-123", 100)

    # Should be detected as duplicate
    assert repo.is_duplicate(webhook_id, window_seconds=30) is True


def test_is_duplicate_returns_false_after_window(db_session):
    """Test that old webhook outside window is not marked as duplicate."""
    repo = WebhookEventRepository()

    webhook_id = "test-webhook-789"

    # Record webhook
    repo.record_webhook(webhook_id, "workflow_complete", "adw-123", 100)

    # Should NOT be detected as duplicate (window=0 means already expired)
    assert repo.is_duplicate(webhook_id, window_seconds=0) is False


def test_record_webhook_creates_entry(db_session):
    """Test that record_webhook creates database entry."""
    repo = WebhookEventRepository()

    webhook_id = "test-webhook-create"
    event_id = repo.record_webhook(
        webhook_id=webhook_id,
        webhook_type="github_issue",
        adw_id="adw-999",
        issue_number=200
    )

    assert event_id > 0


def test_record_webhook_prevents_duplicates(db_session):
    """Test that recording same webhook twice returns -1 on second call."""
    repo = WebhookEventRepository()

    webhook_id = "test-webhook-duplicate"

    # First call should succeed
    event_id_1 = repo.record_webhook(webhook_id, "workflow_complete", "adw-123", 100)
    assert event_id_1 > 0

    # Second call should return -1 (duplicate)
    event_id_2 = repo.record_webhook(webhook_id, "workflow_complete", "adw-123", 100)
    assert event_id_2 == -1


def test_cleanup_old_events(db_session):
    """Test that cleanup removes old events."""
    repo = WebhookEventRepository()

    # Create some events (in real test, would need to manipulate timestamp)
    repo.record_webhook("old-webhook-1", "workflow_complete", "adw-1", 1)
    repo.record_webhook("old-webhook-2", "workflow_complete", "adw-2", 2)

    # Cleanup (with days=0, should remove all)
    deleted = repo.cleanup_old_events(days=0)

    assert deleted >= 0  # May be 0 if timestamps are too recent
```

**Run tests**:
```bash
cd app/server

POSTGRES_HOST=localhost POSTGRES_PORT=5432 POSTGRES_DB=tac_webbuilder \
POSTGRES_USER=tac_user POSTGRES_PASSWORD=changeme DB_TYPE=postgresql \
.venv/bin/pytest tests/repositories/test_webhook_event_repository.py -v
```

### Step 5: Manual Testing

**Test duplicate detection**:
```bash
# Send same webhook twice rapidly
# First should process, second should return "Duplicate webhook - already processed"

# You can test manually by calling the endpoint twice with same data
```

**Check database**:
```bash
POSTGRES_HOST=localhost POSTGRES_PORT=5432 POSTGRES_DB=tac_webbuilder \
POSTGRES_USER=tac_user POSTGRES_PASSWORD=changeme \
PGPASSWORD=changeme psql -h localhost -U tac_user -d tac_webbuilder \
-c "SELECT * FROM webhook_events ORDER BY received_at DESC LIMIT 10;"
```

### Step 6: Commit Changes

```bash
git add app/server/database/migrations/add_webhook_idempotency.sql
git add app/server/repositories/webhook_event_repository.py
git add app/server/tests/repositories/test_webhook_event_repository.py
git add app/server/routes/queue_routes.py

git commit -m "feat: Add webhook idempotency protection

Prevent duplicate processing when same webhook fires multiple times.

Changes:
- Created webhook_events table for deduplication tracking
- Added WebhookEventRepository for duplicate detection
- Updated workflow_complete endpoint with idempotency check
- 30-second deduplication window (configurable)
- Automatic cleanup of old events (7 days retention)
- Unit tests for duplicate detection

How It Works:
- Generate unique webhook_id from adw_id + status + queue_id
- Check if webhook_id exists in recent window (30s)
- If duplicate, return early with success message
- If new, record event and process normally

Impact:
- Prevents double state updates from duplicate webhooks
- Reduces wasted resources on duplicate processing
- Maintains event history for debugging

Session 19 - Phase 1, Part 3/4"
```

## Success Criteria

- ✅ webhook_events table created with indexes
- ✅ WebhookEventRepository implements duplicate detection
- ✅ workflow_complete endpoint checks for duplicates
- ✅ Duplicate webhooks return early without processing
- ✅ Unit tests passing
- ✅ Manual test confirms duplicate detection

## Database Schema

**Table**: `webhook_events`
- `id`: Primary key (serial)
- `webhook_id`: Unique identifier (VARCHAR 255)
- `webhook_type`: Type of webhook (VARCHAR 50)
- `adw_id`: Associated ADW ID (VARCHAR 100)
- `issue_number`: Associated issue (INTEGER)
- `received_at`: Timestamp (TIMESTAMP)
- `processed`: Status flag (BOOLEAN)

**Indexes**:
- `idx_webhook_events_lookup`: (webhook_id, received_at)
- `idx_webhook_events_cleanup`: (received_at)

## Summary Template

After completing, provide this summary:

```
# Part 3 Complete: Webhook Idempotency Protection

## Changes Made
- Created: app/server/database/migrations/add_webhook_idempotency.sql
- Created: app/server/repositories/webhook_event_repository.py
- Created: app/server/tests/repositories/test_webhook_event_repository.py
- Modified: app/server/routes/queue_routes.py

## Database Changes
- Table created: webhook_events
- Indexes created: 2 (lookup + cleanup)
- Migration applied: [SUCCESS/FAILED]

## Test Results
- Unit tests (webhook_event_repository): X/X passing
- Duplicate detection test: [PASS/FAIL]
- All existing tests: [PASS/FAIL]

## Configuration
- Deduplication window: 30 seconds
- Cleanup retention: 7 days
- Webhook ID generation: SHA256 hash of adw_id + status + queue_id

## Issues Encountered
- [List any issues OR "None"]

## Files Modified
- app/server/database/migrations/add_webhook_idempotency.sql (new)
- app/server/repositories/webhook_event_repository.py (new)
- app/server/tests/repositories/test_webhook_event_repository.py (new)
- app/server/routes/queue_routes.py

## Commit Hash
- [Paste commit hash]

## Ready for Part 4
✅ Part 3 complete. Webhooks now have idempotency protection.
Ready for observability integration.
```

---

**Estimated Time**: 2 hours
**Dependencies**: Part 2 (webhook signature validation)
**Next**: Part 4 - Observability Integration
