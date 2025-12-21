"""
Task Log Repository

Handles database operations for ADW task/phase logs.
"""

import json
import logging

from core.models.observability import (
    IssueProgress,
    TaskLog,
    TaskLogCreate,
    TaskLogFilters,
    ToolCallRecord,
)
from database.factory import get_database_adapter

logger = logging.getLogger(__name__)


class TaskLogRepository:
    """Repository for task log database operations"""

    def __init__(self):
        self.adapter = get_database_adapter()

    @staticmethod
    def _deserialize_tool_calls(tool_calls_json: str | None) -> list[ToolCallRecord]:
        """Deserialize tool_calls JSONB to list of ToolCallRecord objects."""
        if not tool_calls_json:
            return []

        try:
            # PostgreSQL returns JSONB as a JSON string or dict
            if isinstance(tool_calls_json, str):
                tool_calls_data = json.loads(tool_calls_json)
            else:
                tool_calls_data = tool_calls_json

            return [ToolCallRecord(**tc) for tc in tool_calls_data]
        except (json.JSONDecodeError, TypeError, ValueError):
            logger.warning("Failed to deserialize tool_calls, returning empty list")
            return []

    def create(self, task_log: TaskLogCreate) -> TaskLog:
        """
        Create a new task log entry.

        Args:
            task_log: Task log data

        Returns:
            Created TaskLog with ID

        Raises:
            Exception: If database operation fails
        """
        # Serialize tool_calls to JSON
        tool_calls_json = json.dumps([tc.model_dump() for tc in task_log.tool_calls])

        query = """
            INSERT INTO task_logs (
                adw_id, issue_number, workflow_template,
                phase_name, phase_number, phase_status,
                log_message, error_message,
                started_at, completed_at, duration_seconds,
                tokens_used, cost_usd, tool_calls
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s::jsonb)
            RETURNING id, captured_at, created_at
        """

        try:
            with self.adapter.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    query,
                    (
                        task_log.adw_id,
                        task_log.issue_number,
                        task_log.workflow_template,
                        task_log.phase_name,
                        task_log.phase_number,
                        task_log.phase_status,
                        task_log.log_message,
                        task_log.error_message,
                        task_log.started_at,
                        task_log.completed_at,
                        task_log.duration_seconds,
                        task_log.tokens_used,
                        task_log.cost_usd,
                        tool_calls_json,
                    ),
                )
                result = cursor.fetchone()
                conn.commit()

                task_id = result['id']
                captured_at = result['captured_at']
                created_at = result['created_at']

                logger.info(
                    f"Created task log {task_id} for issue #{task_log.issue_number} "
                    f"phase {task_log.phase_name} ({task_log.phase_status}) "
                    f"with {len(task_log.tool_calls)} tool call(s)"
                )

                return TaskLog(
                    id=task_id,
                    adw_id=task_log.adw_id,
                    issue_number=task_log.issue_number,
                    workflow_template=task_log.workflow_template,
                    phase_name=task_log.phase_name,
                    phase_number=task_log.phase_number,
                    phase_status=task_log.phase_status,
                    log_message=task_log.log_message,
                    error_message=task_log.error_message,
                    started_at=task_log.started_at,
                    completed_at=task_log.completed_at,
                    duration_seconds=task_log.duration_seconds,
                    tokens_used=task_log.tokens_used,
                    cost_usd=task_log.cost_usd,
                    tool_calls=task_log.tool_calls,
                    captured_at=captured_at,
                    created_at=created_at,
                )
        except Exception as e:
            logger.error(f"Failed to create task log: {e}")
            raise

    def get_all(self, filters: TaskLogFilters | None = None) -> list[TaskLog]:
        """
        Get all task logs with optional filtering and pagination.

        Args:
            filters: Optional filters (issue_number, adw_id, phase, status)

        Returns:
            List of TaskLog objects
        """
        if filters is None:
            filters = TaskLogFilters()

        query = """
            SELECT id, adw_id, issue_number, workflow_template,
                   phase_name, phase_number, phase_status,
                   log_message, error_message,
                   started_at, completed_at, duration_seconds,
                   tokens_used, cost_usd, tool_calls, captured_at, created_at
            FROM task_logs
            WHERE 1=1
        """
        params = []

        if filters.issue_number:
            query += " AND issue_number = %s"
            params.append(filters.issue_number)

        if filters.adw_id:
            query += " AND adw_id = %s"
            params.append(filters.adw_id)

        if filters.phase_name:
            query += " AND phase_name = %s"
            params.append(filters.phase_name)

        if filters.phase_status:
            query += " AND phase_status = %s"
            params.append(filters.phase_status)

        query += " ORDER BY created_at DESC LIMIT %s OFFSET %s"
        params.extend([filters.limit, filters.offset])

        try:
            with self.adapter.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, params)
                rows = cursor.fetchall()

                logs = []
                for row in rows:
                    logs.append(
                        TaskLog(
                            id=row['id'],
                            adw_id=row['adw_id'],
                            issue_number=row['issue_number'],
                            workflow_template=row['workflow_template'],
                            phase_name=row['phase_name'],
                            phase_number=row['phase_number'],
                            phase_status=row['phase_status'],
                            log_message=row['log_message'],
                            error_message=row['error_message'],
                            started_at=row['started_at'],
                            completed_at=row['completed_at'],
                            duration_seconds=row['duration_seconds'],
                            tokens_used=row['tokens_used'],
                            cost_usd=row['cost_usd'],
                            tool_calls=self._deserialize_tool_calls(row.get('tool_calls')),
                            captured_at=row['captured_at'],
                            created_at=row['created_at'],
                        )
                    )

                logger.info(f"Retrieved {len(logs)} task logs")
                return logs
        except Exception as e:
            logger.error(f"Failed to get task logs: {e}")
            raise

    def get_by_issue(self, issue_number: int) -> list[TaskLog]:
        """
        Get all task logs for a specific issue.

        Args:
            issue_number: GitHub issue number

        Returns:
            List of TaskLog objects ordered by phase_number
        """
        query = """
            SELECT id, adw_id, issue_number, workflow_template,
                   phase_name, phase_number, phase_status,
                   log_message, error_message,
                   started_at, completed_at, duration_seconds,
                   tokens_used, cost_usd, tool_calls, captured_at, created_at
            FROM task_logs
            WHERE issue_number = %s
            ORDER BY phase_number ASC, created_at ASC
        """

        try:
            with self.adapter.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, (issue_number,))
                rows = cursor.fetchall()

                logs = []
                for row in rows:
                    logs.append(
                        TaskLog(
                            id=row['id'],
                            adw_id=row['adw_id'],
                            issue_number=row['issue_number'],
                            workflow_template=row['workflow_template'],
                            phase_name=row['phase_name'],
                            phase_number=row['phase_number'],
                            phase_status=row['phase_status'],
                            log_message=row['log_message'],
                            error_message=row['error_message'],
                            started_at=row['started_at'],
                            completed_at=row['completed_at'],
                            duration_seconds=row['duration_seconds'],
                            tokens_used=row['tokens_used'],
                            cost_usd=row['cost_usd'],
                            tool_calls=self._deserialize_tool_calls(row.get('tool_calls')),
                            captured_at=row['captured_at'],
                            created_at=row['created_at'],
                        )
                    )

                logger.info(f"Retrieved {len(logs)} task logs for issue #{issue_number}")
                return logs
        except Exception as e:
            logger.error(f"Failed to get task logs for issue #{issue_number}: {e}")
            raise

    def get_by_adw_id(self, adw_id: str) -> list[TaskLog]:
        """
        Get all task logs for a specific ADW workflow.

        Args:
            adw_id: ADW workflow ID

        Returns:
            List of TaskLog objects ordered by phase_number
        """
        query = """
            SELECT id, adw_id, issue_number, workflow_template,
                   phase_name, phase_number, phase_status,
                   log_message, error_message,
                   started_at, completed_at, duration_seconds,
                   tokens_used, cost_usd, tool_calls, captured_at, created_at
            FROM task_logs
            WHERE adw_id = %s
            ORDER BY phase_number ASC, created_at ASC
        """

        try:
            with self.adapter.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, (adw_id,))
                rows = cursor.fetchall()

                logs = []
                for row in rows:
                    logs.append(
                        TaskLog(
                            id=row['id'],
                            adw_id=row['adw_id'],
                            issue_number=row['issue_number'],
                            workflow_template=row['workflow_template'],
                            phase_name=row['phase_name'],
                            phase_number=row['phase_number'],
                            phase_status=row['phase_status'],
                            log_message=row['log_message'],
                            error_message=row['error_message'],
                            started_at=row['started_at'],
                            completed_at=row['completed_at'],
                            duration_seconds=row['duration_seconds'],
                            tokens_used=row['tokens_used'],
                            cost_usd=row['cost_usd'],
                            tool_calls=self._deserialize_tool_calls(row.get('tool_calls')),
                            captured_at=row['captured_at'],
                            created_at=row['created_at'],
                        )
                    )

                logger.info(f"Retrieved {len(logs)} task logs for ADW {adw_id}")
                return logs
        except Exception as e:
            logger.error(f"Failed to get task logs for ADW {adw_id}: {e}")
            raise

    def get_issue_progress(self, issue_number: int) -> IssueProgress | None:
        """
        Get progress summary for an issue.

        Args:
            issue_number: GitHub issue number

        Returns:
            IssueProgress object if issue has logs, None otherwise
        """
        query = """
            SELECT issue_number, adw_id, workflow_template,
                   total_phases, completed_phases, failed_phases,
                   latest_phase, last_activity
            FROM v_issue_progress
            WHERE issue_number = %s
        """

        try:
            with self.adapter.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, (issue_number,))
                row = cursor.fetchone()

                if not row:
                    return None

                return IssueProgress(
                    issue_number=row['issue_number'],
                    adw_id=row['adw_id'],
                    workflow_template=row['workflow_template'],
                    total_phases=row['total_phases'],
                    completed_phases=row['completed_phases'],
                    failed_phases=row['failed_phases'],
                    latest_phase=row['latest_phase'],
                    last_activity=row['last_activity'],
                )
        except Exception as e:
            logger.error(f"Failed to get progress for issue #{issue_number}: {e}")
            raise

    def get_latest_by_issue(self, issue_number: int) -> TaskLog | None:
        """
        Get the most recent task log for an issue.

        Args:
            issue_number: GitHub issue number

        Returns:
            Most recent TaskLog or None
        """
        query = """
            SELECT id, adw_id, issue_number, workflow_template,
                   phase_name, phase_number, phase_status,
                   log_message, error_message,
                   started_at, completed_at, duration_seconds,
                   tokens_used, cost_usd, tool_calls, captured_at, created_at
            FROM task_logs
            WHERE issue_number = %s
            ORDER BY phase_number DESC, created_at DESC
            LIMIT 1
        """

        try:
            with self.adapter.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, (issue_number,))
                row = cursor.fetchone()

                if not row:
                    return None

                return TaskLog(
                    id=row['id'],
                    adw_id=row['adw_id'],
                    issue_number=row['issue_number'],
                    workflow_template=row['workflow_template'],
                    phase_name=row['phase_name'],
                    phase_number=row['phase_number'],
                    phase_status=row['phase_status'],
                    log_message=row['log_message'],
                    error_message=row['error_message'],
                    started_at=row['started_at'],
                    completed_at=row['completed_at'],
                    duration_seconds=row['duration_seconds'],
                    tokens_used=row['tokens_used'],
                    cost_usd=row['cost_usd'],
                    tool_calls=self._deserialize_tool_calls(row.get('tool_calls')),
                    captured_at=row['captured_at'],
                    created_at=row['created_at'],
                )
        except Exception as e:
            logger.error(f"Failed to get latest task log for issue #{issue_number}: {e}")
            raise
