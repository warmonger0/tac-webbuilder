"""
Workflow history synchronization and orchestration module.

This module handles the orchestration of workflow history synchronization:
- Scanning agents directory and updating database
- Resyncing cost data from authoritative sources
- Managing update logic for existing workflows
- Coordinating enrichment operations
"""

import json
import logging
from datetime import datetime

from utils.db_connection import get_connection as get_db_connection
from core.workflow_history_utils.database import (
    DB_PATH,
    insert_workflow_history,
    update_workflow_history,
    get_workflow_by_adw_id,
    get_workflow_history,
)
from core.workflow_history_utils.enrichment import enrich_workflow, enrich_cost_data_for_resync
from core.workflow_history_utils.filesystem import scan_agents_directory

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

        # Enrich workflow data with cost, GitHub state, scores, insights, etc.
        # Pass all_workflows only for new workflows (to generate insights)
        all_workflows = None
        if not existing:
            all_workflows, _ = get_workflow_history()

        duration_seconds = enrich_workflow(
            workflow_data=workflow_data,
            adw_id=adw_id,
            is_new=not existing,
            all_workflows=all_workflows
        )

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
            should_generate_insights = False  # Only for new workflows
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

        # If force mode, log that we're clearing existing data
        if force:
            logger.info(f"[RESYNC] Force resync for {adw_id} - clearing existing data")

        # Use enrichment module to extract cost information from source files
        # This will read authoritative cost data and return update dict
        try:
            updates = enrich_cost_data_for_resync(existing, adw_id)
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
