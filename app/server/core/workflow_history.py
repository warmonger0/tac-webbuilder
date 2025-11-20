"""
Workflow history tracking module for ADW workflows.

This module provides database operations for storing and retrieving workflow
execution history, including metadata, costs, performance metrics, token usage,
and detailed status information.
"""

import json
import logging
import sqlite3
from datetime import datetime
from pathlib import Path

from utils.db_connection import get_connection as get_db_connection
from core.cost_estimate_storage import get_cost_estimate
from core.cost_tracker import read_cost_history
from core.data_models import CostData
from core.workflow_analytics import (
    calculate_cost_efficiency_score,
    calculate_nl_input_clarity_score,
    calculate_performance_score,
    calculate_quality_score,
    extract_day_of_week,
    extract_hour,
)
from core.workflow_history_utils.database import (
    DB_PATH,
    init_db,
    insert_workflow_history,
    update_workflow_history_by_issue,
    update_workflow_history,
    get_workflow_by_adw_id,
    get_workflow_history,
    get_history_analytics,
)
from core.workflow_history_utils.filesystem import scan_agents_directory
from core.workflow_history_utils.github_client import fetch_github_issue_state
from core.workflow_history_utils.metrics import (
    calculate_phase_metrics,
    categorize_error,
    estimate_complexity,
)

logger = logging.getLogger(__name__)


