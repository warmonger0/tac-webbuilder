"""
Queue management endpoints for multi-phase workflow tracking.
"""
import logging
import os
import subprocess
from typing import List

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from core.nl_processor import suggest_adw_workflow

logger = logging.getLogger(__name__)


def determine_workflow_for_phase(phase_data: dict, github_poster=None, issue_number: int = None) -> tuple[str, str]:
    """
    Determine the appropriate ADW workflow for a phase based on its characteristics.

    Args:
        phase_data: Phase metadata with title, content, classification info
        github_poster: Optional GitHubPoster to fetch issue details
        issue_number: Optional issue number to fetch classification from GitHub

    Returns:
        Tuple of (workflow_script_name, model_set)

    Examples:
        - Bug: ("adw_sdlc_complete_iso", "lightweight")
        - Feature (high complexity): ("adw_sdlc_complete_iso", "heavy")
        - Feature (low complexity): ("adw_sdlc_complete_iso", "base")
        - UI-only change: ("adw_lightweight_iso", "lightweight")
    """
    # Try to get classification from phase_data
    classification = phase_data.get("classification", "feature")
    complexity = phase_data.get("complexity", "medium")

    # Try to infer from labels if available
    labels = phase_data.get("labels", [])
    if any("bug" in label.lower() for label in labels):
        classification = "bug"
    elif any("chore" in label.lower() for label in labels):
        classification = "chore"

    # Try to infer complexity from phase title/content
    title = phase_data.get("title", "").lower()
    content = phase_data.get("content", "").lower()
    combined_text = f"{title} {content}"

    if any(word in combined_text for word in ["simple", "trivial", "quick", "minor"]):
        complexity = "low"
    elif any(word in combined_text for word in ["complex", "major", "significant", "large"]):
        complexity = "high"

    # Build characteristics
    is_ui_only = any(word in combined_text for word in ["ui", "styling", "css", "style"])
    is_docs_only = any(word in combined_text for word in ["documentation", "readme", "docs"])
    has_backend = any(word in combined_text for word in ["api", "backend", "database", "server"])
    needs_testing = any(word in combined_text for word in ["test", "testing", "pytest", "vitest"])

    characteristics = {
        "ui_only": is_ui_only and not has_backend,
        "backend_changes": has_backend,
        "testing_needed": needs_testing,
        "docs_only": is_docs_only and not has_backend and not needs_testing,
        "file_count_estimate": 1 if (is_ui_only or is_docs_only) and not has_backend else 2
    }

    # Use the suggest_adw_workflow function to determine best workflow
    workflow, model_set = suggest_adw_workflow(classification, complexity, characteristics)

    logger.info(
        f"[Workflow Selection] classification={classification}, complexity={complexity} "
        f"→ {workflow} (model_set={model_set})"
    )

    return workflow, model_set


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


class WorkflowCompleteRequest(BaseModel):
    """Request from workflow completion hook"""
    adw_id: str = Field(..., description="ADW workflow identifier")
    status: str = Field(..., description="Workflow status (completed|failed)")
    issue_number: int | None = Field(None, description="GitHub issue number")
    queue_id: str | None = Field(None, description="Queue ID for this phase")
    phase_number: int | None = Field(None, description="Phase number in multi-phase workflow")
    parent_issue: int | None = Field(None, description="Parent issue for multi-phase workflow")
    trigger_next: bool = Field(False, description="Auto-trigger next phase if this one succeeds")
    metadata: dict = Field(default_factory=dict, description="Additional metadata (cost, duration, etc)")


class WorkflowCompleteResponse(BaseModel):
    """Response after workflow completion notification"""
    success: bool = Field(..., description="Whether notification was processed")
    message: str = Field(..., description="Status message")
    phase_updated: bool = Field(False, description="Whether phase status was updated")
    next_phase_triggered: bool = Field(False, description="Whether next phase was triggered")
    next_phase_number: int | None = Field(None, description="Next phase number that was triggered")
    next_issue_created: int | None = Field(None, description="GitHub issue number created for next phase")


class QueueConfigResponse(BaseModel):
    """Response model for queue configuration"""
    paused: bool = Field(..., description="Whether automatic phase execution is paused")


