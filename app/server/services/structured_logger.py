"""
Structured Logging Service

Service for writing structured logs to JSONL files with per-workflow isolation.
Provides zero-overhead logging with Pydantic serialization.
"""

import json
import logging
import os
import uuid
from datetime import datetime
from pathlib import Path
from threading import Lock
from typing import Optional

from core.models.structured_logs import (
    BaseLogEvent,
    DatabaseLogEvent,
    HTTPLogEvent,
    LogEvent,
    LogLevel,
    LogSource,
    MetricsLogEvent,
    PhaseLogEvent,
    SystemLogEvent,
    WorkflowLogEvent,
)

logger = logging.getLogger(__name__)


class StructuredLogger:
    """
    Structured logging service with JSONL output and per-workflow isolation.

    Features:
    - Writes logs to JSONL files for easy parsing and analysis
    - Per-workflow log isolation (separate files per ADW ID)
    - Pydantic model serialization for type safety
    - Zero-overhead: non-blocking, failures don't raise exceptions
    - Automatic log directory creation
    - Thread-safe file writing

    Usage:
        >>> logger = StructuredLogger()
        >>> logger.log_workflow_event(
        ...     adw_id="adw-abc123",
        ...     issue_number=42,
        ...     message="Phase completed",
        ...     workflow_status="in_progress",
        ...     phase_name="Plan",
        ...     phase_status="completed"
        ... )
    """

    def __init__(
        self,
        log_dir: Optional[Path] = None,
        enable_console: bool = False,
        enable_file: bool = True,
    ):
        """
        Initialize the structured logger.

        Args:
            log_dir: Directory for log files (default: logs/structured/)
            enable_console: Whether to also log to console (default: False)
            enable_file: Whether to write to files (default: True)
        """
        # Use project root logs directory
        if log_dir is None:
            project_root = Path(__file__).parent.parent.parent.parent
            log_dir = project_root / "logs" / "structured"

        self.log_dir = Path(log_dir)
        self.enable_console = enable_console
        self.enable_file = enable_file

        # Thread safety
        self._write_lock = Lock()

        # Create log directory if needed
        if self.enable_file:
            try:
                self.log_dir.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                logger.warning(f"Failed to create log directory {self.log_dir}: {e}")
                self.enable_file = False

    def _get_log_file(self, adw_id: Optional[str] = None, suffix: str = "general") -> Path:
        """
        Get the appropriate log file path.

        Args:
            adw_id: ADW workflow ID for per-workflow isolation
            suffix: Log file suffix (default: "general")

        Returns:
            Path to the log file
        """
        if adw_id:
            # Per-workflow isolation
            return self.log_dir / f"workflow_{adw_id}.jsonl"
        else:
            # General logs
            date_str = datetime.utcnow().strftime("%Y-%m-%d")
            return self.log_dir / f"{suffix}_{date_str}.jsonl"

    def _write_event(self, event: LogEvent) -> bool:
        """
        Write a log event to the appropriate file(s).

        Args:
            event: The log event to write

        Returns:
            True if successful, False otherwise
        """
        try:
            # Serialize to JSON
            event_json = event.model_dump_json(exclude_none=True, by_alias=True)

            # Console output
            if self.enable_console:
                print(event_json)

            # File output
            if self.enable_file:
                # Determine log file
                adw_id = None
                if isinstance(event, (WorkflowLogEvent, PhaseLogEvent)):
                    adw_id = event.adw_id

                log_file = self._get_log_file(adw_id)

                # Thread-safe write
                with self._write_lock:
                    with open(log_file, "a", encoding="utf-8") as f:
                        f.write(event_json + "\n")

            return True

        except Exception as e:
            logger.debug(f"Failed to write structured log: {e}")
            return False

    def log_event(self, event: LogEvent) -> bool:
        """
        Log a generic event.

        Args:
            event: The log event to write

        Returns:
            True if successful, False otherwise
        """
        return self._write_event(event)

    def log_workflow_event(
        self,
        adw_id: str,
        issue_number: int,
        message: str,
        workflow_status: str,
        level: LogLevel = LogLevel.INFO,
        workflow_template: Optional[str] = None,
        phase_name: Optional[str] = None,
        phase_number: Optional[int] = None,
        phase_status: Optional[str] = None,
        duration_seconds: Optional[float] = None,
        tokens_used: Optional[int] = None,
        cost_usd: Optional[float] = None,
        error_message: Optional[str] = None,
        error_type: Optional[str] = None,
        correlation_id: Optional[str] = None,
        **context,
    ) -> bool:
        """
        Log a workflow event.

        Args:
            adw_id: ADW workflow ID
            issue_number: GitHub issue number
            message: Log message
            workflow_status: Overall workflow status
            level: Log level (default: INFO)
            workflow_template: Workflow template name
            phase_name: Current phase name
            phase_number: Current phase number
            phase_status: Phase status
            duration_seconds: Duration in seconds
            tokens_used: Tokens consumed
            cost_usd: Cost in USD
            error_message: Error message if failed
            error_type: Error type/class
            correlation_id: Correlation ID for tracking
            **context: Additional context data

        Returns:
            True if successful, False otherwise
        """
        event = WorkflowLogEvent(
            event_id=f"evt_{uuid.uuid4().hex[:12]}",
            timestamp=datetime.utcnow(),
            level=level,
            source=LogSource.ADW_WORKFLOW,
            message=message,
            context=context,
            correlation_id=correlation_id,
            adw_id=adw_id,
            issue_number=issue_number,
            workflow_template=workflow_template,
            workflow_status=workflow_status,
            phase_name=phase_name,
            phase_number=phase_number,
            phase_status=phase_status,
            duration_seconds=duration_seconds,
            tokens_used=tokens_used,
            cost_usd=cost_usd,
            error_message=error_message,
            error_type=error_type,
        )
        return self._write_event(event)

    def log_phase_event(
        self,
        adw_id: str,
        issue_number: int,
        phase_name: str,
        phase_number: int,
        phase_status: str,
        message: str,
        level: LogLevel = LogLevel.INFO,
        workflow_template: Optional[str] = None,
        started_at: Optional[datetime] = None,
        completed_at: Optional[datetime] = None,
        duration_seconds: Optional[float] = None,
        tokens_used: Optional[int] = None,
        cost_usd: Optional[float] = None,
        error_message: Optional[str] = None,
        correlation_id: Optional[str] = None,
        **context,
    ) -> bool:
        """
        Log a phase event.

        Args:
            adw_id: ADW workflow ID
            issue_number: GitHub issue number
            phase_name: Phase name
            phase_number: Phase number
            phase_status: Phase status
            message: Log message
            level: Log level (default: INFO)
            workflow_template: Workflow template name
            started_at: Phase start time
            completed_at: Phase completion time
            duration_seconds: Duration in seconds
            tokens_used: Tokens consumed
            cost_usd: Cost in USD
            error_message: Error message if failed
            correlation_id: Correlation ID
            **context: Additional context

        Returns:
            True if successful, False otherwise
        """
        event = PhaseLogEvent(
            event_id=f"evt_{uuid.uuid4().hex[:12]}",
            timestamp=datetime.utcnow(),
            level=level,
            source=LogSource.ADW_WORKFLOW,
            message=message,
            context=context,
            correlation_id=correlation_id,
            adw_id=adw_id,
            issue_number=issue_number,
            phase_name=phase_name,
            phase_number=phase_number,
            workflow_template=workflow_template,
            phase_status=phase_status,
            started_at=started_at,
            completed_at=completed_at,
            duration_seconds=duration_seconds,
            tokens_used=tokens_used,
            cost_usd=cost_usd,
            error_message=error_message,
        )
        return self._write_event(event)

    def log_system_event(
        self,
        component: str,
        operation: str,
        status: str,
        message: str,
        level: LogLevel = LogLevel.INFO,
        duration_ms: Optional[float] = None,
        error_message: Optional[str] = None,
        **context,
    ) -> bool:
        """
        Log a system event.

        Args:
            component: System component name
            operation: Operation being performed
            status: Operation status
            message: Log message
            level: Log level (default: INFO)
            duration_ms: Operation duration in ms
            error_message: Error message if failed
            **context: Additional context

        Returns:
            True if successful, False otherwise
        """
        event = SystemLogEvent(
            event_id=f"evt_{uuid.uuid4().hex[:12]}",
            timestamp=datetime.utcnow(),
            level=level,
            source=LogSource.SYSTEM,
            message=message,
            context=context,
            component=component,
            operation=operation,
            status=status,
            duration_ms=duration_ms,
            error_message=error_message,
        )
        return self._write_event(event)

    def log_database_event(
        self,
        operation: str,
        table: str,
        duration_ms: float,
        status: str,
        message: str,
        level: LogLevel = LogLevel.DEBUG,
        query: Optional[str] = None,
        rows_affected: Optional[int] = None,
        error_message: Optional[str] = None,
        **context,
    ) -> bool:
        """
        Log a database event.

        Args:
            operation: Database operation (select, insert, etc.)
            table: Database table name
            duration_ms: Query duration in ms
            status: Operation status
            message: Log message
            level: Log level (default: DEBUG)
            query: SQL query (sanitized)
            rows_affected: Number of rows affected
            error_message: Error message if failed
            **context: Additional context

        Returns:
            True if successful, False otherwise
        """
        event = DatabaseLogEvent(
            event_id=f"evt_{uuid.uuid4().hex[:12]}",
            timestamp=datetime.utcnow(),
            level=level,
            source=LogSource.DATABASE,
            message=message,
            context=context,
            operation=operation,
            table=table,
            duration_ms=duration_ms,
            status=status,
            query=query,
            rows_affected=rows_affected,
            error_message=error_message,
        )
        return self._write_event(event)

    def log_http_event(
        self,
        method: str,
        path: str,
        status_code: int,
        duration_ms: float,
        message: str,
        level: LogLevel = LogLevel.INFO,
        client_ip: Optional[str] = None,
        error_message: Optional[str] = None,
        request_id: Optional[str] = None,
        **context,
    ) -> bool:
        """
        Log an HTTP event.

        Args:
            method: HTTP method
            path: Request path
            status_code: HTTP status code
            duration_ms: Request duration in ms
            message: Log message
            level: Log level (default: INFO)
            client_ip: Client IP address
            error_message: Error message if failed
            request_id: HTTP request ID
            **context: Additional context

        Returns:
            True if successful, False otherwise
        """
        event = HTTPLogEvent(
            event_id=f"evt_{uuid.uuid4().hex[:12]}",
            timestamp=datetime.utcnow(),
            level=level,
            source=LogSource.BACKEND_API,
            message=message,
            context=context,
            request_id=request_id,
            method=method,
            path=path,
            status_code=status_code,
            duration_ms=duration_ms,
            client_ip=client_ip,
            error_message=error_message,
        )
        return self._write_event(event)

    def log_metric(
        self,
        metric_name: str,
        metric_value: float,
        metric_unit: str,
        message: str,
        dimensions: Optional[dict] = None,
        **context,
    ) -> bool:
        """
        Log a metric event.

        Args:
            metric_name: Name of the metric
            metric_value: Metric value
            metric_unit: Unit of measurement
            message: Log message
            dimensions: Metric dimensions (tags)
            **context: Additional context

        Returns:
            True if successful, False otherwise
        """
        event = MetricsLogEvent(
            event_id=f"evt_{uuid.uuid4().hex[:12]}",
            timestamp=datetime.utcnow(),
            level=LogLevel.INFO,
            source=LogSource.SYSTEM,
            message=message,
            context=context,
            metric_name=metric_name,
            metric_value=metric_value,
            metric_unit=metric_unit,
            dimensions=dimensions or {},
        )
        return self._write_event(event)


# Singleton instance
_structured_logger: Optional[StructuredLogger] = None


def get_structured_logger() -> StructuredLogger:
    """
    Get the global structured logger instance.

    Returns:
        StructuredLogger instance
    """
    global _structured_logger
    if _structured_logger is None:
        _structured_logger = StructuredLogger()
    return _structured_logger