def sync_workflow_history() -> int:
    """
    Synchronize workflow history database with agents directory.

    Scans the agents directory for workflows and updates the database:
    - Inserts new workflows
    - Updates existing workflows if status changed
    - Enriches with cost data from cost_tracker

    Returns:
        int: Number of workflows synchronized
    """
    workflows = scan_agents_directory()
    synced_count = 0

    for workflow_data in workflows:
        adw_id = workflow_data["adw_id"]

        # Check if workflow already exists in database
        existing = get_workflow_by_adw_id(adw_id)

        # Try to get cost data
        cost_data = None
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
            logger.debug(f"[SYNC] No cost data for {adw_id}: {e}")

        # Fetch GitHub issue state if issue_number is available
        if workflow_data.get("issue_number"):
            try:
                gh_state = fetch_github_issue_state(int(workflow_data["issue_number"]))
                if gh_state:
                    workflow_data["gh_issue_state"] = gh_state
                    logger.debug(f"[SYNC] Fetched GitHub issue state for #{workflow_data['issue_number']}: {gh_state}")
            except Exception as e:
                logger.debug(f"[SYNC] Could not fetch GitHub issue state for {adw_id}: {e}")

        # Try to get estimated cost from storage (only for new workflows)
        if not existing and workflow_data.get("issue_number"):
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

                    logger.info(f"[SYNC] Loaded cost estimate for {adw_id}: ${cost_estimate.get('estimated_cost_total', 0):.2f} (with {len(estimated_by_phase)} phase estimates)")
            except Exception as e:
                logger.debug(f"[SYNC] Could not load cost estimate for {adw_id}: {e}")

        # Set default workflow_template if not set (use issue_class from state)
        if not workflow_data.get("workflow_template"):
            # Derive from issue_class or use generic "sdlc"
            workflow_data["workflow_template"] = "sdlc"  # Default template

        # Categorize error if error_message exists
        if workflow_data.get("error_message"):
            workflow_data["error_category"] = categorize_error(workflow_data["error_message"])

        # Calculate duration if we have start and end times
        duration_seconds = None
        if workflow_data.get("start_time") and workflow_data["status"] == "completed":
            try:
                start_dt = datetime.fromisoformat(workflow_data["start_time"].replace("Z", "+00:00"))
                # Use current time as end time if not specified
                end_dt = datetime.now()
                duration_seconds = int((end_dt - start_dt).total_seconds())
            except Exception as e:
                logger.debug(f"[SYNC] Could not calculate duration for {adw_id}: {e}")

        # Estimate complexity if we have steps_total and duration
        steps_total = workflow_data.get("steps_total", 0)
        if steps_total > 0 and duration_seconds:
            workflow_data["complexity_actual"] = estimate_complexity(steps_total, duration_seconds)

        # Phase 3A/3B: Calculate temporal fields and scoring metrics
        if workflow_data.get("start_time"):
            workflow_data["hour_of_day"] = extract_hour(workflow_data["start_time"])
            workflow_data["day_of_week"] = extract_day_of_week(workflow_data["start_time"])

        # Set scoring version
        workflow_data["scoring_version"] = "1.0"

        # Calculate scores (with error handling to prevent sync failures)
        try:
            workflow_data["nl_input_clarity_score"] = calculate_nl_input_clarity_score(workflow_data)
        except Exception as e:
            logger.warning(f"[SYNC] Failed to calculate clarity score for {adw_id}: {e}")
            workflow_data["nl_input_clarity_score"] = 0.0

        try:
            workflow_data["cost_efficiency_score"] = calculate_cost_efficiency_score(workflow_data)
        except Exception as e:
            logger.warning(f"[SYNC] Failed to calculate cost efficiency score for {adw_id}: {e}")
            workflow_data["cost_efficiency_score"] = 0.0

        try:
            workflow_data["performance_score"] = calculate_performance_score(workflow_data)
        except Exception as e:
            logger.warning(f"[SYNC] Failed to calculate performance score for {adw_id}: {e}")
            workflow_data["performance_score"] = 0.0

        try:
            workflow_data["quality_score"] = calculate_quality_score(workflow_data)
        except Exception as e:
            logger.warning(f"[SYNC] Failed to calculate quality score for {adw_id}: {e}")
            workflow_data["quality_score"] = 0.0

        # Anomaly Detection & Optimization Recommendations
        # Only generate insights for NEW workflows - skip for existing ones to prevent redundant updates
        should_generate_insights = not existing  # Only for new workflows

        if should_generate_insights:
            try:
                # Get all workflows for comparison (unpack tuple: workflows list and total count)
                all_workflows, _ = get_workflow_history()

                # Detect anomalies
                from core.workflow_analytics import (
                    detect_anomalies,
                    generate_optimization_recommendations,
                )
                anomalies = detect_anomalies(workflow_data, all_workflows)

                # Generate recommendations
                recommendations = generate_optimization_recommendations(workflow_data, anomalies)

                # Serialize to JSON for database storage
                import json
                workflow_data["anomaly_flags"] = json.dumps([a["message"] for a in anomalies])  # Simplified for UI
                workflow_data["optimization_recommendations"] = json.dumps(recommendations)

                logger.debug(f"[SYNC] Generated {len(anomalies)} anomalies and {len(recommendations)} recommendations for {adw_id}")
            except Exception as e:
                logger.warning(f"[SYNC] Failed to generate insights for {adw_id}: {e}")
                workflow_data["anomaly_flags"] = "[]"
                workflow_data["optimization_recommendations"] = "[]"

        if existing:
            # Update existing record if status or other fields changed
            updates = {}

            if existing["status"] != workflow_data["status"]:
                updates["status"] = workflow_data["status"]

            if workflow_data.get("current_phase") and existing["current_phase"] != workflow_data["current_phase"]:
                updates["current_phase"] = workflow_data["current_phase"]

            if duration_seconds and not existing["duration_seconds"]:
                updates["duration_seconds"] = duration_seconds

            # Update cost data with status-aware logic to prevent staleness
            # - Only update if cost has ACTUALLY CHANGED (prevent redundant writes)
            # - For running workflows, only update if cost increased (progressive tracking)
            # - Never allow cost decreases (prevents data corruption from out-of-order syncs)
            if workflow_data.get("cost_breakdown"):
                old_cost = existing.get("actual_cost_total", 0.0)
                new_cost = workflow_data.get("actual_cost_total", 0.0)
                status = workflow_data.get("status", "unknown")

                should_update = False
                update_reason = ""

                # For completed/failed workflows, only update if cost actually changed
                if status in ["completed", "failed"] and new_cost != old_cost:
                    should_update = True
                    update_reason = f"final cost changed for {status} workflow: ${old_cost:.4f} → ${new_cost:.4f}"
                # For running workflows, only update if cost increased
                elif status == "running" and new_cost > old_cost:
                    should_update = True
                    update_reason = f"progressive increase from ${old_cost:.4f} to ${new_cost:.4f}"
                # Skip if no change or decrease
                else:
                    update_reason = f"no change (${old_cost:.4f} = ${new_cost:.4f})" if new_cost == old_cost else "no update needed"

                if should_update:
                    updates["cost_breakdown"] = workflow_data["cost_breakdown"]
                    updates["actual_cost_total"] = new_cost
                    updates["input_tokens"] = workflow_data.get("input_tokens", 0)
                    updates["cached_tokens"] = workflow_data.get("cached_tokens", 0)
                    updates["cache_hit_tokens"] = workflow_data.get("cache_hit_tokens", 0)
                    updates["cache_miss_tokens"] = workflow_data.get("cache_miss_tokens", 0)
                    updates["output_tokens"] = workflow_data.get("output_tokens", 0)
                    updates["total_tokens"] = workflow_data.get("total_tokens", 0)
                    updates["cache_efficiency_percent"] = workflow_data.get("cache_efficiency_percent", 0.0)
                    logger.debug(f"[SYNC] Cost update for {adw_id} ({status}): ${old_cost:.4f} → ${new_cost:.4f} ({update_reason})")
                else:
                    logger.debug(f"[SYNC] Cost update skipped for {adw_id} ({status}): {update_reason}")

            # Update performance metrics if available and not already set
            if workflow_data.get("phase_durations") and not existing.get("phase_durations"):
                updates["phase_durations"] = workflow_data["phase_durations"]
                updates["bottleneck_phase"] = workflow_data.get("bottleneck_phase")
                updates["idle_time_seconds"] = workflow_data.get("idle_time_seconds")

            # Update error category if available and not already set
            if workflow_data.get("error_category") and not existing.get("error_category"):
                updates["error_category"] = workflow_data["error_category"]

            # Update complexity if available and not already set
            if workflow_data.get("complexity_actual") and not existing.get("complexity_actual"):
                updates["complexity_actual"] = workflow_data["complexity_actual"]

            # Anomaly Detection & Recommendations - Only update if we generated new insights
            # (We only generate insights for new workflows, so this block rarely runs)
            if should_generate_insights and "anomaly_flags" in workflow_data:
                try:
                    # workflow_data has JSON strings, existing has parsed Python objects
                    new_anomaly_flags = json.loads(workflow_data.get("anomaly_flags", "[]"))
                    old_anomaly_flags = existing.get("anomaly_flags", [])
                    if new_anomaly_flags != old_anomaly_flags:
                        updates["anomaly_flags"] = workflow_data["anomaly_flags"]
                except Exception:
                    # If comparison fails, skip update (don't cause unnecessary writes)
                    pass

            if should_generate_insights and "optimization_recommendations" in workflow_data:
                try:
                    new_recommendations = json.loads(workflow_data.get("optimization_recommendations", "[]"))
                    old_recommendations = existing.get("optimization_recommendations", [])
                    if new_recommendations != old_recommendations:
                        updates["optimization_recommendations"] = workflow_data["optimization_recommendations"]
                except Exception:
                    # If comparison fails, skip update (don't cause unnecessary writes)
                    pass

            if updates:
                update_workflow_history(adw_id, **updates)
                synced_count += 1
        else:
            # Insert new workflow
            insert_data = {
                **workflow_data,
                "created_at": workflow_data.get("start_time", datetime.now().isoformat()),
            }

            if duration_seconds:
                insert_data["duration_seconds"] = duration_seconds

            insert_workflow_history(**insert_data)
            synced_count += 1

    # Workflow Similarity Analysis - Skip to avoid redundant processing on every sync
    # Similarity detection is expensive and should only run:
    # 1. During initial backfill (one-time)
    # 2. When explicitly requested via API
    # 3. NOT on every routine sync
    # This phase is intentionally disabled for performance - re-enable only if needed
    logger.debug("[SYNC] Skipping similarity analysis (performance optimization)")

    # Pattern Learning - Skip to avoid redundant processing on every sync
    # Pattern detection is expensive and should only run:
    # 1. During initial backfill (one-time)
    # 2. When explicitly requested via API
    # 3. NOT on every routine sync
    # This phase is intentionally disabled for performance - re-enable only if needed
    logger.debug("[SYNC] Skipping pattern learning (performance optimization)")

    # Only log if we actually synced something
    if synced_count > 0:
        logger.info(f"[SYNC] Synchronized {synced_count} workflows")
    return synced_count


