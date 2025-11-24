"""
Queue management endpoints for multi-phase workflow tracking.
"""
import logging
import os
import subprocess
from typing import List

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

# Router will be created with dependencies injected from server.py
router = APIRouter(prefix="/api/queue", tags=["Phase Queue"])


class PhaseQueueItemResponse(BaseModel):
    """Response model for phase queue item"""
    queue_id: str = Field(..., description="Unique queue identifier")
    parent_issue: int = Field(..., description="Parent GitHub issue number")
    phase_number: int = Field(..., description="Phase number")
    issue_number: int | None = Field(None, description="Child GitHub issue number")
    status: str = Field(..., description="Phase status")
    depends_on_phase: int | None = Field(None, description="Phase number this depends on")
    phase_data: dict = Field(..., description="Phase metadata")
    created_at: str = Field(..., description="Creation timestamp")
    updated_at: str = Field(..., description="Last update timestamp")
    error_message: str | None = Field(None, description="Error message if failed/blocked")
    adw_id: str | None = Field(None, description="ADW ID for running workflow")
    pr_number: int | None = Field(None, description="Pull request number")


class QueueListResponse(BaseModel):
    """Response model for queue list"""
    phases: List[PhaseQueueItemResponse] = Field(..., description="List of queued phases")
    total: int = Field(..., description="Total number of phases")


class EnqueueRequest(BaseModel):
    """Request to enqueue a phase"""
    parent_issue: int = Field(..., description="Parent GitHub issue number")
    phase_number: int = Field(..., description="Phase number")
    phase_data: dict = Field(..., description="Phase metadata {title, content, externalDocs}")
    depends_on_phase: int | None = Field(None, description="Phase number this depends on")


class EnqueueResponse(BaseModel):
    """Response after enqueueing a phase"""
    queue_id: str = Field(..., description="Unique queue identifier")
    message: str = Field(..., description="Success message")


class DequeueResponse(BaseModel):
    """Response after dequeueing a phase"""
    success: bool = Field(..., description="Whether dequeue was successful")
    message: str = Field(..., description="Status message")


class ExecutePhaseResponse(BaseModel):
    """Response after executing a phase"""
    success: bool = Field(..., description="Whether execution started successfully")
    message: str = Field(..., description="Status message")
    issue_number: int | None = Field(None, description="GitHub issue number for the phase")
    adw_id: str | None = Field(None, description="ADW ID for the workflow")


