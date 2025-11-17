# Phase 1.3: Database Integration - Implementation Guide

**Parent:** Phase 1 - Pattern Detection Engine
**Depends On:** Phase 1.1, Phase 1.2
**Duration:** 1-2 days
**Priority:** HIGH
**Status:** Ready to implement

---

## Overview

Integrate the pattern detection engine with the database to persist patterns, track occurrences, update statistics, and automatically process workflows during sync. This connects the pure pattern detection logic to the persistence layer.

---

## Goals

1. ✅ Record pattern occurrences in `operation_patterns` table
2. ✅ Link patterns to workflows via `pattern_occurrences` table
3. ✅ Calculate and update pattern statistics (tokens, cost, savings)
4. ✅ Integrate with `sync_workflow_history()` for automatic detection
5. ✅ Ensure idempotent operations (safe to re-run)

---

## Architecture

```
sync_workflow_history()
         │
         ▼
  ┌──────────────────┐
  │ All workflows    │
  │ from ADW state   │
  └────────┬─────────┘
           │
           ▼
    ┌─────────────────────────┐
    │ For each workflow:      │
    │   process_and_persist() │
    └──────────┬──────────────┘
               │
      ┌────────┴────────┐
      │                 │
      ▼                 ▼
┌──────────┐    ┌───────────────┐
│ operation│    │ pattern_      │
│ patterns │    │ occurrences   │
└──────────┘    └───────────────┘
      │
      ▼
┌──────────────────────┐
│ Update statistics:   │
│ • avg_tokens         │
│ • avg_cost           │
│ • confidence_score   │
│ • monthly_savings    │
└──────────────────────┘
```

---

## Implementation

### File: `app/server/core/pattern_persistence.py`

New module for database operations:

