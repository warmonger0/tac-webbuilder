"""
Metric calculation functions for workflow history.

This module provides pure functions for calculating performance metrics,
categorizing errors, and estimating workflow complexity.
"""

import logging
from datetime import datetime
from typing import Dict, Optional

from core.data_models import CostData

logger = logging.getLogger(__name__)


def calculate_phase_metrics(cost_data: CostData) -> dict:
    """
    Calculate phase-level performance metrics from cost_data.

    Args:
        cost_data: CostData object containing phase information with timestamps

    Returns:
        Dict containing:
            - phase_durations: Dict[str, int] - Duration in seconds per phase
            - bottleneck_phase: Optional[str] - Phase that took >30% of total time
            - idle_time_seconds: int - Idle time between phases
    """
    if not cost_data or not cost_data.phases:
        return {
            "phase_durations": None,
            "bottleneck_phase": None,
            "idle_time_seconds": None,
        }

    phase_durations = {}
    timestamps = []

    # Extract timestamps and calculate durations
    for phase in cost_data.phases:
        if phase.timestamp:
            try:
                # Parse ISO timestamp
                timestamp = datetime.fromisoformat(phase.timestamp.replace("Z", "+00:00"))
                timestamps.append((phase.phase, timestamp))
            except Exception as e:
                logger.debug(f"Could not parse timestamp for phase {phase.phase}: {e}")

    # Calculate durations between consecutive phases
    if len(timestamps) >= 2:
        # Sort by timestamp
        timestamps.sort(key=lambda x: x[1])

        for i in range(len(timestamps) - 1):
            phase_name = timestamps[i][0]
            start_time = timestamps[i][1]
            end_time = timestamps[i + 1][1]
            duration_seconds = int((end_time - start_time).total_seconds())
            phase_durations[phase_name] = duration_seconds

        # Add duration for last phase (if we have end time, otherwise skip)
        # We don't have end time for last phase, so we skip it
        # Could estimate based on average or leave as-is

    if not phase_durations:
        return {
            "phase_durations": None,
            "bottleneck_phase": None,
            "idle_time_seconds": None,
        }

    # Calculate total duration
    total_duration = sum(phase_durations.values())

    # Detect bottleneck (phase taking >30% of total time)
    bottleneck_phase = None
    if total_duration > 0:
        for phase, duration in phase_durations.items():
            if duration / total_duration > 0.30:
                bottleneck_phase = phase
                break  # Take first bottleneck found

    # Calculate idle time (for now, set to 0 as we don't have explicit idle tracking)
    # This would require more detailed timestamp tracking in the cost data
    idle_time_seconds = 0

    return {
        "phase_durations": phase_durations,
        "bottleneck_phase": bottleneck_phase,
        "idle_time_seconds": idle_time_seconds,
    }


def categorize_error(error_message: str) -> str:
    """
    Categorize error message into standard types.

    Args:
        error_message: The error message string

    Returns:
        str: Error category - "syntax_error", "timeout", "api_quota", "validation", or "unknown"
    """
    if not error_message:
        return "unknown"

    error_lower = error_message.lower()

    # Check for syntax errors
    if any(keyword in error_lower for keyword in [
        "syntaxerror", "syntax error", "indentationerror", "indentation error",
        "parsing error", "parse error", "invalid syntax"
    ]):
        return "syntax_error"

    # Check for timeout errors
    if any(keyword in error_lower for keyword in [
        "timeout", "timeouterror", "connection timeout", "timed out",
        "deadline exceeded"
    ]):
        return "timeout"

    # Check for API quota/rate limit errors
    if any(keyword in error_lower for keyword in [
        "quota", "rate limit", "429", "too many requests",
        "quota exceeded", "rate_limit_error"
    ]):
        return "api_quota"

    # Check for validation errors
    if any(keyword in error_lower for keyword in [
        "validationerror", "validation error", "invalid input",
        "schema error", "schema validation", "invalid data"
    ]):
        return "validation"

    return "unknown"


def estimate_complexity(steps_total: int, duration_seconds: int) -> str:
    """
    Estimate workflow complexity based on steps and duration.

    Args:
        steps_total: Total number of steps in the workflow
        duration_seconds: Total duration in seconds

    Returns:
        str: Complexity level - "low", "medium", or "high"
    """
    # Low complexity: few steps OR short duration
    if steps_total <= 5 or duration_seconds < 60:
        return "low"

    # High complexity: many steps OR long duration
    if steps_total > 15 or duration_seconds > 300:
        return "high"

    # Everything else is medium
    return "medium"
