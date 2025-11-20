"""
Type definitions and models for workflow history.

This module contains type definitions, enums, constants, and dataclasses
used throughout the workflow history tracking system.
"""

from enum import Enum
from dataclasses import dataclass
from typing import Optional


class WorkflowStatus(Enum):
    """Workflow execution status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class ErrorCategory(Enum):
    """Categories of errors that can occur during workflow execution."""
    SYNTAX_ERROR = "syntax_error"
    TIMEOUT = "timeout"
    API_QUOTA = "api_quota"
    VALIDATION = "validation"
    UNKNOWN = "unknown"


class ComplexityLevel(Enum):
    """Workflow complexity levels based on steps and duration."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


@dataclass
class WorkflowFilter:
    """Filter criteria for querying workflow history."""
    issue_number: Optional[int] = None
    status: Optional[WorkflowStatus] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    model: Optional[str] = None
    template: Optional[str] = None
    search: Optional[str] = None


# Constants
DEFAULT_SCORING_VERSION = "1.0"
BOTTLENECK_THRESHOLD = 0.30  # 30% of total time
LOW_COMPLEXITY_STEPS = 5
LOW_COMPLEXITY_DURATION = 60  # seconds
HIGH_COMPLEXITY_STEPS = 15
HIGH_COMPLEXITY_DURATION = 300  # seconds
