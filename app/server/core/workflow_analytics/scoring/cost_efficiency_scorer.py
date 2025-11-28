"""
Cost Efficiency Scoring.

This module calculates cost efficiency scores for workflow execution.
"""

import logging

from ..helpers import detect_complexity

logger = logging.getLogger(__name__)


def calculate_cost_efficiency_score(workflow: dict) -> float:
    """
    Calculate cost efficiency score (0-100).

    Evaluates based on:
    - Budget variance (under budget = higher score)
    - Cache efficiency (>50% cache hit rate = bonus)
    - Retry penalty (each retry reduces score)
    - Model appropriateness (matches complexity level)

    Args:
        workflow: Workflow data containing cost metrics

    Returns:
        Cost efficiency score between 0.0 and 100.0
        Returns 0.0 for legacy workflows without estimated_cost_total
    """
    try:
        # Validate required data
        estimated_cost = workflow.get("estimated_cost_total")
        if estimated_cost is None or estimated_cost == 0:
            # Legacy workflow without cost estimate - return default score
            logger.debug(f"[SCORING] No estimated_cost_total for workflow {workflow.get('adw_id', 'unknown')} - using default score")
            return 0.0

        actual_cost = workflow.get("actual_cost_total", 0) or 0

        # Calculate budget variance score (60 points max)
        if actual_cost <= estimated_cost * 0.8:
            # Well under budget
            budget_score = 60.0
        elif actual_cost <= estimated_cost:
            # Under budget
            ratio = actual_cost / estimated_cost
            budget_score = 50.0 + (1.0 - ratio) * 50.0
        elif actual_cost <= estimated_cost * 1.2:
            # Slightly over budget
            ratio = actual_cost / estimated_cost
            budget_score = 40.0 - (ratio - 1.0) * 50.0
        else:
            # Significantly over budget
            ratio = actual_cost / estimated_cost
            budget_score = max(10.0, 40.0 - (ratio - 1.2) * 30.0)

        # Cache efficiency bonus (10 points max)
        cache_read_tokens = workflow.get("cache_read_tokens", 0) or 0
        total_input_tokens = workflow.get("total_input_tokens", 0) or 0

        cache_score = 0
        if total_input_tokens > 0:
            cache_efficiency = cache_read_tokens / total_input_tokens
            if cache_efficiency > 0.5:
                cache_score = 10.0
            elif cache_efficiency > 0.3:
                cache_score = 6.0
            elif cache_efficiency > 0.1:
                cache_score = 3.0

        # Retry penalty (10 points deduction per retry)
        retry_count = workflow.get("retry_count", 0) or 0
        retry_penalty = retry_count * 10

        # Model appropriateness scoring (10 points max)
        complexity = detect_complexity(workflow)
        model = workflow.get("model_used", "").lower()

        model_score = 0
        if complexity == "simple" and "haiku" in model or complexity == "complex" and "sonnet" in model:
            model_score = 10  # Perfect match
        elif complexity == "medium":
            model_score = 8   # Either model is fine
        elif "sonnet" in model and complexity == "simple":
            model_score = 5   # Overkill but works
        elif "haiku" in model and complexity == "complex":
            model_score = 3   # Underpowered
        else:
            model_score = 5   # Unknown model, neutral score

        # Combine scores: reweight to incorporate model component
        # budget_score (60) + cache_score (10) = 70 points
        # Reweight to 90%, then add model_score (10)
        base_total = budget_score + cache_score - retry_penalty
        final_score = base_total * 0.9 + model_score

        return max(0.0, min(100.0, final_score))

    except ValueError:
        # Re-raise ValueError for missing estimated cost
        raise
    except Exception as e:
        logger.error(f"Error calculating cost efficiency score: {e}")
        return 0.0
