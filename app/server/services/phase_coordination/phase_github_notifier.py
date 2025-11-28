"""
Phase GitHub Notifier

Posts GitHub comments on parent issues about phase status changes.
"""

import logging
import os

from utils.process_runner import ProcessRunner

from services.phase_queue_service import PhaseQueueService

logger = logging.getLogger(__name__)


class PhaseGitHubNotifier:
    """
    Posts GitHub comments about phase completions and failures.

    Notifies parent issues when child phases complete, fail, or
    transition to next phases.
    """

    def __init__(self, phase_queue_service: PhaseQueueService):
        """
        Initialize PhaseGitHubNotifier.

        Args:
            phase_queue_service: PhaseQueueService instance for querying phase state
        """
        self.phase_queue_service = phase_queue_service

    async def post_phase_comment(
        self,
        parent_issue: int,
        phase_number: int,
        child_issue: int,
        status: str,
        error_message: str | None = None
    ):
        """
        Post a comment to the parent GitHub issue about phase completion/failure.

        Args:
            parent_issue: Parent GitHub issue number
            phase_number: Phase number that completed/failed
            child_issue: Child issue number for this phase
            status: Phase status ('completed' or 'failed')
            error_message: Error message (for failed status)
        """
        try:
            # Format comment based on status
            if status == "completed":
                comment = self._format_completion_comment(
                    parent_issue, phase_number, child_issue
                )
            elif status == "failed":
                comment = self._format_failure_comment(
                    phase_number, child_issue, error_message
                )
            else:
                logger.warning(f"[WARNING] Unknown status '{status}' for GitHub comment")
                return

            # Post comment using gh CLI
            result = ProcessRunner.run_gh_command([
                "issue", "comment", str(parent_issue),
                "--body", comment
            ])

            if result.success:
                logger.info(
                    f"[SUCCESS] Posted GitHub comment on issue #{parent_issue} "
                    f"for Phase {phase_number} ({status})"
                )
            else:
                logger.error(
                    f"[ERROR] Failed to post GitHub comment: {result.stderr}"
                )

        except Exception as e:
            logger.error(
                f"[ERROR] Failed to post GitHub comment on issue #{parent_issue}: {str(e)}"
            )

    def _format_completion_comment(
        self, parent_issue: int, phase_number: int, child_issue: int
    ) -> str:
        """
        Format completion comment for a successful phase.

        Args:
            parent_issue: Parent issue number
            phase_number: Phase that completed
            child_issue: Child issue number

        Returns:
            Formatted markdown comment
        """
        comment = f"""## Phase {phase_number} Completed ✅

**Issue:** #{child_issue}
**Status:** Completed

Phase {phase_number} has completed successfully."""

        # Check if there are more phases
        all_phases = self.phase_queue_service.get_queue_by_parent(parent_issue)
        next_phase = next((p for p in all_phases if p.phase_number == phase_number + 1), None)

        if next_phase:
            comment += f" Moving to Phase {phase_number + 1}."
        else:
            comment += " All phases complete!"

        repo = os.environ.get('GITHUB_REPO', 'owner/repo')
        comment += f"\n\n[View Phase {phase_number} Details](https://github.com/{repo}/issues/{child_issue})"

        return comment

    def _format_failure_comment(
        self, phase_number: int, child_issue: int, error_message: str | None
    ) -> str:
        """
        Format failure comment for a failed phase.

        Args:
            phase_number: Phase that failed
            child_issue: Child issue number
            error_message: Error message

        Returns:
            Formatted markdown comment
        """
        repo = os.environ.get('GITHUB_REPO', 'owner/repo')

        return f"""## Phase {phase_number} Failed ❌

**Issue:** #{child_issue}
**Status:** Failed
**Error:** {error_message or 'Unknown error'}

Phase {phase_number} has failed. Subsequent phases have been blocked.

[View Phase {phase_number} Details](https://github.com/{repo}/issues/{child_issue})"""
