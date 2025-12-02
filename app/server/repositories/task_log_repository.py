"""
Task Log Repository

Handles database operations for ADW task/phase logs.
"""

import logging
from typing import List, Optional

from core.models.observability import IssueProgress, TaskLog, TaskLogCreate, TaskLogFilters
from database.factory import get_database_adapter

logger = logging.getLogger(__name__)


class TaskLogRepository:
    """Repository for task log database operations"""

    def __init__(self):
        self.adapter = get_database_adapter()

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
        query = """
            INSERT INTO task_logs (
                adw_id, issue_number, workflow_template,
                phase_name, phase_number, phase_status,
                log_message, error_message,
                started_at, completed_at, duration_seconds,
                tokens_used, cost_usd
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
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
                    ),
                )
                result = cursor.fetchone()
                conn.commit()

                task_id = result[0]
                captured_at = result[1]
                created_at = result[2]

                logger.info(
                    f"Created task log {task_id} for issue #{task_log.issue_number} "
                    f"phase {task_log.phase_name} ({task_log.phase_status})"
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
                    captured_at=captured_at,
                    created_at=created_at,
                )
        except Exception as e:
            logger.error(f"Failed to create task log: {e}")
            raise

    def get_all(self, filters: Optional[TaskLogFilters] = None) -> List[TaskLog]:
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
                   tokens_used, cost_usd, captured_at, created_at
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
                            id=row[0],
                            adw_id=row[1],
                            issue_number=row[2],
                            workflow_template=row[3],
                            phase_name=row[4],
                            phase_number=row[5],
                            phase_status=row[6],
                            log_message=row[7],
                            error_message=row[8],
                            started_at=row[9],
                            completed_at=row[10],
                            duration_seconds=row[11],
                            tokens_used=row[12],
                            cost_usd=row[13],
                            captured_at=row[14],
                            created_at=row[15],
                        )
                    )

                logger.info(f"Retrieved {len(logs)} task logs")
                return logs
        except Exception as e:
            logger.error(f"Failed to get task logs: {e}")
            raise

    def get_by_issue(self, issue_number: int) -> List[TaskLog]:
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
                   tokens_used, cost_usd, captured_at, created_at
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
                            id=row[0],
                            adw_id=row[1],
                            issue_number=row[2],
                            workflow_template=row[3],
                            phase_name=row[4],
                            phase_number=row[5],
                            phase_status=row[6],
                            log_message=row[7],
                            error_message=row[8],
                            started_at=row[9],
                            completed_at=row[10],
                            duration_seconds=row[11],
                            tokens_used=row[12],
                            cost_usd=row[13],
                            captured_at=row[14],
                            created_at=row[15],
                        )
                    )

                logger.info(f"Retrieved {len(logs)} task logs for issue #{issue_number}")
                return logs
        except Exception as e:
            logger.error(f"Failed to get task logs for issue #{issue_number}: {e}")
            raise

    def get_by_adw_id(self, adw_id: str) -> List[TaskLog]:
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
                   tokens_used, cost_usd, captured_at, created_at
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
                            id=row[0],
                            adw_id=row[1],
                            issue_number=row[2],
                            workflow_template=row[3],
                            phase_name=row[4],
                            phase_number=row[5],
                            phase_status=row[6],
                            log_message=row[7],
                            error_message=row[8],
                            started_at=row[9],
                            completed_at=row[10],
                            duration_seconds=row[11],
                            tokens_used=row[12],
                            cost_usd=row[13],
                            captured_at=row[14],
                            created_at=row[15],
                        )
                    )

                logger.info(f"Retrieved {len(logs)} task logs for ADW {adw_id}")
                return logs
        except Exception as e:
            logger.error(f"Failed to get task logs for ADW {adw_id}: {e}")
            raise

    def get_issue_progress(self, issue_number: int) -> Optional[IssueProgress]:
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
                    issue_number=row[0],
                    adw_id=row[1],
                    workflow_template=row[2],
                    total_phases=row[3],
                    completed_phases=row[4],
                    failed_phases=row[5],
                    latest_phase=row[6],
                    last_activity=row[7],
                )
        except Exception as e:
            logger.error(f"Failed to get progress for issue #{issue_number}: {e}")
            raise

    def get_latest_by_issue(self, issue_number: int) -> Optional[TaskLog]:
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
                   tokens_used, cost_usd, captured_at, created_at
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
                    id=row[0],
                    adw_id=row[1],
                    issue_number=row[2],
                    workflow_template=row[3],
                    phase_name=row[4],
                    phase_number=row[5],
                    phase_status=row[6],
                    log_message=row[7],
                    error_message=row[8],
                    started_at=row[9],
                    completed_at=row[10],
                    duration_seconds=row[11],
                    tokens_used=row[12],
                    cost_usd=row[13],
                    captured_at=row[14],
                    created_at=row[15],
                )
        except Exception as e:
            logger.error(f"Failed to get latest task log for issue #{issue_number}: {e}")
            raise
