"""
Observability API Routes

Endpoints for task logs, user prompts, and webhook event logging.
"""

import logging

from core.models.observability import (
    IssueProgress,
    TaskLog,
    TaskLogCreate,
    TaskLogFilters,
    UserPrompt,
    UserPromptCreate,
    UserPromptFilters,
    UserPromptWithProgress,
)
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from repositories.task_log_repository import TaskLogRepository
from repositories.user_prompt_repository import UserPromptRepository
from services.structured_logger import StructuredLogger

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/observability", tags=["Observability"])


# =========================================================================
# Webhook Event Models
# =========================================================================

class WebhookLogRequest(BaseModel):
    """Request model for webhook observability logging."""

    adw_id: str | None = Field(None, description="ADW ID if applicable")
    issue_number: int = Field(..., description="GitHub issue number")
    message: str = Field(..., description="Log message")
    webhook_type: str = Field(..., description="Type of webhook (github_issue, workflow_complete, etc.)")
    phase_status: str = Field(..., description="Phase status (received, processed, failed)")
    duration_seconds: float | None = Field(None, description="Processing time in seconds")
    event_data: dict = Field(default_factory=dict, description="Additional event data")


def init_observability_routes(
    task_log_repository: TaskLogRepository | None = None,
    user_prompt_repository: UserPromptRepository | None = None,
):
    """
    Initialize observability routes with optional repository injection.

    Args:
        task_log_repository: TaskLogRepository instance (creates new if None)
        user_prompt_repository: UserPromptRepository instance (creates new if None)
    """
    task_repo = task_log_repository or TaskLogRepository()
    prompt_repo = user_prompt_repository or UserPromptRepository()

    # =========================================================================
    # User Prompt Routes
    # =========================================================================

    @router.post("/user-prompts", response_model=UserPrompt, status_code=201)
    async def create_user_prompt(prompt: UserPromptCreate) -> UserPrompt:
        """
        Create a new user prompt log entry.

        This endpoint is called automatically when a user submits a request.
        """
        try:
            return prompt_repo.create(prompt)
        except Exception as e:
            logger.error(f"Error creating user prompt log: {e}")
            raise HTTPException(status_code=500, detail="Failed to create user prompt log")

    @router.get("/user-prompts", response_model=list[UserPrompt])
    async def get_user_prompts(
        session_id: str | None = None,
        issue_number: int | None = None,
        issue_type: str | None = None,
        is_multi_phase: bool | None = None,
        limit: int = Query(50, ge=1, le=1000),
        offset: int = Query(0, ge=0),
    ) -> list[UserPrompt]:
        """
        Get user prompts with optional filtering.

        Args:
            session_id: Filter by session ID
            issue_number: Filter by GitHub issue number
            issue_type: Filter by issue type (feature, bug, chore)
            is_multi_phase: Filter by multi-phase status
            limit: Maximum number to return (1-1000, default: 50)
            offset: Number to skip (default: 0)

        Returns:
            List of user prompts
        """
        try:
            filters = UserPromptFilters(
                session_id=session_id,
                issue_number=issue_number,
                issue_type=issue_type,
                is_multi_phase=is_multi_phase,
                limit=limit,
                offset=offset,
            )
            return prompt_repo.get_all(filters)
        except Exception as e:
            logger.error(f"Error retrieving user prompts: {e}")
            raise HTTPException(status_code=500, detail="Failed to retrieve user prompts")

    @router.get("/user-prompts/with-progress", response_model=list[UserPromptWithProgress])
    async def get_user_prompts_with_progress(
        session_id: str | None = None,
        issue_number: int | None = None,
        limit: int = Query(50, ge=1, le=1000),
        offset: int = Query(0, ge=0),
    ) -> list[UserPromptWithProgress]:
        """
        Get user prompts with linked task progress.

        Args:
            session_id: Filter by session ID
            issue_number: Filter by GitHub issue number
            limit: Maximum number to return (1-1000, default: 50)
            offset: Number to skip (default: 0)

        Returns:
            List of user prompts with progress info
        """
        try:
            filters = UserPromptFilters(
                session_id=session_id,
                issue_number=issue_number,
                limit=limit,
                offset=offset,
            )
            return prompt_repo.get_with_progress(filters)
        except Exception as e:
            logger.error(f"Error retrieving user prompts with progress: {e}")
            raise HTTPException(status_code=500, detail="Failed to retrieve user prompts with progress")

    @router.get("/user-prompts/{request_id}", response_model=UserPrompt)
    async def get_user_prompt_by_id(request_id: str) -> UserPrompt:
        """
        Get a user prompt by request ID.

        Args:
            request_id: Request ID to lookup

        Returns:
            UserPrompt if found

        Raises:
            404: If request not found
        """
        try:
            prompt = prompt_repo.get_by_request_id(request_id)
            if not prompt:
                raise HTTPException(status_code=404, detail=f"User prompt {request_id} not found")
            return prompt
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error retrieving user prompt {request_id}: {e}")
            raise HTTPException(status_code=500, detail="Failed to retrieve user prompt")

    # =========================================================================
    # Webhook Event Routes
    # =========================================================================

    @router.post("/log-webhook-event")
    async def log_webhook_event(request: WebhookLogRequest) -> dict:
        """
        Log webhook event to observability system.

        Called by external webhook server to persist observability data.
        This endpoint receives events from the lightweight webhook server
        and logs them using StructuredLogger + TaskLog for pattern analysis.
        """
        try:
            # Initialize StructuredLogger
            structured_logger = StructuredLogger()

            # Determine log level based on phase_status
            level_map = {
                "received": "info",
                "processed": "info",
                "failed": "error",
            }
            level = level_map.get(request.phase_status.lower(), "info")

            # Log to structured logger
            structured_logger.log_webhook_event(
                adw_id=request.adw_id,
                issue_number=request.issue_number,
                message=request.message,
                webhook_type=request.webhook_type,
                level=level,
                event_data=request.event_data,
                duration_seconds=request.duration_seconds,
            )

            # Create task log entry for pattern analysis (if ADW ID provided)
            if request.adw_id:
                # Map webhook phase_status to TaskLog status
                status_map = {
                    "received": "started",
                    "processed": "completed",
                    "failed": "failed",
                }
                task_status = status_map.get(request.phase_status.lower(), "started")

                task_log_entry = TaskLogCreate(
                    adw_id=request.adw_id,
                    issue_number=request.issue_number,
                    workflow_template=request.event_data.get("workflow", "unknown"),
                    phase_name="webhook_event",
                    phase_status=task_status,
                    log_message=request.message,
                    duration_seconds=request.duration_seconds,
                )
                task_repo.create(task_log_entry)

            return {
                "status": "logged",
                "message": "Webhook event logged successfully",
                "webhook_type": request.webhook_type,
            }

        except Exception as e:
            # Don't fail webhook processing if logging fails
            logger.error(f"Failed to log webhook event: {e}")
            raise HTTPException(
                status_code=500, detail=f"Failed to log webhook event: {str(e)}"
            ) from e

    # =========================================================================
    # Task Log Routes
    # =========================================================================

    @router.post("/task-logs", response_model=TaskLog, status_code=201)
    async def create_task_log(task_log: TaskLogCreate) -> TaskLog:
        """
        Create a new task log entry.

        This endpoint is called automatically by ADW workflows when phases complete.
        """
        try:
            return task_repo.create(task_log)
        except Exception as e:
            logger.error(f"Error creating task log: {e}")
            raise HTTPException(status_code=500, detail="Failed to create task log")

    @router.get("/task-logs", response_model=list[TaskLog])
    async def get_task_logs(
        issue_number: int | None = None,
        adw_id: str | None = None,
        phase_name: str | None = None,
        phase_status: str | None = None,
        limit: int = Query(50, ge=1, le=1000),
        offset: int = Query(0, ge=0),
    ) -> list[TaskLog]:
        """
        Get task logs with optional filtering.

        Args:
            issue_number: Filter by GitHub issue number
            adw_id: Filter by ADW workflow ID
            phase_name: Filter by phase name
            phase_status: Filter by phase status
            limit: Maximum number to return (1-1000, default: 50)
            offset: Number to skip (default: 0)

        Returns:
            List of task logs
        """
        try:
            filters = TaskLogFilters(
                issue_number=issue_number,
                adw_id=adw_id,
                phase_name=phase_name,
                phase_status=phase_status,
                limit=limit,
                offset=offset,
            )
            return task_repo.get_all(filters)
        except Exception as e:
            logger.error(f"Error retrieving task logs: {e}")
            raise HTTPException(status_code=500, detail="Failed to retrieve task logs")

    @router.get("/task-logs/issue/{issue_number}", response_model=list[TaskLog])
    async def get_task_logs_by_issue(issue_number: int) -> list[TaskLog]:
        """
        Get all task logs for a specific issue.

        Args:
            issue_number: GitHub issue number

        Returns:
            List of task logs ordered by phase_number
        """
        try:
            return task_repo.get_by_issue(issue_number)
        except Exception as e:
            logger.error(f"Error retrieving task logs for issue #{issue_number}: {e}")
            raise HTTPException(status_code=500, detail="Failed to retrieve task logs for issue")

    @router.get("/task-logs/adw/{adw_id}", response_model=list[TaskLog])
    async def get_task_logs_by_adw(adw_id: str) -> list[TaskLog]:
        """
        Get all task logs for a specific ADW workflow.

        Args:
            adw_id: ADW workflow ID

        Returns:
            List of task logs ordered by phase_number
        """
        try:
            return task_repo.get_by_adw_id(adw_id)
        except Exception as e:
            logger.error(f"Error retrieving task logs for ADW {adw_id}: {e}")
            raise HTTPException(status_code=500, detail="Failed to retrieve task logs for ADW")

    @router.get("/task-logs/issue/{issue_number}/latest", response_model=TaskLog)
    async def get_latest_task_log(issue_number: int) -> TaskLog:
        """
        Get the most recent task log for an issue.

        Args:
            issue_number: GitHub issue number

        Returns:
            Most recent TaskLog

        Raises:
            404: If no logs found for issue
        """
        try:
            log = task_repo.get_latest_by_issue(issue_number)
            if not log:
                raise HTTPException(status_code=404, detail=f"No task logs found for issue #{issue_number}")
            return log
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error retrieving latest task log for issue #{issue_number}: {e}")
            raise HTTPException(status_code=500, detail="Failed to retrieve latest task log")

    # =========================================================================
    # Progress Routes
    # =========================================================================

    @router.get("/progress/issue/{issue_number}", response_model=IssueProgress)
    async def get_issue_progress(issue_number: int) -> IssueProgress:
        """
        Get progress summary for an issue.

        Args:
            issue_number: GitHub issue number

        Returns:
            Issue progress summary

        Raises:
            404: If no progress data found for issue
        """
        try:
            progress = task_repo.get_issue_progress(issue_number)
            if not progress:
                raise HTTPException(status_code=404, detail=f"No progress data found for issue #{issue_number}")
            return progress
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error retrieving progress for issue #{issue_number}: {e}")
            raise HTTPException(status_code=500, detail="Failed to retrieve issue progress")

    return router
