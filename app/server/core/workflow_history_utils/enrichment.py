"""
Workflow data enrichment utilities.

This module provides functions for enriching workflow data with additional
information from various sources including cost tracking, GitHub, analytics,
and scoring systems.
"""

import json
import logging
from datetime import datetime

from core.cost_estimate_storage import get_cost_estimate
from core.cost_tracker import read_cost_history
from core.workflow_analytics import (
    calculate_cost_efficiency_score,
    calculate_nl_input_clarity_score,
    calculate_performance_score,
    calculate_quality_score,
    detect_anomalies,
    extract_day_of_week,
    extract_hour,
    generate_optimization_recommendations,
)
from core.workflow_history_utils.github_client import fetch_github_issue_state
from core.workflow_history_utils.metrics import (
    calculate_phase_metrics,
    categorize_error,
    estimate_complexity,
)

logger = logging.getLogger(__name__)


def enrich_cost_data(workflow_data: dict, adw_id: str) -> None:
    """
    Enrich workflow data with actual cost information from cost_tracker.

    Modifies workflow_data in place, adding:
    - actual_cost_total
    - cost_breakdown (with by_phase data)
    - token_breakdown (input, cached, cache_hit, cache_miss, output, total)
    - cache_efficiency_percent
    - phase_durations, bottleneck_phase, idle_time_seconds
    - model_used (if not already set)

    Args:
        workflow_data: Dictionary containing workflow information
        adw_id: ADW workflow identifier
    """
    try:
        cost_data = read_cost_history(adw_id)

        # Extract cost information if available
        if cost_data and hasattr(cost_data, 'total_cost'):
            workflow_data["actual_cost_total"] = cost_data.total_cost

            # Populate cost_breakdown with by_phase data
            if hasattr(cost_data, 'phases') and cost_data.phases:
                by_phase = {phase.phase: phase.cost for phase in cost_data.phases}
                workflow_data["cost_breakdown"] = {
                    "estimated_total": workflow_data.get("estimated_cost_total", 0.0),
                    "actual_total": cost_data.total_cost,
                    "estimated_per_step": workflow_data.get("estimated_cost_per_step", 0.0),
                    "actual_per_step": workflow_data.get("actual_cost_per_step", 0.0),
                    "cost_per_token": workflow_data.get("cost_per_token", 0.0),
                    "by_phase": by_phase
                }

            # Populate token_breakdown
            if hasattr(cost_data, 'phases') and cost_data.phases:
                # Aggregate tokens across all phases
                total_input = sum(p.tokens.input_tokens for p in cost_data.phases)
                total_cache_creation = sum(p.tokens.cache_creation_tokens for p in cost_data.phases)
                total_cache_read = sum(p.tokens.cache_read_tokens for p in cost_data.phases)
                total_output = sum(p.tokens.output_tokens for p in cost_data.phases)

                workflow_data["input_tokens"] = total_input
                workflow_data["cached_tokens"] = total_cache_creation
                workflow_data["cache_hit_tokens"] = total_cache_read
                workflow_data["cache_miss_tokens"] = total_input  # Approximation
                workflow_data["output_tokens"] = total_output
                workflow_data["total_tokens"] = total_input + total_cache_creation + total_cache_read + total_output
                workflow_data["cache_efficiency_percent"] = cost_data.cache_efficiency_percent

            # Calculate performance metrics
            phase_metrics = calculate_phase_metrics(cost_data)
            if phase_metrics["phase_durations"]:
                workflow_data["phase_durations"] = phase_metrics["phase_durations"]
                workflow_data["bottleneck_phase"] = phase_metrics["bottleneck_phase"]
                workflow_data["idle_time_seconds"] = phase_metrics["idle_time_seconds"]

            # Extract model from cost_data if not already set
            if not workflow_data.get("model_used") and hasattr(cost_data, 'phases') and cost_data.phases:
                # Use the model from the first phase (they're usually all the same)
                workflow_data["model_used"] = cost_data.phases[0].model if cost_data.phases else None

    except Exception as e:
        logger.debug(f"[ENRICH] No cost data for {adw_id}: {e}")