def resync_workflow_cost(adw_id: str, force: bool = False) -> dict:
    """
    Resync cost data for a single workflow from source files.

    Args:
        adw_id: ADW workflow identifier
        force: If True, clears existing cost data before resync

    Returns:
        Dict with keys:
            - success: bool - Whether resync succeeded
            - adw_id: str - The workflow ID
            - error: Optional[str] - Error message if failed
            - cost_updated: bool - Whether cost was actually updated
    """
    try:
        # Check if workflow exists
        existing = get_workflow_by_adw_id(adw_id)
        if not existing:
            return {
                "success": False,
                "adw_id": adw_id,
                "error": f"Workflow not found: {adw_id}",
                "cost_updated": False
            }

        # Read authoritative cost data from source files
        try:
            cost_data = read_cost_history(adw_id)
        except FileNotFoundError as e:
            return {
                "success": False,
                "adw_id": adw_id,
                "error": f"Cost files not found: {str(e)}",
                "cost_updated": False
            }
        except ValueError as e:
            return {
                "success": False,
                "adw_id": adw_id,
                "error": f"Invalid cost data: {str(e)}",
                "cost_updated": False
            }

        # Prepare cost update data
        updates = {}

        # If force mode, we'll update regardless of current values
        if force:
            logger.info(f"[RESYNC] Force resync for {adw_id} - clearing existing data")

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

        # Update the workflow
        if updates:
            success = update_workflow_history(adw_id, **updates)
            if success:
                logger.info(f"[RESYNC] Successfully resynced cost data for {adw_id}")
                return {
                    "success": True,
                    "adw_id": adw_id,
                    "error": None,
                    "cost_updated": True
                }
            else:
                return {
                    "success": False,
                    "adw_id": adw_id,
                    "error": "Failed to update database",
                    "cost_updated": False
                }
        else:
            return {
                "success": True,
                "adw_id": adw_id,
                "error": None,
                "cost_updated": False
            }

    except Exception as e:
        logger.error(f"[RESYNC] Error resyncing {adw_id}: {e}")
        return {
            "success": False,
            "adw_id": adw_id,
            "error": str(e),
            "cost_updated": False
        }