class SetQueuePausedRequest(BaseModel):
    """Request to set queue paused state"""
    paused: bool = Field(..., description="True to pause automatic execution, False to resume")


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

    @router.get("/config", response_model=QueueConfigResponse)
    async def get_queue_config() -> QueueConfigResponse:
        """
        Get current queue configuration.

        Returns:
            Current pause state of the queue
        """
        try:
            paused = phase_queue_service.is_paused()
            return QueueConfigResponse(paused=paused)

        except Exception as e:
            logger.error(f"[ERROR] Failed to get queue config: {str(e)}")
            raise HTTPException(500, f"Error retrieving queue config: {str(e)}")

    @router.post("/config/pause", response_model=QueueConfigResponse)
    async def set_queue_paused(request: SetQueuePausedRequest) -> QueueConfigResponse:
        """
        Set queue pause state.

        When paused, workflows will not automatically proceed to the next phase.
        When resumed, workflows will automatically kick off the next phase on completion.

        Args:
            request: Pause state to set

        Returns:
            Updated pause state
        """
        try:
            phase_queue_service.set_paused(request.paused)
            logger.info(f"[CONFIG] Queue {'paused' if request.paused else 'resumed'}")
            return QueueConfigResponse(paused=request.paused)

        except Exception as e:
            logger.error(f"[ERROR] Failed to set queue paused state: {str(e)}")
            raise HTTPException(500, f"Error setting queue config: {str(e)}")

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

            # Determine appropriate workflow based on phase characteristics
            workflow, model_set = determine_workflow_for_phase(phase.phase_data)
            logger.info(f"[EXECUTE] Selected workflow: {workflow} (model_set: {model_set})")

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


# Create a separate router for webhook endpoint (not under /api/queue prefix)
webhook_router = APIRouter(prefix="/api", tags=["Webhooks"])