def enrich_cost_estimate(workflow_data: dict, adw_id: str) -> None:
    """
    Enrich workflow data with estimated cost information from cost_estimate_storage.

    Only loads estimates if issue_number is available. Modifies workflow_data in place.

    Args:
        workflow_data: Dictionary containing workflow information
        adw_id: ADW workflow identifier
    """
    if not workflow_data.get("issue_number"):
        return

    try:
        cost_estimate = get_cost_estimate(int(workflow_data["issue_number"]))
        if cost_estimate:
            workflow_data["estimated_cost_total"] = cost_estimate.get("estimated_cost_total", 0.0)

            # Add estimated breakdown to cost_breakdown
            estimated_by_phase = cost_estimate.get("estimated_cost_breakdown", {})

            if "cost_breakdown" not in workflow_data:
                # Create new cost_breakdown with estimates
                workflow_data["cost_breakdown"] = {
                    "estimated_total": cost_estimate.get("estimated_cost_total", 0.0),
                    "actual_total": workflow_data.get("actual_cost_total", 0.0),
                    "by_phase": {},  # Will be populated with actual costs from raw_output.jsonl
                    "estimated_by_phase": estimated_by_phase  # Per-phase estimates
                }
            elif "cost_breakdown" in workflow_data:
                # Update existing cost_breakdown with estimates
                breakdown = json.loads(workflow_data["cost_breakdown"]) if isinstance(workflow_data["cost_breakdown"], str) else workflow_data["cost_breakdown"]
                breakdown["estimated_total"] = cost_estimate.get("estimated_cost_total", 0.0)
                breakdown["estimated_by_phase"] = estimated_by_phase  # Add per-phase estimates
                workflow_data["cost_breakdown"] = breakdown

            logger.info(f"[ENRICH] Loaded cost estimate for {adw_id}: ${cost_estimate.get('estimated_cost_total', 0):.2f} (with {len(estimated_by_phase)} phase estimates)")
    except Exception as e:
        logger.debug(f"[ENRICH] Could not load cost estimate for {adw_id}: {e}")


def enrich_github_state(workflow_data: dict, adw_id: str) -> None:
    """
    Enrich workflow data with GitHub issue state.

    Fetches issue state from GitHub API if issue_number is available.
    Modifies workflow_data in place.

    Args:
        workflow_data: Dictionary containing workflow information
        adw_id: ADW workflow identifier
    """
    if not workflow_data.get("issue_number"):
        return

    try:
        gh_state = fetch_github_issue_state(int(workflow_data["issue_number"]))
        if gh_state:
            workflow_data["gh_issue_state"] = gh_state
            logger.debug(f"[ENRICH] Fetched GitHub issue state for #{workflow_data['issue_number']}: {gh_state}")
    except Exception as e:
        logger.debug(f"[ENRICH] Could not fetch GitHub issue state for {adw_id}: {e}")


def enrich_workflow_template(workflow_data: dict) -> None:
    """
    Set default workflow template if not already set.

    Currently defaults to "sdlc" for all workflows. Future enhancement:
    derive from issue_class or other workflow metadata.

    Args:
        workflow_data: Dictionary containing workflow information
    """
    if not workflow_data.get("workflow_template"):
        # Derive from issue_class or use generic "sdlc"
        workflow_data["workflow_template"] = "sdlc"  # Default template


def enrich_error_category(workflow_data: dict) -> None:
    """
    Categorize error message if present.

    Uses metrics.categorize_error() to classify error types.
    Modifies workflow_data in place.

    Args:
        workflow_data: Dictionary containing workflow information
    """
    if workflow_data.get("error_message"):
        workflow_data["error_category"] = categorize_error(workflow_data["error_message"])


def enrich_duration(workflow_data: dict, adw_id: str) -> int | None:
    """
    Calculate workflow duration from start_time to current time.

    Only calculates for completed workflows with start_time.

    Args:
        workflow_data: Dictionary containing workflow information
        adw_id: ADW workflow identifier

    Returns:
        Duration in seconds, or None if cannot calculate
    """
    if not workflow_data.get("start_time") or workflow_data["status"] != "completed":
        return None

    try:
        start_dt = datetime.fromisoformat(workflow_data["start_time"].replace("Z", "+00:00"))
        # Use current time as end time if not specified
        end_dt = datetime.now()
        duration_seconds = int((end_dt - start_dt).total_seconds())
        return duration_seconds
    except Exception as e:
        logger.debug(f"[ENRICH] Could not calculate duration for {adw_id}: {e}")
        return None


