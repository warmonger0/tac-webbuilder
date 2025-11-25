"""Core domain and business logic models."""

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


# Database Schema Models
class ColumnInfo(BaseModel):
    name: str
    type: str
    nullable: bool = True
    primary_key: bool = False


class TableSchema(BaseModel):
    name: str
    columns: list[ColumnInfo]
    row_count: int
    created_at: datetime


class ColumnInsight(BaseModel):
    column_name: str
    data_type: str
    unique_values: int
    null_count: int
    min_value: Any | None = None
    max_value: Any | None = None
    avg_value: float | None = None
    most_common: list[dict[str, Any]] | None = None


# System Status Models
class ServiceHealth(BaseModel):
    name: str
    status: Literal["healthy", "degraded", "error", "unknown"]
    uptime_seconds: float | None = None
    uptime_human: str | None = None
    message: str | None = None
    details: dict[str, Any] | None = None


# GitHub Issue Generation Models
class GitHubIssue(BaseModel):
    title: str = Field(..., description="Issue title")
    body: str = Field(..., description="Issue body in GitHub markdown format")
    labels: list[str] = Field(default_factory=list, description="Issue labels")
    classification: Literal["feature", "bug", "chore"] = Field(..., description="Issue type classification")
    workflow: str = Field(..., description="ADW workflow command (e.g., adw_sdlc_iso)")
    model_set: Literal["base", "heavy"] = Field(..., description="Model set for ADW workflow")


class ProjectContext(BaseModel):
    path: str = Field(..., description="Project directory path")
    is_new_project: bool = Field(..., description="Whether this is a new project")
    framework: str | None = Field(None, description="Detected framework (e.g., react-vite, nextjs, fastapi)")
    backend: str | None = Field(None, description="Detected backend framework")
    complexity: Literal["low", "medium", "high"] = Field(..., description="Project complexity level")
    build_tools: list[str] | None = Field(default_factory=list, description="Detected build tools")
    package_manager: str | None = Field(None, description="Detected package manager")
    has_git: bool = Field(default=False, description="Whether project has git initialized")


# Multi-Phase Models (imported from queue.py)


# Cost Estimation Models
class CostEstimate(BaseModel):
    """Cost estimate for a workflow execution"""
    level: Literal["lightweight", "standard", "complex"] = Field(..., description="Complexity level")
    min_cost: float = Field(..., description="Minimum estimated cost in dollars")
    max_cost: float = Field(..., description="Maximum estimated cost in dollars")
    confidence: float = Field(..., description="Confidence score (0.0-1.0)")
    reasoning: str = Field(..., description="Explanation of the estimate")
    recommended_workflow: str = Field(..., description="Recommended ADW workflow")


# Routes Visualization Models
class Route(BaseModel):
    path: str = Field(..., description="Route path (e.g., /api/upload)")
    method: str = Field(..., description="HTTP method (GET, POST, PUT, DELETE, PATCH)")
    name: str | None = Field(None, description="Route name or handler identifier")
    summary: str | None = Field(None, description="Route summary from docstring first line")
    description: str | None = Field(None, description="Route description from docstring")
    tags: list[str] = Field(default_factory=list, description="Route tags from FastAPI")
