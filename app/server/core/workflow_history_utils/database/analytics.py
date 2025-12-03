"""
Database analytics operations.

This module provides analytics and aggregate queries for the workflow history system.
"""

import json
import logging
from datetime import datetime, timedelta

from .schema import _get_adapter

logger = logging.getLogger(__name__)


def get_history_analytics() -> dict:
    """
    Calculate analytics summary for all workflow history.

    Returns:
        Dict: Analytics including:
            - total_workflows: Total number of workflows
            - completed_workflows: Number of completed workflows
            - failed_workflows: Number of failed workflows
            - avg_duration_seconds: Average duration in seconds
            - success_rate_percent: Overall success rate (0-100)
            - workflows_by_model: Count by model type
            - workflows_by_template: Count by template type
            - workflows_by_status: Count by status
            - avg_cost: Average cost per workflow
            - total_cost: Total cost across all workflows
            - avg_tokens: Average tokens per workflow
            - avg_cache_efficiency: Average cache efficiency percentage
    """
    adapter = _get_adapter()
    with adapter.get_connection() as conn:
        cursor = conn.cursor()

        # Total workflows
        cursor.execute("SELECT COUNT(*) as total FROM workflow_history")
        total_workflows = cursor.fetchone()["total"]

        # Count by status
        cursor.execute("""
            SELECT status, COUNT(*) as count
            FROM workflow_history
            GROUP BY status
        """)
        status_counts = {row["status"]: row["count"] for row in cursor.fetchall()}

        completed_workflows = status_counts.get("completed", 0)
        failed_workflows = status_counts.get("failed", 0)

        # Calculate success rate
        success_rate = (
            (completed_workflows / total_workflows * 100)
            if total_workflows > 0
            else 0.0
        )

        # Average duration (only for completed workflows)
        cursor.execute("""
            SELECT AVG(duration_seconds) as avg_duration
            FROM workflow_history
            WHERE status = 'completed' AND duration_seconds IS NOT NULL
        """)
        avg_duration_row = cursor.fetchone()
        avg_duration = avg_duration_row["avg_duration"] if avg_duration_row["avg_duration"] else 0.0

        # Count by model
        cursor.execute("""
            SELECT model_used, COUNT(*) as count
            FROM workflow_history
            WHERE model_used IS NOT NULL
            GROUP BY model_used
        """)
        workflows_by_model = {row["model_used"]: row["count"] for row in cursor.fetchall()}

        # Count by template
        cursor.execute("""
            SELECT workflow_template, COUNT(*) as count
            FROM workflow_history
            WHERE workflow_template IS NOT NULL
            GROUP BY workflow_template
        """)
        workflows_by_template = {
            row["workflow_template"]: row["count"] for row in cursor.fetchall()
        }

        # Cost analytics
        cursor.execute("""
            SELECT
                AVG(actual_cost_total) as avg_cost,
                SUM(actual_cost_total) as total_cost
            FROM workflow_history
            WHERE actual_cost_total IS NOT NULL AND actual_cost_total > 0
        """)
        cost_row = cursor.fetchone()
        avg_cost = cost_row["avg_cost"] if cost_row["avg_cost"] else 0.0
        total_cost = cost_row["total_cost"] if cost_row["total_cost"] else 0.0

        # Token analytics
        cursor.execute("""
            SELECT
                AVG(total_tokens) as avg_tokens,
                AVG(cache_efficiency_percent) as avg_cache_efficiency
            FROM workflow_history
            WHERE total_tokens IS NOT NULL AND total_tokens > 0
        """)
        token_row = cursor.fetchone()
        avg_tokens = token_row["avg_tokens"] if token_row["avg_tokens"] else 0.0
        avg_cache_efficiency = token_row["avg_cache_efficiency"] if token_row["avg_cache_efficiency"] else 0.0

        # Calculate cost per successful completion metrics
        all_time_completion = get_cost_per_completion_metrics(days=None)
        seven_day_completion = get_cost_per_completion_metrics(days=7)
        seven_day_trend = get_cost_trend_comparison(current_days=7) if seven_day_completion["completion_count"] > 0 else None

        analytics = {
            "total_workflows": total_workflows,
            "completed_workflows": completed_workflows,
            "failed_workflows": failed_workflows,
            "avg_duration_seconds": avg_duration,
            "success_rate_percent": success_rate,
            "workflows_by_model": workflows_by_model,
            "workflows_by_template": workflows_by_template,
            "workflows_by_status": status_counts,
            "avg_cost": avg_cost,
            "total_cost": total_cost,
            "avg_tokens": avg_tokens,
            "avg_cache_efficiency": avg_cache_efficiency,
            # New cost per completion metrics
            "avg_cost_per_successful_completion": all_time_completion["avg_cost"],
            "cost_per_completion_7d": seven_day_completion["avg_cost"],
            "cost_trend_7d": seven_day_trend["percent_change"] if seven_day_trend else None,
        }

        logger.debug(f"[DB] Generated analytics: {analytics}")
        return analytics