```python
"""
Pattern Persistence - Database operations for pattern learning

Handles all database interactions for pattern detection and tracking.
"""

import json
import logging
import sqlite3
from typing import Dict, List, Optional, Tuple

from .pattern_detector import (
    process_workflow_for_patterns,
    calculate_confidence_score,
)

logger = logging.getLogger(__name__)


# ============================================================================
# PATTERN RECORDING
# ============================================================================

def record_pattern_occurrence(
    pattern_signature: str,
    workflow: Dict,
    db_connection: sqlite3.Connection
) -> Tuple[Optional[int], bool]:
    """
    Record that we observed a pattern in a workflow.

    This function:
    1. Creates or updates the pattern in operation_patterns
    2. Links the pattern to the workflow in pattern_occurrences
    3. Updates pattern statistics

    Args:
        pattern_signature: Pattern signature string (e.g., "test:pytest:backend")
        workflow: Complete workflow dictionary
        db_connection: SQLite database connection

    Returns:
        Tuple of (pattern_id, is_new_pattern)
        Returns (None, False) if workflow_id is missing

    Example:
        >>> pattern_id, is_new = record_pattern_occurrence(
        ...     "test:pytest:backend",
        ...     workflow,
        ...     db_conn
        ... )
        >>> if is_new:
        ...     print(f"New pattern discovered: {pattern_id}")
    """
    cursor = db_connection.cursor()
    workflow_id = workflow.get("workflow_id")

    if not workflow_id:
        logger.warning("[Pattern] Workflow missing workflow_id, cannot record pattern")
        return None, False

    # Check if pattern exists
    cursor.execute(
        """
        SELECT id, occurrence_count, automation_status
        FROM operation_patterns
        WHERE pattern_signature = ?
        """,
        (pattern_signature,)
    )

    existing = cursor.fetchone()

    if existing:
        pattern_id = existing[0]
        occurrence_count = existing[1]
        is_new = False

        # Update existing pattern
        cursor.execute(
            """
            UPDATE operation_patterns
            SET
                occurrence_count = occurrence_count + 1,
                last_seen = datetime('now')
            WHERE id = ?
            """,
            (pattern_id,)
        )

        logger.debug(
            f"[Pattern] Updated pattern {pattern_signature} "
            f"(count: {occurrence_count + 1})"
        )

    else:
        # Create new pattern
        pattern_type = pattern_signature.split(":")[0]  # Extract category

        # Get characteristics from workflow
        from .pattern_detector import extract_pattern_characteristics
        characteristics = extract_pattern_characteristics(workflow)

        cursor.execute(
            """
            INSERT INTO operation_patterns (
                pattern_signature,
                pattern_type,
                typical_input_pattern,
                occurrence_count,
                automation_status,
                confidence_score,
                created_at,
                last_seen
            ) VALUES (?, ?, ?, 1, 'detected', 10.0, datetime('now'), datetime('now'))
            """,
            (
                pattern_signature,
                pattern_type,
                json.dumps(characteristics)
            )
        )

        pattern_id = cursor.lastrowid
        is_new = True

        logger.info(f"[Pattern] New pattern detected: {pattern_signature}")

    # Create pattern occurrence link (if not already exists)
    cursor.execute(
        """
        INSERT OR IGNORE INTO pattern_occurrences (
            pattern_id,
            workflow_id,
            similarity_score,
            matched_characteristics,
            detected_at
        ) VALUES (?, ?, ?, ?, datetime('now'))
        """,
        (
            pattern_id,
            workflow_id,
            100.0,  # Perfect match since it came from this workflow
            json.dumps(characteristics)
        )
    )

    db_connection.commit()

    # Update statistics after committing the occurrence
    update_pattern_statistics(pattern_id, workflow, db_connection)

    return pattern_id, is_new


# ============================================================================
# STATISTICS UPDATES
# ============================================================================

def update_pattern_statistics(
    pattern_id: int,
    workflow: Dict,
    db_connection: sqlite3.Connection
):
    """
    Update pattern statistics based on new workflow data.

    Updates:
    - avg_tokens_with_llm (running average)
    - avg_cost_with_llm (running average)
    - avg_tokens_with_tool (estimated at 5% of LLM tokens)
    - avg_cost_with_tool (estimated at 5% of LLM cost)
    - potential_monthly_savings (extrapolated from current frequency)
    - confidence_score (recalculated from all occurrences)

    Args:
        pattern_id: ID of the pattern to update
        workflow: New workflow data to incorporate
        db_connection: SQLite database connection
    """
    cursor = db_connection.cursor()

    # Get current statistics
    cursor.execute(
        """
        SELECT
            occurrence_count,
            avg_tokens_with_llm,
            avg_cost_with_llm
        FROM operation_patterns
        WHERE id = ?
        """,
        (pattern_id,)
    )

    current = cursor.fetchone()
    if not current:
        logger.warning(f"[Pattern] Pattern {pattern_id} not found for statistics update")
        return

    count = current[0]
    current_avg_tokens = current[1] or 0
    current_avg_cost = current[2] or 0.0

    # Get new workflow metrics
    new_tokens = workflow.get("total_tokens", 0)
    new_cost = workflow.get("actual_cost_total", 0.0)

    # Calculate running average
    if count == 1:
        # First occurrence, use as-is
        avg_tokens = new_tokens
        avg_cost = new_cost
    else:
        # Update running average
        avg_tokens = int((current_avg_tokens * (count - 1) + new_tokens) / count)
        avg_cost = (current_avg_cost * (count - 1) + new_cost) / count

    # Estimate tool cost (typically 95-97% reduction based on Phase 3E results)
    estimated_tool_tokens = int(avg_tokens * 0.05)  # 5% of LLM tokens
    estimated_tool_cost = avg_cost * 0.05  # 5% of LLM cost

    # Calculate potential monthly savings
    # Assume current frequency continues (extrapolate)
    workflows_per_month = count  # Simple extrapolation based on observation period
    savings_per_use = avg_cost - estimated_tool_cost
    potential_monthly_savings = savings_per_use * workflows_per_month

    # Recalculate confidence score
    confidence = _calculate_confidence_from_db(pattern_id, db_connection)

    # Update pattern
    cursor.execute(
        """
        UPDATE operation_patterns
        SET
            avg_tokens_with_llm = ?,
            avg_cost_with_llm = ?,
            avg_tokens_with_tool = ?,
            avg_cost_with_tool = ?,
            potential_monthly_savings = ?,
            confidence_score = ?
        WHERE id = ?
        """,
        (
            avg_tokens,
            avg_cost,
            estimated_tool_tokens,
            estimated_tool_cost,
            potential_monthly_savings,
            confidence,
            pattern_id
        )
    )

    db_connection.commit()

    logger.debug(
        f"[Pattern] Updated statistics for pattern {pattern_id}: "
        f"avg_cost=${avg_cost:.4f}, savings=${potential_monthly_savings:.2f}/mo, "
        f"confidence={confidence:.1f}%"
    )


def _calculate_confidence_from_db(
    pattern_id: int,
    db_connection: sqlite3.Connection
) -> float:
    """
    Calculate confidence score by fetching data from database.

    This is a wrapper around calculate_confidence_score() that handles
    database querying.

    Args:
        pattern_id: Pattern ID to calculate confidence for
        db_connection: SQLite database connection

    Returns:
        Confidence score from 0.0 to 100.0
    """
    cursor = db_connection.cursor()

    # Get pattern data
    cursor.execute(
        """
        SELECT occurrence_count, pattern_type
        FROM operation_patterns
        WHERE id = ?
        """,
        (pattern_id,)
    )

    pattern_row = cursor.fetchone()
    if not pattern_row:
        return 0.0

    pattern_data = {
        "occurrence_count": pattern_row[0],
        "pattern_type": pattern_row[1]
    }

    # Get workflow data for this pattern
    cursor.execute(
        """
        SELECT w.error_count, w.duration_seconds, w.retry_count
        FROM workflow_history w
        JOIN pattern_occurrences po ON po.workflow_id = w.workflow_id
        WHERE po.pattern_id = ?
        """,
        (pattern_id,)
    )

    workflows = []
    for row in cursor.fetchall():
        workflows.append({
            "error_count": row[0],
            "duration_seconds": row[1],
            "retry_count": row[2]
        })

    # Calculate confidence using existing logic
    from .pattern_detector import calculate_confidence_score
    return calculate_confidence_score(pattern_data, workflows)


# ============================================================================
# BATCH PROCESSING
# ============================================================================

def process_and_persist_workflow(
    workflow: Dict,
    db_connection: sqlite3.Connection
) -> Dict:
    """
    Process a workflow for patterns and persist to database.

    This is the main entry point for pattern learning during workflow sync.

    Args:
        workflow: Complete workflow dictionary
        db_connection: SQLite database connection

    Returns:
        Dictionary with processing results:
        {
            'patterns_detected': 2,
            'new_patterns': 1,
            'pattern_ids': [1, 5]
        }

    Example:
        >>> result = process_and_persist_workflow(workflow, db_conn)
        >>> print(f"Detected {result['patterns_detected']} patterns")
    """
    # Detect patterns using pure logic
    detection_result = process_workflow_for_patterns(workflow)
    patterns = detection_result["patterns"]

    result = {
        "patterns_detected": len(patterns),
        "new_patterns": 0,
        "pattern_ids": []
    }

    # Persist each pattern
    for pattern_sig in patterns:
        try:
            pattern_id, is_new = record_pattern_occurrence(
                pattern_sig,
                workflow,
                db_connection
            )

            if pattern_id:
                result["pattern_ids"].append(pattern_id)
                if is_new:
                    result["new_patterns"] += 1

        except Exception as e:
            logger.warning(
                f"[Pattern] Failed to record pattern {pattern_sig} "
                f"for workflow {workflow.get('workflow_id')}: {e}"
            )

    return result


def batch_process_workflows(
    workflows: List[Dict],
    db_connection: sqlite3.Connection
) -> Dict:
    """
    Process multiple workflows for patterns in batch.

    Args:
        workflows: List of workflow dictionaries
        db_connection: SQLite database connection

    Returns:
        Summary statistics:
        {
            'total_workflows': 100,
            'processed': 95,
            'total_patterns': 150,
            'new_patterns': 12,
            'errors': 5
        }
    """
    total_patterns = 0
    new_patterns = 0
    processed = 0
    errors = 0

    for workflow in workflows:
        try:
            result = process_and_persist_workflow(workflow, db_connection)
            total_patterns += result["patterns_detected"]
            new_patterns += result["new_patterns"]
            processed += 1

        except Exception as e:
            logger.error(
                f"[Pattern] Failed to process workflow {workflow.get('workflow_id')}: {e}"
            )
            errors += 1

    return {
        "total_workflows": len(workflows),
        "processed": processed,
        "total_patterns": total_patterns,
        "new_patterns": new_patterns,
        "errors": errors
    }
```