def init_webhook_routes(phase_queue_service, github_poster):
    """
    Initialize webhook routes with service dependencies.

    Args:
        phase_queue_service: PhaseQueueService instance
        github_poster: GitHubPoster instance for creating issues
    """

    @webhook_router.post("/workflow-complete", response_model=WorkflowCompleteResponse)
    async def workflow_complete(request: WorkflowCompleteRequest) -> WorkflowCompleteResponse:
        """
        Handle workflow completion notifications from ADW hooks.

        This endpoint is called by the workflow_complete.sh hook script when
        an ADW workflow finishes. It can automatically trigger the next phase
        if trigger_next is True and the queue is not paused.

        Workflow:
        1. Validate and log the completion notification
        2. Update phase status in queue (completed/failed)
        3. If trigger_next is True and queue not paused:
           a. Find next phase in queue (depends_on_phase = current phase)
           b. If next phase has no issue_number, create GitHub issue
           c. Mark next phase as ready
           d. Auto-execute next phase

        Args:
            request: WorkflowCompleteRequest with adw_id, status, queue_id, trigger_next, etc

        Returns:
            WorkflowCompleteResponse with success status and next phase info
        """
        try:
            logger.info(
                f"[WEBHOOK] Received completion notification: "
                f"adw_id={request.adw_id}, status={request.status}, "
                f"queue_id={request.queue_id}, trigger_next={request.trigger_next}"
            )

            # Initialize response
            response = WorkflowCompleteResponse(
                success=True,
                message="Workflow completion notification received",
                phase_updated=False,
                next_phase_triggered=False
            )

            # Update phase status if queue_id provided
            if request.queue_id:
                new_status = "completed" if request.status == "completed" else "failed"
                updated = phase_queue_service.update_status(request.queue_id, new_status)

                if updated:
                    response.phase_updated = True
                    response.message = f"Phase marked as {new_status}"
                    logger.info(f"[WEBHOOK] Updated phase {request.queue_id} to {new_status}")
                else:
                    logger.warning(f"[WEBHOOK] Queue ID {request.queue_id} not found")
                    response.message = "Queue ID not found, but notification received"

            # Check if we should trigger next phase
            # Only if: trigger_next=True, status=completed, queue not paused
            if not request.trigger_next or request.status != "completed":
                logger.info(f"[WEBHOOK] Not triggering next phase (trigger_next={request.trigger_next}, status={request.status})")
                return response

            # Check if queue is paused
            if phase_queue_service.is_paused():
                logger.info("[WEBHOOK] Queue is paused, skipping auto-trigger")
                response.message += ". Queue is paused, next phase not triggered"
                return response

            # Find next phase
            if not request.parent_issue or not request.phase_number:
                logger.warning("[WEBHOOK] Cannot trigger next phase: missing parent_issue or phase_number")
                return response

            # Get all phases for this parent issue
            phases = phase_queue_service.get_queue_by_parent(request.parent_issue)
            next_phase = None
            for phase in phases:
                if phase.depends_on_phase == request.phase_number:
                    next_phase = phase
                    break

            if not next_phase:
                logger.info(f"[WEBHOOK] No next phase found for parent #{request.parent_issue}, phase {request.phase_number}")
                response.message += ". No next phase to trigger"
                return response

            logger.info(
                f"[WEBHOOK] Found next phase: {next_phase.phase_number} "
                f"(queue_id: {next_phase.queue_id})"
            )

            # Create GitHub issue for next phase if it doesn't have one
            if not next_phase.issue_number:
                logger.info(f"[WEBHOOK] Creating GitHub issue for phase {next_phase.phase_number}")

                # Build issue content from phase_data
                phase_data = next_phase.phase_data
                total_phases = max(p.phase_number for p in phases)

                phase_title = f"Phase {next_phase.phase_number}: {phase_data.get('title', 'Untitled Phase')}"
                phase_body = f"""# Phase {next_phase.phase_number} of {total_phases}

**Execution Order:** After Phase {next_phase.depends_on_phase}

## Description

{phase_data.get('content', 'No description provided')}

"""
                external_docs = phase_data.get('externalDocs', [])
                if external_docs:
                    phase_body += f"""
## Referenced Documents

{chr(10).join(f'- `{doc}`' for doc in external_docs)}

"""

                # Determine workflow for this phase
                phase_workflow, phase_model = determine_workflow_for_phase(phase_data)

                phase_body += f"""
---

**Workflow:** {phase_workflow} with {phase_model} model
"""

                # Use GitHubPoster to create issue
                from core.data_models import GitHubIssue

                phase_issue = GitHubIssue(
                    title=phase_title,
                    body=phase_body,
                    labels=[f"phase-{next_phase.phase_number}", "multi-phase"],
                    classification="feature",
                    workflow="adw_sdlc_iso",
                    model_set="base"
                )

                issue_number = github_poster.post_issue(phase_issue, confirm=False)

                # Update queue with new issue number
                phase_queue_service.update_issue_number(next_phase.queue_id, issue_number)
                next_phase.issue_number = issue_number  # Update local object

                response.next_issue_created = issue_number
                logger.info(f"[WEBHOOK] Created issue #{issue_number} for phase {next_phase.phase_number}")

            # Mark next phase as ready
            phase_queue_service.update_status(next_phase.queue_id, "ready")
            logger.info(f"[WEBHOOK] Marked phase {next_phase.phase_number} as ready")

            # Auto-execute next phase
            import uuid
            adw_id = f"adw-{uuid.uuid4().hex[:8]}"

            # Determine appropriate workflow based on phase characteristics
            workflow, model_set = determine_workflow_for_phase(next_phase.phase_data)
            logger.info(f"[WEBHOOK] Selected workflow: {workflow} (model_set: {model_set})")

            # Build command to launch workflow
            server_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # app/server
            app_dir = os.path.dirname(server_dir)  # app
            repo_root = os.path.dirname(app_dir)  # repo root
            adws_dir = os.path.join(repo_root, "adws")
            workflow_script = os.path.join(adws_dir, f"{workflow}.py")

            if not os.path.exists(workflow_script):
                logger.error(f"[WEBHOOK] Workflow script not found: {workflow_script}")
                response.message += f". Next phase ready but workflow script not found"
                return response

            cmd = ["uv", "run", workflow_script, str(next_phase.issue_number), adw_id]

            logger.info(
                f"[WEBHOOK] Launching {workflow} for phase {next_phase.phase_number} "
                f"(issue #{next_phase.issue_number}, adw_id: {adw_id})"
            )

            # Launch workflow in background
            process = subprocess.Popen(
                cmd,
                cwd=repo_root,
                start_new_session=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )

            # Mark phase as running
            phase_queue_service.update_status(next_phase.queue_id, "running", adw_id=adw_id)

            response.next_phase_triggered = True
            response.next_phase_number = next_phase.phase_number
            response.message = (
                f"Phase {request.phase_number} completed. "
                f"Next phase {next_phase.phase_number} triggered"
                f"{' (issue created)' if response.next_issue_created else ''}"
            )

            logger.info(
                f"[WEBHOOK] Successfully triggered next phase {next_phase.phase_number} "
                f"(adw_id: {adw_id})"
            )

            return response

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"[WEBHOOK] Error processing workflow completion: {str(e)}")
            import traceback
            logger.error(f"Traceback:\n{traceback.format_exc()}")
            raise HTTPException(500, f"Error processing workflow completion: {str(e)}")

    return webhook_router