def enrich_complexity(workflow_data: dict, duration_seconds: int | None) -> None:
    """
    Estimate workflow complexity from steps and duration.

    Uses metrics.estimate_complexity() if steps_total and duration are available.
    Modifies workflow_data in place.

    Args:
        workflow_data: Dictionary containing workflow information
        duration_seconds: Workflow duration in seconds (from enrich_duration)
    """
    steps_total = workflow_data.get("steps_total", 0)
    if steps_total > 0 and duration_seconds:
        workflow_data["complexity_actual"] = estimate_complexity(steps_total, duration_seconds)


def enrich_temporal_fields(workflow_data: dict) -> None:
    """
    Extract temporal fields (hour, day of week) from start_time.

    Uses workflow_analytics temporal extraction functions.
    Modifies workflow_data in place.

    Args:
        workflow_data: Dictionary containing workflow information
    """
    if workflow_data.get("start_time"):
        workflow_data["hour_of_day"] = extract_hour(workflow_data["start_time"])
        workflow_data["day_of_week"] = extract_day_of_week(workflow_data["start_time"])


def enrich_scores(workflow_data: dict, adw_id: str) -> None:
    """
    Calculate scoring metrics for workflow quality assessment.

    Calculates and sets:
    - scoring_version
    - nl_input_clarity_score
    - cost_efficiency_score
    - performance_score
    - quality_score

    All scores default to 0.0 if calculation fails (to prevent sync failures).
    Modifies workflow_data in place.

    Args:
        workflow_data: Dictionary containing workflow information
        adw_id: ADW workflow identifier
    """
    # Set scoring version
    workflow_data["scoring_version"] = "1.0"

    # Calculate scores (with error handling to prevent sync failures)
    try:
        workflow_data["nl_input_clarity_score"] = calculate_nl_input_clarity_score(workflow_data)
    except Exception as e:
        logger.warning(f"[ENRICH] Failed to calculate clarity score for {adw_id}: {e}")
        workflow_data["nl_input_clarity_score"] = 0.0

    try:
        workflow_data["cost_efficiency_score"] = calculate_cost_efficiency_score(workflow_data)
    except Exception as e:
        logger.warning(f"[ENRICH] Failed to calculate cost efficiency score for {adw_id}: {e}")
        workflow_data["cost_efficiency_score"] = 0.0

    try:
        workflow_data["performance_score"] = calculate_performance_score(workflow_data)
    except Exception as e:
        logger.warning(f"[ENRICH] Failed to calculate performance score for {adw_id}: {e}")
        workflow_data["performance_score"] = 0.0

    try:
        workflow_data["quality_score"] = calculate_quality_score(workflow_data)
    except Exception as e:
        logger.warning(f"[ENRICH] Failed to calculate quality score for {adw_id}: {e}")
        workflow_data["quality_score"] = 0.0


def enrich_insights(workflow_data: dict, adw_id: str, all_workflows: list) -> None:
    """
    Generate anomaly detection and optimization recommendations.

    Only generates insights for workflows where should_generate_insights is True.
    Uses workflow_analytics detection and recommendation functions.
    Modifies workflow_data in place.

    Args:
        workflow_data: Dictionary containing workflow information
        adw_id: ADW workflow identifier
        all_workflows: List of all workflows for comparison analysis
    """
    try:
        # Detect anomalies
        anomalies = detect_anomalies(workflow_data, all_workflows)

        # Generate recommendations
        recommendations = generate_optimization_recommendations(workflow_data, anomalies)

        # Serialize to JSON for database storage
        workflow_data["anomaly_flags"] = json.dumps([a["message"] for a in anomalies])  # Simplified for UI
        workflow_data["optimization_recommendations"] = json.dumps(recommendations)

        logger.debug(f"[ENRICH] Generated {len(anomalies)} anomalies and {len(recommendations)} recommendations for {adw_id}")
    except Exception as e:
        logger.warning(f"[ENRICH] Failed to generate insights for {adw_id}: {e}")
        workflow_data["anomaly_flags"] = "[]"
        workflow_data["optimization_recommendations"] = "[]"


