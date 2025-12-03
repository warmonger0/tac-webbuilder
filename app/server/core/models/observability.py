"""
Observability Models

Models for task logs, user prompts, and workflow observability.
"""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

# =====================================================================
# User Prompt Models
# =====================================================================

class UserPrompt(BaseModel):
    """User prompt captured from request submission."""
    id: int | None = None
    request_id: str
    session_id: str | None = None

    # User Input (Raw)
    nl_input: str
    project_path: str | None = None
    auto_post: bool = False

    # Processed Output (Structured)
    issue_title: str | None = None
    issue_body: str | None = None
    issue_type: str | None = None  # 'feature', 'bug', 'chore'
    complexity: str | None = None  # 'ATOMIC', 'DECOMPOSE'

    # Multi-Phase Info
    is_multi_phase: bool = False
    phase_count: int = 1
    parent_issue_number: int | None = None

    # Cost Estimate
    estimated_cost_usd: float | None = None
    estimated_tokens: int | None = None
    model_name: str | None = None

    # GitHub Info
    github_issue_number: int | None = None
    github_issue_url: str | None = None
    posted_at: datetime | None = None

    # Metadata
    created_at: datetime
    captured_at: datetime


class UserPromptCreate(BaseModel):
    """Request model for creating a user prompt log."""
    request_id: str
    session_id: str | None = None
    nl_input: str
    project_path: str | None = None
    auto_post: bool = False
    issue_title: str | None = None
    issue_body: str | None = None
    issue_type: str | None = None
    complexity: str | None = None
    is_multi_phase: bool = False
    phase_count: int = 1
    parent_issue_number: int | None = None
    estimated_cost_usd: float | None = None
    estimated_tokens: int | None = None
    model_name: str | None = None
    github_issue_number: int | None = None
    github_issue_url: str | None = None
    posted_at: datetime | None = None


class UserPromptWithProgress(UserPrompt):
    """User prompt with linked task progress."""
    total_phases: int | None = None
    completed_phases: int | None = None
    failed_phases: int | None = None
    latest_phase: int | None = None
    last_activity: datetime | None = None


# =====================================================================
# Task Log Models
# =====================================================================

class TaskLog(BaseModel):
    """Task log for ADW phase execution."""
    id: int | None = None

    # Task Identification
    adw_id: str
    issue_number: int
    workflow_template: str | None = None

    # Phase Info
    phase_name: str
    phase_number: int | None = None
    phase_status: Literal["started", "completed", "failed", "skipped"]

    # Log Content
    log_message: str
    error_message: str | None = None

    # Timing
    started_at: datetime | None = None
    completed_at: datetime | None = None
    duration_seconds: float | None = None

    # Cost Data
    tokens_used: int | None = None
    cost_usd: float | None = None

    # Metadata
    captured_at: datetime
    created_at: datetime


class TaskLogCreate(BaseModel):
    """Request model for creating a task log."""
    adw_id: str
    issue_number: int
    workflow_template: str | None = None
    phase_name: str
    phase_number: int | None = None
    phase_status: Literal["started", "completed", "failed", "skipped"]
    log_message: str
    error_message: str | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    duration_seconds: float | None = None
    tokens_used: int | None = None
    cost_usd: float | None = None


class IssueProgress(BaseModel):
    """Progress summary for an issue."""
    issue_number: int
    adw_id: str
    workflow_template: str | None = None
    total_phases: int
    completed_phases: int
    failed_phases: int
    latest_phase: int | None = None
    last_activity: datetime | None = None


# =====================================================================
# Query/Filter Models
# =====================================================================

class TaskLogFilters(BaseModel):
    """Filters for querying task logs."""
    issue_number: int | None = None
    adw_id: str | None = None
    phase_name: str | None = None
    phase_status: str | None = None
    limit: int = Field(50, ge=1, le=1000)
    offset: int = Field(0, ge=0)


class UserPromptFilters(BaseModel):
    """Filters for querying user prompts."""
    session_id: str | None = None
    issue_number: int | None = None
    issue_type: str | None = None
    is_multi_phase: bool | None = None
    limit: int = Field(50, ge=1, le=1000)
    offset: int = Field(0, ge=0)
