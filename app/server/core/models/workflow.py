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
    branch_name: str | None = Field(None, description="Git branch name for this workflow")
    plan_file: str | None = Field(None, description="Path to plan file (if completed planning)")
    issue_class: str | None = Field(None, description="Issue classification (e.g., /bug, /feature, /chore)")

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
    avg_cost_per_completion: float = Field(0.0, description="Average cost per workflow execution (includes completed and failed, reflects true system efficiency)")
    cost_trend_7day: float = Field(0.0, description="7-day cost trend percentage (positive = increasing, includes both completed and failed workflows)")
    cost_trend_30day: float = Field(0.0, description="30-day cost trend percentage (positive = increasing, includes both completed and failed workflows)")
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


# Planned Features Models (Panel 5)
class PlannedFeature(BaseModel):
    """Planned feature or session model."""
    id: int | None = None
    item_type: str = Field(..., description="Type: 'session', 'feature', 'bug', 'enhancement'")
    title: str = Field(..., description="Feature or session title")
    description: str | None = Field(None, description="Detailed description")
    status: str = Field(..., description="Status: 'planned', 'in_progress', 'completed', 'cancelled'")
    priority: str | None = Field(None, description="Priority: 'high', 'medium', 'low'")
    estimated_hours: float | None = Field(None, description="Estimated hours to complete")
    actual_hours: float | None = Field(None, description="Actual hours spent")
    session_number: int | None = Field(None, description="Session number (for session items)")
    github_issue_number: int | None = Field(None, description="Related GitHub issue number")
    parent_id: int | None = Field(None, description="Parent feature ID for hierarchical features")
    tags: list[str] = Field(default_factory=list, description="Tags for categorization")
    completion_notes: str | None = Field(None, description="Notes added when completed")
    generated_plan: dict[str, Any] | None = Field(None, description="AI-generated implementation plan (PlanSummary JSON)")
    workflow_type: str | None = Field("adw_sdlc_complete_iso", description="ADW workflow template (e.g., adw_sdlc_complete_iso, adw_sdlc_from_build_iso)")
    created_at: str | None = Field(None, description="Creation timestamp (ISO format)")
    updated_at: str | None = Field(None, description="Last update timestamp (ISO format)")
    started_at: str | None = Field(None, description="Start timestamp (ISO format)")
    completed_at: str | None = Field(None, description="Completion timestamp (ISO format)")

    class Config:
        from_attributes = True


class PlannedFeatureCreate(BaseModel):
    """Model for creating a new planned feature."""
    item_type: str = Field(..., description="Type: 'session', 'feature', 'bug', 'enhancement'")
    title: str = Field(..., description="Feature or session title")
    description: str | None = Field(None, description="Detailed description")
    status: str = Field("planned", description="Initial status (default: 'planned')")
    priority: str | None = Field(None, description="Priority: 'high', 'medium', 'low'")
    estimated_hours: float | None = Field(None, description="Estimated hours to complete")
    session_number: int | None = Field(None, description="Session number (for session items)")
    github_issue_number: int | None = Field(None, description="Related GitHub issue number")
    parent_id: int | None = Field(None, description="Parent feature ID")
    tags: list[str] = Field(default_factory=list, description="Tags for categorization")
    workflow_type: str | None = Field("adw_sdlc_complete_iso", description="ADW workflow template to use")


class PlannedFeatureUpdate(BaseModel):
    """Model for updating a planned feature."""
    title: str | None = Field(None, description="Feature or session title")
    description: str | None = Field(None, description="Detailed description")
    status: str | None = Field(None, description="Status: 'planned', 'in_progress', 'completed', 'cancelled'")
    priority: str | None = Field(None, description="Priority: 'high', 'medium', 'low'")
    estimated_hours: float | None = Field(None, description="Estimated hours to complete")
    actual_hours: float | None = Field(None, description="Actual hours spent")
    github_issue_number: int | None = Field(None, description="Related GitHub issue number")
    tags: list[str] | None = Field(None, description="Tags for categorization")
    completion_notes: str | None = Field(None, description="Notes added when completed")
    generated_plan: dict[str, Any] | None = Field(None, description="AI-generated implementation plan (PlanSummary JSON)")
    workflow_type: str | None = Field(None, description="ADW workflow template to use")