def resync_all_completed_workflows(force: bool = False) -> tuple[int, list[dict], list[str]]:
    """
    Resync cost data for all completed workflows.

    Args:
        force: If True, clears existing cost data before resync

    Returns:
        Tuple containing:
            - resynced_count: int - Number of workflows successfully resynced
            - workflows: List[Dict] - List of workflow summaries
            - errors: List[str] - List of error messages
    """
    try:
        # Get all completed workflows
        with get_db_connection(db_path=str(DB_PATH)) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT adw_id, status FROM workflow_history WHERE status IN ('completed', 'failed')"
            )
            rows = cursor.fetchall()

        workflows_to_resync = [dict(row) for row in rows]
        logger.info(f"[RESYNC] Found {len(workflows_to_resync)} completed/failed workflows to resync")

        resynced_count = 0
        workflows = []
        errors = []

        for workflow in workflows_to_resync:
            adw_id = workflow["adw_id"]
            result = resync_workflow_cost(adw_id, force=force)

            if result["success"]:
                if result["cost_updated"]:
                    resynced_count += 1
                workflows.append({
                    "adw_id": adw_id,
                    "status": workflow["status"],
                    "cost_updated": result["cost_updated"]
                })
            else:
                error_msg = f"{adw_id}: {result['error']}"
                errors.append(error_msg)
                logger.warning(f"[RESYNC] Failed to resync {adw_id}: {result['error']}")

        logger.info(f"[RESYNC] Completed bulk resync: {resynced_count} updated, {len(errors)} errors")
        return resynced_count, workflows, errors

    except Exception as e:
        logger.error(f"[RESYNC] Error in bulk resync: {e}")
        return 0, [], [f"Bulk resync failed: {str(e)}"]
