"""
PhaseQueueRepository

Handles all database operations for the phase queue.
Separates database access from business logic (Repository Pattern).
"""

import json
import logging
from datetime import datetime

from models.phase_queue_item import PhaseQueueItem
from utils.db_connection import get_connection

logger = logging.getLogger(__name__)


class PhaseQueueRepository:
    """Repository for phase queue database operations"""

    def __init__(self, db_path: str = "db/database.db"):
        """
        Initialize repository.

        Args:
            db_path: Path to SQLite database
        """
        self.db_path = db_path

    def insert_phase(self, item: PhaseQueueItem) -> None:
        """
        Insert a phase into the database.

        Args:
            item: PhaseQueueItem to insert

        Raises:
            Exception: If database operation fails
        """
        try:
            with get_connection(self.db_path) as conn:
                conn.execute(
                    """
                    INSERT INTO phase_queue (
                        queue_id, parent_issue, phase_number, status,
                        depends_on_phase, phase_data, created_at, updated_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        item.queue_id,
                        item.parent_issue,
                        item.phase_number,
                        item.status,
                        item.depends_on_phase,
                        json.dumps(item.phase_data),
                        item.created_at,
                        item.updated_at,
                    ),
                )
        except Exception as e:
            logger.error(f"[ERROR] Failed to insert phase: {str(e)}")
            raise

    def find_by_id(self, queue_id: str) -> PhaseQueueItem | None:
        """
        Find a phase by queue_id.

        Args:
            queue_id: Queue ID to find

        Returns:
            PhaseQueueItem or None if not found
        """
        try:
            with get_connection(self.db_path) as conn:
                cursor = conn.execute(
                    "SELECT * FROM phase_queue WHERE queue_id = ?",
                    (queue_id,)
                )
                row = cursor.fetchone()

            return PhaseQueueItem.from_db_row(row) if row else None

        except Exception as e:
            logger.error(f"[ERROR] Failed to find phase by ID: {str(e)}")
            raise

    def find_by_parent(self, parent_issue: int) -> list[PhaseQueueItem]:
        """
        Find all phases for a parent issue.

        Args:
            parent_issue: Parent GitHub issue number

        Returns:
            List of PhaseQueueItems ordered by phase number
        """
        try:
            with get_connection(self.db_path) as conn:
                cursor = conn.execute(
                    """
                    SELECT * FROM phase_queue
                    WHERE parent_issue = ?
                    ORDER BY phase_number ASC
                    """,
                    (parent_issue,)
                )
                rows = cursor.fetchall()

            return [PhaseQueueItem.from_db_row(row) for row in rows]

        except Exception as e:
            logger.error(f"[ERROR] Failed to find phases by parent: {str(e)}")
            raise

    def find_ready_phases(self) -> list[PhaseQueueItem]:
        """
        Find all phases that are ready for execution.

        Returns:
            List of PhaseQueueItems with status='ready' and no issue_number
        """
        try:
            with get_connection(self.db_path) as conn:
                cursor = conn.execute(
                    """
                    SELECT * FROM phase_queue
                    WHERE status = 'ready' AND issue_number IS NULL
                    ORDER BY parent_issue ASC, phase_number ASC
                    """
                )
                rows = cursor.fetchall()

            return [PhaseQueueItem.from_db_row(row) for row in rows]

        except Exception as e:
            logger.error(f"[ERROR] Failed to find ready phases: {str(e)}")
            raise

    def find_all(self) -> list[PhaseQueueItem]:
        """
        Find all phases in the queue.

        Returns:
            List of all PhaseQueueItems ordered by parent issue and phase number
        """
        try:
            with get_connection(self.db_path) as conn:
                cursor = conn.execute(
                    """
                    SELECT * FROM phase_queue
                    ORDER BY parent_issue ASC, phase_number ASC
                    """
                )
                rows = cursor.fetchall()

            return [PhaseQueueItem.from_db_row(row) for row in rows]

        except Exception as e:
            logger.error(f"[ERROR] Failed to find all phases: {str(e)}")
            raise

    def update_status(self, queue_id: str, status: str, adw_id: str | None = None) -> bool:
        """
        Update phase status and optionally set ADW ID.

        Args:
            queue_id: Queue ID to update
            status: New status
            adw_id: Optional ADW ID to associate with the phase

        Returns:
            True if updated, False if not found
        """
        try:
            with get_connection(self.db_path) as conn:
                if adw_id is not None:
                    cursor = conn.execute(
                        """
                        UPDATE phase_queue
                        SET status = ?, adw_id = ?, updated_at = ?
                        WHERE queue_id = ?
                        """,
                        (status, adw_id, datetime.now().isoformat(), queue_id),
                    )
                else:
                    cursor = conn.execute(
                        """
                        UPDATE phase_queue
                        SET status = ?, updated_at = ?
                        WHERE queue_id = ?
                        """,
                        (status, datetime.now().isoformat(), queue_id),
                    )
                return cursor.rowcount > 0

        except Exception as e:
            logger.error(f"[ERROR] Failed to update status: {str(e)}")
            raise

    def update_issue_number(self, queue_id: str, issue_number: int) -> bool:
        """
        Update GitHub issue number for a phase.

        Args:
            queue_id: Queue ID to update
            issue_number: GitHub issue number

        Returns:
            True if updated, False if not found
        """
        try:
            with get_connection(self.db_path) as conn:
                cursor = conn.execute(
                    """
                    UPDATE phase_queue
                    SET issue_number = ?, updated_at = ?
                    WHERE queue_id = ?
                    """,
                    (issue_number, datetime.now().isoformat(), queue_id),
                )
                return cursor.rowcount > 0

        except Exception as e:
            logger.error(f"[ERROR] Failed to update issue number: {str(e)}")
            raise

    def update_error_message(self, queue_id: str, error_message: str) -> bool:
        """
        Update error message for a phase.

        Args:
            queue_id: Queue ID to update
            error_message: Error message

        Returns:
            True if updated, False if not found
        """
        try:
            with get_connection(self.db_path) as conn:
                cursor = conn.execute(
                    """
                    UPDATE phase_queue
                    SET error_message = ?, updated_at = ?
                    WHERE queue_id = ?
                    """,
                    (error_message, datetime.now().isoformat(), queue_id),
                )
                return cursor.rowcount > 0

        except Exception as e:
            logger.error(f"[ERROR] Failed to update error message: {str(e)}")
            raise

    def delete_phase(self, queue_id: str) -> bool:
        """
        Delete a phase from the queue.

        Args:
            queue_id: Queue ID to delete

        Returns:
            True if deleted, False if not found
        """
        try:
            with get_connection(self.db_path) as conn:
                cursor = conn.execute(
                    "DELETE FROM phase_queue WHERE queue_id = ?",
                    (queue_id,)
                )
                return cursor.rowcount > 0

        except Exception as e:
            logger.error(f"[ERROR] Failed to delete phase: {str(e)}")
            raise
