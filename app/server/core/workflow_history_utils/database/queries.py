"""
Database query operations (SELECT).

This module provides all read operations for the workflow history system.
"""

import json
import logging
from datetime import datetime

from .schema import _get_adapter

logger = logging.getLogger(__name__)


def get_workflow_by_adw_id(adw_id: str) -> dict | None:
    """
    Get a single workflow history record by ADW ID.

    Args:
        adw_id: The ADW workflow identifier

    Returns:
        Dict: Workflow history record as a dictionary, or None if not found
    """
    adapter = _get_adapter()
    with adapter.get_connection() as conn:
        cursor = conn.cursor()
        ph = adapter.placeholder()
        cursor.execute(f"SELECT * FROM workflow_history WHERE adw_id = {ph}", (adw_id,))
        row = cursor.fetchone()

        if row:
            result = dict(row)

            # No field name mapping needed - database and code use same names

            # Parse JSON fields
            json_fields = [
                "structured_input", "cost_breakdown", "token_breakdown",
                "phase_durations", "retry_reasons", "error_phase_distribution",
                "anomaly_flags", "optimization_recommendations"  # Phase 3D
            ]
            for field in json_fields:
                if result.get(field):
                    try:
                        # Handle both string (SQLite/PostgreSQL TEXT) and already-parsed (PostgreSQL JSON/JSONB)
                        if isinstance(result[field], str):
                            result[field] = json.loads(result[field])
                        # else: already a dict/list from PostgreSQL JSON column, keep as-is
                    except json.JSONDecodeError:
                        logger.warning(f"[DB] Failed to parse JSON for {field} in ADW {adw_id}")
                        result[field] = None
                    except TypeError as e:
                        logger.warning(f"[DB] TypeError parsing JSON for {field} in ADW {adw_id}: {e} (type: {type(result[field])})")
                        result[field] = None
                else:
                    # Default to empty arrays for Phase 3D fields
                    if field in ["anomaly_flags", "optimization_recommendations"]:
                        result[field] = []
            return result
        return None


def _build_where_clauses(
    ph: str,
    status: str | None,
    model: str | None,
    template: str | None,
    start_date: str | None,
    end_date: str | None,
    search: str | None
) -> tuple[list[str], list]:
    """Build WHERE clauses and parameters for workflow history query."""
    where_clauses = []
    params = []

    if status:
        where_clauses.append(f"status = {ph}")
        params.append(status)

    if model:
        where_clauses.append(f"model_used = {ph}")
        params.append(model)

    if template:
        where_clauses.append(f"workflow_template = {ph}")
        params.append(template)

    if start_date:
        where_clauses.append(f"created_at >= {ph}")
        params.append(start_date)

    if end_date:
        where_clauses.append(f"created_at <= {ph}")
        params.append(end_date)

    if search:
        where_clauses.append(
            f"(adw_id LIKE {ph} OR nl_input LIKE {ph} OR github_url LIKE {ph})"
        )
        search_param = f"%{search}%"
        params.extend([search_param, search_param, search_param])

    return where_clauses, params


def _process_workflow_row(row: dict) -> dict:
    """Process a single workflow row from database."""
    result = dict(row)

    # Parse JSON fields
    json_fields = [
        "structured_input", "cost_breakdown", "token_breakdown",
        "phase_durations", "retry_reasons", "error_phase_distribution",
        "anomaly_flags", "optimization_recommendations"  # Phase 3D
    ]
    for field in json_fields:
        if result.get(field):
            # Check if already parsed (PostgreSQL JSONB returns dict/list directly)
            if isinstance(result[field], (dict, list)):
                # Already parsed, no action needed
                pass
            else:
                # String, need to parse
                try:
                    result[field] = json.loads(result[field])
                except json.JSONDecodeError:
                    logger.warning(f"[DB] Failed to parse JSON for {field}")
                    result[field] = None
        elif field in ["anomaly_flags", "optimization_recommendations"]:
            # Default to empty arrays for Phase 3D fields
            result[field] = []

    # Convert datetime objects to ISO format strings (PostgreSQL returns datetime objects)
    datetime_fields = [
        "created_at", "updated_at", "start_time", "end_time"
    ]
    for field in datetime_fields:
        if result.get(field) and isinstance(result[field], datetime):
            result[field] = result[field].isoformat()

    # Convert None to defaults for score and temporal fields (legacy data compatibility)
    default_fields = {
        "nl_input_clarity_score": 0.0,
        "cost_efficiency_score": 0.0,
        "performance_score": 0.0,
        "quality_score": 0.0,
        "estimated_cost_total": 0.0,
        "hour_of_day": -1,
        "day_of_week": -1,
    }
    for field, default_value in default_fields.items():
        if result.get(field) is None:
            result[field] = default_value

    return result


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
    adapter = _get_adapter()
    with adapter.get_connection() as conn:
        cursor = conn.cursor()
        ph = adapter.placeholder()

        # Build WHERE clauses
        where_clauses, params = _build_where_clauses(
            ph, status, model, template, start_date, end_date, search
        )
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
            SELECT *
            FROM workflow_history
            {where_sql}
            ORDER BY {sort_by} {sort_order}
            LIMIT {ph} OFFSET {ph}
        """
        cursor.execute(query, params + [limit, offset])
        rows = cursor.fetchall()

        results = [_process_workflow_row(row) for row in rows]

        logger.debug(
            f"[DB] Retrieved {len(results)} workflows (total: {total_count}, "
            f"offset: {offset}, limit: {limit})"
        )

        return results, total_count