def _calculate_time_window(days: int) -> tuple[str, str]:
    """
    Calculate ISO-formatted start and end dates for a time window.

    Args:
        days: Number of days to look back from now

    Returns:
        Tuple of (start_date, end_date) in ISO format
    """
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    return start_date.isoformat(), end_date.isoformat()


def get_cost_per_completion_metrics(days: int | None = None) -> dict:
    """
    Calculate average cost per successfully completed workflow.

    Only includes workflows with status='completed' and actual_cost_total > 0.

    Args:
        days: Optional number of days to look back (7, 30, or None for all-time)

    Returns:
        Dict with:
            - avg_cost: Average cost per successful completion
            - completion_count: Number of completed workflows
            - total_cost: Total cost of all completions
            - start_date: Start of time window (ISO format) or None
            - end_date: End of time window (ISO format) or None
    """
    adapter = _get_adapter()
    with adapter.get_connection() as conn:
        cursor = conn.cursor()

        # Build query with optional time filtering
        query = """
            SELECT
                AVG(actual_cost_total) as avg_cost,
                COUNT(*) as completion_count,
                SUM(actual_cost_total) as total_cost
            FROM workflow_history
            WHERE status = 'completed' AND actual_cost_total > 0
        """
        params = []

        start_date = None
        end_date = None
        if days is not None:
            start_date, end_date = _calculate_time_window(days)
            query += f" AND created_at >= {adapter.placeholder()}"
            params.append(start_date)

        logger.debug(f"[DB] Executing cost per completion query: days={days}, start_date={start_date}")
        cursor.execute(query, params)
        row = cursor.fetchone()

        avg_cost = row["avg_cost"] if row["avg_cost"] else 0.0
        completion_count = row["completion_count"] if row["completion_count"] else 0
        total_cost = row["total_cost"] if row["total_cost"] else 0.0

        result = {
            "avg_cost": avg_cost,
            "completion_count": completion_count,
            "total_cost": total_cost,
            "start_date": start_date,
            "end_date": end_date
        }

        logger.debug(f"[DB] Cost per completion metrics: {result}")
        return result


