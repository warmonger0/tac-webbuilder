"""API response models."""

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field

from .domain import ColumnInsight, ServiceHealth, TableSchema
from .workflow import (
    CostData,
    WorkflowHistoryAnalytics,
    WorkflowHistoryItem,
    WorkflowTemplate,
)


# File Upload Models
class FileUploadResponse(BaseModel):
    table_name: str
    table_schema: dict[str, str]  # column_name: data_type
    row_count: int
    sample_data: list[dict[str, Any]]
    error: str | None = None


# Query Models
class QueryResponse(BaseModel):
    sql: str
    results: list[dict[str, Any]]
    columns: list[str]
    row_count: int
    execution_time_ms: float
    error: str | None = None


# Database Schema Models
class DatabaseSchemaResponse(BaseModel):
    tables: list[TableSchema]
    total_tables: int
    error: str | None = None


# Insights Models
class InsightsResponse(BaseModel):
    table_name: str
    insights: list[ColumnInsight]
    generated_at: datetime
    error: str | None = None


# Random Query Generation Models
class RandomQueryResponse(BaseModel):
    query: str
    error: str | None = None


# Health Check Models
class HealthCheckResponse(BaseModel):
    status: Literal["ok", "error"]
    database_connected: bool
    tables_count: int
    version: str = "1.0.0"
    uptime_seconds: float


# System Status Models
class SystemStatusResponse(BaseModel):
    overall_status: Literal["healthy", "degraded", "error"]
    timestamp: str
    services: dict[str, ServiceHealth]
    summary: dict[str, Any]


# GitHub Issue Generation Models
class NLProcessResponse(BaseModel):
    github_issue: "GitHubIssue"  # Forward ref
    project_context: "ProjectContext"  # Forward ref
    error: str | None = None


# Web UI Response Models
class SubmitRequestResponse(BaseModel):
    request_id: str = Field(..., description="Unique ID for this request")
    is_multi_phase: bool | None = Field(None, description="Whether this is a multi-phase request")
    parent_issue_number: int | None = Field(None, description="Parent issue number (for multi-phase)")
    child_issues: list["ChildIssueInfo"] | None = Field(None, description="Child issue info (for multi-phase)")  # Forward ref
    predicted_patterns: list[dict] | None = Field(None, description="Predicted patterns from input")


class ConfirmResponse(BaseModel):
    issue_number: int = Field(..., description="GitHub issue number")
    github_url: str = Field(..., description="GitHub issue URL")


# Routes Visualization Models
class RoutesResponse(BaseModel):
    routes: list["Route"] = Field(..., description="List of routes")  # Forward ref
    total: int = Field(..., description="Total number of routes")


# ADW Workflow Catalog Models
class WorkflowCatalogResponse(BaseModel):
    workflows: list[WorkflowTemplate] = Field(..., description="List of available workflow templates")
    total: int = Field(..., description="Total number of workflows")


# Cost Visualization Models
class CostResponse(BaseModel):
    cost_data: CostData | None = Field(None, description="Cost data if available")
    error: str | None = Field(None, description="Error message if any")


# Workflow History Models
class WorkflowHistoryResponse(BaseModel):
    workflows: list[WorkflowHistoryItem] = Field(..., description="List of workflow history items")
    total_count: int = Field(..., description="Total count of workflows (before pagination)")
    analytics: WorkflowHistoryAnalytics = Field(..., description="Analytics summary")


# Workflow History Resync Models
class ResyncResponse(BaseModel):
    resynced_count: int = Field(..., description="Number of workflows resynced")
    workflows: list[dict[str, Any]] = Field(..., description="List of resynced workflow summaries")
    errors: list[str] = Field(default_factory=list, description="List of error messages")
    message: str | None = Field(None, description="Optional status message")


# ADW Monitor Models
class AdwMonitorResponse(BaseModel):
    """Complete response for ADW monitoring endpoint"""
    summary: "AdwMonitorSummary" = Field(..., description="Summary statistics")  # Forward ref
    workflows: list["AdwWorkflowStatus"] = Field(..., description="List of workflow statuses")  # Forward ref
    last_updated: str = Field(..., description="Last update timestamp (ISO format)")


# Forward references - imported at end to avoid circular imports
from .domain import GitHubIssue, ProjectContext, Route  # noqa: E402
from .queue import ChildIssueInfo  # noqa: E402
from .workflow import AdwMonitorSummary, AdwWorkflowStatus  # noqa: E402

# Rebuild models with forward references
NLProcessResponse.model_rebuild()
SubmitRequestResponse.model_rebuild()
RoutesResponse.model_rebuild()
AdwMonitorResponse.model_rebuild()
