"""
PhaseCoordinator Service

Background service that monitors workflow completions and coordinates
sequential execution of multi-phase workflows.

Responsibilities:
- Poll workflow_history for completed/failed workflows
- Match workflows to phases in queue by issue_number
- Mark phases complete/failed and trigger next phase
- Broadcast WebSocket events for real-time updates
- Post GitHub comments on phase transitions
"""

import asyncio
import contextlib
import logging
from datetime import datetime

from utils.db_connection import get_connection

from services.phase_queue_service import PhaseQueueService

from .phase_github_notifier import PhaseGitHubNotifier
from .workflow_completion_detector import WorkflowCompletionDetector

logger = logging.getLogger(__name__)


class PhaseCoordinator:
    """
    Coordinates sequential execution of multi-phase workflows.

    Polls workflow_history every N seconds to detect completions,
    updates phase queue, and triggers next phases.
    """

    def __init__(
        self,
        phase_queue_service: PhaseQueueService,
        workflow_db_path: str = "db/workflow_history.db",
        poll_interval: float = 10.0,
        websocket_manager = None,
        github_poster = None
    ):
        """
        Initialize PhaseCoordinator.

        Args:
            phase_queue_service: PhaseQueueService instance
            workflow_db_path: Path to workflow_history database
            poll_interval: Polling interval in seconds (default: 10.0)
            websocket_manager: WebSocket manager for real-time updates (optional)
            github_poster: GitHubPoster for just-in-time issue creation (optional)
        """
        self.phase_queue_service = phase_queue_service
        self.workflow_db_path = workflow_db_path
        self.poll_interval = poll_interval
        self.websocket_manager = websocket_manager
        self.github_poster = github_poster
        self._is_running = False
        self._task: asyncio.Task | None = None
        self._processed_workflows = set()  # Track processed workflow IDs

        # Initialize helper components
        self.detector = WorkflowCompletionDetector(workflow_db_path)
        self.notifier = PhaseGitHubNotifier(phase_queue_service)

        logger.info(
            f"[INIT] PhaseCoordinator initialized "
            f"(poll_interval={poll_interval}s, workflow_db={workflow_db_path})"
        )

    async def start(self):
        """Start the background polling task"""
        if self._is_running:
            logger.warning("[WARNING] PhaseCoordinator already running")
            return

        self._is_running = True
        self._task = asyncio.create_task(self._poll_loop())
        logger.info("[START] PhaseCoordinator background task started")

    async def stop(self):
        """Stop the background polling task"""
        if not self._is_running:
            return

        self._is_running = False
        if self._task:
            self._task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._task
        logger.info("[STOP] PhaseCoordinator background task stopped")

    async def _poll_loop(self):
        """Main polling loop - runs continuously"""
        logger.info("[POLL] PhaseCoordinator polling loop started")

        while self._is_running:
            try:
                await self._check_workflow_completions()
            except Exception as e:
                logger.error(f"[ERROR] PhaseCoordinator polling error: {str(e)}")

            # Wait for next poll interval
            await asyncio.sleep(self.poll_interval)

    async def _check_workflow_completions(self):
        """
        Check for completed/failed workflows and update phase queue.

        For each workflow with status='completed' or 'failed':
        1. Find corresponding phase by issue_number
        2. Mark phase complete/failed
        3. Trigger next phase if applicable
        4. Broadcast WebSocket event
        """
        try:
            # Get all running phases from queue
            running_phases = self._get_running_phases()

            if not running_phases:
                # No running phases to monitor
                return

            # Check each running phase's workflow status
            for phase_row in running_phases:
                await self._process_phase_completion(phase_row)

        except Exception as e:
            logger.error(f"[ERROR] Failed to check workflow completions: {str(e)}")

    def _get_running_phases(self):
        """
        Get all running phases from queue.

        Returns:
            List of phase rows with queue_id, issue_number, parent_issue, phase_number
        """
        with get_connection(self.phase_queue_service.repository.db_path) as conn:
            cursor = conn.execute(
                """
                SELECT queue_id, issue_number, parent_issue, phase_number
                FROM phase_queue
                WHERE status = 'running' AND issue_number IS NOT NULL
                """
            )
            return cursor.fetchall()

    async def _process_phase_completion(self, phase_row):
        """
        Process completion or failure of a single phase.

        Args:
            phase_row: Database row with queue_id, issue_number, parent_issue, phase_number
        """
        queue_id = phase_row["queue_id"]
        issue_number = phase_row["issue_number"]
        parent_issue = phase_row["parent_issue"]
        phase_number = phase_row["phase_number"]

        # Check workflow_history for this issue
        workflow_status = self.detector.get_workflow_status(issue_number)

        if workflow_status == "completed":
            await self._handle_phase_success(
                queue_id, phase_number, issue_number, parent_issue
            )

        elif workflow_status == "failed":
            error_msg = self.detector.get_workflow_error(issue_number)
            await self._handle_phase_failure(
                queue_id, phase_number, issue_number, parent_issue, error_msg
            )

    async def _handle_phase_success(
        self, queue_id: str, phase_number: int, issue_number: int, parent_issue: int
    ):
        """
        Handle successful phase completion.

        Args:
            queue_id: Queue ID
            phase_number: Phase number
            issue_number: Child issue number
            parent_issue: Parent issue number
        """
        logger.info(
            f"[SUCCESS] Phase {phase_number} completed "
            f"(issue #{issue_number}, parent #{parent_issue})"
        )

        # Check if queue is paused
        is_paused = self.phase_queue_service.is_paused()

        if is_paused:
            # Queue is paused - mark phase complete but don't trigger next phase
            logger.info(
                f"[PAUSED] Queue is paused. Phase {phase_number} marked complete, "
                f"but next phase will not auto-trigger"
            )
            # Just update status to completed without triggering next phase
            self.phase_queue_service.update_status(queue_id, "completed")
            next_phase_triggered = False
        else:
            # Queue is running - mark phase complete and trigger next phase automatically
            next_phase_triggered = self.phase_queue_service.mark_phase_complete(queue_id)

            # If next phase was triggered, create its GitHub issue just-in-time
            if next_phase_triggered and self.github_poster:
                await self._create_next_phase_issue(parent_issue, phase_number + 1)

        # Broadcast WebSocket event
        await self._broadcast_queue_update(queue_id, "completed", parent_issue)

        # Post GitHub comment
        await self.notifier.post_phase_comment(
            parent_issue, phase_number, issue_number, "completed"
        )

    async def _handle_phase_failure(
        self,
        queue_id: str,
        phase_number: int,
        issue_number: int,
        parent_issue: int,
        error_msg: str | None
    ):
        """
        Handle failed phase.

        Args:
            queue_id: Queue ID
            phase_number: Phase number
            issue_number: Child issue number
            parent_issue: Parent issue number
            error_msg: Error message
        """
        logger.error(
            f"[FAILED] Phase {phase_number} failed "
            f"(issue #{issue_number}, parent #{parent_issue}): {error_msg}"
        )

        # Mark phase failed (blocks dependent phases)
        blocked_ids = self.phase_queue_service.mark_phase_failed(
            queue_id,
            error_msg or "Workflow execution failed"
        )

        # Broadcast WebSocket event for failed phase
        await self._broadcast_queue_update(queue_id, "failed", parent_issue)

        # Broadcast events for blocked phases
        for blocked_id in blocked_ids:
            await self._broadcast_queue_update(blocked_id, "blocked", parent_issue)

        # Post GitHub comment
        await self.notifier.post_phase_comment(
            parent_issue, phase_number, issue_number, "failed", error_msg
        )

    async def _broadcast_queue_update(self, queue_id: str, status: str, parent_issue: int):
        """
        Broadcast WebSocket event for queue update.

        Args:
            queue_id: Queue ID that was updated
            status: New status (completed, failed, blocked, ready, etc.)
            parent_issue: Parent issue number
        """
        if not self.websocket_manager:
            return

        try:
            event = {
                "type": "queue_update",
                "queue_id": queue_id,
                "status": status,
                "parent_issue": parent_issue,
                "timestamp": datetime.now().isoformat()
            }

            await self.websocket_manager.broadcast(event)
            logger.debug(f"[WS] Broadcast queue_update: {queue_id} → {status}")

        except Exception as e:
            logger.error(f"[ERROR] Failed to broadcast WebSocket event: {str(e)}")

    def mark_phase_running(self, queue_id: str):
        """
        Mark a phase as running when workflow starts.

        This should be called by the webhook trigger when starting a workflow.

        Args:
            queue_id: Queue ID to mark as running
        """
        try:
            self.phase_queue_service.update_status(queue_id, "running")
            logger.info(f"[RUNNING] Phase marked as running (queue_id: {queue_id})")
        except Exception as e:
            logger.error(f"[ERROR] Failed to mark phase as running: {str(e)}")

    def get_ready_phases(self):
        """
        Get all phases with status='ready'.

        Returns:
            List of PhaseQueueItem objects
        """
        try:
            items = self.phase_queue_service.get_all_queued()
            return [item for item in items if item.status == "ready"]
        except Exception as e:
            logger.error(f"[ERROR] Failed to get ready phases: {str(e)}")
            return []

    async def _create_next_phase_issue(self, parent_issue: int, next_phase_number: int):
        """
        Create GitHub issue for next phase (just-in-time creation).

        Args:
            parent_issue: Parent issue number
            next_phase_number: Phase number to create issue for
        """
        try:
            # Find the next phase in queue
            all_phases = self.phase_queue_service.get_all_queued()
            next_phase = None
            for phase in all_phases:
                if (phase.parent_issue == parent_issue and
                    phase.phase_number == next_phase_number):
                    next_phase = phase
                    break

            if not next_phase:
                logger.warning(
                    f"[WARNING] No phase found for parent #{parent_issue}, "
                    f"phase {next_phase_number}"
                )
                return

            # Check if issue already created
            if next_phase.issue_number:
                logger.info(
                    f"[SKIP] Phase {next_phase_number} already has issue "
                    f"#{next_phase.issue_number}"
                )
                return

            # Get phase data
            phase_data = next_phase.phase_data
            total_phases = phase_data.get("total_phases", "?")
            title = phase_data.get("title", f"Phase {next_phase_number}")
            content = phase_data.get("content", "")
            external_docs = phase_data.get("externalDocs", [])

            # Create child issue
            from core.data_models import GitHubIssue

            phase_title = f"Phase {next_phase_number}: {title}"
            phase_body = f"""# Phase {next_phase_number} of {total_phases}

**Execution Order:** After Phase {next_phase_number - 1}

## Description

{content}

"""
            if external_docs:
                phase_body += f"""
## Referenced Documents

{chr(10).join(f'- `{doc}`' for doc in external_docs)}

"""

            # Add workflow command to trigger ADW automatically
            phase_body += """
---

**Workflow:** adw_plan_iso with base model
"""

            phase_issue = GitHubIssue(
                title=phase_title,
                body=phase_body,
                labels=[f"phase-{next_phase_number}", "multi-phase"],
                classification="feature",
                workflow="adw_sdlc_iso",
                model_set="base"
            )

            phase_issue_number = self.github_poster.post_issue(phase_issue, confirm=False)
            logger.info(
                f"[CREATED] Just-in-time issue #{phase_issue_number} for "
                f"Phase {next_phase_number}"
            )

            # Update queue with issue number
            self.phase_queue_service.update_issue_number(
                next_phase.queue_id,
                phase_issue_number
            )

        except Exception as e:
            logger.error(
                f"[ERROR] Failed to create just-in-time issue for Phase "
                f"{next_phase_number}: {str(e)}"
            )

    def _get_workflow_status(self, issue_number: int) -> str | None:
        """
        Get workflow status from workflow_history by issue number.

        Wrapper method for backwards compatibility with tests.

        Args:
            issue_number: GitHub issue number

        Returns:
            'completed', 'failed', 'running', 'pending', or None if not found
        """
        return self.detector.get_workflow_status(issue_number)

    def _get_workflow_error(self, issue_number: int) -> str | None:
        """
        Get error message from workflow_history.

        Wrapper method for backwards compatibility with tests.

        Args:
            issue_number: GitHub issue number

        Returns:
            Error message string or None
        """
        return self.detector.get_workflow_error(issue_number)
