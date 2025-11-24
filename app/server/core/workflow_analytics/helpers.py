"""
Helper functions for workflow analytics.

This module provides utility functions for temporal extraction and complexity detection.
"""

import logging
from datetime import datetime

logger = logging.getLogger(__name__)


def extract_hour(timestamp: str) -> int:
    """
    Extract hour (0-23) from ISO timestamp.

    Args:
        timestamp: ISO format timestamp string (e.g., "2025-01-15T14:30:00Z")

    Returns:
        Hour as integer (0-23), or -1 if parsing fails
    """
    try:
        # Handle various ISO format variations (Z, +00:00, etc.)
        if not timestamp:
            return -1

        # Remove timezone markers for consistent parsing
        clean_timestamp = timestamp.replace('Z', '+00:00')

        # Parse ISO format
        dt = datetime.fromisoformat(clean_timestamp)
        return dt.hour
    except (ValueError, AttributeError, TypeError) as e:
        logger.warning(f"Failed to extract hour from timestamp '{timestamp}': {e}")
        return -1


def extract_day_of_week(timestamp: str) -> int:
    """
    Extract day of week from ISO timestamp.

    Args:
        timestamp: ISO format timestamp string

    Returns:
        Day of week as integer (0=Monday, 6=Sunday), or -1 if parsing fails
    """
    try:
        # Handle various ISO format variations
        if not timestamp:
            return -1

        # Remove timezone markers for consistent parsing
        clean_timestamp = timestamp.replace('Z', '+00:00')

        # Parse ISO format
        dt = datetime.fromisoformat(clean_timestamp)
        # Python's weekday() returns 0=Monday, 6=Sunday (exactly what we need)
        return dt.weekday()
    except (ValueError, AttributeError, TypeError) as e:
        logger.warning(f"Failed to extract day of week from timestamp '{timestamp}': {e}")
        return -1


def detect_complexity(workflow: dict) -> str:
    """
    Detect workflow complexity level based on multiple factors.

    Complexity is determined by analyzing:
    - Natural language input length (word count)
    - Execution duration
    - Error count

    Args:
        workflow: Workflow dictionary with metrics

    Returns:
        "simple", "medium", or "complex"

    Complexity thresholds:
        Simple: <50 words AND <300s duration AND <3 errors
        Complex: >200 words OR >1800s duration OR >5 errors
        Medium: Everything else
    """
    try:
        # Support both old and new field names for backward compatibility
        word_count = workflow.get('nl_input_word_count', 0) or 0
        if word_count == 0 and 'nl_input' in workflow:
            # Old format: count words from nl_input text
            nl_input = workflow.get('nl_input', '')
            word_count = len(nl_input.split()) if nl_input else 0

        # Support both old (duration_seconds) and new (total_duration_seconds) field names
        duration = workflow.get('total_duration_seconds', 0) or 0
        if duration == 0:
            duration = workflow.get('duration_seconds', 0) or 0

        # Support both old (error_count) and new (errors list) field names
        if 'errors' in workflow:
            errors = workflow.get('errors', [])
            error_count = len(errors) if isinstance(errors, list) else 0
        else:
            error_count = workflow.get('error_count', 0) or 0

        # Simple: All metrics are low
        if word_count < 50 and duration < 300 and error_count < 3:
            return "simple"

        # Complex: Any metric is very high
        elif word_count > 200 or duration > 1800 or error_count > 5:
            return "complex"

        # Medium: Everything else
        else:
            return "medium"

    except Exception as e:
        logger.error(f"Error detecting complexity: {e}")
        return "medium"  # Default to medium on error