def get_cost_trend_comparison(current_days: int) -> dict:
    """
    Calculate cost trend comparison between current and previous periods.

    Args:
        current_days: Number of days for current period (7 or 30)

    Returns:
        Dict with:
            - current_period: Metrics for current period
            - previous_period: Metrics for previous period
            - percent_change: Percentage change ((current - previous) / previous * 100)
            - trend: 'up' if >1%, 'down' if <-1%, 'neutral' otherwise
    """
    # Get current period metrics
    current_period = get_cost_per_completion_metrics(days=current_days)

    # Calculate previous period dates (e.g., days 8-14 for 7-day comparison)
    adapter = _get_adapter()
    with adapter.get_connection() as conn:
        cursor = conn.cursor()

        end_date = datetime.now() - timedelta(days=current_days)
        start_date = end_date - timedelta(days=current_days)

        query = f"""
            SELECT
                AVG(actual_cost_total) as avg_cost,
                COUNT(*) as completion_count
            FROM workflow_history
            WHERE status = 'completed'
                AND actual_cost_total > 0
                AND created_at >= {adapter.placeholder()}
                AND created_at < {adapter.placeholder()}
        """

        logger.debug(f"[DB] Executing previous period query: {start_date.isoformat()} to {end_date.isoformat()}")
        cursor.execute(query, [start_date.isoformat(), end_date.isoformat()])
        row = cursor.fetchone()

        previous_avg_cost = row["avg_cost"] if row["avg_cost"] else 0.0
        previous_count = row["completion_count"] if row["completion_count"] else 0

        previous_period = {
            "avg_cost": previous_avg_cost,
            "completion_count": previous_count
        }

    # Calculate percentage change and trend direction
    current_avg = current_period["avg_cost"]
    previous_avg = previous_period["avg_cost"]

    if previous_avg > 0:
        percent_change = ((current_avg - previous_avg) / previous_avg) * 100
    else:
        percent_change = 0.0 if current_avg == 0 else 100.0

    # Determine trend direction (±1% threshold)
    if percent_change > 1.0:
        trend = "up"
    elif percent_change < -1.0:
        trend = "down"
    else:
        trend = "neutral"

    result = {
        "current_period": current_period,
        "previous_period": previous_period,
        "percent_change": percent_change,
        "trend": trend
    }

    logger.debug(f"[DB] Cost trend comparison: {result}")
    return result


def get_phase_cost_breakdown(days: int | None = None) -> list[dict]:
    """
    Aggregate costs by phase from cost_breakdown JSON field.

    Args:
        days: Optional number of days to look back (7, 30, or None for all-time)

    Returns:
        List of dicts sorted by cost descending:
            - phase: Phase name
            - total_cost: Total cost for this phase
            - workflow_count: Number of workflows with this phase
            - percent_of_total: Percentage of total cost
    """
    adapter = _get_adapter()
    with adapter.get_connection() as conn:
        cursor = conn.cursor()

        # Build query with optional time filtering
        query = """
            SELECT cost_breakdown, actual_cost_total
            FROM workflow_history
            WHERE status = 'completed'
                AND cost_breakdown IS NOT NULL
                AND actual_cost_total > 0
        """
        params = []

        if days is not None:
            start_date, _ = _calculate_time_window(days)
            query += f" AND created_at >= {adapter.placeholder()}"
            params.append(start_date)

        logger.debug(f"[DB] Executing phase cost breakdown query: days={days}")
        cursor.execute(query, params)
        rows = cursor.fetchall()

        # Aggregate costs by phase
        phase_costs = {}
        phase_workflow_counts = {}
        total_cost = 0.0

        for row in rows:
            cost_breakdown_str = row["cost_breakdown"]
            workflow_cost = row["actual_cost_total"]

            # Parse cost_breakdown JSON
            try:
                if isinstance(cost_breakdown_str, str):
                    cost_breakdown = json.loads(cost_breakdown_str)
                else:
                    cost_breakdown = cost_breakdown_str

                # Extract by_phase if it exists
                by_phase = cost_breakdown.get("by_phase", {})

                for phase, cost in by_phase.items():
                    if phase not in phase_costs:
                        phase_costs[phase] = 0.0
                        phase_workflow_counts[phase] = 0

                    phase_costs[phase] += cost
                    phase_workflow_counts[phase] += 1
                    total_cost += cost

            except (json.JSONDecodeError, TypeError, AttributeError) as e:
                logger.warning(f"[DB] Failed to parse cost_breakdown: {e}")
                continue

        # Build result list
        result = []
        for phase in sorted(phase_costs.keys(), key=lambda p: phase_costs[p], reverse=True):
            percent_of_total = (phase_costs[phase] / total_cost * 100) if total_cost > 0 else 0.0
            result.append({
                "phase": phase,
                "total_cost": phase_costs[phase],
                "workflow_count": phase_workflow_counts[phase],
                "percent_of_total": percent_of_total
            })

        logger.debug(f"[DB] Phase cost breakdown: {len(result)} phases, total_cost={total_cost}")
        return result
