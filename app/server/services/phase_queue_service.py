"""
PhaseQueue Service

Manages the phase queue for multi-phase workflow execution.
Orchestrates between repository (database) and dependency tracker (business logic).
"""

import logging
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from models.phase_queue_item import PhaseQueueItem
from repositories.phase_queue_repository import PhaseQueueRepository
from services.phase_dependency_tracker import PhaseDependencyTracker

logger = logging.getLogger(__name__)


class PhaseQueueService:
    """
    Service for managing multi-phase workflow queue.

    Orchestrates between:
    - PhaseQueueRepository (database operations)
    - PhaseDependencyTracker (dependency logic)
    """

    def __init__(
        self,
        repository: Optional[PhaseQueueRepository] = None,
        dependency_tracker: Optional[PhaseDependencyTracker] = None,
        db_path: str = "db/database.db"
    ):
        """
        Initialize PhaseQueueService.

        Args:
            repository: PhaseQueueRepository instance (or creates default)
            dependency_tracker: PhaseDependencyTracker instance (or creates default)
            db_path: Path to SQLite database (used if repository not provided)
        """
        self.repository = repository or PhaseQueueRepository(db_path)
        self.dependency_tracker = dependency_tracker or PhaseDependencyTracker(self.repository)
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

        item = PhaseQueueItem(
            queue_id=queue_id,
            parent_issue=parent_issue,
            phase_number=phase_number,
            status=status,
            depends_on_phase=depends_on_phase,
            phase_data=phase_data,
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat(),
        )

        try:
            self.repository.insert_phase(item)
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
            deleted = self.repository.delete_phase(queue_id)

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
            ready_phases = self.repository.find_ready_phases()

            if ready_phases:
                item = ready_phases[0]  # Get first ready phase
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
        Mark a phase as completed and trigger next phase.

        Uses PhaseDependencyTracker to:
        1. Mark phase as completed
        2. Trigger next phase (mark as ready)

        Args:
            queue_id: Queue ID to mark complete

        Returns:
            bool: True if next phase was triggered, False otherwise

        Raises:
            Exception: If database operation fails
        """
        try:
            next_queue_id = self.dependency_tracker.trigger_next_phase(queue_id)
            return next_queue_id is not None

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
            return self.dependency_tracker.mark_phase_blocked(queue_id, reason)

        except Exception as e:
            logger.error(f"[ERROR] Failed to mark phase blocked: {str(e)}")
            raise

    def mark_phase_failed(self, queue_id: str, error_message: str) -> List[str]:
        """
        Mark a phase as failed and block all dependent phases.

        Uses PhaseDependencyTracker to:
        1. Mark phase as failed
        2. Block all subsequent phases

        Args:
            queue_id: Queue ID that failed
            error_message: Error message

        Returns:
            List[str]: List of blocked queue IDs

        Raises:
            Exception: If database operation fails
        """
        try:
            return self.dependency_tracker.block_dependent_phases(queue_id, error_message)

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
            items = self.repository.find_by_parent(parent_issue)
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
            items = self.repository.find_all()
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
            updated = self.repository.update_issue_number(queue_id, issue_number)

            if updated:
                logger.info(f"[SUCCESS] Updated issue number: {issue_number} (queue_id: {queue_id})")
            else:
                logger.warning(f"[WARNING] Queue ID not found: {queue_id}")

            return updated

        except Exception as e:
            logger.error(f"[ERROR] Failed to update issue number: {str(e)}")
            raise

    def update_status(self, queue_id: str, status: str, adw_id: str | None = None) -> bool:
        """
        Update the status of a phase and optionally set the ADW ID.

        Args:
            queue_id: Queue ID to update
            status: New status (queued, ready, running, completed, blocked, failed)
            adw_id: Optional ADW ID to associate with the phase

        Returns:
            bool: True if updated, False if not found

        Raises:
            Exception: If database operation fails
        """
        valid_statuses = ["queued", "ready", "running", "completed", "blocked", "failed"]
        if status not in valid_statuses:
            raise ValueError(f"Invalid status: {status}. Must be one of {valid_statuses}")

        try:
            updated = self.repository.update_status(queue_id, status, adw_id)

            if updated:
                logger.info(f"[SUCCESS] Updated status to '{status}' (queue_id: {queue_id}, adw_id: {adw_id})")
            else:
                logger.warning(f"[WARNING] Queue ID not found: {queue_id}")

            return updated

        except Exception as e:
            logger.error(f"[ERROR] Failed to update status: {str(e)}")
            raise

    def is_paused(self) -> bool:
        """
        Check if automatic phase execution is paused.

        Returns:
            bool: True if paused, False if automatic execution enabled

        Raises:
            Exception: If database operation fails
        """
        try:
            return self.repository.get_config_value("queue_paused") == "true"

        except Exception as e:
            logger.error(f"[ERROR] Failed to check pause state: {str(e)}")
            raise

    def set_paused(self, paused: bool) -> None:
        """
        Set automatic phase execution pause state.

        When paused, workflows will not automatically proceed to the next phase.
        When resumed, workflows will kick off the next phase on completion.

        Args:
            paused: True to pause, False to resume

        Raises:
            Exception: If database operation fails
        """
        try:
            self.repository.set_config_value("queue_paused", "true" if paused else "false")
            logger.info(f"[CONFIG] Queue {'paused' if paused else 'resumed'}")

        except Exception as e:
            logger.error(f"[ERROR] Failed to set pause state: {str(e)}")
            raise
