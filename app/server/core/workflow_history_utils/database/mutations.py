"""
Database mutation operations (INSERT, UPDATE).

This module provides all write operations for the workflow history system.
"""

import json
import logging

from utils.db_connection import get_connection as get_db_connection

from .schema import DB_PATH

logger = logging.getLogger(__name__)


# Import pattern validation modules (lazy import to avoid circular dependencies)
def _get_pattern_modules():
    """Lazy import pattern modules to avoid circular dependencies."""
    try:
        from core.pattern_detector import detect_patterns_in_workflow
        from core.pattern_validator import validate_predictions

        return detect_patterns_in_workflow, validate_predictions
    except ImportError as e:
        logger.warning(f"[DB] Pattern validation modules not available: {e}")
        return None, None


def insert_workflow_history(
    adw_id: str,
    issue_number: int | None = None,
    nl_input: str | None = None,
    github_url: str | None = None,
    workflow_template: str | None = None,
    model_used: str | None = None,
    status: str = "pending",
    **kwargs,
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
        ValueError: If status is None or invalid
    """
    # Validate status field to prevent NOT NULL constraint violations
    if status is None or status == "":
        logger.warning(f"[DB] Invalid status '{status}' for {adw_id}, defaulting to 'pending'")
        status = "pending"

    # Ensure status is one of the valid values
    valid_statuses = ["pending", "running", "completed", "failed"]
    if status not in valid_statuses:
        logger.warning(f"[DB] Invalid status '{status}' for {adw_id}, defaulting to 'pending'")
        status = "pending"

    with get_db_connection(db_path=str(DB_PATH)) as conn:
        cursor = conn.cursor()

        # Build dynamic query based on provided kwargs
        fields = [
            "adw_id",
            "issue_number",
            "nl_input",
            "github_url",
            "gh_issue_state",
            "workflow_template",
            "model_used",
            "status",
        ]
        values = [
            adw_id,
            issue_number,
            nl_input,
            github_url,
            kwargs.get("gh_issue_state"),
            workflow_template,
            model_used,
            status,
        ]

        # Add optional fields from kwargs
        optional_fields = [
            "start_time",
            "end_time",
            "duration_seconds",
            "error_message",
            "phase_count",
            "current_phase",
            "success_rate",
            "retry_count",
            "worktree_path",
            "backend_port",
            "frontend_port",
            "concurrent_workflows",
            "input_tokens",
            "output_tokens",
            "cached_tokens",
            "cache_hit_tokens",
            "cache_miss_tokens",
            "total_tokens",
            "cache_efficiency_percent",
            "estimated_cost_total",
            "actual_cost_total",
            "estimated_cost_per_step",
            "actual_cost_per_step",
            "cost_per_token",
            "structured_input",
            "cost_breakdown",
            "token_breakdown",
            "worktree_reused",
            "steps_completed",
            "steps_total",
            "phase_durations",
            "idle_time_seconds",
            "bottleneck_phase",
            "error_category",
            "retry_reasons",
            "error_phase_distribution",
            "recovery_time_seconds",
            "complexity_estimated",
            "complexity_actual",
            # Phase 3A/3B: Analytics scoring fields
            "hour_of_day",
            "day_of_week",
            "scoring_version",
            "nl_input_clarity_score",
            "cost_efficiency_score",
            "performance_score",
            "quality_score",
            # Phase 3D: Insights & recommendations
            "anomaly_flags",
            "optimization_recommendations",
            # Timestamp override (normally auto-set by DB)
            "created_at",
        ]

        # Get existing columns from database to validate fields before inserting
        cursor.execute("PRAGMA table_info(workflow_history)")
        existing_columns = {row["name"] for row in cursor.fetchall()}

        # Map field names from code schema to database schema
        # Note: Currently no mapping needed - code and DB use same names
        field_name_mapping = {}

        for field in optional_fields:
            if field in kwargs:
                # Map field name if needed
                db_field = field_name_mapping.get(field, field)

                # Only add field if column exists in database
                if db_field in existing_columns:
                    fields.append(db_field)
                    # Convert dicts and lists to JSON strings
                    json_fields = [
                        "structured_input",
                        "cost_breakdown",
                        "token_breakdown",
                        "phase_durations",
                        "retry_reasons",
                        "error_phase_distribution",
                        "anomaly_flags",
                        "optimization_recommendations",
                    ]
                    if field in json_fields:
                        if isinstance(kwargs[field], dict | list):
                            values.append(json.dumps(kwargs[field]))
                        else:
                            values.append(kwargs[field])
                    else:
                        values.append(kwargs[field])
                else:
                    logger.debug(
                        f"[DB] Skipping field '{field}' (maps to '{db_field}') - column doesn't exist in database"
                    )

        placeholders = ", ".join(["?" for _ in values])
        fields_str = ", ".join(fields)

        query = f"INSERT INTO workflow_history ({fields_str}) VALUES ({placeholders})"

        cursor.execute(query, values)
        row_id = cursor.lastrowid

        logger.info(f"[DB] Inserted workflow history for ADW {adw_id} (ID: {row_id})")
        return row_id


def update_workflow_history_by_issue(issue_number: int, **kwargs) -> int:
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


def update_workflow_history(adw_id: str, **kwargs) -> bool:
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

        # Get existing columns from database to validate fields before updating
        cursor.execute("PRAGMA table_info(workflow_history)")
        existing_columns = {row["name"] for row in cursor.fetchall()}

        # Convert dicts and lists to JSON strings
        json_fields = [
            "structured_input",
            "cost_breakdown",
            "token_breakdown",
            "phase_durations",
            "retry_reasons",
            "error_phase_distribution",
            "anomaly_flags",
            "optimization_recommendations",
        ]
        for field in json_fields:
            if field in kwargs and isinstance(kwargs[field], dict | list):
                kwargs[field] = json.dumps(kwargs[field])

        # Map field names from code schema to database schema
        # Note: Currently no mapping needed - code and DB use same names
        field_name_mapping = {}

        # Build update query with mapped field names, only including fields that exist in DB
        mapped_kwargs = {}
        for field, value in kwargs.items():
            db_field = field_name_mapping.get(field, field)
            # Only add field if column exists in database
            if db_field in existing_columns:
                mapped_kwargs[db_field] = value
            else:
                logger.debug(
                    f"[DB] Skipping field '{field}' (maps to '{db_field}') - column doesn't exist in database"
                )

        if not mapped_kwargs:
            logger.warning(f"[DB] No valid fields to update for ADW {adw_id}")
            return False

        set_clauses = [f"{field} = ?" for field in mapped_kwargs]
        set_clauses.append("updated_at = CURRENT_TIMESTAMP")

        query = f"""
            UPDATE workflow_history
            SET {", ".join(set_clauses)}
            WHERE adw_id = ?
        """

        values = list(mapped_kwargs.values()) + [adw_id]
        cursor.execute(query, values)

        update_succeeded = cursor.rowcount > 0

        if update_succeeded:
            logger.debug(f"[DB] Updated workflow history for ADW {adw_id}")

            # Check if status changed to 'completed' - trigger pattern validation
            if "status" in kwargs and kwargs["status"] == "completed":
                _trigger_pattern_validation(adw_id, conn)

            return True
        else:
            logger.warning(f"[DB] No workflow found with ADW ID {adw_id}")
            return False


def _trigger_pattern_validation(adw_id: str, db_connection) -> None:
    """
    Trigger pattern prediction validation after workflow completion.

    This function is called automatically when a workflow status changes to 'completed'.
    It validates any pattern predictions made for this workflow against the actual
    patterns detected from the completed workflow.

    Args:
        adw_id: ADW ID of the completed workflow
        db_connection: Database connection (reuse existing connection)
    """
    try:
        # Get pattern modules
        detect_patterns_fn, validate_predictions_fn = _get_pattern_modules()

        if not detect_patterns_fn or not validate_predictions_fn:
            logger.debug(f"[DB] Pattern validation skipped for {adw_id} (modules not available)")
            return

        # Get workflow data
        cursor = db_connection.cursor()
        cursor.execute("SELECT * FROM workflow_history WHERE adw_id = ?", (adw_id,))
        row = cursor.fetchone()

        if not row:
            logger.warning(f"[DB] Workflow {adw_id} not found for validation")
            return

        workflow = dict(row)
        workflow_id = workflow.get("workflow_id")

        if not workflow_id:
            logger.debug(f"[DB] No workflow_id for {adw_id}, skipping validation")
            return

        # Check if there are predictions to validate
        cursor.execute(
            "SELECT COUNT(*) FROM pattern_predictions WHERE workflow_id = ?", (workflow_id,)
        )
        prediction_count = cursor.fetchone()[0]

        if prediction_count == 0:
            logger.debug(f"[DB] No predictions to validate for workflow {workflow_id}")
            return

        # Detect actual patterns from completed workflow
        actual_patterns = detect_patterns_fn(workflow)

        if not actual_patterns:
            logger.debug(f"[DB] No patterns detected in completed workflow {workflow_id}")
            # Still validate to mark predictions as incorrect (false positives)

        # Validate predictions
        validation_result = validate_predictions_fn(
            workflow_id=workflow_id, actual_patterns=actual_patterns, db_connection=db_connection
        )

        logger.info(
            f"[DB] Pattern validation for {adw_id}: "
            f"{validation_result['correct']}/{validation_result['total_predicted']} correct, "
            f"accuracy {validation_result['accuracy']:.2%}"
        )

    except Exception as e:
        # Don't let validation errors crash workflow updates
        logger.error(f"[DB] Pattern validation failed for {adw_id}: {e}", exc_info=True)
