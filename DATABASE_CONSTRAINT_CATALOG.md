# Database Constraint Violation Catalog

**DEFINITIVE REFERENCE FOR ALL DATABASE CONSTRAINTS**

This document maps all CHECK constraints, NOT NULL constraints, and documents what values are ACTUALLY allowed in each table. Created to prevent constraint violations that cause cryptic database errors.

---

## Table of Contents

1. [Phase Queue Constraints](#phase-queue-constraints)
2. [Workflow History Constraints](#workflow-history-constraints)
3. [Context Review Constraints](#context-review-constraints)
4. [Planned Features Constraints](#planned-features-constraints)
5. [Violation Patterns Found](#violation-patterns-found)
6. [Recommended Annotation Comments](#recommended-annotation-comments)
7. [Status Value Map (Which Status Belongs Where)](#status-value-map)

---

## Phase Queue Constraints

**Table:** `phase_queue`
**Schema File:** `/Users/Warmonger0/tac/tac-webbuilder/app/server/services/phase_queue_schema.py`

### CHECK Constraints

#### status CHECK constraint
```sql
CHECK(status IN ('queued', 'ready', 'running', 'completed', 'blocked', 'failed'))
```

**ALLOWED VALUES:**
- `queued` - Phase waiting for dependencies
- `ready` - Phase ready for execution
- `running` - Phase currently executing
- `completed` - Phase finished successfully
- `blocked` - Phase blocked by dependency failure
- `failed` - Phase execution failed

**INVALID VALUES (will cause constraint violation):**
- ❌ `pending` (belongs to workflow_history)
- ❌ `analyzing` (belongs to context_review)
- ❌ `complete` (belongs to context_review)
- ❌ `in_progress` (belongs to planned_features)
- ❌ `cancelled` (belongs to planned_features)
- ❌ `planned` (belongs to planned_features)
- ❌ `building`, `linting`, `testing`, `reviewing`, `documenting`, `shipping`, `cleaning_up`, `verifying` (these are ADW phase names, NOT status values)

### NOT NULL Constraints

- ✅ `phase_number` - REQUIRED (NOT NULL)
- ⚠️ `feature_id` - NULLABLE (was made nullable in migration)
- ⚠️ `issue_number` - NULLABLE
- ✅ `status` - Has DEFAULT 'queued'

### Default Values

- `status` DEFAULT 'queued'
- `depends_on_phases` DEFAULT '[]' (JSONB) or '[]' (TEXT for SQLite)
- `priority` DEFAULT 50
- `created_at` DEFAULT CURRENT_TIMESTAMP
- `updated_at` DEFAULT CURRENT_TIMESTAMP

---

## Workflow History Constraints

**Table:** `workflow_history`
**Schema File:** `/Users/Warmonger0/tac/tac-webbuilder/app/server/core/workflow_history_utils/database/schema.py`

### CHECK Constraints

#### status CHECK constraint
```sql
CHECK(status IN ('pending', 'running', 'completed', 'failed'))
```

**ALLOWED VALUES:**
- `pending` - Workflow queued/waiting
- `running` - Workflow currently executing
- `completed` - Workflow finished successfully
- `failed` - Workflow execution failed

**INVALID VALUES (will cause constraint violation):**
- ❌ `queued`, `ready`, `blocked` (belong to phase_queue)
- ❌ `analyzing`, `complete` (belong to context_review)
- ❌ `in_progress`, `cancelled`, `planned` (belong to planned_features)

### NOT NULL Constraints

- ✅ `adw_id` - REQUIRED (NOT NULL) and UNIQUE
- ✅ `status` - REQUIRED (NOT NULL)
- ⚠️ `issue_number` - NULLABLE
- ⚠️ `nl_input` - NULLABLE
- ⚠️ `github_url` - NULLABLE
- ⚠️ `gh_issue_state` - NULLABLE

### Unique Constraints

- `adw_id` must be UNIQUE

---

## Context Review Constraints

**Table:** `context_reviews`
**Schema File:** `/Users/Warmonger0/tac/tac-webbuilder/app/server/core/context_review/database/schema.py`
**Model File:** `/Users/Warmonger0/tac/tac-webbuilder/app/server/models/context_review.py`

### CHECK Constraints

#### status CHECK constraint
```sql
CHECK(status IN ('pending', 'analyzing', 'complete', 'failed'))
```

**ALLOWED VALUES:**
- `pending` - Review queued
- `analyzing` - AI analysis in progress
- `complete` - Analysis finished (NOTE: NOT "completed")
- `failed` - Analysis failed

**INVALID VALUES (will cause constraint violation):**
- ❌ `completed` (use `complete` instead - this is a common mistake!)
- ❌ `queued`, `ready`, `running`, `blocked` (belong to phase_queue)
- ❌ `in_progress`, `cancelled`, `planned` (belong to planned_features)

#### suggestion_type CHECK constraint (context_suggestions table)
```sql
CHECK(suggestion_type IN ('file-to-modify', 'file-to-create', 'reference', 'risk', 'strategy'))
```

### NOT NULL Constraints

- ✅ `change_description` - REQUIRED (NOT NULL)
- ✅ `project_path` - REQUIRED (NOT NULL)
- ✅ `status` - REQUIRED (NOT NULL)
- ⚠️ `workflow_id` - NULLABLE
- ⚠️ `issue_number` - NULLABLE

---

## Planned Features Constraints

**Table:** `planned_features`
**Schema Files:**
- SQLite: `/Users/Warmonger0/tac/tac-webbuilder/app/server/db/migrations/017_add_planned_features_sqlite.sql`
- PostgreSQL: `/Users/Warmonger0/tac/tac-webbuilder/app/server/db/migrations/017_add_planned_features_postgres.sql`

### CHECK Constraints

#### item_type CHECK constraint
```sql
CHECK(item_type IN ('session', 'feature', 'bug', 'enhancement'))
```

#### status CHECK constraint
```sql
CHECK(status IN ('planned', 'in_progress', 'completed', 'cancelled'))
```

**ALLOWED VALUES:**
- `planned` - Feature planned but not started
- `in_progress` - Feature currently being worked on
- `completed` - Feature finished
- `cancelled` - Feature cancelled

**INVALID VALUES (will cause constraint violation):**
- ❌ `queued`, `ready`, `running`, `blocked`, `failed` (belong to phase_queue)
- ❌ `pending` (belongs to workflow_history and context_review)
- ❌ `analyzing`, `complete` (belong to context_review)

#### priority CHECK constraint
```sql
CHECK(priority IN ('high', 'medium', 'low'))
```

### NOT NULL Constraints

- ✅ `item_type` - REQUIRED (NOT NULL)
- ✅ `title` - REQUIRED (NOT NULL)
- ✅ `status` - REQUIRED (NOT NULL, DEFAULT 'planned')
- ⚠️ `description` - NULLABLE
- ⚠️ `priority` - NULLABLE (but must be one of the allowed values if provided)

### Foreign Key Constraints

- `parent_id` REFERENCES `planned_features(id)` ON DELETE CASCADE

---

## Violation Patterns Found

### CRITICAL: Invalid Status Values in Code

#### 1. Phase Queue Repository - try_acquire_workflow_lock()

**File:** `/Users/Warmonger0/tac/tac-webbuilder/app/server/repositories/phase_queue_repository.py:553-556`

```python
# ❌ VIOLATES CONSTRAINT - These statuses don't exist in phase_queue schema
active_statuses = [
    "running", "planned", "building", "linting", "testing",
    "reviewing", "documenting", "shipping", "cleaning_up", "verifying"
]
```

**PROBLEM:** This code checks if workflows have status in `active_statuses`, but most of these values are INVALID for phase_queue:
- ✅ `running` - OK
- ❌ `planned` - INVALID (belongs to planned_features)
- ❌ `building`, `linting`, `testing`, `reviewing`, `documenting`, `shipping`, `cleaning_up`, `verifying` - INVALID (these are phase NAMES, not status VALUES)

**WHERE IT'S USED:**
- Line 560: `if w.status in active_statuses and w.adw_id != adw_id`
- This prevents multiple workflows on same feature

**FIX NEEDED:**
```python
# ✅ CORRECT - Only use valid phase_queue status values
active_statuses = ["queued", "ready", "running"]
```

#### 2. Preflight Checks - check_database_for_active_workflows()

**File:** `/Users/Warmonger0/tac/tac-webbuilder/adws/adw_modules/preflight_checks.py:241`

```python
# ❌ VIOLATES CONSTRAINT - These statuses don't exist in phase_queue schema
active_statuses = ["running", "planned", "building", "testing", "reviewing", "documenting"]
```

**PROBLEM:** Same issue as above - using invalid status values

**FIX NEEDED:**
```python
# ✅ CORRECT
active_statuses = ["queued", "ready", "running"]
```

### Why These Don't Crash (Yet)

These violations are in READ operations (filtering results), not WRITE operations. The code won't crash UNTIL:
1. Someone tries to INSERT/UPDATE a phase_queue record with these invalid statuses
2. The database CHECK constraint will reject it with: `CHECK constraint failed: status`

The code is checking for statuses that will NEVER exist in the database, making these checks ineffective.

---

## Recommended Annotation Comments

Add these LOUD, OBVIOUS comments to critical files:

### phase_queue_repository.py

```python
# =============================================================================
# SCHEMA CONSTRAINT: phase_queue.status
# =============================================================================
# ALLOWED: 'queued', 'ready', 'running', 'completed', 'blocked', 'failed'
# FORBIDDEN: 'pending', 'analyzing', 'complete', 'in_progress', 'cancelled',
#            'planned', 'building', 'linting', 'testing', etc.
#
# SOURCE: app/server/services/phase_queue_schema.py:44 (PostgreSQL)
#         app/server/services/phase_queue_schema.py:65 (SQLite)
# =============================================================================

# ✅ CORRECT: Only use valid phase_queue statuses
active_statuses = ["queued", "ready", "running"]

# ❌ WRONG: These will NEVER exist in database
# active_statuses = ["running", "planned", "building", ...]
```

### phase_queue_service.py

```python
# =============================================================================
# SCHEMA CONSTRAINT: phase_queue.status CHECK constraint
# =============================================================================
# Database CHECK: status IN ('queued', 'ready', 'running', 'completed', 'blocked', 'failed')
#
# This list MUST match the database schema exactly. Any other value will cause:
# sqlite3.IntegrityError: CHECK constraint failed: status
# psycopg2.errors.CheckViolation: new row violates check constraint
# =============================================================================

valid_statuses = ["queued", "ready", "running", "completed", "blocked", "failed"]
```

### phase_queue_item.py (Model)

```python
class PhaseQueueItem:
    """
    Represents a single phase in the queue.

    SCHEMA CONSTRAINT - status field:
    ================================
    ALLOWED VALUES ONLY:
    - 'queued'    : Phase waiting for dependencies
    - 'ready'     : Phase ready for execution
    - 'running'   : Phase currently executing
    - 'completed' : Phase finished successfully
    - 'blocked'   : Phase blocked by dependency failure
    - 'failed'    : Phase execution failed

    FORBIDDEN VALUES (belong to other tables):
    - 'pending'    → workflow_history
    - 'analyzing'  → context_review
    - 'complete'   → context_review
    - 'in_progress'→ planned_features
    - 'cancelled'  → planned_features
    - 'planned'    → planned_features
    - Phase names like 'building', 'testing', etc. are NOT status values
    """

    def __init__(
        self,
        queue_id: str,
        feature_id: int,
        phase_number: int,
        issue_number: int | None = None,
        status: str = "queued",  # MUST be one of 6 allowed values above
        ...
```

### preflight_checks.py

```python
# =============================================================================
# SCHEMA CONSTRAINT: phase_queue.status
# =============================================================================
# ONLY these statuses exist in phase_queue table:
# - 'queued', 'ready', 'running', 'completed', 'blocked', 'failed'
#
# Phase NAMES (plan, build, test, etc.) are stored in phase_data.phase_name,
# NOT in the status field!
# =============================================================================

# ✅ CORRECT: Check for actual phase_queue statuses
active_statuses = ["queued", "ready", "running"]
```

### context_review.py

```python
# =============================================================================
# SCHEMA CONSTRAINT: context_reviews.status
# =============================================================================
# ALLOWED: 'pending', 'analyzing', 'complete', 'failed'
#
# ⚠️ COMMON MISTAKE: Using 'completed' instead of 'complete'
# context_reviews uses 'complete' (no 'd' at the end)
# =============================================================================

valid_statuses = ['pending', 'analyzing', 'complete', 'failed']
```

---

## Status Value Map (Which Status Belongs Where)

### Status Values by Table

| Status Value | phase_queue | workflow_history | context_review | planned_features |
|-------------|------------|------------------|----------------|------------------|
| `queued` | ✅ | ❌ | ❌ | ❌ |
| `ready` | ✅ | ❌ | ❌ | ❌ |
| `running` | ✅ | ✅ | ❌ | ❌ |
| `completed` | ✅ | ✅ | ❌ | ✅ |
| `blocked` | ✅ | ❌ | ❌ | ❌ |
| `failed` | ✅ | ✅ | ✅ | ❌ |
| `pending` | ❌ | ✅ | ✅ | ❌ |
| `analyzing` | ❌ | ❌ | ✅ | ❌ |
| `complete` | ❌ | ❌ | ✅ (no 'd'!) | ❌ |
| `planned` | ❌ | ❌ | ❌ | ✅ |
| `in_progress` | ❌ | ❌ | ❌ | ✅ |
| `cancelled` | ❌ | ❌ | ❌ | ✅ |

### Common Confusion Points

#### 1. "completed" vs "complete"
- `completed` (with 'd') → Used by: phase_queue, workflow_history, planned_features
- `complete` (no 'd') → Used by: context_review ONLY
- **Common mistake:** Using "completed" in context_review code

#### 2. Phase NAMES vs Status VALUES
- Phase NAMES: `plan`, `build`, `test`, `review`, `document`, `ship` (stored in phase_data)
- Status VALUES: `queued`, `ready`, `running`, `completed`, `blocked`, `failed` (stored in status column)
- **Common mistake:** Using phase names like "building", "testing" as status values

#### 3. "pending" belongs to TWO tables
- Used by: workflow_history AND context_review
- NOT used by: phase_queue (uses "queued" instead) or planned_features (uses "planned" instead)

#### 4. "running" is shared by TWO tables
- Used by: phase_queue AND workflow_history
- NOT used by: context_review (uses "analyzing") or planned_features (uses "in_progress")

---

## Quick Reference by Table

### phase_queue
```python
# ONLY these 6 statuses are valid:
VALID_STATUSES = ['queued', 'ready', 'running', 'completed', 'blocked', 'failed']

# feature_id is NULLABLE (was made nullable in recent migration)
# phase_number is NOT NULL (required)
# status has DEFAULT 'queued'
```

### workflow_history
```python
# ONLY these 4 statuses are valid:
VALID_STATUSES = ['pending', 'running', 'completed', 'failed']

# adw_id is UNIQUE and NOT NULL
# status is NOT NULL
```

### context_reviews
```python
# ONLY these 4 statuses are valid:
# NOTE: It's "complete" not "completed"!
VALID_STATUSES = ['pending', 'analyzing', 'complete', 'failed']

# change_description is NOT NULL
# project_path is NOT NULL
# status is NOT NULL
```

### planned_features
```python
# ONLY these 4 statuses are valid:
VALID_STATUSES = ['planned', 'in_progress', 'completed', 'cancelled']

# ONLY these 3 priorities are valid (if provided):
VALID_PRIORITIES = ['high', 'medium', 'low']

# ONLY these 4 item_types are valid:
VALID_ITEM_TYPES = ['session', 'feature', 'bug', 'enhancement']

# item_type is NOT NULL
# title is NOT NULL
# status is NOT NULL, DEFAULT 'planned'
```

---

## Files That Need Fixing

### High Priority (Potential Constraint Violations)

1. **`/Users/Warmonger0/tac/tac-webbuilder/app/server/repositories/phase_queue_repository.py`**
   - Line 553-556: `active_statuses` list contains invalid values
   - Fix: Change to `["queued", "ready", "running"]`

2. **`/Users/Warmonger0/tac/tac-webbuilder/adws/adw_modules/preflight_checks.py`**
   - Line 241: `active_statuses` list contains invalid values
   - Fix: Change to `["queued", "ready", "running"]`

### Medium Priority (Add Validation Comments)

3. **`/Users/Warmonger0/tac/tac-webbuilder/app/server/services/phase_queue_service.py`**
   - Line 326: Has correct validation, needs annotation comment
   - Add: Schema constraint documentation comment

4. **`/Users/Warmonger0/tac/tac-webbuilder/app/server/models/phase_queue_item.py`**
   - No validation in __init__, relies on database constraint
   - Add: Docstring with allowed values and validation logic

5. **`/Users/Warmonger0/tac/tac-webbuilder/app/server/models/context_review.py`**
   - Line 42: Has validation, needs prominent comment about "complete" vs "completed"
   - Add: Warning comment

---

## Testing Constraint Violations

To verify constraints are working:

### Test phase_queue constraint:
```python
from repositories.phase_queue_repository import PhaseQueueRepository
from models.phase_queue_item import PhaseQueueItem

repo = PhaseQueueRepository()

# This SHOULD fail:
item = PhaseQueueItem(
    queue_id="test-123",
    feature_id=1,
    phase_number=1,
    status="planned"  # ❌ Invalid for phase_queue
)
repo.create(item)  # Should raise: CHECK constraint failed: status
```

### Test workflow_history constraint:
```sql
-- This SHOULD fail:
INSERT INTO workflow_history (adw_id, status)
VALUES ('test-adw', 'queued');
-- Error: CHECK constraint failed: status
```

### Test context_review constraint:
```sql
-- This SHOULD fail:
INSERT INTO context_reviews (change_description, project_path, status)
VALUES ('test', '/path', 'completed');
-- Error: CHECK constraint failed: status

-- This SHOULD succeed:
INSERT INTO context_reviews (change_description, project_path, status)
VALUES ('test', '/path', 'complete');
-- Success!
```

---

## Summary

**Key Takeaways:**

1. **NEVER mix status values between tables** - Each table has its own allowed set
2. **"complete" vs "completed"** - context_review uses "complete" (no 'd')
3. **Phase names ≠ Status values** - "building", "testing" are NOT statuses
4. **Two files need immediate fixing** - Repository and preflight checks use invalid status lists
5. **Add annotation comments** - Make constraints LOUD and OBVIOUS in code

**When in doubt:**
- Check this catalog
- Check the schema file for the table
- Look for the CHECK constraint definition
- Test your assumption with a simple INSERT

**Database will reject invalid values with:**
- SQLite: `CHECK constraint failed: status`
- PostgreSQL: `new row violates check constraint "tablename_status_check"`
