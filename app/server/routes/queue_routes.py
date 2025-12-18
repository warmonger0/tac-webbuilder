"""
Queue management endpoints for multi-phase workflow tracking.
"""
import hashlib
import logging
import os
import subprocess
import time

from core.models.observability import TaskLogCreate
from core.nl_processor import suggest_adw_workflow
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field, field_validator
from repositories.task_log_repository import TaskLogRepository
from repositories.webhook_event_repository import WebhookEventRepository
from services.structured_logger import StructuredLogger
from services.planned_features_service import PlannedFeaturesService
from core.models import PlannedFeatureUpdate
from utils.webhook_security import validate_webhook_request

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
router = APIRouter(prefix="/queue", tags=["Phase Queue"])


class PhaseQueueItemResponse(BaseModel):
    """Response model for phase queue item"""
    queue_id: str = Field(..., description="Unique queue identifier")
    feature_id: int = Field(..., description="Feature ID from planned_features table")
    phase_number: int = Field(..., description="Phase number")
    issue_number: int | None = Field(None, description="Child GitHub issue number")
    status: str = Field(..., description="Phase status")
    depends_on_phases: list[int] = Field(default_factory=list, description="List of phase numbers this depends on")
    phase_data: dict = Field(..., description="Phase metadata")
    created_at: str = Field(..., description="Creation timestamp")
    updated_at: str = Field(..., description="Last update timestamp")
    error_message: str | None = Field(None, description="Error message if failed/blocked")
    adw_id: str | None = Field(None, description="ADW ID for running workflow")
    pr_number: int | None = Field(None, description="Pull request number")


class QueueListResponse(BaseModel):
    """Response model for queue list"""
    phases: list[PhaseQueueItemResponse] = Field(..., description="List of queued phases")
    total: int = Field(..., description="Total number of phases")


class EnqueueRequest(BaseModel):
    """Request to enqueue a phase"""
    feature_id: int = Field(
        ge=0,
        description="Feature ID from planned_features table (0 for legacy workflows)"
    )
    phase_number: int = Field(
        ge=1,
        le=20,
        description="Phase number (1-20, typically 1-10)"
    )
    phase_data: dict = Field(
        description="Phase metadata {title, content, externalDocs, workflow_type, adw_id}"
    )
    depends_on_phases: list[int] = Field(
        default_factory=list,
        description="List of phase numbers this phase depends on"
    )

    @field_validator('phase_data')
    @classmethod
    def validate_phase_data(cls, v: dict) -> dict:
        """Validate phase_data contains required fields."""
        required_fields = ['workflow_type', 'adw_id']
        missing_fields = [field for field in required_fields if field not in v]

        if missing_fields:
            raise ValueError(
                f"phase_data missing required fields: {', '.join(missing_fields)}. "
                f"Required: {required_fields}"
            )

        # Validate workflow_type is a string
        if not isinstance(v.get('workflow_type'), str):
            raise ValueError("phase_data.workflow_type must be a string")

        # Validate adw_id is a string
        if not isinstance(v.get('adw_id'), str):
            raise ValueError("phase_data.adw_id must be a string")

        # Validate workflow_type is not empty
        if not v['workflow_type'].strip():
            raise ValueError("phase_data.workflow_type cannot be empty")

        # Validate adw_id is not empty
        if not v['adw_id'].strip():
            raise ValueError("phase_data.adw_id cannot be empty")

        return v

    @field_validator('depends_on_phases')
    @classmethod
    def validate_depends_on_phases(cls, v: list[int], info) -> list[int]:
        """Ensure all dependencies are valid phase numbers less than current phase."""
        if v and 'phase_number' in info.data:
            phase_number = info.data['phase_number']
            for dep_phase in v:
                if dep_phase >= phase_number:
                    raise ValueError(
                        f"Dependency phase {dep_phase} must be less than current phase_number ({phase_number})"
                    )
        return v


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


