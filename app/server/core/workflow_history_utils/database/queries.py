"""
Database query operations (SELECT).

This module provides all read operations for the workflow history system.
"""

import json
import logging

from utils.db_connection import get_connection as get_db_connection

from .schema import DB_PATH

logger = logging.getLogger(__name__)


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

            # No field name mapping needed - database and code use same names

            # Parse JSON fields
            json_fields = [
                "structured_input",
                "cost_breakdown",
                "token_breakdown",
                "phase_durations",
                "retry_reasons",
                "error_phase_distribution",
                "anomaly_flags",
                "optimization_recommendations",  # Phase 3D
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
    sort_order: str = "DESC",
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
            where_clauses.append("(adw_id LIKE ? OR nl_input LIKE ? OR github_url LIKE ?)")
            search_param = f"%{search}%"
            params.extend([search_param, search_param, search_param])

        where_sql = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""

        # Get total count (before pagination)
        count_query = f"SELECT COUNT(*) as total FROM workflow_history {where_sql}"
        cursor.execute(count_query, params)
        total_count = cursor.fetchone()["total"]

        # Validate sort_by field to prevent SQL injection
        valid_sort_fields = [
            "created_at",
            "updated_at",
            "start_time",
            "end_time",
            "duration_seconds",
            "status",
            "adw_id",
            "issue_number",
            "actual_cost_total",
            "total_tokens",
            "cache_efficiency_percent",
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
            LIMIT ? OFFSET ?
        """
        cursor.execute(query, params + [limit, offset])
        rows = cursor.fetchall()

        results = []
        for row in rows:
            result = dict(row)

            # No field name mapping needed - database and code use same names

            # Parse JSON fields
            json_fields = [
                "structured_input",
                "cost_breakdown",
                "token_breakdown",
                "phase_durations",
                "retry_reasons",
                "error_phase_distribution",
                "anomaly_flags",
                "optimization_recommendations",  # Phase 3D
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

            results.append(result)

        logger.debug(
            f"[DB] Retrieved {len(results)} workflows (total: {total_count}, "
            f"offset: {offset}, limit: {limit})"
        )

        return results, total_count


# ============================================================================
# PATTERN VALIDATION QUERIES (Phase 4)
# ============================================================================


def get_pattern_predictions(workflow_id: str) -> list[dict]:
    """
    Get all pattern predictions for a specific workflow.

    Args:
        workflow_id: Workflow ID to fetch predictions for

    Returns:
        List of prediction dictionaries with pattern information
    """
    with get_db_connection(db_path=str(DB_PATH)) as conn:
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT
                pp.id,
                pp.workflow_id,
                pp.pattern_id,
                pp.pattern_signature,
                pp.predicted_at,
                pp.predicted_confidence,
                pp.was_correct,
                pp.validated_at,
                p.pattern_type,
                p.occurrence_count,
                p.confidence_score
            FROM pattern_predictions pp
            JOIN operation_patterns p ON pp.pattern_id = p.id
            WHERE pp.workflow_id = ?
            ORDER BY pp.predicted_confidence DESC
            """,
            (workflow_id,),
        )

        rows = cursor.fetchall()
        return [dict(row) for row in rows]


def get_pattern_accuracy_history(pattern_id: int, limit: int = 50) -> list[dict]:
    """
    Get validation history for a specific pattern.

    Args:
        pattern_id: Pattern ID to fetch history for
        limit: Maximum number of records to return

    Returns:
        List of validation result dictionaries
    """
    with get_db_connection(db_path=str(DB_PATH)) as conn:
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT
                pp.id,
                pp.workflow_id,
                pp.predicted_at,
                pp.predicted_confidence,
                pp.was_correct,
                pp.validated_at,
                w.adw_id,
                w.nl_input,
                w.status
            FROM pattern_predictions pp
            JOIN workflow_history w ON pp.workflow_id = w.workflow_id
            WHERE pp.pattern_id = ? AND pp.was_correct IS NOT NULL
            ORDER BY pp.validated_at DESC
            LIMIT ?
            """,
            (pattern_id, limit),
        )

        rows = cursor.fetchall()
        return [dict(row) for row in rows]


def get_validation_summary_by_pattern_type() -> list[dict]:
    """
    Get validation metrics grouped by pattern type.

    Returns:
        List of dictionaries with validation metrics per pattern type
    """
    with get_db_connection(db_path=str(DB_PATH)) as conn:
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT
                p.pattern_type,
                COUNT(DISTINCT p.id) as pattern_count,
                COUNT(pp.id) as total_predictions,
                SUM(CASE WHEN pp.was_correct = 1 THEN 1 ELSE 0 END) as correct_predictions,
                SUM(CASE WHEN pp.was_correct = 0 THEN 1 ELSE 0 END) as incorrect_predictions,
                CAST(SUM(CASE WHEN pp.was_correct = 1 THEN 1 ELSE 0 END) AS REAL) /
                    NULLIF(COUNT(CASE WHEN pp.was_correct IS NOT NULL THEN 1 END), 0) as accuracy_rate,
                AVG(p.prediction_accuracy) as avg_pattern_accuracy,
                AVG(pp.predicted_confidence) as avg_predicted_confidence
            FROM operation_patterns p
            LEFT JOIN pattern_predictions pp ON pp.pattern_id = p.id
            GROUP BY p.pattern_type
            ORDER BY accuracy_rate DESC
            """
        )

        rows = cursor.fetchall()
        results = []
        for row in rows:
            result = dict(row)
            # Convert None to 0.0 for numeric fields
            if result["accuracy_rate"] is None:
                result["accuracy_rate"] = 0.0
            if result["avg_pattern_accuracy"] is None:
                result["avg_pattern_accuracy"] = 0.0
            if result["avg_predicted_confidence"] is None:
                result["avg_predicted_confidence"] = 0.0
            results.append(result)

        return results


