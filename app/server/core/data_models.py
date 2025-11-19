from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


# File Upload Models
class FileUploadRequest(BaseModel):
    # Handled by FastAPI UploadFile, no request model needed
    pass

class FileUploadResponse(BaseModel):
    table_name: str
    table_schema: dict[str, str]  # column_name: data_type
    row_count: int
    sample_data: list[dict[str, Any]]
    error: str | None = None

# Query Models
class QueryRequest(BaseModel):
    query: str = Field(..., description="Natural language query")
    llm_provider: Literal["openai", "anthropic"] = "openai"
    table_name: str | None = None  # If querying specific table

class QueryResponse(BaseModel):
    sql: str
    results: list[dict[str, Any]]
    columns: list[str]
    row_count: int
    execution_time_ms: float
    error: str | None = None

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

class DatabaseSchemaRequest(BaseModel):
    pass  # No input needed

class DatabaseSchemaResponse(BaseModel):
    tables: list[TableSchema]
    total_tables: int
    error: str | None = None

# Insights Models
class InsightsRequest(BaseModel):
    table_name: str
    column_names: list[str] | None = None  # If None, analyze all columns

class ColumnInsight(BaseModel):
    column_name: str
    data_type: str
    unique_values: int
    null_count: int
    min_value: Any | None = None
    max_value: Any | None = None
    avg_value: float | None = None
    most_common: list[dict[str, Any]] | None = None

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
    uptime_seconds: float | None = None
    uptime_human: str | None = None
    message: str | None = None
    details: dict[str, Any] | None = None

class SystemStatusResponse(BaseModel):
    overall_status: Literal["healthy", "degraded", "error"]
    timestamp: str
    services: dict[str, ServiceHealth]
    summary: dict[str, Any]

# Export Models
class ExportRequest(BaseModel):
    table_name: str = Field(..., description="Name of the table to export")

class QueryExportRequest(BaseModel):
    data: list[dict[str, Any]] = Field(..., description="Query result data to export")
    columns: list[str] = Field(..., description="Column names for the export")

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

class NLProcessRequest(BaseModel):
    nl_input: str = Field(..., description="Natural language input describing the desired feature/bug/chore")
    project_path: str | None = Field(None, description="Path to project directory for context detection")

class NLProcessResponse(BaseModel):
    github_issue: GitHubIssue
    project_context: ProjectContext
    error: str | None = None

# Web UI Request Models
class SubmitRequestData(BaseModel):
    nl_input: str = Field(..., description="Natural language description of the request")
    project_path: str | None = Field(None, description="Optional project path for context")
    auto_post: bool = Field(False, description="If True, auto-post to GitHub without confirmation")

class SubmitRequestResponse(BaseModel):
    request_id: str = Field(..., description="Unique ID for this request")

class ConfirmResponse(BaseModel):
    issue_number: int = Field(..., description="GitHub issue number")
    github_url: str = Field(..., description="GitHub issue URL")

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
    handler: str = Field(..., description="Handler function name")
    description: str = Field(..., description="Route description from docstring")

class RoutesResponse(BaseModel):
    routes: list[Route] = Field(..., description="List of routes")
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
    phases: list[str] = Field(..., description="List of phases in execution order")
    purpose: str = Field(..., description="What this workflow does")
    cost_range: str = Field(..., description="Estimated cost range (e.g., $0.20-0.50)")
    best_for: list[str] = Field(..., description="Best use cases")

class WorkflowCatalogResponse(BaseModel):
    workflows: list[WorkflowTemplate] = Field(..., description="List of available workflow templates")
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
    timestamp: str | None = Field(None, description="ISO 8601 timestamp")

class CostData(BaseModel):
    adw_id: str = Field(..., description="ADW workflow identifier")
    phases: list[PhaseCost] = Field(..., description="List of phase costs")
    total_cost: float = Field(..., description="Total cost in dollars")
    cache_efficiency_percent: float = Field(..., description="Cache efficiency percentage (0-100)")
    cache_savings_amount: float = Field(..., description="Estimated savings from caching in dollars")
    total_tokens: int = Field(..., description="Total number of tokens used")

