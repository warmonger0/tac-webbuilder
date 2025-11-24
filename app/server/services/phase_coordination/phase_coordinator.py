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
import logging
from datetime import datetime
from typing import Optional

from services.phase_queue_service import PhaseQueueService
from utils.db_connection import get_connection

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
        websocket_manager = None
    ):
        """
        Initialize PhaseCoordinator.

        Args:
            phase_queue_service: PhaseQueueService instance
            workflow_db_path: Path to workflow_history database
            poll_interval: Polling interval in seconds (default: 10.0)
            websocket_manager: WebSocket manager for real-time updates (optional)
        """
        self.phase_queue_service = phase_queue_service
        self.workflow_db_path = workflow_db_path
        self.poll_interval = poll_interval
        self.websocket_manager = websocket_manager
        self._is_running = False
        self._task: Optional[asyncio.Task] = None
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
            try:
                await self._task
            except asyncio.CancelledError:
                pass
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

        # Mark phase complete (triggers next phase automatically)
        self.phase_queue_service.mark_phase_complete(queue_id)

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
        error_msg: Optional[str]
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
