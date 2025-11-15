from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any, Literal
from datetime import datetime

# File Upload Models
class FileUploadRequest(BaseModel):
    # Handled by FastAPI UploadFile, no request model needed
    pass

class FileUploadResponse(BaseModel):
    table_name: str
    table_schema: Dict[str, str]  # column_name: data_type
    row_count: int
    sample_data: List[Dict[str, Any]]
    error: Optional[str] = None

# Query Models  
class QueryRequest(BaseModel):
    query: str = Field(..., description="Natural language query")
    llm_provider: Literal["openai", "anthropic"] = "openai"
    table_name: Optional[str] = None  # If querying specific table

class QueryResponse(BaseModel):
    sql: str
    results: List[Dict[str, Any]]
    columns: List[str]
    row_count: int
    execution_time_ms: float
    error: Optional[str] = None

# Database Schema Models
class ColumnInfo(BaseModel):
    name: str
    type: str
    nullable: bool = True
    primary_key: bool = False

class TableSchema(BaseModel):
    name: str
    columns: List[ColumnInfo]
    row_count: int
    created_at: datetime

class DatabaseSchemaRequest(BaseModel):
    pass  # No input needed

class DatabaseSchemaResponse(BaseModel):
    tables: List[TableSchema]
    total_tables: int
    error: Optional[str] = None

# Insights Models
class InsightsRequest(BaseModel):
    table_name: str
    column_names: Optional[List[str]] = None  # If None, analyze all columns

class ColumnInsight(BaseModel):
    column_name: str
    data_type: str
    unique_values: int
    null_count: int
    min_value: Optional[Any] = None
    max_value: Optional[Any] = None
    avg_value: Optional[float] = None
    most_common: Optional[List[Dict[str, Any]]] = None

class InsightsResponse(BaseModel):
    table_name: str
    insights: List[ColumnInsight]
    generated_at: datetime
    error: Optional[str] = None

# Random Query Generation Models
class RandomQueryResponse(BaseModel):
    query: str
    error: Optional[str] = None

# Health Check Models
class HealthCheckRequest(BaseModel):
    pass

class HealthCheckResponse(BaseModel):
    status: Literal["ok", "error"]
    database_connected: bool
    tables_count: int
    version: str = "1.0.0"
    uptime_seconds: float

# System Status Models
class ServiceHealth(BaseModel):
    name: str
    status: Literal["healthy", "degraded", "error", "unknown"]
    uptime_seconds: Optional[float] = None
    uptime_human: Optional[str] = None
    message: Optional[str] = None
    details: Optional[Dict[str, Any]] = None

class SystemStatusResponse(BaseModel):
    overall_status: Literal["healthy", "degraded", "error"]
    timestamp: str
    services: Dict[str, ServiceHealth]
    summary: Dict[str, Any]

# Export Models
class ExportRequest(BaseModel):
    table_name: str = Field(..., description="Name of the table to export")

class QueryExportRequest(BaseModel):
    data: List[Dict[str, Any]] = Field(..., description="Query result data to export")
    columns: List[str] = Field(..., description="Column names for the export")

# GitHub Issue Generation Models
class GitHubIssue(BaseModel):
    title: str = Field(..., description="Issue title")
    body: str = Field(..., description="Issue body in GitHub markdown format")
    labels: List[str] = Field(default_factory=list, description="Issue labels")
    classification: Literal["feature", "bug", "chore"] = Field(..., description="Issue type classification")
    workflow: str = Field(..., description="ADW workflow command (e.g., adw_sdlc_iso)")
    model_set: Literal["base", "heavy"] = Field(..., description="Model set for ADW workflow")

class ProjectContext(BaseModel):
    path: str = Field(..., description="Project directory path")
    is_new_project: bool = Field(..., description="Whether this is a new project")
    framework: Optional[str] = Field(None, description="Detected framework (e.g., react-vite, nextjs, fastapi)")
    backend: Optional[str] = Field(None, description="Detected backend framework")
    complexity: Literal["low", "medium", "high"] = Field(..., description="Project complexity level")
    build_tools: Optional[List[str]] = Field(default_factory=list, description="Detected build tools")
    package_manager: Optional[str] = Field(None, description="Detected package manager")
    has_git: bool = Field(default=False, description="Whether project has git initialized")

class NLProcessRequest(BaseModel):
    nl_input: str = Field(..., description="Natural language input describing the desired feature/bug/chore")
    project_path: Optional[str] = Field(None, description="Path to project directory for context detection")

class NLProcessResponse(BaseModel):
    github_issue: GitHubIssue
    project_context: ProjectContext
    error: Optional[str] = None

# Web UI Request Models
class SubmitRequestData(BaseModel):
    nl_input: str = Field(..., description="Natural language description of the request")
    project_path: Optional[str] = Field(None, description="Optional project path for context")
    auto_post: bool = Field(False, description="If True, auto-post to GitHub without confirmation")

