"""
PhaseQueue Service

Manages the phase queue for multi-phase workflow execution.
Handles enqueueing phases, dependency tracking, and sequential execution coordination.
"""

import json
import logging
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from utils.db_connection import get_connection

logger = logging.getLogger(__name__)


class PhaseQueueItem:
    """Represents a single phase in the queue"""

    def __init__(
        self,
        queue_id: str,
        parent_issue: int,
        phase_number: int,
        issue_number: Optional[int] = None,
        status: str = "queued",
        depends_on_phase: Optional[int] = None,
        phase_data: Optional[Dict[str, Any]] = None,
        created_at: Optional[str] = None,
        updated_at: Optional[str] = None,
        error_message: Optional[str] = None,
    ):
        self.queue_id = queue_id
        self.parent_issue = parent_issue
        self.phase_number = phase_number
        self.issue_number = issue_number
        self.status = status
        self.depends_on_phase = depends_on_phase
        self.phase_data = phase_data or {}
        self.created_at = created_at or datetime.now().isoformat()
        self.updated_at = updated_at or datetime.now().isoformat()
        self.error_message = error_message

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "queue_id": self.queue_id,
            "parent_issue": self.parent_issue,
            "phase_number": self.phase_number,
            "issue_number": self.issue_number,
            "status": self.status,
            "depends_on_phase": self.depends_on_phase,
            "phase_data": self.phase_data,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "error_message": self.error_message,
        }

    @classmethod
    def from_db_row(cls, row) -> "PhaseQueueItem":
        """Create PhaseQueueItem from database row"""
        phase_data = json.loads(row["phase_data"]) if row["phase_data"] else {}
        return cls(
            queue_id=row["queue_id"],
            parent_issue=row["parent_issue"],
            phase_number=row["phase_number"],
            issue_number=row["issue_number"],
            status=row["status"],
            depends_on_phase=row["depends_on_phase"],
            phase_data=phase_data,
            created_at=row["created_at"],
            updated_at=row["updated_at"],
            error_message=row["error_message"],
        )