async def _get_queue_config_handler(phase_queue_service) -> QueueConfigResponse:
    """Handler for getting queue configuration."""
    paused = phase_queue_service.is_paused()
    return QueueConfigResponse(paused=paused)


async def _set_queue_paused_handler(request: SetQueuePausedRequest, phase_queue_service) -> QueueConfigResponse:
    """Handler for setting queue pause state."""
    phase_queue_service.set_paused(request.paused)
    logger.info(f"[CONFIG] Queue {'paused' if request.paused else 'resumed'}")
    return QueueConfigResponse(paused=request.paused)


async def _get_all_queued_handler(phase_queue_service) -> QueueListResponse:
    """Handler for getting all queued phases."""
    items = phase_queue_service.get_all_queued()
    phases = [
        PhaseQueueItemResponse(**item.to_dict())
        for item in items
    ]
    return QueueListResponse(phases=phases, total=len(phases))


async def _get_queue_by_parent_handler(parent_issue: int, phase_queue_service) -> QueueListResponse:
    """Handler for getting phases by parent issue."""
    items = phase_queue_service.get_queue_by_parent(parent_issue)
    phases = [
        PhaseQueueItemResponse(**item.to_dict())
        for item in items
    ]
    return QueueListResponse(phases=phases, total=len(phases))


async def _enqueue_phase_handler(request: EnqueueRequest, phase_queue_service) -> EnqueueResponse:
    """Handler for enqueueing a new phase."""
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


async def _dequeue_phase_handler(queue_id: str, phase_queue_service) -> DequeueResponse:
    """Handler for dequeueing a phase."""
    success = phase_queue_service.dequeue(queue_id)
    if success:
        return DequeueResponse(
            success=True,
            message=f"Phase {queue_id} removed from queue"
        )
    else:
        raise HTTPException(404, f"Queue ID {queue_id} not found")