class SubmitRequestResponse(BaseModel):
    request_id: str = Field(..., description="Unique ID for this request")

class ConfirmResponse(BaseModel):
    issue_number: int = Field(..., description="GitHub issue number")
    github_url: str = Field(..., description="GitHub issue URL")

# Routes Visualization Models
class Route(BaseModel):
    path: str = Field(..., description="Route path (e.g., /api/upload)")
    method: str = Field(..., description="HTTP method (GET, POST, PUT, DELETE, PATCH)")
    handler: str = Field(..., description="Handler function name")
    description: str = Field(..., description="Route description from docstring")

class RoutesResponse(BaseModel):
    routes: List[Route] = Field(..., description="List of routes")
    total: int = Field(..., description="Total number of routes")

# Workflow Models
class Workflow(BaseModel):
    adw_id: str = Field(..., description="Unique identifier for the workflow")
    issue_number: int = Field(..., description="GitHub issue number")
    phase: str = Field(..., description="Current workflow phase (plan, build, test, review, document, ship)")
    github_url: str = Field(..., description="GitHub URL for the workflow")

# ADW Workflow Catalog Models
class WorkflowTemplate(BaseModel):
    name: str = Field(..., description="Workflow filename (e.g., adw_sdlc_iso)")
    display_name: str = Field(..., description="Human-readable name")
    phases: List[str] = Field(..., description="List of phases in execution order")
    purpose: str = Field(..., description="What this workflow does")
    cost_range: str = Field(..., description="Estimated cost range (e.g., $0.20-0.50)")
    best_for: List[str] = Field(..., description="Best use cases")

class WorkflowCatalogResponse(BaseModel):
    workflows: List[WorkflowTemplate] = Field(..., description="List of available workflow templates")
    total: int = Field(..., description="Total number of workflows")

# Cost Visualization Models
class TokenBreakdown(BaseModel):
    input_tokens: int = Field(..., description="Number of input tokens")
    cache_creation_tokens: int = Field(..., description="Number of cache creation tokens")
    cache_read_tokens: int = Field(..., description="Number of cache read tokens")
    output_tokens: int = Field(..., description="Number of output tokens")

class PhaseCost(BaseModel):
    phase: str = Field(..., description="Workflow phase name (plan, build, test, review, document, ship)")
    cost: float = Field(..., description="Cost in dollars for this phase")
    tokens: TokenBreakdown = Field(..., description="Token breakdown for this phase")
    timestamp: Optional[str] = Field(None, description="ISO 8601 timestamp")

class CostData(BaseModel):
    adw_id: str = Field(..., description="ADW workflow identifier")
    phases: List[PhaseCost] = Field(..., description="List of phase costs")
    total_cost: float = Field(..., description="Total cost in dollars")
    cache_efficiency_percent: float = Field(..., description="Cache efficiency percentage (0-100)")
    cache_savings_amount: float = Field(..., description="Estimated savings from caching in dollars")
    total_tokens: int = Field(..., description="Total number of tokens used")

class CostResponse(BaseModel):
    cost_data: Optional[CostData] = Field(None, description="Cost data if available")
    error: Optional[str] = Field(None, description="Error message if any")

# Workflow History Models
class WorkflowHistoryCostBreakdown(BaseModel):
    estimated_total: float = Field(0.0, description="Estimated total cost")
    actual_total: float = Field(0.0, description="Actual total cost")
    estimated_per_step: float = Field(0.0, description="Estimated cost per step")
    actual_per_step: float = Field(0.0, description="Actual cost per step")
    cost_per_token: float = Field(0.0, description="Cost per token")
    by_phase: Optional[Dict[str, float]] = Field(None, description="Cost breakdown by phase")

class WorkflowHistoryTokenBreakdown(BaseModel):
    input_tokens: int = Field(0, description="Number of input tokens")
    output_tokens: int = Field(0, description="Number of output tokens")
    cached_tokens: int = Field(0, description="Number of cached tokens")
    cache_hit_tokens: int = Field(0, description="Number of cache hit tokens")
    cache_miss_tokens: int = Field(0, description="Number of cache miss tokens")
    total_tokens: int = Field(0, description="Total number of tokens")

