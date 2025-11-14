"""
Workflow history tracking module for ADW workflows.

This module provides database operations and business logic for tracking
workflow execution history including costs, performance metrics, and status.
"""

import sqlite3
import logging
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime
import os

from core.data_models import (
    WorkflowHistoryItem,
    WorkflowHistoryResponse,
    WorkflowHistoryFilter,
    WorkflowHistorySummary,
    CostData,
)
from core.cost_tracker import read_cost_history

logger = logging.getLogger(__name__)

# Database path
DB_PATH = Path(__file__).parent.parent / "db" / "database.db"


def get_db_connection() -> sqlite3.Connection:
    """Get database connection with proper settings"""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def init_workflow_history_db() -> None:
    """Initialize workflow_history table if it doesn't exist"""
    conn = get_db_connection()
    cursor = conn.cursor()

    # Create table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS workflow_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            adw_id TEXT NOT NULL,
            issue_number INTEGER,
            workflow_template TEXT,
            model_set TEXT,
            status TEXT NOT NULL,
            started_at TIMESTAMP NOT NULL,
            completed_at TIMESTAMP,
            user_input TEXT,
            github_url TEXT,
            total_duration_seconds REAL,
            worktree_path TEXT,
            backend_port INTEGER,
            frontend_port INTEGER,
            concurrent_workflows INTEGER,
            error_message TEXT
        )
    """)

    # Create indexes
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_adw_id
        ON workflow_history(adw_id)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_started_at
        ON workflow_history(started_at DESC)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_status
        ON workflow_history(status)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_workflow_template
        ON workflow_history(workflow_template)
    """)

    conn.commit()
    conn.close()
    logger.info("[DB] Workflow history table initialized")


def record_workflow_start(
    adw_id: str,
    issue_number: Optional[int] = None,
    workflow_template: Optional[str] = None,
    model_set: Optional[str] = None,
    user_input: Optional[str] = None,
    github_url: Optional[str] = None,
    backend_port: Optional[int] = None,
    frontend_port: Optional[int] = None,
    concurrent_workflows: Optional[int] = None,
) -> None:
    """Record workflow start event"""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO workflow_history (
            adw_id, issue_number, workflow_template, model_set, status,
            started_at, user_input, github_url, backend_port, frontend_port,
            concurrent_workflows
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        adw_id,
        issue_number,
        workflow_template,
        model_set,
        "in_progress",
        datetime.now().isoformat(),
        user_input,
        github_url,
        backend_port,
        frontend_port,
        concurrent_workflows,
    ))

    conn.commit()
    conn.close()
    logger.info(f"[DB] Recorded workflow start: {adw_id}")


def record_workflow_complete(
    adw_id: str,
    total_duration_seconds: float,
) -> None:
    """Record workflow completion"""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE workflow_history
        SET status = ?,
            completed_at = ?,
            total_duration_seconds = ?
        WHERE adw_id = ? AND status = 'in_progress'
    """, (
        "completed",
        datetime.now().isoformat(),
        total_duration_seconds,
        adw_id,
    ))

    conn.commit()
    conn.close()
    logger.info(f"[DB] Recorded workflow completion: {adw_id}")


def record_workflow_failed(
    adw_id: str,
    error_message: str,
) -> None:
    """Record workflow failure"""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE workflow_history
        SET status = ?,
            completed_at = ?,
            error_message = ?
        WHERE adw_id = ? AND status = 'in_progress'
    """, (
        "failed",
        datetime.now().isoformat(),
        error_message,
        adw_id,
    ))

    conn.commit()
    conn.close()
    logger.info(f"[DB] Recorded workflow failure: {adw_id}")


