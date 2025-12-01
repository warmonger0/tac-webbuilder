"""
PhaseQueueRepository

Handles all database operations for the phase queue.
Separates database access from business logic (Repository Pattern).
"""

import json
import logging
from datetime import datetime

from database import get_database_adapter
from models.phase_queue_item import PhaseQueueItem

logger = logging.getLogger(__name__)


class PhaseQueueRepository:
    """Repository for phase queue database operations"""

    def __init__(self):
        """
        Initialize repository.

        Uses database adapter from factory (SQLite or PostgreSQL based on DB_TYPE env var).
        """
        self.adapter = get_database_adapter()

    def insert_phase(self, item: PhaseQueueItem) -> None:
        """
        Insert a phase into the database.

        Automatically sets:
        - queue_position (based on ROWID for FIFO ordering)
        - priority (from item, default 50)
        - ready_timestamp (if status is 'ready')

        Args:
            item: PhaseQueueItem to insert

        Raises:
            Exception: If database operation fails
        """
        try:
            with self.adapter.get_connection() as conn:
                # Get next queue_position (max + 1)
                cursor = conn.execute("SELECT COALESCE(MAX(queue_position), 0) + 1 FROM phase_queue")
                next_position = cursor.fetchone()[0]

                ph = self.adapter.placeholder()
                conn.execute(
                    f"""
                    INSERT INTO phase_queue (
                        queue_id, parent_issue, phase_number, status,
                        depends_on_phase, phase_data, created_at, updated_at,
                        priority, queue_position, ready_timestamp
                    )
                    VALUES ({ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph})
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
                        getattr(item, 'priority', 50),  # Default to normal priority
                        next_position,
                        item.created_at if item.status == 'ready' else None,
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
            with self.adapter.get_connection() as conn:
                ph = self.adapter.placeholder()
                cursor = conn.execute(
                    f"SELECT * FROM phase_queue WHERE queue_id = {ph}",
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
            with self.adapter.get_connection() as conn:
                ph = self.adapter.placeholder()
                cursor = conn.execute(
                    f"""
                    SELECT * FROM phase_queue
                    WHERE parent_issue = {ph}
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
            with self.adapter.get_connection() as conn:
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
            with self.adapter.get_connection() as conn:
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

        Also sets timestamps:
        - ready_timestamp when transitioning to 'ready'
        - started_timestamp when transitioning to 'running'

        Args:
            queue_id: Queue ID to update
            status: New status
            adw_id: Optional ADW ID to associate with the phase

        Returns:
            True if updated, False if not found
        """
        try:
            with self.adapter.get_connection() as conn:
                ph = self.adapter.placeholder()
                now_fn = self.adapter.now_function()

                # Build dynamic SQL based on status transitions
                updates = [f"status = {ph}", f"updated_at = {ph}"]
                params = [status, datetime.now().isoformat()]

                if adw_id is not None:
                    updates.append(f"adw_id = {ph}")
                    params.append(adw_id)

                if status == "ready":
                    updates.append(f"ready_timestamp = {now_fn}")
                elif status == "running":
                    updates.append(f"started_timestamp = {now_fn}")

                params.append(queue_id)

                cursor = conn.execute(
                    f"""
                    UPDATE phase_queue
                    SET {', '.join(updates)}
                    WHERE queue_id = {ph}
                    """,
                    tuple(params),
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
            with self.adapter.get_connection() as conn:
                ph = self.adapter.placeholder()
                cursor = conn.execute(
                    f"""
                    UPDATE phase_queue
                    SET issue_number = {ph}, updated_at = {ph}
                    WHERE queue_id = {ph}
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
            with self.adapter.get_connection() as conn:
                ph = self.adapter.placeholder()
                cursor = conn.execute(
                    f"""
                    UPDATE phase_queue
                    SET error_message = {ph}, updated_at = {ph}
                    WHERE queue_id = {ph}
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
            with self.adapter.get_connection() as conn:
                ph = self.adapter.placeholder()
                cursor = conn.execute(
                    f"DELETE FROM phase_queue WHERE queue_id = {ph}",
                    (queue_id,)
                )
                return cursor.rowcount > 0

        except Exception as e:
            logger.error(f"[ERROR] Failed to delete phase: {str(e)}")
            raise

    def get_config_value(self, config_key: str) -> str | None:
        """
        Get a configuration value from queue_config table.

        Args:
            config_key: Configuration key to retrieve

        Returns:
            Configuration value or None if not found
        """
        try:
            with self.adapter.get_connection() as conn:
                ph = self.adapter.placeholder()
                cursor = conn.execute(
                    f"SELECT config_value FROM queue_config WHERE config_key = {ph}",
                    (config_key,)
                )
                row = cursor.fetchone()
                return row[0] if row else None

        except Exception as e:
            logger.error(f"[ERROR] Failed to get config value: {str(e)}")
            raise

    def set_config_value(self, config_key: str, config_value: str) -> None:
        """
        Set a configuration value in queue_config table.

        Args:
            config_key: Configuration key to set
            config_value: Value to set

        Raises:
            Exception: If database operation fails
        """
        try:
            with self.adapter.get_connection() as conn:
                ph = self.adapter.placeholder()
                conn.execute(
                    f"""
                    INSERT INTO queue_config (config_key, config_value, updated_at)
                    VALUES ({ph}, {ph}, {ph})
                    ON CONFLICT(config_key) DO UPDATE SET
                        config_value = excluded.config_value,
                        updated_at = excluded.updated_at
                    """,
                    (config_key, config_value, datetime.now().isoformat()),
                )

        except Exception as e:
            logger.error(f"[ERROR] Failed to set config value: {str(e)}")
            raise
