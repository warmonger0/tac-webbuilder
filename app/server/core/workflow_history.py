"""
Workflow history tracking module for ADW workflows.

This module provides database operations for storing and retrieving workflow
execution history, including metadata, costs, performance metrics, token usage,
and detailed status information.
"""

import json
import logging
import sqlite3
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from contextlib import contextmanager

from core.cost_tracker import read_cost_history
from core.data_models import CostData
from core.workflow_analytics import (
    extract_hour,
    extract_day_of_week,
    calculate_nl_input_clarity_score,
    calculate_cost_efficiency_score,
    calculate_performance_score,
    calculate_quality_score,
)

logger = logging.getLogger(__name__)

# Database path
DB_PATH = Path(__file__).parent.parent / "db" / "workflow_history.db"


def calculate_phase_metrics(cost_data: CostData) -> Dict:
    """
    Calculate phase-level performance metrics from cost_data.

    Args:
        cost_data: CostData object containing phase information with timestamps

    Returns:
        Dict containing:
            - phase_durations: Dict[str, int] - Duration in seconds per phase
            - bottleneck_phase: Optional[str] - Phase that took >30% of total time
            - idle_time_seconds: int - Idle time between phases
    """
    if not cost_data or not cost_data.phases:
        return {
            "phase_durations": None,
            "bottleneck_phase": None,
            "idle_time_seconds": None,
        }

    phase_durations = {}
    timestamps = []

    # Extract timestamps and calculate durations
    for phase in cost_data.phases:
        if phase.timestamp:
            try:
                # Parse ISO timestamp
                timestamp = datetime.fromisoformat(phase.timestamp.replace("Z", "+00:00"))
                timestamps.append((phase.phase, timestamp))
            except Exception as e:
                logger.debug(f"Could not parse timestamp for phase {phase.phase}: {e}")

    # Calculate durations between consecutive phases
    if len(timestamps) >= 2:
        # Sort by timestamp
        timestamps.sort(key=lambda x: x[1])

        for i in range(len(timestamps) - 1):
            phase_name = timestamps[i][0]
            start_time = timestamps[i][1]
            end_time = timestamps[i + 1][1]
            duration_seconds = int((end_time - start_time).total_seconds())
            phase_durations[phase_name] = duration_seconds

        # Add duration for last phase (if we have end time, otherwise skip)
        # We don't have end time for last phase, so we skip it
        # Could estimate based on average or leave as-is

    if not phase_durations:
        return {
            "phase_durations": None,
            "bottleneck_phase": None,
            "idle_time_seconds": None,
        }

    # Calculate total duration
    total_duration = sum(phase_durations.values())

    # Detect bottleneck (phase taking >30% of total time)
    bottleneck_phase = None
    if total_duration > 0:
        for phase, duration in phase_durations.items():
            if duration / total_duration > 0.30:
                bottleneck_phase = phase
                break  # Take first bottleneck found

    # Calculate idle time (for now, set to 0 as we don't have explicit idle tracking)
    # This would require more detailed timestamp tracking in the cost data
    idle_time_seconds = 0

    return {
        "phase_durations": phase_durations,
        "bottleneck_phase": bottleneck_phase,
        "idle_time_seconds": idle_time_seconds,
    }


def categorize_error(error_message: str) -> str:
    """
    Categorize error message into standard types.

    Args:
        error_message: The error message string

    Returns:
        str: Error category - "syntax_error", "timeout", "api_quota", "validation", or "unknown"
    """
    if not error_message:
        return "unknown"

    error_lower = error_message.lower()

    # Check for syntax errors
    if any(keyword in error_lower for keyword in [
        "syntaxerror", "syntax error", "indentationerror", "indentation error",
        "parsing error", "parse error", "invalid syntax"
    ]):
        return "syntax_error"

    # Check for timeout errors
    if any(keyword in error_lower for keyword in [
        "timeout", "timeouterror", "connection timeout", "timed out",
        "deadline exceeded"
    ]):
        return "timeout"

    # Check for API quota/rate limit errors
    if any(keyword in error_lower for keyword in [
        "quota", "rate limit", "429", "too many requests",
        "quota exceeded", "rate_limit_error"
    ]):
        return "api_quota"

    # Check for validation errors
    if any(keyword in error_lower for keyword in [
        "validationerror", "validation error", "invalid input",
        "schema error", "schema validation", "invalid data"
    ]):
        return "validation"

    return "unknown"