---

## Integration with Workflow History

### Modify: `app/server/core/workflow_history.py`

Add pattern learning to the sync process:

```python
# Add import at top of file
from .pattern_persistence import process_and_persist_workflow

def sync_workflow_history() -> int:
    """
    Sync workflow history from ADW state files.

    Now includes pattern learning.
    """
    # ... existing sync logic ...

    # Phase 3E: Second pass - Calculate similar workflows
    # ... existing similar workflow code ...

    # NEW: Pattern Learning Pass
    logger.info("[SYNC] Phase: Pattern Learning")
    try:
        patterns_detected = 0
        new_patterns = 0

        with get_db_connection() as conn:
            for workflow in all_workflows:
                try:
                    result = process_and_persist_workflow(workflow, conn)
                    patterns_detected += result['patterns_detected']
                    new_patterns += result['new_patterns']

                    if result['patterns_detected'] > 0:
                        logger.debug(
                            f"[SYNC] Workflow {workflow['adw_id']}: "
                            f"detected {result['patterns_detected']} pattern(s)"
                        )

                except Exception as e:
                    logger.warning(
                        f"[SYNC] Failed to process patterns for {workflow['adw_id']}: {e}"
                    )

        logger.info(
            f"[SYNC] Pattern learning complete: "
            f"{patterns_detected} patterns detected, {new_patterns} new"
        )

    except Exception as e:
        logger.error(f"[SYNC] Pattern learning failed: {e}")
        # Don't fail entire sync if pattern learning fails

    return synced_count
```

