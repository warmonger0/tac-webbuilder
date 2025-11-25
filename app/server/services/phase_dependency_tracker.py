"""
PhaseDependencyTracker

Handles phase dependency logic for multi-phase workflow execution.
Manages phase completion triggering and failure blocking.
"""

import logging

from repositories.phase_queue_repository import PhaseQueueRepository

logger = logging.getLogger(__name__)


class PhaseDependencyTracker:
    """Handle phase dependencies and triggering"""

    def __init__(self, repository: PhaseQueueRepository):
        """
        Initialize tracker.

        Args:
            repository: PhaseQueueRepository instance for database access
        """
        self.repository = repository

    def trigger_next_phase(self, completed_queue_id: str) -> str | None:
        """
        Mark phase as completed and trigger next phase in sequence.

        Args:
            completed_queue_id: Queue ID of completed phase

        Returns:
            queue_id of next phase (if triggered), or None

        Raises:
            Exception: If database operation fails
        """
        # Get completed phase info
        completed_phase = self.repository.find_by_id(completed_queue_id)
        if not completed_phase:
            logger.warning(f"[WARNING] Queue ID not found: {completed_queue_id}")
            return None

        parent_issue = completed_phase.parent_issue
        completed_phase_number = completed_phase.phase_number

        # Mark this phase as completed
        self.repository.update_status(completed_queue_id, "completed")
        logger.info(
            f"[SUCCESS] Phase {completed_phase_number} marked complete "
            f"(parent: #{parent_issue}, queue_id: {completed_queue_id})"
        )

        # Find next phase in sequence
        next_phase_number = completed_phase_number + 1
        all_phases = self.repository.find_by_parent(parent_issue)

        next_phase = None
        for phase in all_phases:
            if phase.phase_number == next_phase_number and phase.status == "queued":
                next_phase = phase
                break

        if next_phase:
            # Mark next phase as ready
            self.repository.update_status(next_phase.queue_id, "ready")
            logger.info(
                f"[SUCCESS] Phase {next_phase_number} marked as ready "
                f"(parent: #{parent_issue})"
            )
            return next_phase.queue_id

        return None

    def block_dependent_phases(self, failed_queue_id: str, error_message: str) -> list[str]:
        """
        Mark phase as failed and block all dependent phases.

        Args:
            failed_queue_id: Queue ID that failed
            error_message: Error message

        Returns:
            List of blocked queue IDs

        Raises:
            Exception: If database operation fails
        """
        # Get failed phase info
        failed_phase = self.repository.find_by_id(failed_queue_id)
        if not failed_phase:
            logger.warning(f"[WARNING] Queue ID not found: {failed_queue_id}")
            return []

        parent_issue = failed_phase.parent_issue
        failed_phase_number = failed_phase.phase_number

        # Mark this phase as failed
        self.repository.update_status(failed_queue_id, "failed")
        self.repository.update_error_message(failed_queue_id, error_message)
        logger.info(
            f"[SUCCESS] Phase {failed_phase_number} marked failed "
            f"(parent: #{parent_issue})"
        )

        # Find and block all subsequent phases
        all_phases = self.repository.find_by_parent(parent_issue)
        blocked_ids = []
        block_reason = f"Phase {failed_phase_number} failed: {error_message}"

        for phase in all_phases:
            if phase.phase_number > failed_phase_number and phase.status in ["queued", "ready"]:
                self.repository.update_status(phase.queue_id, "blocked")
                self.repository.update_error_message(phase.queue_id, block_reason)
                blocked_ids.append(phase.queue_id)
                logger.info(
                    f"[SUCCESS] Phase {phase.phase_number} blocked "
                    f"(parent: #{parent_issue})"
                )

        logger.info(
            f"[SUCCESS] Blocked {len(blocked_ids)} dependent phases "
            f"(parent: #{parent_issue})"
        )
        return blocked_ids

    def mark_phase_blocked(self, queue_id: str, reason: str) -> bool:
        """
        Mark a phase as blocked due to dependency failure.

        Args:
            queue_id: Queue ID to block
            reason: Reason for blocking

        Returns:
            True if updated, False if not found

        Raises:
            Exception: If database operation fails
        """
        updated = self.repository.update_status(queue_id, "blocked")
        if updated:
            self.repository.update_error_message(queue_id, reason)
            logger.info(f"[SUCCESS] Phase blocked (queue_id: {queue_id}, reason: {reason})")
        else:
            logger.warning(f"[WARNING] Queue ID not found: {queue_id}")

        return updated
