"""
Quality Scoring.

This module calculates quality scores for workflow execution.
"""

import logging

logger = logging.getLogger(__name__)


def calculate_quality_score(workflow: dict) -> float:
    """
    Calculate quality score (0-100).

    Evaluates based on:
    - Error rate (0 errors = 90-100 score)
    - Retry count penalty (-5 per retry)
    - Error category weighting (syntax_error=-10, timeout=-8, api_quota=-5)
    - PR/CI success bonus

    Args:
        workflow: Workflow data containing error and quality metrics

    Returns:
        Quality score between 0.0 and 100.0
    """
    try:
        error_count = workflow.get("error_count", 0) or 0
        retry_count = workflow.get("retry_count", 0) or 0

        # Start with high base score for perfect execution
        if error_count == 0 and retry_count == 0:
            base_score = 95.0
        elif error_count == 0:
            # No errors but had retries
            base_score = 90.0 - (retry_count * 5)
        else:
            # Has errors - start lower
            base_score = max(40.0, 80.0 - (error_count * 10))

        # Retry penalty
        retry_penalty = retry_count * 5
        base_score -= retry_penalty

        # Error category weighting (if error details available)
        error_types = workflow.get("error_types", [])
        if error_types:
            error_severity_map = {
                "syntax_error": -10,
                "type_error": -10,
                "timeout": -8,
                "rate_limit": -8,
                "api_quota": -5,
                "network": -5,
                "validation": -7,
            }

            for error_type in error_types:
                error_type_lower = error_type.lower() if isinstance(error_type, str) else ""
                for error_key, penalty in error_severity_map.items():
                    if error_key in error_type_lower:
                        base_score += penalty  # penalty is negative
                        break

        # PR/CI success bonus
        pr_success = workflow.get("pr_merged", False)
        ci_success = workflow.get("ci_passed", False)

        if pr_success:
            base_score += 5
        if ci_success:
            base_score += 5

        return max(0.0, min(100.0, base_score))

    except Exception as e:
        logger.error(f"Error calculating quality score: {e}")
        return 0.0