def enrich_cost_data_for_resync(existing: dict, adw_id: str) -> dict:
    """
    Enrich cost data specifically for resync operations.

    Reads cost data from cost_tracker and returns update dict for database.
    Used by resync_workflow_cost() to update existing workflows.

    Args:
        existing: Existing workflow record from database
        adw_id: ADW workflow identifier

    Returns:
        Dict with update fields, or empty dict if no updates
    """
    updates = {}

    cost_data = read_cost_history(adw_id)

    # Extract cost information
    if cost_data and hasattr(cost_data, 'total_cost'):
        updates["actual_cost_total"] = cost_data.total_cost

        # Populate cost_breakdown with by_phase data
        if hasattr(cost_data, 'phases') and cost_data.phases:
            by_phase = {phase.phase: phase.cost for phase in cost_data.phases}
            updates["cost_breakdown"] = {
                "estimated_total": existing.get("estimated_cost_total", 0.0),
                "actual_total": cost_data.total_cost,
                "estimated_per_step": existing.get("estimated_cost_per_step", 0.0),
                "actual_per_step": existing.get("actual_cost_per_step", 0.0),
                "cost_per_token": existing.get("cost_per_token", 0.0),
                "by_phase": by_phase
            }

        # Populate token_breakdown
        if hasattr(cost_data, 'phases') and cost_data.phases:
            # Aggregate tokens across all phases
            total_input = sum(p.tokens.input_tokens for p in cost_data.phases)
            total_cache_creation = sum(p.tokens.cache_creation_tokens for p in cost_data.phases)
            total_cache_read = sum(p.tokens.cache_read_tokens for p in cost_data.phases)
            total_output = sum(p.tokens.output_tokens for p in cost_data.phases)

            updates["input_tokens"] = total_input
            updates["cached_tokens"] = total_cache_creation
            updates["cache_hit_tokens"] = total_cache_read
            updates["cache_miss_tokens"] = total_input  # Approximation
            updates["output_tokens"] = total_output
            updates["total_tokens"] = total_input + total_cache_creation + total_cache_read + total_output
            updates["cache_efficiency_percent"] = cost_data.cache_efficiency_percent

        # Calculate performance metrics
        phase_metrics = calculate_phase_metrics(cost_data)
        if phase_metrics["phase_durations"]:
            updates["phase_durations"] = phase_metrics["phase_durations"]
            updates["bottleneck_phase"] = phase_metrics["bottleneck_phase"]
            updates["idle_time_seconds"] = phase_metrics["idle_time_seconds"]

    return updates


def enrich_workflow(
    workflow_data: dict,
    adw_id: str,
    is_new: bool,
    all_workflows: list | None = None
) -> int | None:
    """
    Main enrichment orchestrator - applies all enrichment functions.

    Enriches workflow_data with information from multiple sources:
    1. Cost data from cost_tracker
    2. Cost estimates (new workflows only)
    3. GitHub issue state
    4. Workflow template defaults
    5. Error categorization
    6. Duration calculation
    7. Complexity estimation
    8. Temporal fields (hour, day of week)
    9. Scoring metrics
    10. Insights (anomalies, recommendations) - new workflows only

    Args:
        workflow_data: Dictionary containing workflow information
        adw_id: ADW workflow identifier
        is_new: Whether this is a new workflow (not in database yet)
        all_workflows: Optional list of all workflows for insight generation

    Returns:
        Duration in seconds (if calculated), or None
    """
    # 1. Cost data from cost_tracker
    enrich_cost_data(workflow_data, adw_id)

    # 2. Cost estimates (only for new workflows)
    if is_new:
        enrich_cost_estimate(workflow_data, adw_id)

    # 3. GitHub issue state
    enrich_github_state(workflow_data, adw_id)

    # 4. Workflow template
    enrich_workflow_template(workflow_data)

    # 5. Error categorization
    enrich_error_category(workflow_data)

    # 6. Duration calculation
    duration_seconds = enrich_duration(workflow_data, adw_id)

    # 7. Complexity estimation
    enrich_complexity(workflow_data, duration_seconds)

    # 8. Temporal fields
    enrich_temporal_fields(workflow_data)

    # 9. Scoring metrics
    enrich_scores(workflow_data, adw_id)

    # 10. Insights (only for new workflows with all_workflows provided)
    if is_new and all_workflows is not None:
        enrich_insights(workflow_data, adw_id, all_workflows)

    return duration_seconds
