"""
Pattern Recognition Logging Infrastructure

Provides structured JSON logging for all pattern recognition operations
across all phases (prediction, detection, validation, analytics).

This logging system enables:
- Performance monitoring and optimization
- Error tracking and debugging
- Pattern accuracy validation
- Analytics and insights generation
"""
import json
import logging
import time
import traceback
from collections.abc import Callable
from contextlib import contextmanager
from datetime import datetime
from functools import wraps
from typing import Any


def get_pattern_logger() -> logging.Logger:
    """
    Get configured logger for pattern recognition operations.

    Returns:
        Configured logger with JSON formatting
    """
    logger = logging.getLogger("pattern_recognition")

    # Only configure if not already configured
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        logger.propagate = False

        # File handler for all pattern recognition logs
        file_handler = logging.FileHandler(
            "logs/pattern_recognition.log",
            encoding="utf-8"
        )
        file_handler.setLevel(logging.INFO)

        # Console handler for errors only
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.ERROR)

        # Simple formatter (JSON structure added in log_pattern_event)
        formatter = logging.Formatter("%(message)s")
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)

        logger.addHandler(file_handler)
        logger.addHandler(console_handler)

    return logger


def log_pattern_event(
    event_type: str,
    data: dict[str, Any],
    level: str = "INFO"
) -> None:
    """
    Log a pattern recognition event with structured JSON format.

    Args:
        event_type: Type of event (e.g., "prediction_start", "validation_complete")
        data: Event-specific data to include in log
        level: Log level (INFO, WARNING, ERROR)

    Example:
        >>> log_pattern_event(
        ...     "prediction_complete",
        ...     {"patterns_found": 2, "confidence_avg": 0.75}
        ... )
    """
    logger = get_pattern_logger()

    # Build structured log entry
    log_entry = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "component": "pattern_recognition",
        "event_type": event_type,
        **data
    }

    # Convert to JSON string
    log_message = json.dumps(log_entry, default=str)

    # Log at appropriate level
    log_level = getattr(logging, level.upper(), logging.INFO)
    logger.log(log_level, log_message)


def log_pattern_performance(func: Callable) -> Callable:
    """
    Decorator to automatically log performance metrics for pattern operations.

    Logs function entry, duration, result summary, and any exceptions.

    Usage:
        @log_pattern_performance
        def predict_patterns_from_input(nl_input: str) -> list:
            # ... implementation
            return predictions

    Args:
        func: Function to wrap with performance logging

    Returns:
        Wrapped function with automatic performance tracking
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        func_name = func.__name__
        start_time = time.time()

        # Log function entry
        log_pattern_event(
            f"{func_name}_start",
            {
                "function": func_name,
                "args_count": len(args),
                "kwargs_keys": list(kwargs.keys())
            }
        )

        try:
            # Execute function
            result = func(*args, **kwargs)
            duration_ms = (time.time() - start_time) * 1000

            # Log success with duration
            log_pattern_event(
                f"{func_name}_complete",
                {
                    "function": func_name,
                    "duration_ms": round(duration_ms, 2),
                    "result_type": type(result).__name__,
                    "result_length": len(result) if hasattr(result, "__len__") else None,
                    "success": True
                }
            )

            return result

        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000

            # Log error with stack trace
            log_pattern_event(
                f"{func_name}_error",
                {
                    "function": func_name,
                    "duration_ms": round(duration_ms, 2),
                    "error_type": type(e).__name__,
                    "error_message": str(e),
                    "stack_trace": traceback.format_exc(),
                    "success": False
                },
                level="ERROR"
            )

            # Re-raise exception
            raise

    return wrapper


@contextmanager
def PatternOperationContext(operation_name: str, metadata: dict[str, Any] | None = None):  # noqa: N802
    """
    Context manager for logging pattern recognition operations.

    Logs operation start, completion, duration, and handles errors.
    Use for multi-step operations or operations without @decorator.

    Usage:
        with PatternOperationContext("pattern_validation", {"request_id": "123"}):
            # ... validation logic
            validate_predictions(predictions)

    Args:
        operation_name: Name of the operation being performed
        metadata: Optional metadata to include in logs

    Yields:
        None
    """
    start_time = time.time()
    metadata = metadata or {}

    # Log operation start
    log_pattern_event(
        f"{operation_name}_start",
        {
            "operation": operation_name,
            **metadata
        }
    )

    try:
        yield
        duration_ms = (time.time() - start_time) * 1000

        # Log successful completion
        log_pattern_event(
            f"{operation_name}_complete",
            {
                "operation": operation_name,
                "duration_ms": round(duration_ms, 2),
                "success": True,
                **metadata
            }
        )

    except Exception as e:
        duration_ms = (time.time() - start_time) * 1000

        # Log error
        log_pattern_event(
            f"{operation_name}_error",
            {
                "operation": operation_name,
                "duration_ms": round(duration_ms, 2),
                "error_type": type(e).__name__,
                "error_message": str(e),
                "stack_trace": traceback.format_exc(),
                "success": False,
                **metadata
            },
            level="ERROR"
        )

        # Re-raise exception
        raise