class WorkflowHistoryItem(BaseModel):
    # Core fields
    id: int = Field(..., description="Workflow history record ID")
    adw_id: str = Field(..., description="ADW workflow identifier")
    issue_number: Optional[int] = Field(None, description="GitHub issue number")
    nl_input: Optional[str] = Field(None, description="Natural language input from user")
    github_url: Optional[str] = Field(None, description="GitHub issue URL")
    workflow_template: Optional[str] = Field(None, description="Workflow template name")
    model_used: Optional[str] = Field(None, description="Model used for workflow")
    status: Literal["pending", "running", "completed", "failed"] = Field(..., description="Workflow status")

    # Time tracking
    start_time: Optional[str] = Field(None, description="Start time (ISO format)")
    end_time: Optional[str] = Field(None, description="End time (ISO format)")
    duration_seconds: Optional[int] = Field(None, description="Duration in seconds")
    created_at: str = Field(..., description="Record creation time")
    updated_at: str = Field(..., description="Last update time")

    # Progress tracking
    error_message: Optional[str] = Field(None, description="Error message if failed")
    phase_count: Optional[int] = Field(None, description="Total number of phases")
    current_phase: Optional[str] = Field(None, description="Current phase name")
    success_rate: Optional[float] = Field(None, description="Success rate percentage")
    retry_count: int = Field(0, description="Number of retries")
    steps_completed: int = Field(0, description="Number of steps completed")
    steps_total: int = Field(0, description="Total number of steps")

    # Resource usage
    worktree_path: Optional[str] = Field(None, description="Path to worktree")
    backend_port: Optional[int] = Field(None, description="Backend server port")
    frontend_port: Optional[int] = Field(None, description="Frontend server port")
    concurrent_workflows: int = Field(0, description="Number of concurrent workflows")
    worktree_reused: bool = Field(False, description="Whether worktree was reused")

    # Token metrics
    input_tokens: int = Field(0, description="Number of input tokens")
    output_tokens: int = Field(0, description="Number of output tokens")
    cached_tokens: int = Field(0, description="Number of cached tokens")
    cache_hit_tokens: int = Field(0, description="Number of cache hit tokens")
    cache_miss_tokens: int = Field(0, description="Number of cache miss tokens")
    total_tokens: int = Field(0, description="Total number of tokens")
    cache_efficiency_percent: float = Field(0.0, description="Cache efficiency percentage")

    # Cost metrics
    estimated_cost_total: float = Field(0.0, description="Estimated total cost")
    actual_cost_total: float = Field(0.0, description="Actual total cost")
    estimated_cost_per_step: float = Field(0.0, description="Estimated cost per step")
    actual_cost_per_step: float = Field(0.0, description="Actual cost per step")
    cost_per_token: float = Field(0.0, description="Cost per token")

    # Structured data
    structured_input: Optional[Dict[str, Any]] = Field(None, description="Structured workflow input")
    cost_breakdown: Optional[WorkflowHistoryCostBreakdown] = Field(None, description="Cost breakdown details")
    token_breakdown: Optional[WorkflowHistoryTokenBreakdown] = Field(None, description="Token breakdown details")

class WorkflowHistoryAnalytics(BaseModel):
    total_workflows: int = Field(0, description="Total number of workflows")
    completed_workflows: int = Field(0, description="Number of completed workflows")
    failed_workflows: int = Field(0, description="Number of failed workflows")
    avg_duration_seconds: float = Field(0.0, description="Average duration in seconds")
    success_rate_percent: float = Field(0.0, description="Overall success rate percentage")
    workflows_by_model: Dict[str, int] = Field(default_factory=dict, description="Workflow count by model")
    workflows_by_template: Dict[str, int] = Field(default_factory=dict, description="Workflow count by template")
    workflows_by_status: Dict[str, int] = Field(default_factory=dict, description="Workflow count by status")
    avg_cost: float = Field(0.0, description="Average cost per workflow")
    total_cost: float = Field(0.0, description="Total cost across all workflows")
    avg_tokens: float = Field(0.0, description="Average tokens per workflow")
    avg_cache_efficiency: float = Field(0.0, description="Average cache efficiency percentage")

class WorkflowHistoryFilters(BaseModel):
    limit: Optional[int] = Field(20, description="Maximum number of records to return")
    offset: Optional[int] = Field(0, description="Number of records to skip")
    status: Optional[str] = Field(None, description="Filter by status")
    model: Optional[str] = Field(None, description="Filter by model")
    template: Optional[str] = Field(None, description="Filter by template")
    start_date: Optional[str] = Field(None, description="Filter by start date (ISO format)")
    end_date: Optional[str] = Field(None, description="Filter by end date (ISO format)")
    search: Optional[str] = Field(None, description="Search in ADW ID, nl_input, or github_url")
    sort_by: Optional[str] = Field("created_at", description="Field to sort by")
    sort_order: Optional[Literal["ASC", "DESC"]] = Field("DESC", description="Sort order")

class WorkflowHistoryResponse(BaseModel):
    workflows: List[WorkflowHistoryItem] = Field(..., description="List of workflow history items")
    total_count: int = Field(..., description="Total count of workflows (before pagination)")
    analytics: WorkflowHistoryAnalytics = Field(..., description="Analytics summary")