async def _execute_phase_handler(queue_id: str, phase_queue_service) -> ExecutePhaseResponse:
    """Handler for execute phase endpoint."""
    # Get phase from queue
    phase = phase_queue_service.repository.get_by_id(queue_id)

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

    # Determine appropriate workflow
    workflow, model_set = determine_workflow_for_phase(phase.phase_data)
    logger.info(f"[EXECUTE] Selected workflow: {workflow} (model_set: {model_set})")

    # Build command to launch workflow
    server_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    app_dir = os.path.dirname(server_dir)
    repo_root = os.path.dirname(app_dir)
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
    subprocess.Popen(
        cmd,
        cwd=repo_root,
        start_new_session=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    # Mark phase as running
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


def _register_query_routes(router_obj, phase_queue_service):
    """Register GET endpoints for queue queries."""

    @router_obj.get("", response_model=QueueListResponse)
    async def get_all_queued() -> QueueListResponse:
        """Get all phases in the queue."""
        import time
        start = time.time()
        logger.info(f"[PERF] GET /queue started")
        try:
            result = await _get_all_queued_handler(phase_queue_service)
            elapsed = time.time() - start
            logger.info(f"[PERF] GET /queue completed in {elapsed:.3f}s")
            return result
        except Exception as e:
            logger.error(f"[ERROR] Failed to get queued phases: {str(e)}")
            raise HTTPException(500, f"Error retrieving queue: {str(e)}") from e

    @router_obj.get("/config", response_model=QueueConfigResponse)
    async def get_queue_config() -> QueueConfigResponse:
        """Get current queue configuration."""
        try:
            return await _get_queue_config_handler(phase_queue_service)
        except Exception as e:
            logger.error(f"[ERROR] Failed to get queue config: {str(e)}")
            raise HTTPException(500, f"Error retrieving queue config: {str(e)}") from e

    @router_obj.get("/{parent_issue}", response_model=QueueListResponse)
    async def get_queue_by_parent(parent_issue: int) -> QueueListResponse:
        """Get all phases for a specific parent issue."""
        try:
            return await _get_queue_by_parent_handler(parent_issue, phase_queue_service)
        except Exception as e:
            logger.error(f"[ERROR] Failed to get phases for issue #{parent_issue}: {str(e)}")
            raise HTTPException(500, f"Error retrieving phases: {str(e)}") from e


def _register_mutation_routes(router_obj, phase_queue_service):
    """Register POST/DELETE endpoints for queue mutations."""

    @router_obj.post("/config/pause", response_model=QueueConfigResponse)
    async def set_queue_paused(request: SetQueuePausedRequest) -> QueueConfigResponse:
        """Set queue pause state."""
        try:
            return await _set_queue_paused_handler(request, phase_queue_service)
        except Exception as e:
            logger.error(f"[ERROR] Failed to set queue paused state: {str(e)}")
            raise HTTPException(500, f"Error setting queue config: {str(e)}") from e

    @router_obj.post("/enqueue", response_model=EnqueueResponse)
    async def enqueue_phase(request: EnqueueRequest) -> EnqueueResponse:
        """Enqueue a new phase."""
        try:
            return await _enqueue_phase_handler(request, phase_queue_service)
        except Exception as e:
            logger.error(f"[ERROR] Failed to enqueue phase: {str(e)}")
            raise HTTPException(500, f"Error enqueueing phase: {str(e)}") from e

    @router_obj.delete("/{queue_id}", response_model=DequeueResponse)
    async def dequeue_phase(queue_id: str) -> DequeueResponse:
        """Remove a phase from the queue."""
        try:
            return await _dequeue_phase_handler(queue_id, phase_queue_service)
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"[ERROR] Failed to dequeue phase: {str(e)}")
            raise HTTPException(500, f"Error dequeueing phase: {str(e)}") from e

    @router_obj.post("/{queue_id}/execute", response_model=ExecutePhaseResponse)
    async def execute_phase(queue_id: str) -> ExecutePhaseResponse:
        """Manually trigger execution of a phase."""
        try:
            return await _execute_phase_handler(queue_id, phase_queue_service)
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"[ERROR] Failed to execute phase: {str(e)}")
            import traceback
            logger.error(f"Traceback:\n{traceback.format_exc()}")
            raise HTTPException(500, f"Error executing phase: {str(e)}") from e


def init_queue_routes(phase_queue_service):
    """Initialize queue routes with service dependencies."""
    _register_query_routes(router, phase_queue_service)
    _register_mutation_routes(router, phase_queue_service)
    return router


# Create a separate router for webhook endpoint (not under /queue prefix)
webhook_router = APIRouter(prefix="", tags=["Webhooks"])


def _update_phase_status(
    phase_queue_service,
    request: WorkflowCompleteRequest,
    response: WorkflowCompleteResponse
) -> None:
    """Update phase status if queue_id provided (modifies response in place)."""
    if not request.queue_id:
        return

    new_status = "completed" if request.status == "completed" else "failed"
    updated = phase_queue_service.update_status(request.queue_id, new_status)

    if updated:
        response.phase_updated = True
        response.message = f"Phase marked as {new_status}"
        logger.info(f"[WEBHOOK] Updated phase {request.queue_id} to {new_status}")
    else:
        logger.warning(f"[WEBHOOK] Queue ID {request.queue_id} not found")
        response.message = "Queue ID not found, but notification received"