# Cost Analytics Models
class PhaseBreakdownResponse(BaseModel):
    """Response model for phase cost breakdown."""
    phase_costs: dict[str, float] = Field(..., description="Cost by phase name")
    phase_percentages: dict[str, float] = Field(..., description="Percentage by phase name")
    phase_counts: dict[str, int] = Field(..., description="Occurrence count by phase name")
    total: float = Field(..., description="Total cost across all phases")
    average_per_workflow: float = Field(..., description="Average cost per workflow")
    workflow_count: int = Field(..., description="Number of workflows analyzed")


class WorkflowBreakdownResponse(BaseModel):
    """Response model for workflow type cost breakdown."""
    by_type: dict[str, float] = Field(..., description="Total cost by workflow type")
    count_by_type: dict[str, int] = Field(..., description="Workflow count by type")
    average_by_type: dict[str, float] = Field(..., description="Average cost by type")


class TimeSeriesDataPointResponse(BaseModel):
    """Single data point in time series."""
    date: str = Field(..., description="Date (ISO format)")
    cost: float = Field(..., description="Total cost for this date")
    workflow_count: int = Field(..., description="Number of workflows on this date")


class TrendAnalysisResponse(BaseModel):
    """Response model for cost trend analysis."""
    daily_costs: list[TimeSeriesDataPointResponse] = Field(..., description="Daily cost data points")
    moving_average: list[float] = Field(..., description="7-day moving average")
    trend_direction: str = Field(..., description="Trend direction: increasing, decreasing, stable")
    percentage_change: float = Field(..., description="Overall percentage change")
    total_cost: float = Field(..., description="Total cost in period")
    average_daily_cost: float = Field(..., description="Average cost per day")


class OptimizationOpportunityResponse(BaseModel):
    """Response model for optimization opportunity."""
    category: str = Field(..., description="Category: phase, workflow_type, outlier")
    description: str = Field(..., description="Description of the opportunity")
    current_cost: float = Field(..., description="Current cost")
    target_cost: float = Field(..., description="Target cost")
    estimated_savings: float = Field(..., description="Estimated monthly savings")
    recommendation: str = Field(..., description="Actionable recommendation")
    priority: str = Field(..., description="Priority: high, medium, low")


# Error Analytics Models
class ErrorSummary(BaseModel):
    """Summary statistics for workflow errors."""
    total_workflows: int = Field(..., description="Total number of workflows analyzed")
    failed_workflows: int = Field(..., description="Number of failed workflows")
    failure_rate: float = Field(..., description="Failure rate percentage (0-100)")
    top_errors: list[tuple[str, int]] = Field(..., description="Top error patterns with counts")
    most_problematic_phase: str | None = Field(None, description="Phase with most failures")
    error_categories: dict[str, int] = Field(default_factory=dict, description="Error count by category")


class PhaseErrorBreakdown(BaseModel):
    """Error analysis broken down by workflow phase."""
    phase_error_counts: dict[str, int] = Field(..., description="Error count by phase name")
    phase_failure_rates: dict[str, float] = Field(..., description="Failure rate by phase (0-100)")
    total_errors: int = Field(..., description="Total number of errors across all phases")
    most_error_prone_phase: str | None = Field(None, description="Phase with highest error rate")


class ErrorPattern(BaseModel):
    """Detected error pattern with metadata."""
    pattern_name: str = Field(..., description="Pattern name (e.g., 'Import Error', 'Connection Error')")
    pattern_category: str = Field(..., description="Error category")
    occurrences: int = Field(..., description="Number of times this pattern occurred")
    example_message: str = Field(..., description="Example error message")
    affected_workflows: list[str] = Field(default_factory=list, description="List of affected ADW IDs")
    recommendation: str = Field(..., description="Actionable debugging recommendation")
    severity: str = Field(..., description="Severity: high, medium, low")


