"""
Workflow history tracking module for ADW workflows.

This module provides database operations for storing and retrieving workflow
execution history, including metadata, costs, performance metrics, and status.
"""

import json
import logging
import sqlite3
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from contextlib import contextmanager

from core.cost_tracker import read_cost_history

logger = logging.getLogger(__name__)

# Database path
DB_PATH = Path(__file__).parent.parent / "db" / "workflow_history.db"


@contextmanager
def get_db_connection():
    """Context manager for database connections"""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row  # Return rows as dictionaries
    try:
        yield conn
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()


def init_db():
    """
    Initialize the workflow history database with schema.

    Creates the workflow_history table with all required fields and indexes.
    Safe to call multiple times - creates tables only if they don't exist.
    """
    # Ensure db directory exists
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    with get_db_connection() as conn:
        cursor = conn.cursor()

        # Create workflow_history table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS workflow_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                adw_id TEXT NOT NULL UNIQUE,
                issue_number INTEGER,
                nl_input TEXT,
                github_url TEXT,
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

        logger.info(f"[DB] Workflow history database initialized at {DB_PATH}")


def insert_workflow_history(
    adw_id: str,
    issue_number: Optional[int] = None,
    nl_input: Optional[str] = None,
    github_url: Optional[str] = None,
    workflow_template: Optional[str] = None,
    model_used: Optional[str] = None,
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
        **kwargs: Additional optional fields (worktree_path, ports, etc.)

    Returns:
        int: The ID of the inserted record

    Raises:
        sqlite3.IntegrityError: If a workflow with this adw_id already exists
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()

        # Build dynamic query based on provided kwargs
        fields = [
            "adw_id", "issue_number", "nl_input", "github_url",
            "workflow_template", "model_used", "status"
        ]
        values = [
            adw_id, issue_number, nl_input, github_url,
            workflow_template, model_used, status
        ]

        # Add optional fields from kwargs
        optional_fields = [
            "start_time", "end_time", "duration_seconds", "error_message",
            "phase_count", "current_phase", "success_rate", "retry_count",
            "worktree_path", "backend_port", "frontend_port", "concurrent_workflows"
        ]

        for field in optional_fields:
            if field in kwargs:
                fields.append(field)
                values.append(kwargs[field])

        placeholders = ", ".join(["?" for _ in values])
        fields_str = ", ".join(fields)

        query = f"INSERT INTO workflow_history ({fields_str}) VALUES ({placeholders})"

        cursor.execute(query, values)
        row_id = cursor.lastrowid

        logger.info(f"[DB] Inserted workflow history for ADW {adw_id} (ID: {row_id})")
        return row_id


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

    with get_db_connection() as conn:
        cursor = conn.cursor()

        # Build update query
        set_clauses = [f"{field} = ?" for field in kwargs.keys()]
        set_clauses.append("updated_at = CURRENT_TIMESTAMP")

        query = f"""
            UPDATE workflow_history
            SET {", ".join(set_clauses)}
            WHERE adw_id = ?
        """

        values = list(kwargs.values()) + [adw_id]
        cursor.execute(query, values)

        if cursor.rowcount > 0:
            logger.info(f"[DB] Updated workflow history for ADW {adw_id}")
            return True
        else:
            logger.warning(f"[DB] No workflow found with ADW ID {adw_id}")
            return False


def get_workflow_by_adw_id(adw_id: str) -> Optional[Dict]:
    """
    Get a single workflow history record by ADW ID.

    Args:
        adw_id: The ADW workflow identifier

    Returns:
        Dict: Workflow history record as a dictionary, or None if not found
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM workflow_history WHERE adw_id = ?", (adw_id,))
        row = cursor.fetchone()

        if row:
            return dict(row)
        return None


def get_workflow_history(
    limit: int = 20,
    offset: int = 0,
    status: Optional[str] = None,
    model: Optional[str] = None,
    template: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    search: Optional[str] = None,
    sort_by: str = "created_at",
    sort_order: str = "DESC"
) -> Tuple[List[Dict], int]:
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
    with get_db_connection() as conn:
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
            "duration_seconds", "status", "adw_id", "issue_number"
        ]
        if sort_by not in valid_sort_fields:
            sort_by = "created_at"

        # Validate sort_order
        sort_order = sort_order.upper()
        if sort_order not in ["ASC", "DESC"]:
            sort_order = "DESC"

        # Get paginated results
        query = f"""
            SELECT * FROM workflow_history
            {where_sql}
            ORDER BY {sort_by} {sort_order}
            LIMIT ? OFFSET ?
        """
        cursor.execute(query, params + [limit, offset])
        rows = cursor.fetchall()

        results = [dict(row) for row in rows]

        logger.info(
            f"[DB] Retrieved {len(results)} workflows (total: {total_count}, "
            f"offset: {offset}, limit: {limit})"
        )

        return results, total_count


def get_history_analytics() -> Dict:
    """
    Calculate analytics summary for all workflow history.

    Returns:
        Dict: Analytics including:
            - total_workflows: Total number of workflows
            - completed_workflows: Number of completed workflows
            - failed_workflows: Number of failed workflows
            - avg_duration: Average duration in seconds
            - success_rate: Overall success rate (0-100)
            - workflows_by_model: Count by model type
            - workflows_by_template: Count by template type
            - workflows_by_status: Count by status
    """
    with get_db_connection() as conn:
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

        analytics = {
            "total_workflows": total_workflows,
            "completed_workflows": completed_workflows,
            "failed_workflows": failed_workflows,
            "avg_duration_seconds": avg_duration,
            "success_rate_percent": success_rate,
            "workflows_by_model": workflows_by_model,
            "workflows_by_template": workflows_by_template,
            "workflows_by_status": status_counts,
        }

        logger.info(f"[DB] Generated analytics: {analytics}")
        return analytics


def scan_agents_directory() -> List[Dict]:
    """
    Scan the agents directory for workflow state files and extract metadata.

    Returns:
        List[Dict]: List of workflow metadata dictionaries with fields:
            - adw_id: ADW workflow identifier
            - issue_number: GitHub issue number (if available)
            - nl_input: Natural language input
            - github_url: GitHub issue URL
            - workflow_template: Template name
            - model_used: Model identifier
            - status: Current status
            - start_time: Start timestamp
            - current_phase: Current workflow phase
            - worktree_path: Path to worktree
    """
    # Locate agents directory
    project_root = Path(__file__).parent.parent.parent.parent
    agents_dir = project_root / "agents"

    if not agents_dir.exists():
        logger.warning(f"[SCAN] Agents directory not found: {agents_dir}")
        return []

    workflows = []

    # Iterate through subdirectories in agents/
    for adw_dir in agents_dir.iterdir():
        if not adw_dir.is_dir():
            continue

        adw_id = adw_dir.name
        state_file = adw_dir / "adw_state.json"

        if not state_file.exists():
            logger.debug(f"[SCAN] No adw_state.json found for {adw_id}")
            continue

        try:
            with open(state_file, 'r') as f:
                state_data = json.load(f)

            # Extract metadata from state file
            workflow = {
                "adw_id": adw_id,
                "issue_number": state_data.get("issue_number"),
                "nl_input": state_data.get("nl_input"),
                "github_url": state_data.get("github_url"),
                "workflow_template": state_data.get("workflow_template", state_data.get("workflow")),
                "model_used": state_data.get("model_used", state_data.get("model")),
                "status": state_data.get("status", "unknown"),
                "start_time": state_data.get("start_time"),
                "current_phase": state_data.get("current_phase"),
                "worktree_path": str(adw_dir),
            }

            # Infer status if not explicitly set
            if workflow["status"] == "unknown":
                # Check if there's an error file
                error_file = adw_dir / "error.log"
                if error_file.exists():
                    workflow["status"] = "failed"
                else:
                    # Check for completion indicators
                    completed_phases = [
                        d for d in adw_dir.iterdir()
                        if d.is_dir() and d.name in ["plan", "build", "test", "review", "document", "ship"]
                    ]
                    if len(completed_phases) >= 3:
                        workflow["status"] = "completed"
                    else:
                        workflow["status"] = "running"

            workflows.append(workflow)
            logger.debug(f"[SCAN] Found workflow {adw_id}: {workflow['status']}")

        except Exception as e:
            logger.error(f"[SCAN] Error parsing {state_file}: {e}")
            continue

    logger.info(f"[SCAN] Scanned agents directory, found {len(workflows)} workflows")
    return workflows


def sync_workflow_history() -> int:
    """
    Synchronize workflow history database with agents directory.

    Scans the agents directory for workflows and updates the database:
    - Inserts new workflows
    - Updates existing workflows if status changed
    - Enriches with cost data from cost_tracker

    Returns:
        int: Number of workflows synchronized
    """
    workflows = scan_agents_directory()
    synced_count = 0

    for workflow_data in workflows:
        adw_id = workflow_data["adw_id"]

        # Check if workflow already exists in database
        existing = get_workflow_by_adw_id(adw_id)

        # Try to get cost data
        cost_data = None
        try:
            cost_data = read_cost_history(adw_id)

            # Extract model from cost data if not in state
            if not workflow_data.get("model_used") and cost_data.phases:
                # The model is stored in the phase, we need to re-parse to get it
                # For now, we'll use a default
                workflow_data["model_used"] = "claude-sonnet-4-5"  # Default

        except Exception as e:
            logger.debug(f"[SYNC] No cost data for {adw_id}: {e}")

        # Calculate duration if we have start and end times
        duration_seconds = None
        if workflow_data.get("start_time") and workflow_data["status"] == "completed":
            try:
                start_dt = datetime.fromisoformat(workflow_data["start_time"].replace("Z", "+00:00"))
                # Use current time as end time if not specified
                end_dt = datetime.now()
                duration_seconds = int((end_dt - start_dt).total_seconds())
            except Exception as e:
                logger.debug(f"[SYNC] Could not calculate duration for {adw_id}: {e}")

        if existing:
            # Update existing record if status or other fields changed
            updates = {}

            if existing["status"] != workflow_data["status"]:
                updates["status"] = workflow_data["status"]

            if workflow_data.get("current_phase") and existing["current_phase"] != workflow_data["current_phase"]:
                updates["current_phase"] = workflow_data["current_phase"]

            if duration_seconds and not existing["duration_seconds"]:
                updates["duration_seconds"] = duration_seconds

            if updates:
                update_workflow_history(adw_id, **updates)
                synced_count += 1
        else:
            # Insert new workflow
            insert_data = {
                **workflow_data,
                "created_at": workflow_data.get("start_time", datetime.now().isoformat()),
            }

            if duration_seconds:
                insert_data["duration_seconds"] = duration_seconds

            insert_workflow_history(**insert_data)
            synced_count += 1

    logger.info(f"[SYNC] Synchronized {synced_count} workflows")
    return synced_count
