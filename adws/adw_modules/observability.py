"""
ADW Observability Module

Helper functions for logging ADW workflow execution to the observability system.

Logs to both:
- Backend API (for database storage)
- JSONL files (for structured logging and analysis)
"""

import logging
import os
import sys
import urllib.request
import urllib.error
import json
from datetime import datetime
from typing import Optional, Literal

from adw_modules.structured_logger import get_adw_logger

logger = logging.getLogger(__name__)

# Backend API base URL
BACKEND_BASE_URL = os.environ.get("BACKEND_URL", "http://localhost:8000")

# Get structured logger instance
structured_logger = get_adw_logger()


def log_task_completion(
    adw_id: str,
    issue_number: int,
    phase_name: str,
    phase_number: int,
    phase_status: Literal["started", "completed", "failed", "skipped"],
    log_message: str,
    workflow_template: Optional[str] = None,
    error_message: Optional[str] = None,
    started_at: Optional[datetime] = None,
    completed_at: Optional[datetime] = None,
    duration_seconds: Optional[float] = None,
    tokens_used: Optional[int] = None,
    cost_usd: Optional[float] = None,
) -> bool:
    """
    Log task/phase completion to the observability system.

    This function makes a POST request to the backend API to record the phase completion.
    It's designed to be **zero-overhead** - failures are logged but don't block workflows.

    Args:
        adw_id: ADW workflow ID
        issue_number: GitHub issue number
        phase_name: Name of the phase (e.g., "Plan", "Build", "Test")
        phase_number: Phase number (1-9)
        phase_status: Status of the phase
        log_message: Log message (e.g., "✅ Isolated planning phase completed")
        workflow_template: Workflow template name (e.g., "adw_sdlc_complete_iso")
        error_message: Error message if phase_status is "failed"
        started_at: When the phase started
        completed_at: When the phase completed
        duration_seconds: Duration of the phase
        tokens_used: Tokens consumed during the phase
        cost_usd: Cost in USD

    Returns:
        True if logging succeeded, False otherwise (never raises exceptions)

    Example:
        >>> log_task_completion(
        ...     adw_id="adw-abc123",
        ...     issue_number=42,
        ...     phase_name="Plan",
        ...     phase_number=1,
        ...     phase_status="completed",
        ...     log_message="✅ Isolated planning phase completed",
        ...     workflow_template="adw_sdlc_complete_iso"
        ... )
        True
    """
    api_url = f"{BACKEND_BASE_URL}/api/v1/observability/task-logs"

    # Build payload
    payload = {
        "adw_id": adw_id,
        "issue_number": issue_number,
        "phase_name": phase_name,
        "phase_number": phase_number,
        "phase_status": phase_status,
        "log_message": log_message,
    }

    # Add optional fields
    if workflow_template:
        payload["workflow_template"] = workflow_template
    if error_message:
        payload["error_message"] = error_message
    if started_at:
        payload["started_at"] = started_at.isoformat()
    if completed_at:
        payload["completed_at"] = completed_at.isoformat()
    if duration_seconds is not None:
        payload["duration_seconds"] = duration_seconds
    if tokens_used is not None:
        payload["tokens_used"] = tokens_used
    if cost_usd is not None:
        payload["cost_usd"] = cost_usd

    # Write to structured JSONL logs (zero-overhead, non-blocking)
    try:
        structured_logger.log_phase(
            adw_id=adw_id,
            issue_number=issue_number,
            phase_name=phase_name,
            phase_number=phase_number,
            phase_status=phase_status,
            message=log_message,
            workflow_template=workflow_template,
            started_at=started_at,
            completed_at=completed_at,
            duration_seconds=duration_seconds,
            tokens_used=tokens_used,
            cost_usd=cost_usd,
            error_message=error_message,
        )
    except Exception as e:
        logger.debug(f"[STRUCTURED_LOG] Failed to write structured log: {e}")

    # Make API call to backend (for database storage)
    try:
        # Make POST request
        req = urllib.request.Request(
            api_url,
            data=json.dumps(payload).encode('utf-8'),
            headers={'Content-Type': 'application/json'},
            method='POST'
        )

        with urllib.request.urlopen(req, timeout=5) as response:
            if response.status in (200, 201):
                logger.info(
                    f"[OBSERVABILITY] Logged task completion: issue #{issue_number}, "
                    f"phase {phase_name} ({phase_status})"
                )
                return True
            else:
                logger.warning(
                    f"[OBSERVABILITY] Unexpected response {response.status} logging task completion"
                )
                return False

    except urllib.error.URLError as e:
        logger.debug(f"[OBSERVABILITY] Backend API not available for task logging: {e}")
        return False
    except Exception as e:
        logger.debug(f"[OBSERVABILITY] Failed to log task completion: {e}")
        return False


def log_phase_start(
    adw_id: str,
    issue_number: int,
    phase_name: str,
    phase_number: int,
    workflow_template: Optional[str] = None,
) -> bool:
    """
    Log phase start.

    Convenience wrapper around log_task_completion for phase starts.

    Args:
        adw_id: ADW workflow ID
        issue_number: GitHub issue number
        phase_name: Name of the phase
        phase_number: Phase number (1-9)
        workflow_template: Workflow template name

    Returns:
        True if logging succeeded, False otherwise
    """
    return log_task_completion(
        adw_id=adw_id,
        issue_number=issue_number,
        phase_name=phase_name,
        phase_number=phase_number,
        phase_status="started",
        log_message=f"🚀 {phase_name} phase started",
        workflow_template=workflow_template,
        started_at=datetime.now(),
    )