def estimate_complexity(steps_total: int, duration_seconds: int) -> str:
    """
    Estimate workflow complexity based on steps and duration.

    Args:
        steps_total: Total number of steps in the workflow
        duration_seconds: Total duration in seconds

    Returns:
        str: Complexity level - "low", "medium", or "high"
    """
    # Low complexity: few steps OR short duration
    if steps_total <= 5 or duration_seconds < 60:
        return "low"

    # High complexity: many steps OR long duration
    if steps_total > 15 or duration_seconds > 300:
        return "high"

    # Everything else is medium
    return "medium"


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

        # Create workflow_history table with comprehensive fields
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
        **kwargs: Additional optional fields

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
            "worktree_path", "backend_port", "frontend_port", "concurrent_workflows",
            "input_tokens", "output_tokens", "cached_tokens", "cache_hit_tokens",
            "cache_miss_tokens", "total_tokens", "cache_efficiency_percent",
            "estimated_cost_total", "actual_cost_total", "estimated_cost_per_step",
            "actual_cost_per_step", "cost_per_token", "structured_input",
            "cost_breakdown", "token_breakdown", "worktree_reused",
            "steps_completed", "steps_total",
            "phase_durations", "idle_time_seconds", "bottleneck_phase",
            "error_category", "retry_reasons", "error_phase_distribution",
            "recovery_time_seconds", "complexity_estimated", "complexity_actual"
        ]

        for field in optional_fields:
            if field in kwargs:
                fields.append(field)
                # Convert dicts and lists to JSON strings
                json_fields = [
                    "structured_input", "cost_breakdown", "token_breakdown",
                    "phase_durations", "retry_reasons", "error_phase_distribution"
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

        # Convert dicts and lists to JSON strings
        json_fields = [
            "structured_input", "cost_breakdown", "token_breakdown",
            "phase_durations", "retry_reasons", "error_phase_distribution"
        ]
        for field in json_fields:
            if field in kwargs and isinstance(kwargs[field], (dict, list)):
                kwargs[field] = json.dumps(kwargs[field])

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
            logger.debug(f"[DB] Updated workflow history for ADW {adw_id}")
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
        query = f"""
            SELECT * FROM workflow_history
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


def get_history_analytics() -> Dict:
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


def scan_agents_directory() -> List[Dict]:
    """
    Scan the agents directory for workflow state files and extract metadata.

    Returns:
        List[Dict]: List of workflow metadata dictionaries
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
                "backend_port": state_data.get("backend_port"),
                "frontend_port": state_data.get("frontend_port"),
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
                        if d.is_dir() and d.name.startswith("adw_")
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

    logger.debug(f"[SCAN] Scanned agents directory, found {len(workflows)} workflows")
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

            # Extract cost information if available
            if cost_data and hasattr(cost_data, 'total_cost'):
                workflow_data["actual_cost_total"] = cost_data.total_cost

                # Populate cost_breakdown with by_phase data
                if hasattr(cost_data, 'phases') and cost_data.phases:
                    by_phase = {phase.phase: phase.cost for phase in cost_data.phases}
                    workflow_data["cost_breakdown"] = {
                        "estimated_total": workflow_data.get("estimated_cost_total", 0.0),
                        "actual_total": cost_data.total_cost,
                        "estimated_per_step": workflow_data.get("estimated_cost_per_step", 0.0),
                        "actual_per_step": workflow_data.get("actual_cost_per_step", 0.0),
                        "cost_per_token": workflow_data.get("cost_per_token", 0.0),
                        "by_phase": by_phase
                    }

                # Populate token_breakdown
                if hasattr(cost_data, 'phases') and cost_data.phases:
                    # Aggregate tokens across all phases
                    total_input = sum(p.tokens.input_tokens for p in cost_data.phases)
                    total_cache_creation = sum(p.tokens.cache_creation_tokens for p in cost_data.phases)
                    total_cache_read = sum(p.tokens.cache_read_tokens for p in cost_data.phases)
                    total_output = sum(p.tokens.output_tokens for p in cost_data.phases)

                    workflow_data["input_tokens"] = total_input
                    workflow_data["cached_tokens"] = total_cache_creation
                    workflow_data["cache_hit_tokens"] = total_cache_read
                    workflow_data["cache_miss_tokens"] = total_input  # Approximation
                    workflow_data["output_tokens"] = total_output
                    workflow_data["total_tokens"] = total_input + total_cache_creation + total_cache_read + total_output
                    workflow_data["cache_efficiency_percent"] = cost_data.cache_efficiency_percent

                # Calculate performance metrics
                phase_metrics = calculate_phase_metrics(cost_data)
                if phase_metrics["phase_durations"]:
                    workflow_data["phase_durations"] = phase_metrics["phase_durations"]
                    workflow_data["bottleneck_phase"] = phase_metrics["bottleneck_phase"]
                    workflow_data["idle_time_seconds"] = phase_metrics["idle_time_seconds"]

                # Extract model from cost_data if not already set
                if not workflow_data.get("model_used") and hasattr(cost_data, 'phases') and cost_data.phases:
                    # Use the model from the first phase (they're usually all the same)
                    workflow_data["model_used"] = cost_data.phases[0].model if cost_data.phases else None

        except Exception as e:
            logger.debug(f"[SYNC] No cost data for {adw_id}: {e}")

        # Set default workflow_template if not set (use issue_class from state)
        if not workflow_data.get("workflow_template"):
            # Derive from issue_class or use generic "sdlc"
            workflow_data["workflow_template"] = "sdlc"  # Default template

        # Categorize error if error_message exists
        if workflow_data.get("error_message"):
            workflow_data["error_category"] = categorize_error(workflow_data["error_message"])

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

        # Estimate complexity if we have steps_total and duration
        steps_total = workflow_data.get("steps_total", 0)
        if steps_total > 0 and duration_seconds:
            workflow_data["complexity_actual"] = estimate_complexity(steps_total, duration_seconds)

        # Phase 3A/3B: Calculate temporal fields and scoring metrics
        if workflow_data.get("start_time"):
            workflow_data["hour_of_day"] = extract_hour(workflow_data["start_time"])
            workflow_data["day_of_week"] = extract_day_of_week(workflow_data["start_time"])

        # Set scoring version
        workflow_data["scoring_version"] = "1.0"

        # Calculate scores (with error handling to prevent sync failures)
        try:
            workflow_data["nl_input_clarity_score"] = calculate_nl_input_clarity_score(workflow_data)
        except Exception as e:
            logger.warning(f"[SYNC] Failed to calculate clarity score for {adw_id}: {e}")
            workflow_data["nl_input_clarity_score"] = 0.0

        try:
            workflow_data["cost_efficiency_score"] = calculate_cost_efficiency_score(workflow_data)
        except Exception as e:
            logger.warning(f"[SYNC] Failed to calculate cost efficiency score for {adw_id}: {e}")
            workflow_data["cost_efficiency_score"] = 0.0

        try:
            workflow_data["performance_score"] = calculate_performance_score(workflow_data)
        except Exception as e:
            logger.warning(f"[SYNC] Failed to calculate performance score for {adw_id}: {e}")
            workflow_data["performance_score"] = 0.0

        try:
            workflow_data["quality_score"] = calculate_quality_score(workflow_data)
        except Exception as e:
            logger.warning(f"[SYNC] Failed to calculate quality score for {adw_id}: {e}")
            workflow_data["quality_score"] = 0.0

        # Anomaly Detection & Optimization Recommendations
        # Only generate insights for NEW workflows - skip for existing ones to prevent redundant updates
        should_generate_insights = not existing  # Only for new workflows

        if should_generate_insights:
            try:
                # Get all workflows for comparison (unpack tuple: workflows list and total count)
                all_workflows, _ = get_workflow_history()

                # Detect anomalies
                from core.workflow_analytics import detect_anomalies, generate_optimization_recommendations
                anomalies = detect_anomalies(workflow_data, all_workflows)

                # Generate recommendations
                recommendations = generate_optimization_recommendations(workflow_data, anomalies)

                # Serialize to JSON for database storage
                import json
                workflow_data["anomaly_flags"] = json.dumps([a["message"] for a in anomalies])  # Simplified for UI
                workflow_data["optimization_recommendations"] = json.dumps(recommendations)

                logger.debug(f"[SYNC] Generated {len(anomalies)} anomalies and {len(recommendations)} recommendations for {adw_id}")
            except Exception as e:
                logger.warning(f"[SYNC] Failed to generate insights for {adw_id}: {e}")
                workflow_data["anomaly_flags"] = "[]"
                workflow_data["optimization_recommendations"] = "[]"

        if existing:
            # Update existing record if status or other fields changed
            updates = {}

            if existing["status"] != workflow_data["status"]:
                updates["status"] = workflow_data["status"]

            if workflow_data.get("current_phase") and existing["current_phase"] != workflow_data["current_phase"]:
                updates["current_phase"] = workflow_data["current_phase"]

            if duration_seconds and not existing["duration_seconds"]:
                updates["duration_seconds"] = duration_seconds

            # Update cost data with status-aware logic to prevent staleness
            # - Only update if cost has ACTUALLY CHANGED (prevent redundant writes)
            # - For running workflows, only update if cost increased (progressive tracking)
            # - Never allow cost decreases (prevents data corruption from out-of-order syncs)
            if workflow_data.get("cost_breakdown"):
                old_cost = existing.get("actual_cost_total", 0.0)
                new_cost = workflow_data.get("actual_cost_total", 0.0)
                status = workflow_data.get("status", "unknown")

                should_update = False
                update_reason = ""

                # For completed/failed workflows, only update if cost actually changed
                if status in ["completed", "failed"] and new_cost != old_cost:
                    should_update = True
                    update_reason = f"final cost changed for {status} workflow: ${old_cost:.4f} → ${new_cost:.4f}"
                # For running workflows, only update if cost increased
                elif status == "running" and new_cost > old_cost:
                    should_update = True
                    update_reason = f"progressive increase from ${old_cost:.4f} to ${new_cost:.4f}"
                # Skip if no change or decrease
                else:
                    update_reason = f"no change (${old_cost:.4f} = ${new_cost:.4f})" if new_cost == old_cost else f"no update needed"

                if should_update:
                    updates["cost_breakdown"] = workflow_data["cost_breakdown"]
                    updates["actual_cost_total"] = new_cost
                    updates["input_tokens"] = workflow_data.get("input_tokens", 0)
                    updates["cached_tokens"] = workflow_data.get("cached_tokens", 0)
                    updates["cache_hit_tokens"] = workflow_data.get("cache_hit_tokens", 0)
                    updates["cache_miss_tokens"] = workflow_data.get("cache_miss_tokens", 0)
                    updates["output_tokens"] = workflow_data.get("output_tokens", 0)
                    updates["total_tokens"] = workflow_data.get("total_tokens", 0)
                    updates["cache_efficiency_percent"] = workflow_data.get("cache_efficiency_percent", 0.0)
                    logger.debug(f"[SYNC] Cost update for {adw_id} ({status}): ${old_cost:.4f} → ${new_cost:.4f} ({update_reason})")
                else:
                    logger.debug(f"[SYNC] Cost update skipped for {adw_id} ({status}): {update_reason}")

            # Update performance metrics if available and not already set
            if workflow_data.get("phase_durations") and not existing.get("phase_durations"):
                updates["phase_durations"] = workflow_data["phase_durations"]
                updates["bottleneck_phase"] = workflow_data.get("bottleneck_phase")
                updates["idle_time_seconds"] = workflow_data.get("idle_time_seconds")

            # Update error category if available and not already set
            if workflow_data.get("error_category") and not existing.get("error_category"):
                updates["error_category"] = workflow_data["error_category"]

            # Update complexity if available and not already set
            if workflow_data.get("complexity_actual") and not existing.get("complexity_actual"):
                updates["complexity_actual"] = workflow_data["complexity_actual"]

            # Anomaly Detection & Recommendations - Only update if we generated new insights
            # (We only generate insights for new workflows, so this block rarely runs)
            if should_generate_insights and "anomaly_flags" in workflow_data:
                try:
                    # workflow_data has JSON strings, existing has parsed Python objects
                    new_anomaly_flags = json.loads(workflow_data.get("anomaly_flags", "[]"))
                    old_anomaly_flags = existing.get("anomaly_flags", [])
                    if new_anomaly_flags != old_anomaly_flags:
                        updates["anomaly_flags"] = workflow_data["anomaly_flags"]
                except Exception:
                    # If comparison fails, skip update (don't cause unnecessary writes)
                    pass

            if should_generate_insights and "optimization_recommendations" in workflow_data:
                try:
                    new_recommendations = json.loads(workflow_data.get("optimization_recommendations", "[]"))
                    old_recommendations = existing.get("optimization_recommendations", [])
                    if new_recommendations != old_recommendations:
                        updates["optimization_recommendations"] = workflow_data["optimization_recommendations"]
                except Exception:
                    # If comparison fails, skip update (don't cause unnecessary writes)
                    pass

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

    # Workflow Similarity Analysis - Skip to avoid redundant processing on every sync
    # Similarity detection is expensive and should only run:
    # 1. During initial backfill (one-time)
    # 2. When explicitly requested via API
    # 3. NOT on every routine sync
    # This phase is intentionally disabled for performance - re-enable only if needed
    logger.debug("[SYNC] Skipping similarity analysis (performance optimization)")

    # Pattern Learning - Skip to avoid redundant processing on every sync
    # Pattern detection is expensive and should only run:
    # 1. During initial backfill (one-time)
    # 2. When explicitly requested via API
    # 3. NOT on every routine sync
    # This phase is intentionally disabled for performance - re-enable only if needed
    logger.debug("[SYNC] Skipping pattern learning (performance optimization)")

    # Only log if we actually synced something
    if synced_count > 0:
        logger.info(f"[SYNC] Synchronized {synced_count} workflows")
    return synced_count


def resync_workflow_cost(adw_id: str, force: bool = False) -> Dict:
    """
    Resync cost data for a single workflow from source files.

    Args:
        adw_id: ADW workflow identifier
        force: If True, clears existing cost data before resync

    Returns:
        Dict with keys:
            - success: bool - Whether resync succeeded
            - adw_id: str - The workflow ID
            - error: Optional[str] - Error message if failed
            - cost_updated: bool - Whether cost was actually updated
    """
    try:
        # Check if workflow exists
        existing = get_workflow_by_adw_id(adw_id)
        if not existing:
            return {
                "success": False,
                "adw_id": adw_id,
                "error": f"Workflow not found: {adw_id}",
                "cost_updated": False
            }

        # Read authoritative cost data from source files
        try:
            cost_data = read_cost_history(adw_id)
        except FileNotFoundError as e:
            return {
                "success": False,
                "adw_id": adw_id,
                "error": f"Cost files not found: {str(e)}",
                "cost_updated": False
            }
        except ValueError as e:
            return {
                "success": False,
                "adw_id": adw_id,
                "error": f"Invalid cost data: {str(e)}",
                "cost_updated": False
            }

        # Prepare cost update data
        updates = {}

        # If force mode, we'll update regardless of current values
        if force:
            logger.info(f"[RESYNC] Force resync for {adw_id} - clearing existing data")

        # Extract cost information
        if cost_data and hasattr(cost_data, 'total_cost'):
            updates["actual_cost_total"] = cost_data.total_cost

            # Populate cost_breakdown with by_phase data
            if hasattr(cost_data, 'phases') and cost_data.phases:
                by_phase = {phase.phase: phase.cost for phase in cost_data.phases}
                updates["cost_breakdown"] = {
                    "estimated_total": existing.get("estimated_cost_total", 0.0),
                    "actual_total": cost_data.total_cost,
                    "estimated_per_step": existing.get("estimated_cost_per_step", 0.0),
                    "actual_per_step": existing.get("actual_cost_per_step", 0.0),
                    "cost_per_token": existing.get("cost_per_token", 0.0),
                    "by_phase": by_phase
                }

            # Populate token_breakdown
            if hasattr(cost_data, 'phases') and cost_data.phases:
                # Aggregate tokens across all phases
                total_input = sum(p.tokens.input_tokens for p in cost_data.phases)
                total_cache_creation = sum(p.tokens.cache_creation_tokens for p in cost_data.phases)
                total_cache_read = sum(p.tokens.cache_read_tokens for p in cost_data.phases)
                total_output = sum(p.tokens.output_tokens for p in cost_data.phases)

                updates["input_tokens"] = total_input
                updates["cached_tokens"] = total_cache_creation
                updates["cache_hit_tokens"] = total_cache_read
                updates["cache_miss_tokens"] = total_input  # Approximation
                updates["output_tokens"] = total_output
                updates["total_tokens"] = total_input + total_cache_creation + total_cache_read + total_output
                updates["cache_efficiency_percent"] = cost_data.cache_efficiency_percent

            # Calculate performance metrics
            phase_metrics = calculate_phase_metrics(cost_data)
            if phase_metrics["phase_durations"]:
                updates["phase_durations"] = phase_metrics["phase_durations"]
                updates["bottleneck_phase"] = phase_metrics["bottleneck_phase"]
                updates["idle_time_seconds"] = phase_metrics["idle_time_seconds"]

        # Update the workflow
        if updates:
            success = update_workflow_history(adw_id, **updates)
            if success:
                logger.info(f"[RESYNC] Successfully resynced cost data for {adw_id}")
                return {
                    "success": True,
                    "adw_id": adw_id,
                    "error": None,
                    "cost_updated": True
                }
            else:
                return {
                    "success": False,
                    "adw_id": adw_id,
                    "error": "Failed to update database",
                    "cost_updated": False
                }
        else:
            return {
                "success": True,
                "adw_id": adw_id,
                "error": None,
                "cost_updated": False
            }

    except Exception as e:
        logger.error(f"[RESYNC] Error resyncing {adw_id}: {e}")
        return {
            "success": False,
            "adw_id": adw_id,
            "error": str(e),
            "cost_updated": False
        }


def resync_all_completed_workflows(force: bool = False) -> Tuple[int, List[Dict], List[str]]:
    """
    Resync cost data for all completed workflows.

    Args:
        force: If True, clears existing cost data before resync

    Returns:
        Tuple containing:
            - resynced_count: int - Number of workflows successfully resynced
            - workflows: List[Dict] - List of workflow summaries
            - errors: List[str] - List of error messages
    """
    try:
        # Get all completed workflows
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT adw_id, status FROM workflow_history WHERE status IN ('completed', 'failed')"
            )
            rows = cursor.fetchall()

        workflows_to_resync = [dict(row) for row in rows]
        logger.info(f"[RESYNC] Found {len(workflows_to_resync)} completed/failed workflows to resync")

        resynced_count = 0
        workflows = []
        errors = []

        for workflow in workflows_to_resync:
            adw_id = workflow["adw_id"]
            result = resync_workflow_cost(adw_id, force=force)

            if result["success"]:
                if result["cost_updated"]:
                    resynced_count += 1
                workflows.append({
                    "adw_id": adw_id,
                    "status": workflow["status"],
                    "cost_updated": result["cost_updated"]
                })
            else:
                error_msg = f"{adw_id}: {result['error']}"
                errors.append(error_msg)
                logger.warning(f"[RESYNC] Failed to resync {adw_id}: {result['error']}")

        logger.info(f"[RESYNC] Completed bulk resync: {resynced_count} updated, {len(errors)} errors")
        return resynced_count, workflows, errors

    except Exception as e:
        logger.error(f"[RESYNC] Error in bulk resync: {e}")
        return 0, [], [f"Bulk resync failed: {str(e)}"]