def get_reliable_patterns(
    min_accuracy: float = 0.70, min_occurrences: int = 5, limit: int = 20
) -> list[dict]:
    """
    Get patterns with high prediction accuracy (reliable automation candidates).

    Args:
        min_accuracy: Minimum prediction accuracy (0.0 to 1.0)
        min_occurrences: Minimum number of occurrences
        limit: Maximum number of patterns to return

    Returns:
        List of reliable pattern dictionaries sorted by accuracy
    """
    with get_db_connection(db_path=str(DB_PATH)) as conn:
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT
                p.*,
                p.prediction_accuracy * 100 as accuracy_percent,
                (SELECT COUNT(*) FROM pattern_predictions pp
                 WHERE pp.pattern_id = p.id AND pp.was_correct = 1) as correct_predictions,
                (SELECT COUNT(*) FROM pattern_predictions pp
                 WHERE pp.pattern_id = p.id AND pp.was_correct = 0) as incorrect_predictions,
                (SELECT COUNT(*) FROM pattern_predictions pp
                 WHERE pp.pattern_id = p.id AND pp.was_correct IS NOT NULL) as total_validated
            FROM operation_patterns p
            WHERE p.prediction_accuracy >= ?
            AND p.occurrence_count >= ?
            ORDER BY p.prediction_accuracy DESC, p.occurrence_count DESC
            LIMIT ?
            """,
            (min_accuracy, min_occurrences, limit),
        )

        rows = cursor.fetchall()
        return [dict(row) for row in rows]


def get_recent_validations(limit: int = 100) -> list[dict]:
    """
    Get recently validated pattern predictions.

    Args:
        limit: Maximum number of validations to return

    Returns:
        List of recent validation dictionaries
    """
    with get_db_connection(db_path=str(DB_PATH)) as conn:
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT
                pp.id,
                pp.workflow_id,
                pp.pattern_signature,
                pp.predicted_confidence,
                pp.was_correct,
                pp.predicted_at,
                pp.validated_at,
                p.pattern_type,
                p.automation_status,
                p.prediction_accuracy,
                w.adw_id,
                w.nl_input
            FROM pattern_predictions pp
            JOIN operation_patterns p ON pp.pattern_id = p.id
            JOIN workflow_history w ON pp.workflow_id = w.workflow_id
            WHERE pp.validated_at IS NOT NULL
            ORDER BY pp.validated_at DESC
            LIMIT ?
            """,
            (limit,),
        )

        rows = cursor.fetchall()
        return [dict(row) for row in rows]