def init_queue_routes(phase_queue_service):
    """
    Initialize queue routes with service dependencies.

    This function is called from server.py to inject service dependencies.
    """

    @router.get("", response_model=QueueListResponse)
    async def get_all_queued() -> QueueListResponse:
        """
        Get all phases in the queue.

        Returns all phases regardless of status, ordered by parent issue and phase number.
        """
        try:
            items = phase_queue_service.get_all_queued()
            phases = [
                PhaseQueueItemResponse(**item.to_dict())
                for item in items
            ]
            return QueueListResponse(phases=phases, total=len(phases))

        except Exception as e:
            logger.error(f"[ERROR] Failed to get queued phases: {str(e)}")
            raise HTTPException(500, f"Error retrieving queue: {str(e)}")

    @router.get("/{parent_issue}", response_model=QueueListResponse)
    async def get_queue_by_parent(parent_issue: int) -> QueueListResponse:
        """
        Get all phases for a specific parent issue.

        Args:
            parent_issue: Parent GitHub issue number

        Returns:
            List of phases for this parent issue
        """
        try:
            items = phase_queue_service.get_queue_by_parent(parent_issue)
            phases = [
                PhaseQueueItemResponse(**item.to_dict())
                for item in items
            ]
            return QueueListResponse(phases=phases, total=len(phases))

        except Exception as e:
            logger.error(f"[ERROR] Failed to get phases for issue #{parent_issue}: {str(e)}")
            raise HTTPException(500, f"Error retrieving phases: {str(e)}")

    @router.post("/enqueue", response_model=EnqueueResponse)
    async def enqueue_phase(request: EnqueueRequest) -> EnqueueResponse:
        """
        Enqueue a new phase.

        Args:
            request: Phase details including parent issue, phase number, and metadata

        Returns:
            Queue ID and confirmation message
        """
        try:
            queue_id = phase_queue_service.enqueue(
                parent_issue=request.parent_issue,
                phase_number=request.phase_number,
                phase_data=request.phase_data,
                depends_on_phase=request.depends_on_phase,
            )
            return EnqueueResponse(
                queue_id=queue_id,
                message=f"Phase {request.phase_number} enqueued for issue #{request.parent_issue}"
            )

        except Exception as e:
            logger.error(f"[ERROR] Failed to enqueue phase: {str(e)}")
            raise HTTPException(500, f"Error enqueueing phase: {str(e)}")

    @router.delete("/{queue_id}", response_model=DequeueResponse)
    async def dequeue_phase(queue_id: str) -> DequeueResponse:
        """
        Remove a phase from the queue.

        Args:
            queue_id: Queue ID to remove

        Returns:
            Success status and message
        """
        try:
            success = phase_queue_service.dequeue(queue_id)
            if success:
                return DequeueResponse(
                    success=True,
                    message=f"Phase {queue_id} removed from queue"
                )
            else:
                raise HTTPException(404, f"Queue ID {queue_id} not found")

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"[ERROR] Failed to dequeue phase: {str(e)}")
            raise HTTPException(500, f"Error dequeueing phase: {str(e)}")

    @router.post("/{queue_id}/execute", response_model=ExecutePhaseResponse)
    async def execute_phase(queue_id: str) -> ExecutePhaseResponse:
        """
        Manually trigger execution of a phase.

        This endpoint launches the ADW workflow for a ready phase.
        The phase must have an associated GitHub issue number.

        Args:
            queue_id: Queue ID to execute

        Returns:
            Execution status and details
        """
        try:
            # Get phase from queue
            items = phase_queue_service.get_all_queued()
            phase = None
            for item in items:
                if item.queue_id == queue_id:
                    phase = item
                    break

            if not phase:
                raise HTTPException(404, f"Queue ID {queue_id} not found")

            # Validate phase status
            if phase.status != "ready":
                raise HTTPException(
                    400,
                    f"Phase must be 'ready' to execute (current status: {phase.status})"
                )

            # Check if phase has an issue number
            if not phase.issue_number:
                raise HTTPException(
                    400,
                    "Phase does not have a GitHub issue. Create an issue first before executing."
                )

            # Generate ADW ID
            import uuid
            adw_id = f"adw-{uuid.uuid4().hex[:8]}"

            # Determine workflow (default to adw_plan_iso for phases)
            workflow = "adw_plan_iso"

            # Build command to launch workflow
            # __file__ is in app/server/routes/queue_routes.py
            # Go up: routes -> server -> app -> repo_root
            server_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # app/server
            app_dir = os.path.dirname(server_dir)  # app
            repo_root = os.path.dirname(app_dir)  # repo root
            adws_dir = os.path.join(repo_root, "adws")
            workflow_script = os.path.join(adws_dir, f"{workflow}.py")

            if not os.path.exists(workflow_script):
                raise HTTPException(500, f"Workflow script not found: {workflow_script}")

            cmd = ["uv", "run", workflow_script, str(phase.issue_number), adw_id]

            logger.info(
                f"[EXECUTE] Launching {workflow} for phase {queue_id} "
                f"(issue #{phase.issue_number}, adw_id: {adw_id})"
            )

            # Launch workflow in background
            process = subprocess.Popen(
                cmd,
                cwd=repo_root,
                start_new_session=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )

            # Mark phase as running and store ADW ID
            phase_queue_service.update_status(queue_id, "running", adw_id=adw_id)

            logger.info(
                f"[SUCCESS] Workflow launched for phase {queue_id} "
                f"(issue #{phase.issue_number}, adw_id: {adw_id})"
            )

            return ExecutePhaseResponse(
                success=True,
                message=f"Workflow {workflow} started for phase {phase.phase_number}",
                issue_number=phase.issue_number,
                adw_id=adw_id
            )

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"[ERROR] Failed to execute phase: {str(e)}")
            import traceback
            logger.error(f"Traceback:\n{traceback.format_exc()}")
            raise HTTPException(500, f"Error executing phase: {str(e)}")

    return router
