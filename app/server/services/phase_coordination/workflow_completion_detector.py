"""
Workflow Completion Detector

Detects workflow status and errors from workflow_history database.
"""

import logging
from typing import Optional

from database import SQLiteAdapter

logger = logging.getLogger(__name__)


class WorkflowCompletionDetector:
    """
    Detects workflow completion status from workflow_history database.

    Provides methods to query workflow status and error messages
    for issue-based workflow tracking.
    """

    def __init__(self, workflow_db_path: str = "db/workflow_history.db"):
        """
        Initialize WorkflowCompletionDetector.

        Args:
            workflow_db_path: Path to workflow_history database
        """
        self.workflow_db_path = workflow_db_path
        self.adapter = SQLiteAdapter(db_path=workflow_db_path)

    def get_workflow_status(self, issue_number: int) -> Optional[str]:
        """
        Get workflow status from workflow_history by issue number.

        Only returns 'completed' or 'failed' if end_time is set (real completion).
        Ignores placeholder/phantom records with status but no timestamps.

        Args:
            issue_number: GitHub issue number

        Returns:
            'completed', 'failed', 'running', 'pending', or None if not found
        """
        try:
            with self.adapter.get_connection() as conn:
                ph = self.adapter.placeholder()
                cursor = conn.execute(
                    f"""
                    SELECT status, end_time FROM workflow_history
                    WHERE issue_number = {ph}
                    ORDER BY created_at DESC
                    LIMIT 1
                    """,
                    (issue_number,)
                )
                row = cursor.fetchone()
                if not row:
                    return None

                status = row["status"]
                end_time = row["end_time"]

                # Only trust 'completed' or 'failed' if end_time is set
                # This prevents phantom/placeholder records from being treated as real completions
                if status in ('completed', 'failed') and not end_time:
                    logger.warning(
                        f"[PHANTOM] Issue #{issue_number} has status='{status}' but no end_time - "
                        f"treating as 'running'"
                    )
                    return 'running'

                return status
        except Exception as e:
            logger.error(f"[ERROR] Failed to get workflow status for issue #{issue_number}: {str(e)}")
            return None

    def get_workflow_error(self, issue_number: int) -> Optional[str]:
        """
        Get error message from workflow_history.

        Args:
            issue_number: GitHub issue number

        Returns:
            Error message string or None
        """
        try:
            with self.adapter.get_connection() as conn:
                ph = self.adapter.placeholder()
                cursor = conn.execute(
                    f"""
                    SELECT error_message FROM workflow_history
                    WHERE issue_number = {ph} AND status = 'failed'
                    ORDER BY created_at DESC
                    LIMIT 1
                    """,
                    (issue_number,)
                )
                row = cursor.fetchone()
                return row["error_message"] if row else None
        except Exception as e:
            logger.error(f"[ERROR] Failed to get workflow error for issue #{issue_number}: {str(e)}")
            return None
