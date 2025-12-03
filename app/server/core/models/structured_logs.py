"""
Structured Logging Models

Pydantic models for structured logging with JSONL serialization.
Extends the observability models with additional context and metadata.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field


class LogLevel(str, Enum):
    """Log severity levels."""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class LogSource(str, Enum):
    """Source of the log event."""
    ADW_WORKFLOW = "adw_workflow"
    BACKEND_API = "backend_api"
    FRONTEND = "frontend"
    DATABASE = "database"
    SYSTEM = "system"


class BaseLogEvent(BaseModel):
    """Base model for all log events with common fields."""

    # Event Identification
    event_id: str = Field(description="Unique event ID")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Event timestamp (UTC)")
    level: LogLevel = Field(default=LogLevel.INFO, description="Log severity level")
    source: LogSource = Field(description="Source of the log event")

    # Context
    message: str = Field(description="Human-readable log message")
    context: dict[str, Any] = Field(default_factory=dict, description="Additional context data")

    # Correlation
    correlation_id: str | None = Field(None, description="Correlation ID for tracking related events")
    session_id: str | None = Field(None, description="User session ID")
    request_id: str | None = Field(None, description="HTTP request ID")

    class Config:
        json_schema_extra = {
            "example": {
                "event_id": "evt_abc123",
                "timestamp": "2025-12-02T10:30:00Z",
                "level": "info",
                "source": "system",
                "message": "Application started",
                "context": {"version": "0.1.0"},
            }
        }


class WorkflowLogEvent(BaseLogEvent):
    """Log event for ADW workflow execution."""

    # Workflow Identification
    adw_id: str = Field(description="ADW workflow ID")
    issue_number: int = Field(description="GitHub issue number")
    workflow_template: str | None = Field(None, description="Workflow template name")

    # Workflow Status
    workflow_status: Literal["started", "in_progress", "completed", "failed", "cancelled"] = Field(
        description="Overall workflow status"
    )

    # Phase Info (if applicable)
    phase_name: str | None = Field(None, description="Current phase name")
    phase_number: int | None = Field(None, description="Current phase number")
    phase_status: Literal["started", "completed", "failed", "skipped"] | None = Field(
        None, description="Phase status"
    )

    # Metrics
    duration_seconds: float | None = Field(None, description="Duration in seconds")
    tokens_used: int | None = Field(None, description="Tokens consumed")
    cost_usd: float | None = Field(None, description="Cost in USD")

    # Error Info
    error_message: str | None = Field(None, description="Error message if failed")
    error_type: str | None = Field(None, description="Error type/class")
    stack_trace: str | None = Field(None, description="Stack trace if available")

    class Config:
        json_schema_extra = {
            "example": {
                "event_id": "evt_wf_123",
                "timestamp": "2025-12-02T10:30:00Z",
                "level": "info",
                "source": "adw_workflow",
                "message": "Phase completed successfully",
                "adw_id": "adw-abc123",
                "issue_number": 42,
                "workflow_template": "adw_sdlc_complete_iso",
                "workflow_status": "in_progress",
                "phase_name": "Plan",
                "phase_number": 1,
                "phase_status": "completed",
                "duration_seconds": 45.2,
                "tokens_used": 15000,
                "cost_usd": 0.05,
            }
        }


class PhaseLogEvent(BaseLogEvent):
    """Log event specifically for ADW phase execution."""

    # Phase Identification
    adw_id: str
    issue_number: int
    phase_name: str
    phase_number: int
    workflow_template: str | None = None

    # Phase Details
    phase_status: Literal["started", "completed", "failed", "skipped"]
    phase_type: str | None = Field(None, description="Type of phase (plan, build, test, etc.)")

    # Execution Details
    started_at: datetime | None = None
    completed_at: datetime | None = None
    duration_seconds: float | None = None

    # Metrics
    tokens_used: int | None = None
    cost_usd: float | None = None
    cache_hits: int | None = Field(None, description="Number of cache hits")
    cache_efficiency: float | None = Field(None, description="Cache efficiency percentage")

    # Quality Metrics
    lint_errors: int | None = Field(None, description="Number of lint errors")
    test_pass_rate: float | None = Field(None, description="Test pass rate percentage")

    # Error Info
    error_message: str | None = None
    error_type: str | None = None
    retry_count: int | None = Field(None, description="Number of retries attempted")


class SystemLogEvent(BaseLogEvent):
    """Log event for system-level operations."""

    # System Component
    component: str = Field(description="System component name")
    operation: str = Field(description="Operation being performed")

    # Operation Result
    status: Literal["started", "success", "failure", "warning"] = Field(
        description="Operation status"
    )

    # Performance Metrics
    duration_ms: float | None = Field(None, description="Operation duration in milliseconds")
    memory_usage_mb: float | None = Field(None, description="Memory usage in MB")
    cpu_usage_percent: float | None = Field(None, description="CPU usage percentage")

    # Error Info
    error_message: str | None = None
    error_type: str | None = None


class DatabaseLogEvent(BaseLogEvent):
    """Log event for database operations."""

    # Database Operation
    operation: Literal["select", "insert", "update", "delete", "migrate"] = Field(
        description="Database operation type"
    )
    table: str = Field(description="Database table name")

    # Query Details
    query: str | None = Field(None, description="SQL query (sanitized)")
    params_count: int | None = Field(None, description="Number of parameters")

    # Performance
    duration_ms: float = Field(description="Query duration in milliseconds")
    rows_affected: int | None = Field(None, description="Number of rows affected")

    # Result
    status: Literal["success", "failure"] = Field(description="Operation status")
    error_message: str | None = None


class HTTPLogEvent(BaseLogEvent):
    """Log event for HTTP requests."""

    # Request Details
    method: str = Field(description="HTTP method (GET, POST, etc.)")
    path: str = Field(description="Request path")
    status_code: int = Field(description="HTTP status code")

    # Client Info
    client_ip: str | None = Field(None, description="Client IP address")
    user_agent: str | None = Field(None, description="User agent string")

    # Performance
    duration_ms: float = Field(description="Request duration in milliseconds")
    response_size_bytes: int | None = Field(None, description="Response size in bytes")

    # Error Info (for 4xx/5xx)
    error_message: str | None = None
    error_type: str | None = None


class MetricsLogEvent(BaseLogEvent):
    """Log event for metrics and measurements."""

    # Metric Details
    metric_name: str = Field(description="Name of the metric")
    metric_value: float = Field(description="Metric value")
    metric_unit: str = Field(description="Unit of measurement")

    # Dimensions
    dimensions: dict[str, str] = Field(
        default_factory=dict,
        description="Metric dimensions (tags)"
    )

    # Aggregation
    aggregation_type: Literal["sum", "avg", "min", "max", "count"] | None = Field(
        None, description="Type of aggregation"
    )
    sample_count: int | None = Field(None, description="Number of samples")


# Type alias for any log event
LogEvent = (
    BaseLogEvent
    | WorkflowLogEvent
    | PhaseLogEvent
    | SystemLogEvent
    | DatabaseLogEvent
    | HTTPLogEvent
    | MetricsLogEvent
)
