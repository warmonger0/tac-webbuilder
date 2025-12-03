"""
Structured Logger for ADW Workflows

Lightweight structured logging for ADW workflows with JSONL output.
Self-contained with no dependencies on backend server code.
"""

import json
import logging
import os
import uuid
from datetime import datetime
from pathlib import Path
from threading import Lock
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class ADWStructuredLogger:
    """
    Structured logger for ADW workflows with JSONL output.

    Writes structured logs to JSONL files with per-workflow isolation.
    Zero-overhead design: failures don't raise exceptions.
    """

    def __init__(self, log_dir: Optional[Path] = None):
        """
        Initialize the ADW structured logger.

        Args:
            log_dir: Directory for log files (default: logs/structured/)
        """
        # Use project root logs directory
        if log_dir is None:
            project_root = Path(__file__).parent.parent.parent
            log_dir = project_root / "logs" / "structured"

        self.log_dir = Path(log_dir)
        self._write_lock = Lock()

        # Create log directory
        try:
            self.log_dir.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            logger.warning(f"Failed to create log directory {self.log_dir}: {e}")

    def _write_log(self, log_data: Dict[str, Any], adw_id: str) -> bool:
        """
        Write a log entry to the appropriate JSONL file.

        Args:
            log_data: Log data dictionary
            adw_id: ADW workflow ID for file isolation

        Returns:
            True if successful, False otherwise
        """
        try:
            # Get workflow-specific log file
            log_file = self.log_dir / f"workflow_{adw_id}.jsonl"

            # Thread-safe write
            with self._write_lock:
                with open(log_file, "a", encoding="utf-8") as f:
                    json.dump(log_data, f, default=str)
                    f.write("\n")

            return True

        except Exception as e:
            logger.debug(f"Failed to write structured log: {e}")
            return False

    def log_phase(
        self,
        adw_id: str,
        issue_number: int,
        phase_name: str,
        phase_number: int,
        phase_status: str,
        message: str,
        workflow_template: Optional[str] = None,
        started_at: Optional[datetime] = None,
        completed_at: Optional[datetime] = None,
        duration_seconds: Optional[float] = None,
        tokens_used: Optional[int] = None,
        cost_usd: Optional[float] = None,
        error_message: Optional[str] = None,
        **context,
    ) -> bool:
        """
        Log a phase event.

        Args:
            adw_id: ADW workflow ID
            issue_number: GitHub issue number
            phase_name: Phase name
            phase_number: Phase number
            phase_status: Phase status (started, completed, failed, skipped)
            message: Log message
            workflow_template: Workflow template name
            started_at: Phase start time
            completed_at: Phase completion time
            duration_seconds: Duration in seconds
            tokens_used: Tokens consumed
            cost_usd: Cost in USD
            error_message: Error message if failed
            **context: Additional context

        Returns:
            True if successful, False otherwise
        """
        # Build log entry
        log_data = {
            "event_id": f"evt_{uuid.uuid4().hex[:12]}",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": "error" if phase_status == "failed" else "info",
            "source": "adw_workflow",
            "event_type": "phase",
            "message": message,
            # Workflow info
            "adw_id": adw_id,
            "issue_number": issue_number,
            "workflow_template": workflow_template,
            # Phase info
            "phase_name": phase_name,
            "phase_number": phase_number,
            "phase_status": phase_status,
            # Timing
            "started_at": started_at.isoformat() if started_at else None,
            "completed_at": completed_at.isoformat() if completed_at else None,
            "duration_seconds": duration_seconds,
            # Metrics
            "tokens_used": tokens_used,
            "cost_usd": cost_usd,
            # Error info
            "error_message": error_message,
            # Additional context
            "context": context if context else {},
        }

        # Remove None values
        log_data = {k: v for k, v in log_data.items() if v is not None}

        return self._write_log(log_data, adw_id)

    def log_workflow(
        self,
        adw_id: str,
        issue_number: int,
        workflow_status: str,
        message: str,
        workflow_template: Optional[str] = None,
        duration_seconds: Optional[float] = None,
        total_tokens: Optional[int] = None,
        total_cost_usd: Optional[float] = None,
        error_message: Optional[str] = None,
        **context,
    ) -> bool:
        """
        Log a workflow-level event.

        Args:
            adw_id: ADW workflow ID
            issue_number: GitHub issue number
            workflow_status: Workflow status (started, completed, failed, etc.)
            message: Log message
            workflow_template: Workflow template name
            duration_seconds: Total duration in seconds
            total_tokens: Total tokens consumed
            total_cost_usd: Total cost in USD
            error_message: Error message if failed
            **context: Additional context

        Returns:
            True if successful, False otherwise
        """
        log_data = {
            "event_id": f"evt_{uuid.uuid4().hex[:12]}",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": "error" if workflow_status == "failed" else "info",
            "source": "adw_workflow",
            "event_type": "workflow",
            "message": message,
            # Workflow info
            "adw_id": adw_id,
            "issue_number": issue_number,
            "workflow_template": workflow_template,
            "workflow_status": workflow_status,
            # Metrics
            "duration_seconds": duration_seconds,
            "total_tokens": total_tokens,
            "total_cost_usd": total_cost_usd,
            # Error info
            "error_message": error_message,
            # Additional context
            "context": context if context else {},
        }

        # Remove None values
        log_data = {k: v for k, v in log_data.items() if v is not None}

        return self._write_log(log_data, adw_id)


# Singleton instance
_adw_logger: Optional[ADWStructuredLogger] = None


def get_adw_logger() -> ADWStructuredLogger:
    """
    Get the global ADW structured logger instance.

    Returns:
        ADWStructuredLogger instance
    """
    global _adw_logger
    if _adw_logger is None:
        _adw_logger = ADWStructuredLogger()
    return _adw_logger