def get_workflow_history(filters: WorkflowHistoryFilter) -> WorkflowHistoryResponse:
    """Query workflow history with filters and pagination"""
    conn = get_db_connection()
    cursor = conn.cursor()

    # Build WHERE clause
    where_clauses = []
    params = []

    if filters.model_filter and filters.model_filter != "all":
        where_clauses.append("model_set = ?")
        params.append(filters.model_filter)

    if filters.template_filter and filters.template_filter != "all":
        where_clauses.append("workflow_template = ?")
        params.append(filters.template_filter)

    if filters.status_filter and filters.status_filter != "all":
        where_clauses.append("status = ?")
        params.append(filters.status_filter)

    if filters.date_from:
        where_clauses.append("started_at >= ?")
        params.append(filters.date_from)

    if filters.date_to:
        where_clauses.append("started_at <= ?")
        params.append(filters.date_to)

    if filters.search_query:
        # Search in ADW ID, issue number, or user input
        where_clauses.append(
            "(adw_id LIKE ? OR CAST(issue_number AS TEXT) LIKE ? OR user_input LIKE ?)"
        )
        search_pattern = f"%{filters.search_query}%"
        params.extend([search_pattern, search_pattern, search_pattern])

    where_sql = "WHERE " + " AND ".join(where_clauses) if where_clauses else ""

    # Build ORDER BY clause
    order_column = {
        "date": "started_at",
        "duration": "total_duration_seconds",
        "status": "status",
    }.get(filters.sort_by, "started_at")

    order_direction = "ASC" if filters.order == "asc" else "DESC"
    order_sql = f"ORDER BY {order_column} {order_direction}"

    # Count total matching records
    count_sql = f"SELECT COUNT(*) FROM workflow_history {where_sql}"
    cursor.execute(count_sql, params)
    total_count = cursor.fetchone()[0]

    # Query with pagination
    query_sql = f"""
        SELECT * FROM workflow_history
        {where_sql}
        {order_sql}
        LIMIT ? OFFSET ?
    """
    cursor.execute(query_sql, params + [filters.limit, filters.offset])

    rows = cursor.fetchall()
    conn.close()

    # Convert to WorkflowHistoryItem objects
    items = []
    for row in rows:
        item = WorkflowHistoryItem(
            id=row["id"],
            adw_id=row["adw_id"],
            issue_number=row["issue_number"],
            workflow_template=row["workflow_template"],
            model_set=row["model_set"],
            status=row["status"],
            started_at=row["started_at"],
            completed_at=row["completed_at"],
            user_input=row["user_input"],
            github_url=row["github_url"],
            total_duration_seconds=row["total_duration_seconds"],
            worktree_path=row["worktree_path"],
            backend_port=row["backend_port"],
            frontend_port=row["frontend_port"],
            concurrent_workflows=row["concurrent_workflows"],
            error_message=row["error_message"],
            cost_data=None,  # Will be enriched separately
        )
        items.append(item)

    return WorkflowHistoryResponse(
        items=items,
        total=total_count,
        filters_applied=filters,
    )


def enrich_with_cost_data(history_item: WorkflowHistoryItem) -> WorkflowHistoryItem:
    """Enrich workflow history item with cost data from cost_tracker"""
    try:
        cost_data = read_cost_history(history_item.adw_id)
        history_item.cost_data = cost_data
    except (FileNotFoundError, ValueError) as e:
        logger.debug(f"[COST] No cost data available for {history_item.adw_id}: {e}")
        history_item.cost_data = None
    except Exception as e:
        logger.error(f"[COST] Error reading cost data for {history_item.adw_id}: {e}")
        history_item.cost_data = None

    return history_item


def get_workflow_history_summary() -> WorkflowHistorySummary:
    """Calculate summary statistics for all workflows"""
    conn = get_db_connection()
    cursor = conn.cursor()

    # Total workflows
    cursor.execute("SELECT COUNT(*) FROM workflow_history")
    total_workflows = cursor.fetchone()[0]

    # Average duration for completed workflows
    cursor.execute("""
        SELECT AVG(total_duration_seconds)
        FROM workflow_history
        WHERE status = 'completed' AND total_duration_seconds IS NOT NULL
    """)
    result = cursor.fetchone()[0]
    avg_duration = float(result) if result else 0.0

    # Success rate
    cursor.execute("""
        SELECT
            COUNT(CASE WHEN status = 'completed' THEN 1 END) * 100.0 / COUNT(*) as success_rate
        FROM workflow_history
        WHERE status IN ('completed', 'failed')
    """)
    result = cursor.fetchone()[0]
    success_rate = float(result) if result else 0.0

    # Workflow counts by template
    cursor.execute("""
        SELECT workflow_template, COUNT(*) as count
        FROM workflow_history
        WHERE workflow_template IS NOT NULL
        GROUP BY workflow_template
        ORDER BY count DESC
    """)
    workflow_counts = {row[0]: row[1] for row in cursor.fetchall()}

    # Workflow counts by model
    cursor.execute("""
        SELECT model_set, COUNT(*) as count
        FROM workflow_history
        WHERE model_set IS NOT NULL
        GROUP BY model_set
        ORDER BY count DESC
    """)
    model_counts = {row[0]: row[1] for row in cursor.fetchall()}

    conn.close()

    # Calculate cost metrics (would need to aggregate from cost_tracker)
    # For now, return placeholder values
    avg_cost = 0.0
    cache_efficiency = 0.0

    return WorkflowHistorySummary(
        total_workflows=total_workflows,
        avg_cost=avg_cost,
        avg_duration=avg_duration,
        success_rate=success_rate,
        cache_efficiency=cache_efficiency,
        workflow_counts=workflow_counts,
        model_counts=model_counts,
    )


def get_concurrent_workflow_count() -> int:
    """Count active workflows from agents directory"""
    agents_dir = Path(__file__).parent.parent.parent.parent / "agents"

    if not agents_dir.exists():
        return 0

    count = 0
    for adw_dir in agents_dir.iterdir():
        if adw_dir.is_dir():
            state_file = adw_dir / "adw_state.json"
            if state_file.exists():
                count += 1

    return count


# Initialize database on module import
init_workflow_history_db()
