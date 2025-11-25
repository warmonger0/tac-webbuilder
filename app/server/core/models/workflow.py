"""Workflow execution and history models."""

from typing import Any, Literal

from pydantic import BaseModel, Field


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


# ADW Monitor Models
class AdwWorkflowStatus(BaseModel):
    """Status of a single ADW workflow for monitoring"""
    adw_id: str = Field(..., description="ADW workflow identifier")
    issue_number: int | None = Field(None, description="GitHub issue number (parent issue)")
    pr_number: int | None = Field(None, description="Pull request number created for this issue")
    issue_class: str = Field("", description="Issue classification (/bug, /feature, etc.)")
    title: str = Field("", description="Workflow title (truncated nl_input)")
    status: Literal["running", "completed", "failed", "paused", "queued"] = Field(..., description="Current workflow status")
    current_phase: str | None = Field(None, description="Current phase name")
    phase_progress: float = Field(0.0, description="Phase progress percentage (0-100)")
    workflow_template: str = Field("", description="Workflow template name")
    start_time: str | None = Field(None, description="Start time (ISO format)")
    end_time: str | None = Field(None, description="End time (ISO format)")
    duration_seconds: int | None = Field(None, description="Duration in seconds")
    github_url: str | None = Field(None, description="GitHub issue URL")
    worktree_path: str | None = Field(None, description="Path to worktree directory")
    current_cost: float | None = Field(None, description="Current cost in dollars")
    estimated_cost_total: float | None = Field(None, description="Estimated total cost in dollars")
    error_count: int = Field(0, description="Number of errors encountered")
    last_error: str | None = Field(None, description="Last error message")
    is_process_active: bool = Field(False, description="Whether process is actively running")
    phases_completed: list[str] = Field(default_factory=list, description="List of completed phase names")
    total_phases: int = Field(8, description="Total number of phases in workflow")


class AdwMonitorSummary(BaseModel):
    """Summary statistics for ADW monitoring"""
    total: int = Field(0, description="Total number of workflows")
    running: int = Field(0, description="Number of running workflows")
    completed: int = Field(0, description="Number of completed workflows")
    failed: int = Field(0, description="Number of failed workflows")
    paused: int = Field(0, description="Number of paused workflows")


# ADW Health Check Models
class PortHealthCheck(BaseModel):
    """Health check for port allocation"""
    status: Literal["ok", "warning", "critical"] = Field(..., description="Health status")
    backend_port: int | None = Field(None, description="Backend port number")
    frontend_port: int | None = Field(None, description="Frontend port number")
    available: bool = Field(True, description="Whether ports are available")
    in_use: bool = Field(False, description="Whether ports are currently in use")
    conflicts: list[dict[str, Any]] = Field(default_factory=list, description="List of port conflicts")
    warnings: list[str] = Field(default_factory=list, description="Warning messages")


class WorktreeHealthCheck(BaseModel):
    """Health check for worktree status"""
    status: Literal["ok", "warning", "critical"] = Field(..., description="Health status")
    path: str | None = Field(None, description="Worktree directory path")
    exists: bool = Field(False, description="Whether worktree directory exists")
    clean: bool = Field(True, description="Whether worktree has no uncommitted changes")
    uncommitted_files: list[str] = Field(default_factory=list, description="List of uncommitted files")
    git_registered: bool = Field(False, description="Whether git knows about this worktree")
    warnings: list[str] = Field(default_factory=list, description="Warning messages")


class StateFileHealthCheck(BaseModel):
    """Health check for state file validity"""
    status: Literal["ok", "warning", "critical"] = Field(..., description="Health status")
    path: str = Field(..., description="State file path")
    exists: bool = Field(False, description="Whether state file exists")
    valid: bool = Field(False, description="Whether state file is valid JSON")
    last_modified: str | None = Field(None, description="Last modification time (ISO format)")
    age_seconds: int | None = Field(None, description="Age of state file in seconds")
    warnings: list[str] = Field(default_factory=list, description="Warning messages")


class ProcessHealthCheck(BaseModel):
    """Health check for running processes"""
    status: Literal["ok", "warning", "critical"] = Field(..., description="Health status")
    active: bool = Field(False, description="Whether any processes are running")
    processes: list[dict[str, Any]] = Field(default_factory=list, description="List of running processes")
    warnings: list[str] = Field(default_factory=list, description="Warning messages")


class AdwHealthCheckResponse(BaseModel):
    """Complete health check response for an ADW workflow"""
    adw_id: str = Field(..., description="ADW workflow identifier")
    overall_health: Literal["ok", "warning", "critical"] = Field(..., description="Overall health status")
    checks: dict[str, Any] = Field(..., description="Individual health checks (ports, worktree, state_file, process)")
    warnings: list[str] = Field(default_factory=list, description="All warning messages")
    checked_at: str = Field(..., description="Timestamp of health check (ISO format)")
