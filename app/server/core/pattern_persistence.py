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
    extract_pattern_characteristics,
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
    workflow_id = workflow.get("workflow_id") or workflow.get("id")

    if not workflow_id:
        logger.debug(f"[Pattern] Workflow {workflow.get('adw_id', 'unknown')} missing workflow_id and id, cannot record pattern")
        return None, False

    # Get characteristics from workflow (used for both new and existing patterns)
    characteristics = extract_pattern_characteristics(workflow)

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
        SELECT
            CASE WHEN w.error_message IS NOT NULL AND w.error_message != '' THEN 1 ELSE 0 END as error_count,
            w.duration_seconds,
            w.retry_count
        FROM workflow_history w
        JOIN pattern_occurrences po ON po.workflow_id = w.workflow_id
        WHERE po.pattern_id = ?
        """,
        (pattern_id,)
    )

    workflows = []
    for row in cursor.fetchall():
        workflows.append({
            "error_count": row[0] if row[0] is not None else 0,
            "duration_seconds": row[1] if row[1] is not None else 0,
            "retry_count": row[2] if row[2] is not None else 0
        })

    # Calculate confidence using existing logic
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