---

## Unit Tests

### File: `app/server/tests/test_pattern_persistence.py`

```python
"""
Unit tests for pattern persistence.
"""

import pytest
import sqlite3
import json
from core.pattern_persistence import (
    record_pattern_occurrence,
    update_pattern_statistics,
    process_and_persist_workflow,
    batch_process_workflows,
)


@pytest.fixture
def mock_db():
    """Create in-memory SQLite database for testing."""
    conn = sqlite3.connect(":memory:")
    cursor = conn.cursor()

    # Create tables (matching schema.sql)
    cursor.execute("""
        CREATE TABLE operation_patterns (
            id INTEGER PRIMARY KEY,
            pattern_signature TEXT UNIQUE,
            pattern_type TEXT,
            occurrence_count INTEGER DEFAULT 1,
            avg_tokens_with_llm INTEGER DEFAULT 0,
            avg_cost_with_llm REAL DEFAULT 0.0,
            avg_tokens_with_tool INTEGER DEFAULT 0,
            avg_cost_with_tool REAL DEFAULT 0.0,
            typical_input_pattern TEXT,
            automation_status TEXT DEFAULT 'detected',
            confidence_score REAL DEFAULT 10.0,
            potential_monthly_savings REAL DEFAULT 0.0,
            created_at TEXT,
            last_seen TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE pattern_occurrences (
            id INTEGER PRIMARY KEY,
            pattern_id INTEGER,
            workflow_id TEXT,
            similarity_score REAL,
            matched_characteristics TEXT,
            detected_at TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE workflow_history (
            workflow_id TEXT PRIMARY KEY,
            error_count INTEGER,
            duration_seconds INTEGER,
            retry_count INTEGER,
            total_tokens INTEGER,
            actual_cost_total REAL
        )
    """)

    conn.commit()
    return conn


class TestPatternRecording:
    """Test recording pattern occurrences."""

    def test_create_new_pattern(self, mock_db):
        workflow = {
            "workflow_id": "wf-123",
            "nl_input": "Run backend tests with pytest",
            "duration_seconds": 120,
            "error_count": 0,
            "total_tokens": 5000,
            "actual_cost_total": 0.50
        }

        pattern_id, is_new = record_pattern_occurrence(
            "test:pytest:backend",
            workflow,
            mock_db
        )

        assert pattern_id is not None
        assert is_new is True

        # Verify pattern created
        cursor = mock_db.cursor()
        cursor.execute("SELECT * FROM operation_patterns WHERE id = ?", (pattern_id,))
        pattern = cursor.fetchone()
        assert pattern is not None
        assert pattern[1] == "test:pytest:backend"  # pattern_signature
        assert pattern[3] == 1  # occurrence_count

    def test_update_existing_pattern(self, mock_db):
        workflow1 = {
            "workflow_id": "wf-123",
            "nl_input": "Run backend tests",
            "duration_seconds": 120,
            "error_count": 0,
            "total_tokens": 5000,
            "actual_cost_total": 0.50
        }

        workflow2 = {
            "workflow_id": "wf-456",
            "nl_input": "Run backend tests again",
            "duration_seconds": 125,
            "error_count": 0,
            "total_tokens": 5200,
            "actual_cost_total": 0.52
        }

        # First occurrence
        pattern_id1, is_new1 = record_pattern_occurrence(
            "test:pytest:backend",
            workflow1,
            mock_db
        )

        # Second occurrence
        pattern_id2, is_new2 = record_pattern_occurrence(
            "test:pytest:backend",
            workflow2,
            mock_db
        )

        assert pattern_id1 == pattern_id2  # Same pattern
        assert is_new1 is True
        assert is_new2 is False

        # Verify occurrence count updated
        cursor = mock_db.cursor()
        cursor.execute("SELECT occurrence_count FROM operation_patterns WHERE id = ?", (pattern_id1,))
        count = cursor.fetchone()[0]
        assert count == 2

    def test_missing_workflow_id(self, mock_db):
        workflow = {
            "nl_input": "Run tests",
            "duration_seconds": 120
            # Missing workflow_id
        }

        pattern_id, is_new = record_pattern_occurrence(
            "test:generic:all",
            workflow,
            mock_db
        )

        assert pattern_id is None
        assert is_new is False


class TestStatisticsUpdate:
    """Test pattern statistics updates."""

    def test_first_workflow_statistics(self, mock_db):
        # Create pattern first
        cursor = mock_db.cursor()
        cursor.execute(
            """
            INSERT INTO operation_patterns (
                id, pattern_signature, pattern_type, occurrence_count
            ) VALUES (1, 'test:pytest:backend', 'test', 1)
            """
        )
        mock_db.commit()

        workflow = {
            "workflow_id": "wf-123",
            "total_tokens": 5000,
            "actual_cost_total": 0.50,
            "duration_seconds": 120,
            "error_count": 0
        }

        update_pattern_statistics(1, workflow, mock_db)

        # Check updated statistics
        cursor.execute("SELECT avg_tokens_with_llm, avg_cost_with_llm FROM operation_patterns WHERE id = 1")
        tokens, cost = cursor.fetchone()
        assert tokens == 5000
        assert cost == 0.50

    def test_running_average(self, mock_db):
        # Create pattern with existing stats
        cursor = mock_db.cursor()
        cursor.execute(
            """
            INSERT INTO operation_patterns (
                id, pattern_signature, pattern_type, occurrence_count,
                avg_tokens_with_llm, avg_cost_with_llm
            ) VALUES (1, 'test:pytest:backend', 'test', 2, 5000, 0.50)
            """
        )
        mock_db.commit()

        # Add third workflow
        workflow = {
            "workflow_id": "wf-789",
            "total_tokens": 6000,
            "actual_cost_total": 0.60,
            "duration_seconds": 120,
            "error_count": 0
        }

        update_pattern_statistics(1, workflow, mock_db)

        # Check running average
        cursor.execute("SELECT avg_tokens_with_llm, avg_cost_with_llm FROM operation_patterns WHERE id = 1")
        tokens, cost = cursor.fetchone()
        # Average of (5000, 6000) = 5500
        assert tokens == 5500
        # Average of (0.50, 0.60) = 0.55
        assert abs(cost - 0.55) < 0.01


class TestBatchProcessing:
    """Test batch workflow processing."""

    def test_process_single_workflow(self, mock_db):
        workflow = {
            "workflow_id": "wf-123",
            "nl_input": "Run backend tests with pytest",
            "duration_seconds": 120,
            "error_count": 0,
            "total_tokens": 5000,
            "actual_cost_total": 0.50,
            "workflow_template": None,
            "error_message": None
        }

        result = process_and_persist_workflow(workflow, mock_db)

        assert result["patterns_detected"] >= 1
        assert "test:pytest:backend" in [
            row[1] for row in mock_db.execute("SELECT * FROM operation_patterns")
        ]

    def test_batch_process_workflows(self, mock_db):
        workflows = [
            {
                "workflow_id": f"wf-{i}",
                "nl_input": "Run backend tests with pytest",
                "duration_seconds": 120,
                "error_count": 0,
                "total_tokens": 5000,
                "actual_cost_total": 0.50,
                "workflow_template": None,
                "error_message": None
            }
            for i in range(5)
        ]

        result = batch_process_workflows(workflows, mock_db)

        assert result["total_workflows"] == 5
        assert result["processed"] == 5
        assert result["total_patterns"] >= 5
        assert result["errors"] == 0
```