class ErrorTrendDataPoint(BaseModel):
    """Single data point in error trend analysis."""
    date: str = Field(..., description="Date (ISO format)")
    error_count: int = Field(..., description="Number of errors on this date")
    failure_rate: float = Field(..., description="Failure rate percentage for this date")
    workflow_count: int = Field(..., description="Total workflows on this date")


class ErrorTrends(BaseModel):
    """Error trend data over time."""
    daily_errors: list[ErrorTrendDataPoint] = Field(..., description="Daily error trends")
    trend_direction: str = Field(..., description="Trend direction: increasing, decreasing, stable")
    percentage_change: float = Field(..., description="Overall percentage change in error rate")
    average_daily_failures: float = Field(..., description="Average failures per day")


class DebugRecommendation(BaseModel):
    """Debugging recommendation based on error analysis."""
    issue: str = Field(..., description="Issue description")
    severity: str = Field(..., description="Severity: high, medium, low")
    root_cause: str = Field(..., description="Likely root cause")
    solution: str = Field(..., description="Recommended solution")
    estimated_fix_time: str = Field(..., description="Estimated time to fix")
    affected_count: int = Field(..., description="Number of workflows affected")


# Latency Analytics Models
class PhaseStatsResponse(BaseModel):
    """Statistics for a single phase."""
    p50: float = Field(..., description="Median latency (50th percentile) in seconds")
    p95: float = Field(..., description="95th percentile latency in seconds")
    p99: float = Field(..., description="99th percentile latency in seconds")
    average: float = Field(..., description="Average latency in seconds")
    min: float = Field(..., description="Minimum latency in seconds")
    max: float = Field(..., description="Maximum latency in seconds")
    std_dev: float = Field(..., description="Standard deviation in seconds")
    sample_count: int = Field(..., description="Number of workflows analyzed")


class PhaseLatencyBreakdownResponse(BaseModel):
    """Latency breakdown by workflow phase."""
    phase_latencies: dict[str, PhaseStatsResponse] = Field(..., description="Latency stats by phase name")
    total_duration_avg: float = Field(..., description="Average total workflow duration in seconds")


class LatencySummaryResponse(BaseModel):
    """Overall latency summary statistics."""
    total_workflows: int = Field(..., description="Total number of workflows analyzed")
    average_duration_seconds: float = Field(..., description="Average workflow duration in seconds")
    p50_duration: float = Field(..., description="Median workflow duration (50th percentile) in seconds")
    p95_duration: float = Field(..., description="95th percentile workflow duration in seconds")
    p99_duration: float = Field(..., description="99th percentile workflow duration in seconds")
    slowest_phase: str = Field(..., description="Phase with highest average latency")
    slowest_phase_avg: float = Field(..., description="Average latency of slowest phase in seconds")


class BottleneckResponse(BaseModel):
    """Identified performance bottleneck."""
    phase: str = Field(..., description="Phase name")
    p95_latency: float = Field(..., description="95th percentile latency for this phase in seconds")
    threshold: float = Field(..., description="Threshold used for bottleneck detection in seconds")
    percentage_over_threshold: float = Field(..., description="Estimated percentage of workflows exceeding threshold")
    affected_workflows: int = Field(..., description="Estimated number of affected workflows")
    recommendation: str = Field(..., description="Optimization recommendation for this bottleneck")
    estimated_speedup: str = Field(..., description="Estimated speedup potential (e.g., '30-40% faster')")


class TimeSeriesLatencyDataPointResponse(BaseModel):
    """Single data point in latency time series."""
    date: str = Field(..., description="Date (ISO format)")
    duration: float = Field(..., description="Average duration for this date in seconds")
    workflow_count: int = Field(..., description="Number of workflows on this date")


class TrendDataResponse(BaseModel):
    """Latency trend analysis over time."""
    daily_latencies: list[TimeSeriesLatencyDataPointResponse] = Field(..., description="Daily latency data points")
    moving_average: list[float] = Field(..., description="7-day moving average of latencies")
    trend_direction: str = Field(..., description="Trend direction: increasing, decreasing, stable")
    percentage_change: float = Field(..., description="Overall percentage change in latency")
    average_daily_duration: float = Field(..., description="Average duration per day in seconds")