class PhaseQueueService:
    """
    Service for managing multi-phase workflow queue.

    Responsibilities:
    - Enqueue phases with dependency tracking
    - Mark phases as ready/running/completed/blocked/failed
    - Find next ready phase for execution
    - Query queue state
    """

    def __init__(self, db_path: str = "db/database.db"):
        """
        Initialize PhaseQueueService.

        Args:
            db_path: Path to SQLite database (default: db/database.db)
        """
        self.db_path = db_path
        logger.info(f"[INIT] PhaseQueueService initialized (db: {db_path})")

    def enqueue(
        self,
        parent_issue: int,
        phase_number: int,
        phase_data: Dict[str, Any],
        depends_on_phase: Optional[int] = None,
    ) -> str:
        """
        Enqueue a phase for execution.

        Args:
            parent_issue: Parent GitHub issue number
            phase_number: Phase number (1, 2, 3, ...)
            phase_data: Phase metadata {title, content, externalDocs}
            depends_on_phase: Phase number this phase depends on (None for Phase 1)

        Returns:
            queue_id: Unique identifier for this queue entry

        Raises:
            Exception: If database operation fails
        """
        queue_id = str(uuid.uuid4())
        status = "ready" if phase_number == 1 else "queued"  # Phase 1 is ready immediately

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
                        queue_id,
                        parent_issue,
                        phase_number,
                        status,
                        depends_on_phase,
                        json.dumps(phase_data),
                        datetime.now().isoformat(),
                        datetime.now().isoformat(),
                    ),
                )

            logger.info(
                f"[SUCCESS] Enqueued Phase {phase_number} for issue #{parent_issue} "
                f"(queue_id: {queue_id}, status: {status})"
            )
            return queue_id

        except Exception as e:
            logger.error(f"[ERROR] Failed to enqueue phase: {str(e)}")
            raise

    def dequeue(self, queue_id: str) -> bool:
        """
        Remove a phase from the queue.

        Args:
            queue_id: Queue ID to remove

        Returns:
            bool: True if deleted, False if not found

        Raises:
            Exception: If database operation fails
        """
        try:
            with get_connection(self.db_path) as conn:
                cursor = conn.execute(
                    "DELETE FROM phase_queue WHERE queue_id = ?",
                    (queue_id,)
                )
                deleted = cursor.rowcount > 0

            if deleted:
                logger.info(f"[SUCCESS] Dequeued phase (queue_id: {queue_id})")
            else:
                logger.warning(f"[WARNING] Queue ID not found: {queue_id}")

            return deleted

        except Exception as e:
            logger.error(f"[ERROR] Failed to dequeue phase: {str(e)}")
            raise

    def get_next_ready(self) -> Optional[PhaseQueueItem]:
        """
        Get the next phase that is ready for execution.

        A phase is ready if:
        - Status is 'ready'
        - No issue_number assigned yet (not started)

        Returns:
            PhaseQueueItem or None if no phases are ready

        Raises:
            Exception: If database operation fails
        """
        try:
            with get_connection(self.db_path) as conn:
                cursor = conn.execute(
                    """
                    SELECT * FROM phase_queue
                    WHERE status = 'ready' AND issue_number IS NULL
                    ORDER BY parent_issue ASC, phase_number ASC
                    LIMIT 1
                    """
                )
                row = cursor.fetchone()

            if row:
                item = PhaseQueueItem.from_db_row(row)
                logger.info(
                    f"[SUCCESS] Found ready phase: Phase {item.phase_number} "
                    f"for issue #{item.parent_issue}"
                )
                return item
            else:
                logger.debug("[DEBUG] No ready phases in queue")
                return None

        except Exception as e:
            logger.error(f"[ERROR] Failed to get next ready phase: {str(e)}")
            raise

    def mark_phase_complete(self, queue_id: str) -> bool:
        """
        Mark a phase as completed and check for dependent phases.

        When a phase completes:
        1. Update its status to 'completed'
        2. Find phases that depend on this phase
        3. Mark dependent phases as 'ready' if their dependencies are met

        Args:
            queue_id: Queue ID to mark complete

        Returns:
            bool: True if updated, False if not found

        Raises:
            Exception: If database operation fails
        """
        try:
            with get_connection(self.db_path) as conn:
                # Get the completed phase info
                cursor = conn.execute(
                    "SELECT parent_issue, phase_number FROM phase_queue WHERE queue_id = ?",
                    (queue_id,)
                )
                row = cursor.fetchone()

                if not row:
                    logger.warning(f"[WARNING] Queue ID not found: {queue_id}")
                    return False

                parent_issue = row["parent_issue"]
                completed_phase_number = row["phase_number"]

                # Mark this phase as completed
                conn.execute(
                    """
                    UPDATE phase_queue
                    SET status = 'completed', updated_at = ?
                    WHERE queue_id = ?
                    """,
                    (datetime.now().isoformat(), queue_id),
                )

                # Find dependent phases (next phase in sequence)
                next_phase_number = completed_phase_number + 1
                cursor = conn.execute(
                    """
                    SELECT queue_id FROM phase_queue
                    WHERE parent_issue = ? AND phase_number = ? AND status = 'queued'
                    """,
                    (parent_issue, next_phase_number),
                )
                dependent_rows = cursor.fetchall()

                # Mark dependent phases as ready
                for dep_row in dependent_rows:
                    conn.execute(
                        """
                        UPDATE phase_queue
                        SET status = 'ready', updated_at = ?
                        WHERE queue_id = ?
                        """,
                        (datetime.now().isoformat(), dep_row["queue_id"]),
                    )
                    logger.info(
                        f"[SUCCESS] Phase {next_phase_number} marked as ready "
                        f"(parent: #{parent_issue})"
                    )

            logger.info(
                f"[SUCCESS] Phase {completed_phase_number} marked complete "
                f"(parent: #{parent_issue}, queue_id: {queue_id})"
            )
            return True

        except Exception as e:
            logger.error(f"[ERROR] Failed to mark phase complete: {str(e)}")
            raise

    def mark_phase_blocked(self, queue_id: str, reason: str) -> bool:
        """
        Mark a phase as blocked due to dependency failure.

        Args:
            queue_id: Queue ID to block
            reason: Reason for blocking (error message)

        Returns:
            bool: True if updated, False if not found

        Raises:
            Exception: If database operation fails
        """
        try:
            with get_connection(self.db_path) as conn:
                cursor = conn.execute(
                    """
                    UPDATE phase_queue
                    SET status = 'blocked', error_message = ?, updated_at = ?
                    WHERE queue_id = ?
                    """,
                    (reason, datetime.now().isoformat(), queue_id),
                )
                updated = cursor.rowcount > 0

            if updated:
                logger.info(f"[SUCCESS] Phase blocked (queue_id: {queue_id}, reason: {reason})")
            else:
                logger.warning(f"[WARNING] Queue ID not found: {queue_id}")

            return updated

        except Exception as e:
            logger.error(f"[ERROR] Failed to mark phase blocked: {str(e)}")
            raise

    def mark_phase_failed(self, queue_id: str, error_message: str) -> List[str]:
        """
        Mark a phase as failed and block all dependent phases.

        Args:
            queue_id: Queue ID that failed
            error_message: Error message

        Returns:
            List[str]: List of blocked queue IDs

        Raises:
            Exception: If database operation fails
        """
        try:
            with get_connection(self.db_path) as conn:
                # Get the failed phase info
                cursor = conn.execute(
                    "SELECT parent_issue, phase_number FROM phase_queue WHERE queue_id = ?",
                    (queue_id,)
                )
                row = cursor.fetchone()

                if not row:
                    logger.warning(f"[WARNING] Queue ID not found: {queue_id}")
                    return []

                parent_issue = row["parent_issue"]
                failed_phase_number = row["phase_number"]

                # Mark this phase as failed
                conn.execute(
                    """
                    UPDATE phase_queue
                    SET status = 'failed', error_message = ?, updated_at = ?
                    WHERE queue_id = ?
                    """,
                    (error_message, datetime.now().isoformat(), queue_id),
                )

                # Block all subsequent phases
                cursor = conn.execute(
                    """
                    SELECT queue_id FROM phase_queue
                    WHERE parent_issue = ? AND phase_number > ? AND status IN ('queued', 'ready')
                    """,
                    (parent_issue, failed_phase_number),
                )
                blocked_rows = cursor.fetchall()

                blocked_ids = []
                block_reason = f"Phase {failed_phase_number} failed: {error_message}"
                for blocked_row in blocked_rows:
                    blocked_id = blocked_row["queue_id"]
                    conn.execute(
                        """
                        UPDATE phase_queue
                        SET status = 'blocked', error_message = ?, updated_at = ?
                        WHERE queue_id = ?
                        """,
                        (block_reason, datetime.now().isoformat(), blocked_id),
                    )
                    blocked_ids.append(blocked_id)

            logger.info(
                f"[SUCCESS] Phase {failed_phase_number} marked failed, "
                f"blocked {len(blocked_ids)} dependent phases "
                f"(parent: #{parent_issue})"
            )
            return blocked_ids

        except Exception as e:
            logger.error(f"[ERROR] Failed to mark phase failed: {str(e)}")
            raise

    def get_queue_by_parent(self, parent_issue: int) -> List[PhaseQueueItem]:
        """
        Get all phases for a parent issue.

        Args:
            parent_issue: Parent GitHub issue number

        Returns:
            List of PhaseQueueItems ordered by phase number

        Raises:
            Exception: If database operation fails
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

            items = [PhaseQueueItem.from_db_row(row) for row in rows]
            logger.info(f"[SUCCESS] Retrieved {len(items)} phases for issue #{parent_issue}")
            return items

        except Exception as e:
            logger.error(f"[ERROR] Failed to get queue by parent: {str(e)}")
            raise

    def get_all_queued(self) -> List[PhaseQueueItem]:
        """
        Get all phases in the queue (all statuses).

        Returns:
            List of PhaseQueueItems ordered by parent issue and phase number

        Raises:
            Exception: If database operation fails
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

            items = [PhaseQueueItem.from_db_row(row) for row in rows]
            logger.info(f"[SUCCESS] Retrieved {len(items)} phases from queue")
            return items

        except Exception as e:
            logger.error(f"[ERROR] Failed to get all queued phases: {str(e)}")
            raise

    def update_issue_number(self, queue_id: str, issue_number: int) -> bool:
        """
        Update the GitHub issue number for a phase.

        Called after creating the child GitHub issue.

        Args:
            queue_id: Queue ID to update
            issue_number: GitHub issue number

        Returns:
            bool: True if updated, False if not found

        Raises:
            Exception: If database operation fails
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
                updated = cursor.rowcount > 0

            if updated:
                logger.info(f"[SUCCESS] Updated issue number: {issue_number} (queue_id: {queue_id})")
            else:
                logger.warning(f"[WARNING] Queue ID not found: {queue_id}")

            return updated

        except Exception as e:
            logger.error(f"[ERROR] Failed to update issue number: {str(e)}")
            raise

    def update_status(self, queue_id: str, status: str) -> bool:
        """
        Update the status of a phase.

        Args:
            queue_id: Queue ID to update
            status: New status (queued, ready, running, completed, blocked, failed)

        Returns:
            bool: True if updated, False if not found

        Raises:
            Exception: If database operation fails
        """
        valid_statuses = ["queued", "ready", "running", "completed", "blocked", "failed"]
        if status not in valid_statuses:
            raise ValueError(f"Invalid status: {status}. Must be one of {valid_statuses}")

        try:
            with get_connection(self.db_path) as conn:
                cursor = conn.execute(
                    """
                    UPDATE phase_queue
                    SET status = ?, updated_at = ?
                    WHERE queue_id = ?
                    """,
                    (status, datetime.now().isoformat(), queue_id),
                )
                updated = cursor.rowcount > 0

            if updated:
                logger.info(f"[SUCCESS] Updated status to '{status}' (queue_id: {queue_id})")
            else:
                logger.warning(f"[WARNING] Queue ID not found: {queue_id}")

            return updated

        except Exception as e:
            logger.error(f"[ERROR] Failed to update status: {str(e)}")
            raise