def _sync_planned_feature_status(request: WorkflowCompleteRequest) -> None:
    """
    Auto-sync planned_features table based on workflow completion.

    Updates the planned feature status when an ADW workflow completes:
    - Completed workflow → Mark feature as 'completed'
    - Failed workflow → Keep as 'in_progress', add failure notes with phase info

    Args:
        request: WorkflowCompleteRequest with issue_number, status, metadata
    """
    if not request.issue_number:
        return

    try:
        planned_features_service = PlannedFeaturesService()

        # Find all features with this github_issue_number
        all_features = planned_features_service.get_all()
        matching_features = [
            f for f in all_features
            if f.github_issue_number == request.issue_number
        ]

        if not matching_features:
            logger.debug(
                f"[WEBHOOK] No planned feature found for issue #{request.issue_number}"
            )
            return

        for feature in matching_features:
            if request.status == "completed":
                # Workflow succeeded - mark feature as completed
                update_data = PlannedFeatureUpdate(
                    status="completed",
                    completion_notes=(
                        f"Completed by ADW workflow {request.adw_id}. "
                        f"Metadata: {request.metadata}"
                    )
                )
                planned_features_service.update(feature.id, update_data)
                logger.info(
                    f"[WEBHOOK] Marked planned feature #{feature.id} "
                    f"(issue #{request.issue_number}) as completed"
                )
            else:
                # Workflow failed - keep in_progress, add failure notes
                phase_info = f"Phase {request.phase_number}" if request.phase_number else "Unknown phase"
                update_data = PlannedFeatureUpdate(
                    completion_notes=(
                        f"⚠️ Workflow failed at {phase_info} (ADW: {request.adw_id}). "
                        f"Metadata: {request.metadata}. "
                        f"Status kept as '{feature.status}' for retry."
                    )
                )
                planned_features_service.update(feature.id, update_data)
                logger.warning(
                    f"[WEBHOOK] Recorded failure for planned feature #{feature.id} "
                    f"(issue #{request.issue_number}) at {phase_info}"
                )

    except Exception as e:
        # Don't fail the webhook if planned_features sync fails
        logger.error(
            f"[WEBHOOK] Error syncing planned feature for issue #{request.issue_number}: {e}",
            exc_info=True
        )


def _find_next_phase(phase_queue_service, request: WorkflowCompleteRequest):
    """Find the next phase to execute."""
    # Find next phase directly (optimized - no N+1 query)
    next_phase = phase_queue_service.repository.find_by_depends_on_phase(
        request.parent_issue,
        request.phase_number
    )

    # If no next phase in current parent, check hopper
    if not next_phase:
        logger.info(
            f"[WEBHOOK] No next phase in parent #{request.parent_issue}. "
            "Checking hopper for other ready Phase 1s..."
        )

        from services.hopper_sorter import HopperSorter
        sorter = HopperSorter()
        next_phase = sorter.get_next_phase_1()

        if next_phase:
            logger.info(
                f"[WEBHOOK] Hopper selected next parent: #{next_phase.parent_issue} "
                f"(priority={next_phase.priority}, position={next_phase.queue_position})"
            )
        else:
            logger.info("[WEBHOOK] Hopper empty - no more Phase 1s to start")

    return next_phase


def _create_phase_issue(github_poster, next_phase, phase_queue_service) -> int:
    """Create GitHub issue for a phase."""
    logger.info(f"[WEBHOOK] Creating GitHub issue for phase {next_phase.phase_number}")

    phase_data = next_phase.phase_data

    # Fetch all phases only when needed (for total_phases count)
    phases = phase_queue_service.get_queue_by_parent(next_phase.parent_issue)
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
    logger.info(f"[WEBHOOK] Created issue #{issue_number} for phase {next_phase.phase_number}")

    return issue_number