class OptimizationRecommendationResponse(BaseModel):
    """Optimization recommendation for improving latency."""
    target: str = Field(..., description="Target phase or component for optimization")
    current_latency: float = Field(..., description="Current average latency in seconds")
    target_latency: float = Field(..., description="Target latency after optimization in seconds")
    improvement_percentage: float = Field(..., description="Expected improvement percentage")
    actions: list[str] = Field(..., description="List of specific optimization actions")


# ROI Tracking Models (Session 12)
class PatternExecution(BaseModel):
    """Individual pattern execution instance for ROI tracking."""
    id: int | None = Field(None, description="Execution record ID")
    pattern_id: str = Field(..., description="Reference to pattern being executed")
    workflow_id: int | None = Field(None, description="Reference to workflow where pattern was executed")
    execution_time_seconds: float = Field(..., description="Actual execution time in seconds")
    estimated_time_seconds: float = Field(..., description="Estimated execution time in seconds")
    actual_cost: float = Field(..., description="Actual cost in USD")
    estimated_cost: float = Field(..., description="Estimated cost in USD")
    success: bool = Field(..., description="Whether execution completed successfully")
    error_message: str | None = Field(None, description="Error details if execution failed")
    executed_at: str | None = Field(None, description="Execution timestamp (ISO format)")


class PatternROISummary(BaseModel):
    """Aggregated ROI metrics for a pattern."""
    pattern_id: str = Field(..., description="Pattern identifier")
    total_executions: int = Field(0, description="Total number of executions")
    successful_executions: int = Field(0, description="Number of successful executions")
    success_rate: float = Field(0.0, description="Success rate (0.0 to 1.0)")
    total_time_saved_seconds: float = Field(0.0, description="Total time saved across all successful executions")
    total_cost_saved_usd: float = Field(0.0, description="Total cost saved across all successful executions")
    average_time_saved_seconds: float = Field(0.0, description="Average time saved per successful execution")
    average_cost_saved_usd: float = Field(0.0, description="Average cost saved per successful execution")
    roi_percentage: float = Field(0.0, description="Return on investment percentage: (savings / investment) * 100")
    last_updated: str | None = Field(None, description="Last update timestamp (ISO format)")


class ROIReport(BaseModel):
    """Comprehensive ROI report for a pattern."""
    pattern_id: str = Field(..., description="Pattern identifier")
    pattern_name: str = Field(..., description="Human-readable pattern name")
    approval_date: str = Field(..., description="Pattern approval date (ISO format)")
    executions: list[PatternExecution] = Field(default_factory=list, description="List of execution records")
    summary: PatternROISummary = Field(..., description="Aggregated ROI summary")
    effectiveness_rating: str = Field(..., description="Effectiveness rating: excellent, good, acceptable, poor, failed")
    recommendation: str = Field(..., description="Actionable recommendation based on performance")


# Confidence Update Models (Session 13)
class ConfidenceUpdate(BaseModel):
    """Record of a confidence score update for a pattern."""
    id: int | None = Field(None, description="Update record ID")
    pattern_id: str = Field(..., description="Pattern identifier")
    old_confidence: float = Field(..., description="Previous confidence score (0.0-1.0)")
    new_confidence: float = Field(..., description="New confidence score (0.0-1.0)")
    adjustment_reason: str = Field(..., description="Human-readable explanation for adjustment")
    roi_data: dict[str, Any] = Field(default_factory=dict, description="Snapshot of ROI metrics at time of update")
    updated_by: str = Field("system", description="Who/what triggered the update")
    updated_at: str | None = Field(None, description="Timestamp when confidence was updated (ISO format)")


class StatusChangeRecommendation(BaseModel):
    """Recommendation for pattern status change based on performance."""
    pattern_id: str = Field(..., description="Pattern identifier")
    current_status: str = Field(..., description="Current pattern status (approved, pending, rejected)")
    recommended_status: str = Field(..., description="Recommended new status")
    reason: str = Field(..., description="Explanation for the recommendation")
    severity: str = Field(..., description="Recommendation severity: high, medium, low")
    confidence_score: float | None = Field(None, description="Current confidence score")
    roi_percentage: float | None = Field(None, description="Current ROI percentage")
