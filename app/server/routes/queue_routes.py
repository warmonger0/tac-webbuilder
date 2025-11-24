"""
Queue management endpoints for multi-phase workflow tracking.
"""
import logging
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

    return router