---

## Testing Strategy

### Run Unit Tests

```bash
cd app/server
pytest tests/test_pattern_persistence.py -v
```

### Integration Test

```bash
# Test with real database
cd app/server
python -c "
from core.workflow_history import sync_workflow_history
synced = sync_workflow_history()
print(f'Synced {synced} workflows with pattern learning')
"

# Check results
sqlite3 db/workflow_history.db "
SELECT pattern_signature, occurrence_count, confidence_score
FROM operation_patterns
ORDER BY occurrence_count DESC
LIMIT 10;
"
```

---

## Success Criteria

- [ ] ✅ **All unit tests pass** - 15+ tests green
- [ ] ✅ **Patterns persisted** - Data in operation_patterns table
- [ ] ✅ **Occurrences linked** - Data in pattern_occurrences table
- [ ] ✅ **Statistics calculated** - avg_tokens, avg_cost, confidence_score populated
- [ ] ✅ **Sync integration works** - Patterns detected during normal sync
- [ ] ✅ **Idempotent** - Re-running sync doesn't duplicate patterns

---

## Deliverables

1. ✅ `app/server/core/pattern_persistence.py` (~350 lines)
2. ✅ Modified `app/server/core/workflow_history.py` (~50 lines added)
3. ✅ `app/server/tests/test_pattern_persistence.py` (~250 lines)

**Total Lines of Code:** ~650 lines

---

## Next Steps

After completing Phase 1.3:

1. Run all unit tests to verify correctness
2. Test integration with workflow sync
3. Verify database schema compatibility
4. **Proceed to Phase 1.4: Backfill & Validation**

---

## Notes

- Uses **SQLite transactions** for data consistency
- **Running averages** prevent need to recalculate from all rows
- **Error handling** ensures sync continues even if pattern learning fails
- **Idempotent** operations allow safe re-runs
