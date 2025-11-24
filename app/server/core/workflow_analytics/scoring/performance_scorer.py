"""
Performance Scoring.

This module calculates performance scores for workflow execution.
"""

import logging

logger = logging.getLogger(__name__)


def calculate_performance_score(workflow: dict) -> float:
    """
    Calculate performance score (0-100).

    Evaluates based on:
    - Duration compared to similar workflows
    - Bottleneck detection (phases taking >30% of time)
    - Idle time penalties
    - Absolute duration fallback if no similar workflows

    Args:
        workflow: Workflow data containing duration and phase metrics

    Returns:
        Performance score between 0.0 and 100.0
    """
    try:
        duration = workflow.get("duration_seconds", 0) or 0
        if duration <= 0:
            return 0.0

        # Use baseline of 180s (3 minutes) as reasonable workflow time
        baseline_duration = 180.0

        # Check if we have similar workflow data for comparison
        similar_avg_duration = workflow.get("similar_avg_duration")
        if similar_avg_duration and similar_avg_duration > 0:
            baseline_duration = similar_avg_duration

        # Calculate base score from duration comparison
        ratio = duration / baseline_duration
        if ratio <= 0.5:
            # Much faster than average
            base_score = 95.0
        elif ratio <= 0.75:
            # Faster than average
            base_score = 85.0 + (0.75 - ratio) * 40.0
        elif ratio <= 1.0:
            # Around average
            base_score = 70.0 + (1.0 - ratio) * 60.0
        elif ratio <= 1.5:
            # Slower than average
            base_score = 50.0 + (1.5 - ratio) * 40.0
        elif ratio <= 2.0:
            # Much slower
            base_score = 30.0 + (2.0 - ratio) * 40.0
        else:
            # Very slow
            base_score = max(10.0, 30.0 - (ratio - 2.0) * 10.0)

        # Bottleneck detection penalty
        phase_durations = workflow.get("phase_durations", {})
        if phase_durations and duration > 0:
            for phase, phase_duration in phase_durations.items():
                if phase_duration and phase_duration > duration * 0.3:
                    # Phase takes more than 30% of total time - bottleneck
                    base_score -= 10
                    logger.info(f"Bottleneck detected in phase '{phase}': {phase_duration}s ({phase_duration/duration*100:.1f}%)")
                    break  # Only penalize once

        # Idle time penalty (if available)
        idle_time = workflow.get("idle_time_seconds", 0) or 0
        if idle_time > 0 and duration > 0:
            idle_ratio = idle_time / duration
            if idle_ratio > 0.2:  # More than 20% idle time
                penalty = min(15.0, idle_ratio * 30.0)
                base_score -= penalty

        return max(0.0, min(100.0, base_score))

    except Exception as e:
        logger.error(f"Error calculating performance score: {e}")
        return 0.0