class CostResponse(BaseModel):
    cost_data: CostData | None = Field(None, description="Cost data if available")
    error: str | None = Field(None, description="Error message if any")

# Workflow History Models
class WorkflowHistoryCostBreakdown(BaseModel):
    estimated_total: float = Field(0.0, description="Estimated total cost")
    actual_total: float = Field(0.0, description="Actual total cost")
    estimated_per_step: float = Field(0.0, description="Estimated cost per step")
    actual_per_step: float = Field(0.0, description="Actual cost per step")
    cost_per_token: float = Field(0.0, description="Cost per token")
    by_phase: dict[str, float] | None = Field(None, description="Cost breakdown by phase")

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
    issue_number: int | None = Field(None, description="GitHub issue number")
    nl_input: str | None = Field(None, description="Natural language input from user")
    github_url: str | None = Field(None, description="GitHub issue URL")
    workflow_template: str | None = Field(None, description="Workflow template name")
    model_used: str | None = Field(None, description="Model used for workflow")
    status: Literal["pending", "running", "completed", "failed"] = Field(..., description="Workflow status")

    # Time tracking
    start_time: str | None = Field(None, description="Start time (ISO format)")
    end_time: str | None = Field(None, description="End time (ISO format)")
    duration_seconds: int | None = Field(None, description="Duration in seconds")
    created_at: str = Field(..., description="Record creation time")
    updated_at: str = Field(..., description="Last update time")

    # Progress tracking
    error_message: str | None = Field(None, description="Error message if failed")
    phase_count: int | None = Field(None, description="Total number of phases")
    current_phase: str | None = Field(None, description="Current phase name")
    success_rate: float | None = Field(None, description="Success rate percentage")
    retry_count: int = Field(0, description="Number of retries")
    steps_completed: int = Field(0, description="Number of steps completed")
    steps_total: int = Field(0, description="Total number of steps")

    # Resource usage
    worktree_path: str | None = Field(None, description="Path to worktree")
    backend_port: int | None = Field(None, description="Backend server port")
    frontend_port: int | None = Field(None, description="Frontend server port")
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
    structured_input: dict[str, Any] | None = Field(None, description="Structured workflow input")
    cost_breakdown: WorkflowHistoryCostBreakdown | None = Field(None, description="Cost breakdown details")
    token_breakdown: WorkflowHistoryTokenBreakdown | None = Field(None, description="Token breakdown details")

    # Performance metrics
    phase_durations: dict[str, int] | None = Field(None, description="Duration in seconds per phase")
    idle_time_seconds: int | None = Field(None, description="Idle time between phases")
    bottleneck_phase: str | None = Field(None, description="Phase that took longest")

    # Error analysis
    error_category: str | None = Field(None, description="Categorized error type")
    retry_reasons: list[str] | None = Field(None, description="List of retry trigger reasons")
    error_phase_distribution: dict[str, int] | None = Field(None, description="Error count by phase")
    recovery_time_seconds: int | None = Field(None, description="Time spent in error recovery")

    # Complexity tracking
    complexity_estimated: str | None = Field(None, description="Estimated complexity (low/medium/high)")
    complexity_actual: str | None = Field(None, description="Actual complexity (low/medium/high)")

    # Phase 3A: Analytics fields (temporal and scoring)
    hour_of_day: int = Field(-1, description="Hour of day (0-23) when workflow started")
    day_of_week: int = Field(-1, description="Day of week (0=Monday, 6=Sunday) when workflow started")
    nl_input_clarity_score: float = Field(0.0, description="Natural language input clarity score (0-100)")
    cost_efficiency_score: float = Field(0.0, description="Cost efficiency score (0-100)")
    performance_score: float = Field(0.0, description="Performance score (0-100)")
    quality_score: float = Field(0.0, description="Quality score (0-100)")

    # Phase 3B: Scoring version tracking
    scoring_version: str | None = Field("1.0", description="Scoring algorithm version")

    # Phase 3D: Insights & Recommendations
    anomaly_flags: list[str] | None = Field(None, description="List of anomaly messages")
    optimization_recommendations: list[str] | None = Field(None, description="List of optimization recommendations")