def log_phase_completion(
    adw_id: str,
    issue_number: int,
    phase_name: str,
    phase_number: int,
    success: bool = True,
    workflow_template: Optional[str] = None,
    error_message: Optional[str] = None,
    started_at: Optional[datetime] = None,
) -> bool:
    """
    Log phase completion.

    Convenience wrapper around log_task_completion for phase completions.

    Args:
        adw_id: ADW workflow ID
        issue_number: GitHub issue number
        phase_name: Name of the phase
        phase_number: Phase number (1-9)
        success: Whether the phase succeeded
        workflow_template: Workflow template name
        error_message: Error message if phase failed
        started_at: When the phase started (for duration calculation)

    Returns:
        True if logging succeeded, False otherwise
    """
    completed_at = datetime.now()
    duration = None
    if started_at:
        duration = (completed_at - started_at).total_seconds()

    status = "completed" if success else "failed"
    message = f"✅ {phase_name} phase completed" if success else f"❌ {phase_name} phase failed"

    return log_task_completion(
        adw_id=adw_id,
        issue_number=issue_number,
        phase_name=phase_name,
        phase_number=phase_number,
        phase_status=status,
        log_message=message,
        workflow_template=workflow_template,
        error_message=error_message,
        started_at=started_at,
        completed_at=completed_at,
        duration_seconds=duration,
    )


# Phase name to number mapping
PHASE_NUMBERS = {
    "Plan": 1,
    "Validate": 2,
    "Build": 3,
    "Lint": 4,
    "Test": 5,
    "Review": 6,
    "Document": 7,
    "Ship": 8,
    "Cleanup": 9,
    "Verify": 10,
}


def get_phase_number(phase_name: str) -> int:
    """
    Get phase number from phase name.

    Args:
        phase_name: Phase name (case-insensitive)

    Returns:
        Phase number (1-10), or 0 if not found
    """
    return PHASE_NUMBERS.get(phase_name.title(), 0)


def track_pattern_execution(
    pattern_id: str,
    workflow_id: Optional[int],
    execution_time_seconds: float,
    estimated_time_seconds: float,
    actual_cost: float,
    estimated_cost: float,
    success: bool,
    error_message: Optional[str] = None,
) -> bool:
    """
    Track pattern execution for ROI analysis (Session 12).

    This function records pattern execution metrics to enable closed-loop ROI tracking.
    It's designed to be **zero-overhead** - failures are logged but don't block workflows.

    Args:
        pattern_id: Pattern identifier being executed
        workflow_id: Workflow ID where pattern was executed (optional)
        execution_time_seconds: Actual execution time in seconds
        estimated_time_seconds: Estimated execution time from pattern approval
        actual_cost: Actual cost in USD
        estimated_cost: Estimated cost from pattern approval
        success: Whether execution completed successfully
        error_message: Error details if execution failed

    Returns:
        True if tracking succeeded, False otherwise (never raises exceptions)

    Example:
        >>> track_pattern_execution(
        ...     pattern_id="test-retry-automation",
        ...     workflow_id=123,
        ...     execution_time_seconds=45.2,
        ...     estimated_time_seconds=60.0,
        ...     actual_cost=0.012,
        ...     estimated_cost=0.015,
        ...     success=True
        ... )
        True
    """
    api_url = f"{BACKEND_BASE_URL}/api/roi-tracking/executions"

    # Build payload
    payload = {
        "pattern_id": pattern_id,
        "workflow_id": workflow_id,
        "execution_time_seconds": execution_time_seconds,
        "estimated_time_seconds": estimated_time_seconds,
        "actual_cost": actual_cost,
        "estimated_cost": estimated_cost,
        "success": success,
        "executed_at": datetime.now().isoformat(),
    }

    if error_message:
        payload["error_message"] = error_message

    # Make API call to backend (for ROI tracking)
    try:
        req = urllib.request.Request(
            api_url,
            data=json.dumps(payload).encode('utf-8'),
            headers={'Content-Type': 'application/json'},
            method='POST'
        )

        with urllib.request.urlopen(req, timeout=5) as response:
            if response.status in (200, 201):
                time_saved = estimated_time_seconds - execution_time_seconds
                cost_saved = estimated_cost - actual_cost
                logger.info(
                    f"[ROI_TRACKING] Recorded execution for pattern {pattern_id}: "
                    f"{'success' if success else 'failed'}, "
                    f"time_saved={time_saved:.1f}s, cost_saved=${cost_saved:.4f}"
                )
                return True
            else:
                logger.warning(
                    f"[ROI_TRACKING] Unexpected response {response.status} tracking pattern execution"
                )
                return False

    except urllib.error.URLError as e:
        logger.debug(f"[ROI_TRACKING] Backend API not available for pattern tracking: {e}")
        return False
    except Exception as e:
        logger.debug(f"[ROI_TRACKING] Failed to track pattern execution: {e}")
        return False
