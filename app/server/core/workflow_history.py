"""
Workflow history data collection and management module.

This module handles collecting workflow execution data from ADW state files,
storing it in SQLite database, and providing query/analytics functionality.
"""

import json
import logging
import sqlite3
from pathlib import Path
from typing import List, Optional
from datetime import datetime

from core.data_models import (
    WorkflowHistoryItem,
    WorkflowHistoryResponse,
    WorkflowHistoryFilter,
    WorkflowExecutionMetrics,
    WorkflowPerformanceMetrics,
    WorkflowResourceMetrics,
    WorkflowAnalytics,
)
from core.cost_tracker import read_cost_history

logger = logging.getLogger(__name__)


def get_db_path() -> Path:
    """Get the path to the workflow history database."""
    project_root = Path(__file__).parent.parent
    db_dir = project_root / "db"
    db_dir.mkdir(exist_ok=True)
    return db_dir / "database.db"


def initialize_database() -> None:
    """Initialize the workflow history database with schema."""
    db_path = get_db_path()
    schema_path = Path(__file__).parent.parent / "db" / "schema.sql"

    if not schema_path.exists():
        logger.warning(f"Schema file not found at {schema_path}")
        return

    try:
        with sqlite3.connect(db_path) as conn:
            with open(schema_path, 'r') as f:
                schema = f.read()
            conn.executescript(schema)
            logger.info("[DB] Workflow history database initialized")
    except Exception as e:
        logger.error(f"[DB] Failed to initialize database: {e}")


def collect_workflow_data(adw_id: str) -> Optional[WorkflowHistoryItem]:
    """
    Collect comprehensive workflow data from ADW state files.

    Reads data from:
    - agents/{adw_id}/ directory
    - Cost data from raw_output.jsonl files via cost_tracker
    - ADW state files (if they exist)

    Args:
        adw_id: The ADW workflow identifier

    Returns:
        WorkflowHistoryItem or None if data cannot be collected
    """
    try:
        project_root = Path(__file__).parent.parent.parent.parent
        agents_dir = project_root / "agents" / adw_id

        if not agents_dir.exists():
            logger.warning(f"Agents directory not found for {adw_id}")
            return None

        # Try to read cost data
        cost_data = None
        try:
            cost_data = read_cost_history(adw_id)
        except Exception as e:
            logger.warning(f"Could not read cost data for {adw_id}: {e}")

        # Read ADW state file if it exists (contains workflow metadata)
        adw_state_file = agents_dir / "adw_state.json"
        adw_state = {}
        if adw_state_file.exists():
            try:
                with open(adw_state_file, 'r') as f:
                    adw_state = json.load(f)
            except Exception as e:
                logger.warning(f"Could not read adw_state.json for {adw_id}: {e}")

        # Extract workflow metadata
        issue_number = adw_state.get("issue_number")
        workflow_template = adw_state.get("workflow_template", "unknown")
        nl_input = adw_state.get("nl_input", "")
        status = adw_state.get("status", "unknown")
        model_used = adw_state.get("model_used", "claude-sonnet-4-5")

        # Map status to valid values
        if status not in ["in_progress", "completed", "failed"]:
            status = "completed" if cost_data else "in_progress"

        # Calculate timing
        start_time = adw_state.get("start_timestamp", datetime.now().isoformat())
        end_time = adw_state.get("end_timestamp")
        completion_time = None

        if end_time and start_time:
            try:
                start_dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
                end_dt = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
                completion_time = (end_dt - start_dt).total_seconds()
            except Exception as e:
                logger.warning(f"Could not calculate completion time: {e}")

        # Build execution metrics
        if cost_data:
            total_tokens = cost_data.total_tokens
            cache_efficiency = cost_data.cache_efficiency_percent
            actual_cost = cost_data.total_cost

            # Sum up token counts from phases
            input_tokens = sum(p.tokens.input_tokens for p in cost_data.phases)
            cache_creation_tokens = sum(p.tokens.cache_creation_tokens for p in cost_data.phases)
            cache_read_tokens = sum(p.tokens.cache_read_tokens for p in cost_data.phases)
            output_tokens = sum(p.tokens.output_tokens for p in cost_data.phases)

            cost_per_token = actual_cost / total_tokens if total_tokens > 0 else 0.0
            phases = cost_data.phases
        else:
            total_tokens = 0
            input_tokens = 0
            cache_creation_tokens = 0
            cache_read_tokens = 0
            output_tokens = 0
            cache_efficiency = 0.0
            actual_cost = 0.0
            cost_per_token = 0.0
            phases = []

        execution_metrics = WorkflowExecutionMetrics(
            total_tokens=total_tokens,
            input_tokens=input_tokens,
            cache_creation_tokens=cache_creation_tokens,
            cache_read_tokens=cache_read_tokens,
            output_tokens=output_tokens,
            cache_efficiency_percent=cache_efficiency,
            estimated_cost_total=0.0,  # Could be calculated from template
            actual_cost_total=actual_cost,
            cost_per_token=cost_per_token,
        )

        # Build performance metrics
        performance_metrics = WorkflowPerformanceMetrics(
            completion_time_seconds=completion_time,
            retry_count=adw_state.get("retry_count", 0),
            success_rate=adw_state.get("success_rate", 100.0 if status == "completed" else 0.0),
            concurrent_workflows_count=adw_state.get("concurrent_workflows", 0),
        )

        # Build resource metrics
        resource_metrics = WorkflowResourceMetrics(
            worktree_id=adw_state.get("worktree_id", adw_id),
            worktree_reused=adw_state.get("worktree_reused", False),
            ports_used=adw_state.get("ports_used", {"frontend": 5173, "backend": 8000}),
            structured_input=adw_state.get("structured_input"),
        )

        # Build workflow history item
        history_item = WorkflowHistoryItem(
            adw_id=adw_id,
            issue_number=issue_number,
            workflow_template=workflow_template,
            start_timestamp=start_time,
            end_timestamp=end_time,
            status=status,  # type: ignore
            nl_input=nl_input,
            model_used=model_used,
            error_message=adw_state.get("error_message"),
            execution_metrics=execution_metrics,
            performance_metrics=performance_metrics,
            resource_metrics=resource_metrics,
            phases=phases,
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat(),
        )

        return history_item

    except Exception as e:
        logger.error(f"Error collecting workflow data for {adw_id}: {e}")
        return None


