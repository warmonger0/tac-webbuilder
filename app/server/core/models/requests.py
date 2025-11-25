"""
Request Models

All API request models for the tac-webbuilder application.
"""

from typing import Any, Literal

from pydantic import BaseModel, Field


# File Upload Models
class FileUploadRequest(BaseModel):
    # Handled by FastAPI UploadFile, no request model needed
    pass


# Query Models
class QueryRequest(BaseModel):
    query: str = Field(..., description="Natural language query")
    llm_provider: Literal["openai", "anthropic"] = "openai"
    table_name: str | None = None  # If querying specific table


# Database Schema Models
class DatabaseSchemaRequest(BaseModel):
    pass  # No input needed


# Insights Models
class InsightsRequest(BaseModel):
    table_name: str
    column_names: list[str] | None = None  # If None, analyze all columns


# Health Check Models
class HealthCheckRequest(BaseModel):
    pass


# Export Models
class ExportRequest(BaseModel):
    table_name: str = Field(..., description="Name of the table to export")


class QueryExportRequest(BaseModel):
    data: list[dict[str, Any]] = Field(..., description="Query result data to export")
    columns: list[str] = Field(..., description="Column names for the export")


# NL Process Models
class NLProcessRequest(BaseModel):
    nl_input: str = Field(..., description="Natural language input describing the desired feature/bug/chore")
    project_path: str | None = Field(None, description="Path to project directory for context detection")


# Web UI Request Models
class SubmitRequestData(BaseModel):
    nl_input: str = Field(..., description="Natural language description of the request")
    project_path: str | None = Field(None, description="Optional project path for context")
    auto_post: bool = Field(False, description="If True, auto-post to GitHub without confirmation")
    phases: list["Phase"] | None = Field(None, description="Optional multi-phase data")  # Forward ref


# Workflow History Models
class WorkflowHistoryFilters(BaseModel):
    limit: int | None = Field(20, description="Maximum number of records to return")
    offset: int | None = Field(0, description="Number of records to skip")
    status: str | None = Field(None, description="Filter by status")
    model: str | None = Field(None, description="Filter by model")
    template: str | None = Field(None, description="Filter by template")
    start_date: str | None = Field(None, description="Filter by start date (ISO format)")
    end_date: str | None = Field(None, description="Filter by end date (ISO format)")
    search: str | None = Field(None, description="Search in ADW ID, nl_input, or github_url")
    sort_by: str | None = Field("created_at", description="Field to sort by")
    sort_order: Literal["ASC", "DESC"] | None = Field("DESC", description="Sort order")


# Workflow History Resync Models
class ResyncRequest(BaseModel):
    adw_id: str | None = Field(None, description="Optional ADW ID to resync single workflow")
    force: bool = Field(False, description="Clear existing cost data before resync")


# Forward references - imported at end to avoid circular imports
from .queue import Phase  # noqa: E402

SubmitRequestData.model_rebuild()