class WorkflowHistoryAnalytics(BaseModel):
    total_workflows: int = Field(0, description="Total number of workflows")
    completed_workflows: int = Field(0, description="Number of completed workflows")
    failed_workflows: int = Field(0, description="Number of failed workflows")
    avg_duration_seconds: float = Field(0.0, description="Average duration in seconds")
    success_rate_percent: float = Field(0.0, description="Overall success rate percentage")
    workflows_by_model: dict[str, int] = Field(default_factory=dict, description="Workflow count by model")
    workflows_by_template: dict[str, int] = Field(default_factory=dict, description="Workflow count by template")
    workflows_by_status: dict[str, int] = Field(default_factory=dict, description="Workflow count by status")
    avg_cost: float = Field(0.0, description="Average cost per workflow")
    total_cost: float = Field(0.0, description="Total cost across all workflows")
    avg_tokens: float = Field(0.0, description="Average tokens per workflow")
    avg_cache_efficiency: float = Field(0.0, description="Average cache efficiency percentage")

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

class WorkflowHistoryResponse(BaseModel):
    workflows: list[WorkflowHistoryItem] = Field(..., description="List of workflow history items")
    total_count: int = Field(..., description="Total count of workflows (before pagination)")
    analytics: WorkflowHistoryAnalytics = Field(..., description="Analytics summary")

# Workflow History Resync Models
class ResyncRequest(BaseModel):
    adw_id: str | None = Field(None, description="Optional ADW ID to resync single workflow")
    force: bool = Field(False, description="Clear existing cost data before resync")

class ResyncResponse(BaseModel):
    resynced_count: int = Field(..., description="Number of workflows resynced")
    workflows: list[dict[str, Any]] = Field(..., description="List of resynced workflow summaries")
    errors: list[str] = Field(default_factory=list, description="List of error messages")
    message: str | None = Field(None, description="Optional status message")

# Phase 3: Advanced Analytics Models
class WorkflowAnalyticsDetail(BaseModel):
    """Detailed analytics for a specific workflow"""
    adw_id: str = Field(..., description="ADW workflow identifier")

    # Efficiency scores
    cost_efficiency_score: float | None = Field(None, description="Cost efficiency score (0-100)")
    performance_score: float | None = Field(None, description="Performance score (0-100)")
    quality_score: float | None = Field(None, description="Quality score (0-100)")

    # Comparisons
    similar_workflow_ids: list[str] = Field(default_factory=list, description="Similar workflow IDs")
    anomaly_flags: list[str] = Field(default_factory=list, description="Detected anomalies")
    optimization_recommendations: list[str] = Field(default_factory=list, description="Optimization tips")

    # Input quality
    nl_input_clarity_score: float | None = Field(None, description="NL input clarity (0-100)")
    nl_input_word_count: int | None = Field(None, description="Word count")

class TrendDataPoint(BaseModel):
    """Single data point in trend analysis"""
    timestamp: str = Field(..., description="Timestamp (ISO format)")
    value: float = Field(..., description="Metric value")
    count: int = Field(0, description="Number of workflows in this period")

class WorkflowTrends(BaseModel):
    """Trend data over time"""
    cost_trend: list[TrendDataPoint] = Field(default_factory=list, description="Cost over time")
    duration_trend: list[TrendDataPoint] = Field(default_factory=list, description="Duration over time")
    success_rate_trend: list[TrendDataPoint] = Field(default_factory=list, description="Success rate over time")
    cache_efficiency_trend: list[TrendDataPoint] = Field(default_factory=list, description="Cache efficiency over time")

class CostPrediction(BaseModel):
    """Cost prediction for a workflow configuration"""
    predicted_cost: float = Field(..., description="Predicted cost in USD")
    confidence: float = Field(..., description="Prediction confidence (0-100)")
    sample_size: int = Field(..., description="Number of historical workflows used")
    min_cost: float = Field(..., description="Minimum cost from historical data")
    max_cost: float = Field(..., description="Maximum cost from historical data")
    avg_cost: float = Field(..., description="Average cost from historical data")