def save_workflow_to_db(item: WorkflowHistoryItem) -> bool:
    """
    Save workflow history item to database.

    Args:
        item: The workflow history item to save

    Returns:
        True if saved successfully, False otherwise
    """
    try:
        db_path = get_db_path()

        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()

            # Check if record already exists
            cursor.execute("SELECT id FROM workflow_history WHERE adw_id = ?", (item.adw_id,))
            existing = cursor.fetchone()

            if existing:
                # Update existing record
                cursor.execute("""
                    UPDATE workflow_history
                    SET issue_number = ?, workflow_template = ?, start_timestamp = ?,
                        end_timestamp = ?, completion_time_seconds = ?, status = ?,
                        error_message = ?, nl_input = ?, structured_input = ?,
                        model_used = ?, estimated_cost_total = ?, actual_cost_total = ?,
                        total_tokens = ?, input_tokens = ?, cache_creation_tokens = ?,
                        cache_read_tokens = ?, output_tokens = ?, cache_efficiency_percent = ?,
                        retry_count = ?, success_rate = ?, worktree_id = ?,
                        worktree_reused = ?, ports_used = ?, concurrent_workflows_count = ?,
                        updated_at = ?
                    WHERE adw_id = ?
                """, (
                    item.issue_number,
                    item.workflow_template,
                    item.start_timestamp,
                    item.end_timestamp,
                    item.performance_metrics.completion_time_seconds,
                    item.status,
                    item.error_message,
                    item.nl_input,
                    json.dumps(item.resource_metrics.structured_input) if item.resource_metrics.structured_input else None,
                    item.model_used,
                    item.execution_metrics.estimated_cost_total,
                    item.execution_metrics.actual_cost_total,
                    item.execution_metrics.total_tokens,
                    item.execution_metrics.input_tokens,
                    item.execution_metrics.cache_creation_tokens,
                    item.execution_metrics.cache_read_tokens,
                    item.execution_metrics.output_tokens,
                    item.execution_metrics.cache_efficiency_percent,
                    item.performance_metrics.retry_count,
                    item.performance_metrics.success_rate,
                    item.resource_metrics.worktree_id,
                    1 if item.resource_metrics.worktree_reused else 0,
                    json.dumps(item.resource_metrics.ports_used),
                    item.performance_metrics.concurrent_workflows_count,
                    datetime.now().isoformat(),
                    item.adw_id,
                ))
                logger.info(f"[DB] Updated workflow history for {item.adw_id}")
            else:
                # Insert new record
                cursor.execute("""
                    INSERT INTO workflow_history (
                        adw_id, issue_number, workflow_template, start_timestamp,
                        end_timestamp, completion_time_seconds, status, error_message,
                        nl_input, structured_input, model_used, estimated_cost_total,
                        actual_cost_total, total_tokens, input_tokens, cache_creation_tokens,
                        cache_read_tokens, output_tokens, cache_efficiency_percent,
                        retry_count, success_rate, worktree_id, worktree_reused,
                        ports_used, concurrent_workflows_count, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    item.adw_id,
                    item.issue_number,
                    item.workflow_template,
                    item.start_timestamp,
                    item.end_timestamp,
                    item.performance_metrics.completion_time_seconds,
                    item.status,
                    item.error_message,
                    item.nl_input,
                    json.dumps(item.resource_metrics.structured_input) if item.resource_metrics.structured_input else None,
                    item.model_used,
                    item.execution_metrics.estimated_cost_total,
                    item.execution_metrics.actual_cost_total,
                    item.execution_metrics.total_tokens,
                    item.execution_metrics.input_tokens,
                    item.execution_metrics.cache_creation_tokens,
                    item.execution_metrics.cache_read_tokens,
                    item.execution_metrics.output_tokens,
                    item.execution_metrics.cache_efficiency_percent,
                    item.performance_metrics.retry_count,
                    item.performance_metrics.success_rate,
                    item.resource_metrics.worktree_id,
                    1 if item.resource_metrics.worktree_reused else 0,
                    json.dumps(item.resource_metrics.ports_used),
                    item.performance_metrics.concurrent_workflows_count,
                    item.created_at,
                    item.updated_at,
                ))
                logger.info(f"[DB] Inserted workflow history for {item.adw_id}")

            conn.commit()
            return True

    except Exception as e:
        logger.error(f"Error saving workflow to database: {e}")
        return False


def get_workflow_history(filters: WorkflowHistoryFilter) -> WorkflowHistoryResponse:
    """
    Query workflow history from database with filters and sorting.

    Args:
        filters: Filter and sorting parameters

    Returns:
        WorkflowHistoryResponse with items and analytics
    """
    try:
        db_path = get_db_path()

        with sqlite3.connect(db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            # Build WHERE clause
            where_clauses = []
            params = []

            if filters.filter_status:
                where_clauses.append("status = ?")
                params.append(filters.filter_status)

            if filters.filter_template:
                where_clauses.append("workflow_template = ?")
                params.append(filters.filter_template)

            if filters.filter_model:
                where_clauses.append("model_used = ?")
                params.append(filters.filter_model)

            if filters.date_from:
                where_clauses.append("start_timestamp >= ?")
                params.append(filters.date_from)

            if filters.date_to:
                where_clauses.append("start_timestamp <= ?")
                params.append(filters.date_to)

            if filters.search_query:
                where_clauses.append("(nl_input LIKE ? OR adw_id LIKE ?)")
                search_pattern = f"%{filters.search_query}%"
                params.extend([search_pattern, search_pattern])

            where_clause = " AND ".join(where_clauses) if where_clauses else "1=1"

            # Build ORDER BY clause
            sort_field_map = {
                "date": "start_timestamp",
                "cost": "actual_cost_total",
                "duration": "completion_time_seconds",
                "success_rate": "success_rate",
                "model": "model_used",
            }
            sort_field = sort_field_map.get(filters.sort_by, "start_timestamp")
            order = filters.order.upper()

            # Get total count
            count_query = f"SELECT COUNT(*) FROM workflow_history WHERE {where_clause}"
            cursor.execute(count_query, params)
            total = cursor.fetchone()[0]

            # Get paginated results
            query = f"""
                SELECT * FROM workflow_history
                WHERE {where_clause}
                ORDER BY {sort_field} {order}
                LIMIT ? OFFSET ?
            """
            cursor.execute(query, params + [filters.limit, filters.offset])
            rows = cursor.fetchall()

            # Convert rows to WorkflowHistoryItem objects
            items = []
            for row in rows:
                try:
                    # Parse JSON fields
                    structured_input = json.loads(row["structured_input"]) if row["structured_input"] else None
                    ports_used = json.loads(row["ports_used"]) if row["ports_used"] else {}

                    # Try to get phase data from cost tracker
                    phases = []
                    try:
                        cost_data = read_cost_history(row["adw_id"])
                        phases = cost_data.phases
                    except Exception:
                        pass

                    item = WorkflowHistoryItem(
                        id=row["id"],
                        adw_id=row["adw_id"],
                        issue_number=row["issue_number"],
                        workflow_template=row["workflow_template"],
                        start_timestamp=row["start_timestamp"],
                        end_timestamp=row["end_timestamp"],
                        status=row["status"],  # type: ignore
                        nl_input=row["nl_input"],
                        model_used=row["model_used"],
                        error_message=row["error_message"],
                        execution_metrics=WorkflowExecutionMetrics(
                            total_tokens=row["total_tokens"] or 0,
                            input_tokens=row["input_tokens"] or 0,
                            cache_creation_tokens=row["cache_creation_tokens"] or 0,
                            cache_read_tokens=row["cache_read_tokens"] or 0,
                            output_tokens=row["output_tokens"] or 0,
                            cache_efficiency_percent=row["cache_efficiency_percent"] or 0.0,
                            estimated_cost_total=row["estimated_cost_total"] or 0.0,
                            actual_cost_total=row["actual_cost_total"] or 0.0,
                            cost_per_token=(row["actual_cost_total"] / row["total_tokens"])
                                if row["total_tokens"] and row["total_tokens"] > 0 else 0.0,
                        ),
                        performance_metrics=WorkflowPerformanceMetrics(
                            completion_time_seconds=row["completion_time_seconds"],
                            retry_count=row["retry_count"] or 0,
                            success_rate=row["success_rate"] or 0.0,
                            concurrent_workflows_count=row["concurrent_workflows_count"] or 0,
                        ),
                        resource_metrics=WorkflowResourceMetrics(
                            worktree_id=row["worktree_id"],
                            worktree_reused=bool(row["worktree_reused"]),
                            ports_used=ports_used,
                            structured_input=structured_input,
                        ),
                        phases=phases,
                        created_at=row["created_at"],
                        updated_at=row["updated_at"],
                    )
                    items.append(item)
                except Exception as e:
                    logger.error(f"Error parsing workflow history row: {e}")
                    continue

            # Calculate analytics
            analytics = calculate_analytics(items, cursor)

            return WorkflowHistoryResponse(
                items=items,
                analytics=analytics,
                total=total,
                has_more=(filters.offset + filters.limit) < total,
            )

    except Exception as e:
        logger.error(f"Error querying workflow history: {e}")
        # Return empty response on error
        return WorkflowHistoryResponse(
            items=[],
            analytics=WorkflowAnalytics(),
            total=0,
            has_more=False,
        )


def calculate_analytics(items: List[WorkflowHistoryItem], cursor: sqlite3.Cursor) -> WorkflowAnalytics:
    """
    Calculate aggregate analytics from workflow history items.

    Args:
        items: List of workflow history items (current page)
        cursor: Database cursor for additional queries

    Returns:
        WorkflowAnalytics object with aggregated metrics
    """
    try:
        # Get all-time statistics from database
        cursor.execute("""
            SELECT
                COUNT(*) as total_workflows,
                AVG(actual_cost_total) as avg_cost,
                AVG(completion_time_seconds) as avg_duration,
                AVG(success_rate) as avg_success_rate,
                AVG(cache_efficiency_percent) as avg_cache_efficiency,
                SUM(actual_cost_total) as total_cost,
                SUM(total_tokens) as total_tokens
            FROM workflow_history
        """)
        stats = cursor.fetchone()

        # Calculate cost by model
        cursor.execute("""
            SELECT model_used, AVG(actual_cost_total) as avg_cost
            FROM workflow_history
            WHERE model_used IS NOT NULL
            GROUP BY model_used
        """)
        avg_cost_by_model = {row[0]: row[1] for row in cursor.fetchall()}

        # Calculate cost by template
        cursor.execute("""
            SELECT workflow_template, AVG(actual_cost_total) as avg_cost
            FROM workflow_history
            GROUP BY workflow_template
        """)
        avg_cost_by_template = {row[0]: row[1] for row in cursor.fetchall()}

        # Get most expensive workflows
        cursor.execute("""
            SELECT adw_id, nl_input, actual_cost_total, workflow_template
            FROM workflow_history
            ORDER BY actual_cost_total DESC
            LIMIT 5
        """)
        most_expensive = [
            {
                "adw_id": row[0],
                "nl_input": row[1][:100] + "..." if len(row[1]) > 100 else row[1],
                "cost": row[2],
                "template": row[3],
            }
            for row in cursor.fetchall()
        ]

        # Calculate token efficiency by model
        cursor.execute("""
            SELECT model_used, AVG(actual_cost_total / NULLIF(total_tokens, 0)) as cost_per_token
            FROM workflow_history
            WHERE model_used IS NOT NULL AND total_tokens > 0
            GROUP BY model_used
        """)
        token_efficiency = {row[0]: row[1] for row in cursor.fetchall()}

        return WorkflowAnalytics(
            total_workflows=stats[0] or 0,
            avg_cost_by_model=avg_cost_by_model,
            avg_cost_by_template=avg_cost_by_template,
            avg_completion_time=stats[1] or 0.0,
            overall_success_rate=stats[3] or 0.0,
            cache_hit_rate=stats[4] or 0.0,
            most_expensive_workflows=most_expensive,
            token_efficiency_by_model=token_efficiency,
            total_cost_all_time=stats[5] or 0.0,
            total_tokens_all_time=int(stats[6] or 0),
        )

    except Exception as e:
        logger.error(f"Error calculating analytics: {e}")
        return WorkflowAnalytics()


def update_workflow_status(adw_id: str, status: str) -> bool:
    """
    Update workflow status in database.

    Args:
        adw_id: The ADW workflow identifier
        status: New status (in_progress, completed, failed)

    Returns:
        True if updated successfully, False otherwise
    """
    try:
        db_path = get_db_path()

        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE workflow_history
                SET status = ?, updated_at = ?
                WHERE adw_id = ?
            """, (status, datetime.now().isoformat(), adw_id))
            conn.commit()

            if cursor.rowcount > 0:
                logger.info(f"[DB] Updated status for {adw_id} to {status}")
                return True
            else:
                logger.warning(f"[DB] No workflow found with adw_id {adw_id}")
                return False

    except Exception as e:
        logger.error(f"Error updating workflow status: {e}")
        return False


def sync_all_workflows() -> int:
    """
    Sync all workflows from agents/ directory to database.

    Scans the agents/ directory and updates database with latest workflow data.

    Returns:
        Number of workflows synced
    """
    try:
        project_root = Path(__file__).parent.parent.parent.parent
        agents_dir = project_root / "agents"

        if not agents_dir.exists():
            logger.warning("Agents directory not found")
            return 0

        synced = 0
        for adw_dir in agents_dir.iterdir():
            if adw_dir.is_dir():
                adw_id = adw_dir.name
                workflow_data = collect_workflow_data(adw_id)
                if workflow_data and save_workflow_to_db(workflow_data):
                    synced += 1

        logger.info(f"[SYNC] Synced {synced} workflows to database")
        return synced

    except Exception as e:
        logger.error(f"Error syncing workflows: {e}")
        return 0