def _launch_workflow(next_phase) -> tuple[str, bool]:
    """Launch workflow for next phase. Returns (adw_id, success)."""
    import uuid
    adw_id = f"adw-{uuid.uuid4().hex[:8]}"

    # Determine appropriate workflow
    workflow, model_set = determine_workflow_for_phase(next_phase.phase_data)
    logger.info(f"[WEBHOOK] Selected workflow: {workflow} (model_set: {model_set})")

    # Build command to launch workflow
    server_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    app_dir = os.path.dirname(server_dir)
    repo_root = os.path.dirname(app_dir)
    adws_dir = os.path.join(repo_root, "adws")
    workflow_script = os.path.join(adws_dir, f"{workflow}.py")

    if not os.path.exists(workflow_script):
        logger.error(f"[WEBHOOK] Workflow script not found: {workflow_script}")
        return adw_id, False

    cmd = ["uv", "run", workflow_script, str(next_phase.issue_number), adw_id]

    logger.info(
        f"[WEBHOOK] Launching {workflow} for phase {next_phase.phase_number} "
        f"(issue #{next_phase.issue_number}, adw_id: {adw_id})"
    )

    # Launch workflow in background
    subprocess.Popen(
        cmd,
        cwd=repo_root,
        start_new_session=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    return adw_id, True


def init_webhook_routes(phase_queue_service, github_poster, websocket_manager=None):
    """
    Initialize webhook routes with service dependencies.

    Args:
        phase_queue_service: PhaseQueueService instance
        github_poster: GitHubPoster instance for creating issues
        websocket_manager: Optional WebSocket ConnectionManager for event broadcasting
    """

    async def _broadcast_workflow_completed(request: 'WorkflowCompleteRequest'):
        """Helper to broadcast workflow_completed event via WebSocket."""
        if websocket_manager:
            try:
                from datetime import datetime

                await websocket_manager.broadcast({
                    "type": "workflow_completed",
                    "data": {
                        "queue_id": request.queue_id,
                        "feature_id": request.parent_issue,  # Will be feature_id after migration
                        "phase_number": request.phase_number,
                        "status": request.status,  # "completed" or "failed"
                        "adw_id": request.adw_id,
                        "timestamp": datetime.now().isoformat()
                    }
                })

                logger.info(
                    f"[WEBHOOK] Broadcasted workflow_completed event: "
                    f"queue_id={request.queue_id}, status={request.status}"
                )
            except Exception as e:
                # Don't fail webhook if broadcast fails
                logger.error(f"[WEBHOOK] Failed to broadcast event: {e}")

    @webhook_router.post("/workflow-complete", response_model=WorkflowCompleteResponse)
    async def workflow_complete(
        http_request: Request,
        request: WorkflowCompleteRequest
    ) -> WorkflowCompleteResponse:
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
            http_request: FastAPI Request object for signature validation
            request: WorkflowCompleteRequest with adw_id, status, queue_id, trigger_next, etc

        Returns:
            WorkflowCompleteResponse with success status and next phase info
        """
        # Initialize observability services
        structured_logger = StructuredLogger()
        task_log_repo = TaskLogRepository()
        start_time = time.time()

        # Log webhook received
        structured_logger.log_webhook_event(
            adw_id=request.adw_id,
            issue_number=request.parent_issue,
            message=f"Workflow complete webhook received (status={request.status})",
            webhook_type="workflow_complete",
            event_data={
                "status": request.status,
                "queue_id": request.queue_id,
                "phase_number": request.phase_number,
                "trigger_next": request.trigger_next
            }
        )

        # VALIDATE SIGNATURE
        try:
            await validate_webhook_request(http_request, webhook_type="internal")
        except HTTPException:
            logger.warning("[WEBHOOK] Internal webhook signature validation failed")
            # For internal webhooks, log and continue (or enforce with: raise)

        # CHECK FOR DUPLICATE (idempotency)
        webhook_repo = WebhookEventRepository()

        # Generate unique webhook ID from request data
        webhook_id = hashlib.sha256(
            f"{request.adw_id}:{request.status}:{request.queue_id}".encode()
        ).hexdigest()[:16]

        if webhook_repo.is_duplicate(webhook_id, window_seconds=30):
            logger.warning(
                f"[WEBHOOK] Duplicate webhook detected for adw_id={request.adw_id}, "
                f"queue_id={request.queue_id}"
            )
            return WorkflowCompleteResponse(
                success=True,
                message="Duplicate webhook - already processed",
                phase_updated=False,
                next_phase_triggered=False
            )

        # Record webhook event
        webhook_repo.record_webhook(
            webhook_id=webhook_id,
            webhook_type="workflow_complete",
            adw_id=request.adw_id,
            issue_number=request.parent_issue
        )

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

            # Update phase status
            _update_phase_status(phase_queue_service, request, response)

            # Auto-sync planned_features status based on workflow completion
            _sync_planned_feature_status(request)

            # Check if we should trigger next phase
            if not request.trigger_next or request.status != "completed":
                logger.info(f"[WEBHOOK] Not triggering next phase (trigger_next={request.trigger_next}, status={request.status})")
                await _broadcast_workflow_completed(request)
                return response

            # Check if queue is paused
            if phase_queue_service.is_paused():
                logger.info("[WEBHOOK] Queue is paused, skipping auto-trigger")
                response.message += ". Queue is paused, next phase not triggered"
                await _broadcast_workflow_completed(request)
                return response

            # Validate required fields
            if not request.parent_issue or not request.phase_number:
                logger.warning("[WEBHOOK] Cannot trigger next phase: missing parent_issue or phase_number")
                await _broadcast_workflow_completed(request)
                return response

            # Find next phase
            next_phase = _find_next_phase(phase_queue_service, request)

            if not next_phase:
                response.message += ". No more phases in queue"
                await _broadcast_workflow_completed(request)
                return response

            logger.info(
                f"[WEBHOOK] Found next phase: {next_phase.phase_number} "
                f"(queue_id: {next_phase.queue_id})"
            )

            # Create GitHub issue if needed
            if not next_phase.issue_number:
                issue_number = _create_phase_issue(github_poster, next_phase, phase_queue_service)
                phase_queue_service.update_issue_number(next_phase.queue_id, issue_number)
                next_phase.issue_number = issue_number
                response.next_issue_created = issue_number

            # Mark next phase as ready
            phase_queue_service.update_status(next_phase.queue_id, "ready")
            logger.info(f"[WEBHOOK] Marked phase {next_phase.phase_number} as ready")

            # Launch workflow
            adw_id, success = _launch_workflow(next_phase)

            if not success:
                response.message += ". Next phase ready but workflow script not found"
                await _broadcast_workflow_completed(request)
                return response

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

            # Log successful processing before returning
            elapsed_time = time.time() - start_time

            structured_logger.log_webhook_event(
                adw_id=request.adw_id,
                issue_number=request.parent_issue,
                message="Workflow complete webhook processed successfully",
                webhook_type="workflow_complete",
                duration_seconds=elapsed_time,
                event_data={
                    "phase_updated": response.phase_updated,
                    "next_phase_triggered": response.next_phase_triggered,
                    "next_phase_number": response.next_phase_number
                }
            )

            # Create TaskLog entry
            try:
                task_log_repo.create(TaskLogCreate(
                    adw_id=request.adw_id,
                    issue_number=request.parent_issue,
                    workflow_template="workflow_complete",
                    phase_name=f"phase_{request.phase_number}_complete",
                    phase_status=request.status,
                    log_message=f"Phase {request.phase_number} marked {request.status} via webhook",
                    duration_seconds=elapsed_time
                ))
            except Exception as log_error:
                logger.warning(f"Failed to create TaskLog entry: {log_error}")

            # ✅ Emit WebSocket event for PhaseCoordinator
            await _broadcast_workflow_completed(request)

            return response

        except HTTPException:
            raise
        except Exception as e:
            # Log failure
            elapsed_time = time.time() - start_time

            structured_logger.log_webhook_event(
                adw_id=request.adw_id,
                issue_number=request.parent_issue,
                message=f"Workflow complete webhook failed: {str(e)}",
                webhook_type="workflow_complete",
                duration_seconds=elapsed_time,
                error_message=str(e),
                event_data={
                    "error_type": type(e).__name__
                }
            )

            logger.error(f"[WEBHOOK] Error processing workflow completion: {str(e)}")
            import traceback
            logger.error(f"Traceback:\n{traceback.format_exc()}")
            raise HTTPException(500, f"Error processing workflow completion: {str(e)}") from e

    return webhook_router
