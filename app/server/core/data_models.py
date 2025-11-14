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
class WorkflowExecutionMetrics(BaseModel):
    total_tokens: int = Field(..., description="Total number of tokens used")
    input_tokens: int = Field(..., description="Number of input tokens")
    cache_creation_tokens: int = Field(..., description="Number of cache creation tokens")
    cache_read_tokens: int = Field(..., description="Number of cache read tokens")
    output_tokens: int = Field(..., description="Number of output tokens")
    cache_efficiency_percent: float = Field(..., description="Cache efficiency percentage (0-100)")
    estimated_cost_total: float = Field(..., description="Estimated total cost in dollars")
    actual_cost_total: float = Field(..., description="Actual total cost in dollars")
    cost_per_token: float = Field(..., description="Average cost per token in dollars")

class WorkflowPerformanceMetrics(BaseModel):
    completion_time_seconds: Optional[float] = Field(None, description="Total completion time in seconds")
    retry_count: int = Field(0, description="Number of retries across all steps")
    success_rate: float = Field(0.0, description="Percentage of successful steps (0-100)")
    concurrent_workflows_count: int = Field(0, description="Number of concurrent workflows during execution")

class WorkflowResourceMetrics(BaseModel):
    worktree_id: Optional[str] = Field(None, description="Worktree identifier")
    worktree_reused: bool = Field(False, description="Whether worktree was reused")
    ports_used: Dict[str, int] = Field(default_factory=dict, description="Port assignments (frontend, backend)")
    structured_input: Optional[Dict[str, Any]] = Field(None, description="Structured workflow input as JSON")

class WorkflowHistoryItem(BaseModel):
    id: Optional[int] = Field(None, description="Database record ID")
    adw_id: str = Field(..., description="Unique ADW identifier")
    issue_number: Optional[int] = Field(None, description="GitHub issue number")
    workflow_template: str = Field(..., description="Workflow template name (e.g., adw_plan_build_test_iso)")
    start_timestamp: str = Field(..., description="Workflow start time (ISO 8601)")
    end_timestamp: Optional[str] = Field(None, description="Workflow end time (ISO 8601)")
    status: Literal["in_progress", "completed", "failed"] = Field(..., description="Workflow execution status")
    nl_input: str = Field(..., description="Original natural language input from user")
    model_used: Optional[str] = Field(None, description="Model used (e.g., claude-sonnet-4-5)")
    error_message: Optional[str] = Field(None, description="Error message if workflow failed")
    execution_metrics: WorkflowExecutionMetrics = Field(..., description="Token usage and cost metrics")
    performance_metrics: WorkflowPerformanceMetrics = Field(..., description="Performance and timing metrics")
    resource_metrics: WorkflowResourceMetrics = Field(..., description="Resource usage metrics")
    phases: List[PhaseCost] = Field(default_factory=list, description="Per-phase cost breakdown")
    created_at: str = Field(..., description="Record creation timestamp (ISO 8601)")
    updated_at: str = Field(..., description="Record last update timestamp (ISO 8601)")

class WorkflowAnalytics(BaseModel):
    total_workflows: int = Field(0, description="Total number of workflows")
    avg_cost_by_model: Dict[str, float] = Field(default_factory=dict, description="Average cost per model")
    avg_cost_by_template: Dict[str, float] = Field(default_factory=dict, description="Average cost per template")
    avg_completion_time: float = Field(0.0, description="Average completion time in seconds")
    overall_success_rate: float = Field(0.0, description="Overall success rate percentage (0-100)")
    cache_hit_rate: float = Field(0.0, description="Overall cache hit rate percentage (0-100)")
    most_expensive_workflows: List[Dict[str, Any]] = Field(default_factory=list, description="Top 5 most expensive workflows")
    token_efficiency_by_model: Dict[str, float] = Field(default_factory=dict, description="Average cost per token by model")
    total_cost_all_time: float = Field(0.0, description="Total cost across all workflows in dollars")
    total_tokens_all_time: int = Field(0, description="Total tokens used across all workflows")

class WorkflowHistoryFilter(BaseModel):
    limit: int = Field(20, description="Maximum number of results to return")
    offset: int = Field(0, description="Number of results to skip")
    sort_by: Literal["date", "cost", "duration", "success_rate", "model"] = Field("date", description="Sort field")
    order: Literal["asc", "desc"] = Field("desc", description="Sort order")
    filter_status: Optional[Literal["in_progress", "completed", "failed"]] = Field(None, description="Filter by status")
    filter_template: Optional[str] = Field(None, description="Filter by workflow template")
    filter_model: Optional[str] = Field(None, description="Filter by model")
    date_from: Optional[str] = Field(None, description="Start date filter (ISO 8601)")
    date_to: Optional[str] = Field(None, description="End date filter (ISO 8601)")
    search_query: Optional[str] = Field(None, description="Search in nl_input or adw_id")

class WorkflowHistoryResponse(BaseModel):
    items: List[WorkflowHistoryItem] = Field(..., description="List of workflow history items")
    analytics: WorkflowAnalytics = Field(..., description="Aggregated analytics")
    total: int = Field(..., description="Total number of items matching filters")
    has_more: bool = Field(..., description="Whether more results are available")