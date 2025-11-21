"""
Database operations for workflow history.

This module provides all database CRUD operations for workflow history tracking,
including schema initialization, insertions, updates, queries, and analytics.
"""

import json
import logging
import sqlite3
from pathlib import Path

from utils.db_connection import get_connection as get_db_connection

logger = logging.getLogger(__name__)

# Database path - relative to this file: core/workflow_history_utils/database.py
DB_PATH = Path(__file__).parent.parent.parent / "db" / "workflow_history.db"


def init_db():
    """
    Initialize the workflow history database with schema.

    Creates the workflow_history table with all required fields and indexes.
    Safe to call multiple times - creates tables only if they don't exist.
    """
    # Ensure db directory exists
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    with get_db_connection(db_path=str(DB_PATH)) as conn:
        cursor = conn.cursor()

        # Create workflow_history table with comprehensive fields
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS workflow_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                adw_id TEXT NOT NULL UNIQUE,
                issue_number INTEGER,
                nl_input TEXT,
                github_url TEXT,
                gh_issue_state TEXT,  -- GitHub issue state: 'open', 'closed', or NULL
                workflow_template TEXT,
                model_used TEXT,
                status TEXT NOT NULL CHECK(status IN ('pending', 'running', 'completed', 'failed')),
                start_time TEXT,
                end_time TEXT,
                duration_seconds INTEGER,
                error_message TEXT,
                phase_count INTEGER,
                current_phase TEXT,
                success_rate REAL,
                retry_count INTEGER DEFAULT 0,
                worktree_path TEXT,
                backend_port INTEGER,
                frontend_port INTEGER,
                concurrent_workflows INTEGER DEFAULT 0,

                -- Token usage fields
                input_tokens INTEGER DEFAULT 0,
                output_tokens INTEGER DEFAULT 0,
                cached_tokens INTEGER DEFAULT 0,
                cache_hit_tokens INTEGER DEFAULT 0,
                cache_miss_tokens INTEGER DEFAULT 0,
                total_tokens INTEGER DEFAULT 0,
                cache_efficiency_percent REAL DEFAULT 0.0,

                -- Cost tracking fields
                estimated_cost_total REAL DEFAULT 0.0,
                actual_cost_total REAL DEFAULT 0.0,
                estimated_cost_per_step REAL DEFAULT 0.0,
                actual_cost_per_step REAL DEFAULT 0.0,
                cost_per_token REAL DEFAULT 0.0,

                -- Structured data fields (JSON)
                structured_input TEXT,  -- JSON object
                cost_breakdown TEXT,    -- JSON object
                token_breakdown TEXT,   -- JSON object

                -- Resource usage
                worktree_reused INTEGER DEFAULT 0,  -- Boolean (0 or 1)
                steps_completed INTEGER DEFAULT 0,
                steps_total INTEGER DEFAULT 0,

                -- Phase 3A: Analytics fields (temporal and scoring)
                hour_of_day INTEGER DEFAULT -1,
                day_of_week INTEGER DEFAULT -1,
                nl_input_clarity_score REAL DEFAULT 0.0,
                cost_efficiency_score REAL DEFAULT 0.0,
                performance_score REAL DEFAULT 0.0,
                quality_score REAL DEFAULT 0.0,

                -- Phase 3B: Scoring version tracking
                scoring_version TEXT DEFAULT '1.0',

                -- Phase 3D: Insights & Recommendations
                anomaly_flags TEXT,  -- JSON array of anomaly objects
                optimization_recommendations TEXT,  -- JSON array of recommendation strings

                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Create indexes for fast queries
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_adw_id ON workflow_history(adw_id)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_status ON workflow_history(status)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_created_at ON workflow_history(created_at DESC)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_issue_number ON workflow_history(issue_number)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_model_used ON workflow_history(model_used)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_workflow_template ON workflow_history(workflow_template)
        """)

        # Migration: Add gh_issue_state column if it doesn't exist
        try:
            cursor.execute("SELECT gh_issue_state FROM workflow_history LIMIT 1")
        except sqlite3.OperationalError:
            # Column doesn't exist, add it
            logger.info("[DB] Adding gh_issue_state column to workflow_history table")
            cursor.execute("ALTER TABLE workflow_history ADD COLUMN gh_issue_state TEXT")
            conn.commit()

        logger.info(f"[DB] Workflow history database initialized at {DB_PATH}")


def insert_workflow_history(
    adw_id: str,
    issue_number: int | None = None,
    nl_input: str | None = None,
    github_url: str | None = None,
    workflow_template: str | None = None,
    model_used: str | None = None,
    status: str = "pending",
    **kwargs
) -> int:
    """
    Insert a new workflow history record.

    Args:
        adw_id: Unique ADW workflow identifier
        issue_number: GitHub issue number
        nl_input: Natural language input from user
        github_url: GitHub URL for the issue
        workflow_template: Name of the workflow template (e.g., 'adw_sdlc_iso')
        model_used: Model used for the workflow (e.g., 'claude-sonnet-4-5')
        status: Workflow status (pending, running, completed, failed)
        **kwargs: Additional optional fields

    Returns:
        int: The ID of the inserted record

    Raises:
        sqlite3.IntegrityError: If a workflow with this adw_id already exists
    """
    with get_db_connection(db_path=str(DB_PATH)) as conn:
        cursor = conn.cursor()

        # Build dynamic query based on provided kwargs
        fields = [
            "adw_id", "issue_number", "nl_input", "github_url", "gh_issue_state",
            "workflow_template", "model_used", "status"
        ]
        values = [
            adw_id, issue_number, nl_input, github_url, kwargs.get("gh_issue_state"),
            workflow_template, model_used, status
        ]

        # Add optional fields from kwargs
        optional_fields = [
            "start_time", "end_time", "duration_seconds", "error_message",
            "phase_count", "current_phase", "success_rate", "retry_count",
            "worktree_path", "backend_port", "frontend_port", "concurrent_workflows",
            "input_tokens", "output_tokens", "cached_tokens", "cache_hit_tokens",
            "cache_miss_tokens", "total_tokens", "cache_efficiency_percent",
            "estimated_cost_total", "actual_cost_total", "estimated_cost_per_step",
            "actual_cost_per_step", "cost_per_token", "structured_input",
            "cost_breakdown", "token_breakdown", "worktree_reused",
            "steps_completed", "steps_total",
            "phase_durations", "idle_time_seconds", "bottleneck_phase",
            "error_category", "retry_reasons", "error_phase_distribution",
            "recovery_time_seconds", "complexity_estimated", "complexity_actual",
            # Phase 3A/3B: Analytics scoring fields
            "hour_of_day", "day_of_week", "scoring_version",
            "nl_input_clarity_score", "cost_efficiency_score",
            "performance_score", "quality_score",
            # Phase 3D: Insights & recommendations
            "anomaly_flags", "optimization_recommendations",
            # Timestamp override (normally auto-set by DB)
            "created_at"
        ]

        for field in optional_fields:
            if field in kwargs:
                fields.append(field)
                # Convert dicts and lists to JSON strings
                json_fields = [
                    "structured_input", "cost_breakdown", "token_breakdown",
                    "phase_durations", "retry_reasons", "error_phase_distribution",
                    "anomaly_flags", "optimization_recommendations"
                ]
                if field in json_fields:
                    if isinstance(kwargs[field], (dict, list)):
                        values.append(json.dumps(kwargs[field]))
                    else:
                        values.append(kwargs[field])
                else:
                    values.append(kwargs[field])

        placeholders = ", ".join(["?" for _ in values])
        fields_str = ", ".join(fields)

        query = f"INSERT INTO workflow_history ({fields_str}) VALUES ({placeholders})"

        cursor.execute(query, values)
        row_id = cursor.lastrowid

        logger.info(f"[DB] Inserted workflow history for ADW {adw_id} (ID: {row_id})")
        return row_id


def update_workflow_history_by_issue(
    issue_number: int,
    **kwargs
) -> int:
    """
    Update all workflow history records for a given issue number.

    Args:
        issue_number: The GitHub issue number
        **kwargs: Fields to update (gh_issue_state, etc.)

    Returns:
        int: Number of records updated
    """
    if not kwargs:
        logger.warning(f"[DB] No fields provided to update for issue #{issue_number}")
        return 0

    with get_db_connection(db_path=str(DB_PATH)) as conn:
        cursor = conn.cursor()

        # Build UPDATE query
        set_clauses = []
        values = []
        for field, value in kwargs.items():
            set_clauses.append(f"{field} = ?")
            values.append(value)

        set_clauses.append("updated_at = CURRENT_TIMESTAMP")
        values.append(issue_number)

        query = f"""
            UPDATE workflow_history
            SET {", ".join(set_clauses)}
            WHERE issue_number = ?
        """

        cursor.execute(query, values)
        updated_count = cursor.rowcount

        if updated_count > 0:
            logger.info(f"[DB] Updated {updated_count} workflow(s) for issue #{issue_number}")
        else:
            logger.warning(f"[DB] No workflows found for issue #{issue_number}")

        return updated_count


def update_workflow_history(
    adw_id: str,
    **kwargs
) -> bool:
    """
    Update an existing workflow history record.

    Args:
        adw_id: The ADW ID to update
        **kwargs: Fields to update (status, end_time, error_message, etc.)

    Returns:
        bool: True if update succeeded, False if no record found
    """
    if not kwargs:
        logger.warning(f"[DB] No fields provided to update for ADW {adw_id}")
        return False

    with get_db_connection(db_path=str(DB_PATH)) as conn:
        cursor = conn.cursor()

        # Convert dicts and lists to JSON strings
        json_fields = [
            "structured_input", "cost_breakdown", "token_breakdown",
            "phase_durations", "retry_reasons", "error_phase_distribution",
            "anomaly_flags", "optimization_recommendations"
        ]
        for field in json_fields:
            if field in kwargs and isinstance(kwargs[field], (dict, list)):
                kwargs[field] = json.dumps(kwargs[field])

        # Build update query
        set_clauses = [f"{field} = ?" for field in kwargs]
        set_clauses.append("updated_at = CURRENT_TIMESTAMP")

        query = f"""
            UPDATE workflow_history
            SET {", ".join(set_clauses)}
            WHERE adw_id = ?
        """

        values = list(kwargs.values()) + [adw_id]
        cursor.execute(query, values)

        if cursor.rowcount > 0:
            logger.debug(f"[DB] Updated workflow history for ADW {adw_id}")
            return True
        else:
            logger.warning(f"[DB] No workflow found with ADW ID {adw_id}")
            return False


def get_workflow_by_adw_id(adw_id: str) -> dict | None:
    """
    Get a single workflow history record by ADW ID.

    Args:
        adw_id: The ADW workflow identifier

    Returns:
        Dict: Workflow history record as a dictionary, or None if not found
    """
    with get_db_connection(db_path=str(DB_PATH)) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM workflow_history WHERE adw_id = ?", (adw_id,))
        row = cursor.fetchone()

        if row:
            result = dict(row)
            # Parse JSON fields
            json_fields = [
                "structured_input", "cost_breakdown", "token_breakdown",
                "phase_durations", "retry_reasons", "error_phase_distribution",
                "anomaly_flags", "optimization_recommendations"  # Phase 3D
            ]
            for field in json_fields:
                if result.get(field):
                    try:
                        result[field] = json.loads(result[field])
                    except json.JSONDecodeError:
                        logger.warning(f"[DB] Failed to parse JSON for {field} in ADW {adw_id}")
                        result[field] = None
                else:
                    # Default to empty arrays for Phase 3D fields
                    if field in ["anomaly_flags", "optimization_recommendations"]:
                        result[field] = []
            return result
        return None


def get_workflow_history(
    limit: int = 20,
    offset: int = 0,
    status: str | None = None,
    model: str | None = None,
    template: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    search: str | None = None,
    sort_by: str = "created_at",
    sort_order: str = "DESC"
) -> tuple[list[dict], int]:
    """
    Get workflow history records with filtering, sorting, and pagination.

    Args:
        limit: Maximum number of records to return (default 20)
        offset: Number of records to skip (default 0)
        status: Filter by status (pending, running, completed, failed)
        model: Filter by model name
        template: Filter by workflow template name
        start_date: Filter workflows created after this date (ISO format)
        end_date: Filter workflows created before this date (ISO format)
        search: Search in ADW ID, nl_input, or github_url
        sort_by: Field to sort by (default: created_at)
        sort_order: Sort order (ASC or DESC, default: DESC)

    Returns:
        Tuple[List[Dict], int]: List of workflow records and total count (before pagination)
    """
    with get_db_connection(db_path=str(DB_PATH)) as conn:
        cursor = conn.cursor()

        # Build WHERE clauses
        where_clauses = []
        params = []

        if status:
            where_clauses.append("status = ?")
            params.append(status)

        if model:
            where_clauses.append("model_used = ?")
            params.append(model)

        if template:
            where_clauses.append("workflow_template = ?")
            params.append(template)

        if start_date:
            where_clauses.append("created_at >= ?")
            params.append(start_date)

        if end_date:
            where_clauses.append("created_at <= ?")
            params.append(end_date)

        if search:
            where_clauses.append(
                "(adw_id LIKE ? OR nl_input LIKE ? OR github_url LIKE ?)"
            )
            search_param = f"%{search}%"
            params.extend([search_param, search_param, search_param])

        where_sql = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""

        # Get total count (before pagination)
        count_query = f"SELECT COUNT(*) as total FROM workflow_history {where_sql}"
        cursor.execute(count_query, params)
        total_count = cursor.fetchone()["total"]

        # Validate sort_by field to prevent SQL injection
        valid_sort_fields = [
            "created_at", "updated_at", "start_time", "end_time",
            "duration_seconds", "status", "adw_id", "issue_number",
            "actual_cost_total", "total_tokens", "cache_efficiency_percent"
        ]
        if sort_by not in valid_sort_fields:
            sort_by = "created_at"

        # Validate sort_order
        sort_order = sort_order.upper()
        if sort_order not in ["ASC", "DESC"]:
            sort_order = "DESC"

        # Get paginated results
        # Note: Use column aliases to bridge schema mismatch between DB and Pydantic models
        # Database has: submission_hour, submission_day_of_week
        # Pydantic expects: hour_of_day, day_of_week
        # This allows existing data to work without migration
        query = f"""
            SELECT
                *,
                submission_hour as hour_of_day,
                submission_day_of_week as day_of_week
            FROM workflow_history
            {where_sql}
            ORDER BY {sort_by} {sort_order}
            LIMIT ? OFFSET ?
        """
        cursor.execute(query, params + [limit, offset])
        rows = cursor.fetchall()

        results = []
        for row in rows:
            result = dict(row)
            # Parse JSON fields
            json_fields = [
                "structured_input", "cost_breakdown", "token_breakdown",
                "phase_durations", "retry_reasons", "error_phase_distribution",
                "anomaly_flags", "optimization_recommendations"  # Phase 3D
            ]
            for field in json_fields:
                if result.get(field):
                    try:
                        result[field] = json.loads(result[field])
                    except json.JSONDecodeError:
                        logger.warning(f"[DB] Failed to parse JSON for {field}")
                        result[field] = None
                else:
                    # Default to empty arrays for Phase 3D fields
                    if field in ["anomaly_flags", "optimization_recommendations"]:
                        result[field] = []

            # Convert None to defaults for score fields (legacy data compatibility)
            score_fields = {
                "nl_input_clarity_score": 0.0,
                "cost_efficiency_score": 0.0,
                "performance_score": 0.0,
                "quality_score": 0.0,
                "estimated_cost_total": 0.0,
            }
            for field, default_value in score_fields.items():
                if result.get(field) is None:
                    result[field] = default_value

            results.append(result)

        logger.debug(
            f"[DB] Retrieved {len(results)} workflows (total: {total_count}, "
            f"offset: {offset}, limit: {limit})"
        )

        return results, total_count


def get_history_analytics() -> dict:
    """
    Calculate analytics summary for all workflow history.

    Returns:
        Dict: Analytics including:
            - total_workflows: Total number of workflows
            - completed_workflows: Number of completed workflows
            - failed_workflows: Number of failed workflows
            - avg_duration_seconds: Average duration in seconds
            - success_rate_percent: Overall success rate (0-100)
            - workflows_by_model: Count by model type
            - workflows_by_template: Count by template type
            - workflows_by_status: Count by status
            - avg_cost: Average cost per workflow
            - total_cost: Total cost across all workflows
            - avg_tokens: Average tokens per workflow
            - avg_cache_efficiency: Average cache efficiency percentage
    """
    with get_db_connection(db_path=str(DB_PATH)) as conn:
        cursor = conn.cursor()

        # Total workflows
        cursor.execute("SELECT COUNT(*) as total FROM workflow_history")
        total_workflows = cursor.fetchone()["total"]

        # Count by status
        cursor.execute("""
            SELECT status, COUNT(*) as count
            FROM workflow_history
            GROUP BY status
        """)
        status_counts = {row["status"]: row["count"] for row in cursor.fetchall()}

        completed_workflows = status_counts.get("completed", 0)
        failed_workflows = status_counts.get("failed", 0)

        # Calculate success rate
        success_rate = (
            (completed_workflows / total_workflows * 100)
            if total_workflows > 0
            else 0.0
        )

        # Average duration (only for completed workflows)
        cursor.execute("""
            SELECT AVG(duration_seconds) as avg_duration
            FROM workflow_history
            WHERE status = 'completed' AND duration_seconds IS NOT NULL
        """)
        avg_duration_row = cursor.fetchone()
        avg_duration = avg_duration_row["avg_duration"] if avg_duration_row["avg_duration"] else 0.0

        # Count by model
        cursor.execute("""
            SELECT model_used, COUNT(*) as count
            FROM workflow_history
            WHERE model_used IS NOT NULL
            GROUP BY model_used
        """)
        workflows_by_model = {row["model_used"]: row["count"] for row in cursor.fetchall()}

        # Count by template
        cursor.execute("""
            SELECT workflow_template, COUNT(*) as count
            FROM workflow_history
            WHERE workflow_template IS NOT NULL
            GROUP BY workflow_template
        """)
        workflows_by_template = {
            row["workflow_template"]: row["count"] for row in cursor.fetchall()
        }

        # Cost analytics
        cursor.execute("""
            SELECT
                AVG(actual_cost_total) as avg_cost,
                SUM(actual_cost_total) as total_cost
            FROM workflow_history
            WHERE actual_cost_total IS NOT NULL AND actual_cost_total > 0
        """)
        cost_row = cursor.fetchone()
        avg_cost = cost_row["avg_cost"] if cost_row["avg_cost"] else 0.0
        total_cost = cost_row["total_cost"] if cost_row["total_cost"] else 0.0

        # Token analytics
        cursor.execute("""
            SELECT
                AVG(total_tokens) as avg_tokens,
                AVG(cache_efficiency_percent) as avg_cache_efficiency
            FROM workflow_history
            WHERE total_tokens IS NOT NULL AND total_tokens > 0
        """)
        token_row = cursor.fetchone()
        avg_tokens = token_row["avg_tokens"] if token_row["avg_tokens"] else 0.0
        avg_cache_efficiency = token_row["avg_cache_efficiency"] if token_row["avg_cache_efficiency"] else 0.0

        analytics = {
            "total_workflows": total_workflows,
            "completed_workflows": completed_workflows,
            "failed_workflows": failed_workflows,
            "avg_duration_seconds": avg_duration,
            "success_rate_percent": success_rate,
            "workflows_by_model": workflows_by_model,
            "workflows_by_template": workflows_by_template,
            "workflows_by_status": status_counts,
            "avg_cost": avg_cost,
            "total_cost": total_cost,
            "avg_tokens": avg_tokens,
            "avg_cache_efficiency": avg_cache_efficiency,
        }

        logger.debug(f"[DB] Generated analytics: {analytics}")
        return analytics
