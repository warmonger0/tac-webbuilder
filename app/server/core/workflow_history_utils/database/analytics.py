"""
Database analytics operations.

This module provides analytics and aggregate queries for the workflow history system.
"""

import logging

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
            - avg_cost_per_completion: Average cost per successfully completed workflow
            - cost_trend_7day: 7-day cost trend percentage (positive = increasing)
            - cost_trend_30day: 30-day cost trend percentage (positive = increasing)
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

        # Average cost per successful completion (only completed workflows)
        cursor.execute("""
            SELECT AVG(actual_cost_total) as avg_cost_per_completion
            FROM workflow_history
            WHERE status = 'completed'
              AND actual_cost_total IS NOT NULL
              AND actual_cost_total > 0
        """)
        completion_cost_row = cursor.fetchone()
        avg_cost_per_completion = (
            completion_cost_row["avg_cost_per_completion"]
            if completion_cost_row["avg_cost_per_completion"]
            else 0.0
        )

        # 7-day trend: Compare last 7 days vs previous 7 days
        cursor.execute("""
            SELECT AVG(actual_cost_total) as avg_cost
            FROM workflow_history
            WHERE status = 'completed'
              AND actual_cost_total IS NOT NULL
              AND actual_cost_total > 0
              AND datetime(created_at) >= datetime('now', '-7 days')
        """)
        cost_7day_current = cursor.fetchone()
        avg_cost_7day_current = (
            cost_7day_current["avg_cost"] if cost_7day_current["avg_cost"] else 0.0
        )

        cursor.execute("""
            SELECT AVG(actual_cost_total) as avg_cost
            FROM workflow_history
            WHERE status = 'completed'
              AND actual_cost_total IS NOT NULL
              AND actual_cost_total > 0
              AND datetime(created_at) >= datetime('now', '-14 days')
              AND datetime(created_at) < datetime('now', '-7 days')
        """)
        cost_7day_previous = cursor.fetchone()
        avg_cost_7day_previous = (
            cost_7day_previous["avg_cost"] if cost_7day_previous["avg_cost"] else 0.0
        )

        # Calculate 7-day trend percentage
        cost_trend_7day = 0.0
        if avg_cost_7day_previous > 0:
            cost_trend_7day = (
                (avg_cost_7day_current - avg_cost_7day_previous) / avg_cost_7day_previous * 100
            )

        # 30-day trend: Compare last 30 days vs previous 30 days
        cursor.execute("""
            SELECT AVG(actual_cost_total) as avg_cost
            FROM workflow_history
            WHERE status = 'completed'
              AND actual_cost_total IS NOT NULL
              AND actual_cost_total > 0
              AND datetime(created_at) >= datetime('now', '-30 days')
        """)
        cost_30day_current = cursor.fetchone()
        avg_cost_30day_current = (
            cost_30day_current["avg_cost"] if cost_30day_current["avg_cost"] else 0.0
        )

        cursor.execute("""
            SELECT AVG(actual_cost_total) as avg_cost
            FROM workflow_history
            WHERE status = 'completed'
              AND actual_cost_total IS NOT NULL
              AND actual_cost_total > 0
              AND datetime(created_at) >= datetime('now', '-60 days')
              AND datetime(created_at) < datetime('now', '-30 days')
        """)
        cost_30day_previous = cursor.fetchone()
        avg_cost_30day_previous = (
            cost_30day_previous["avg_cost"] if cost_30day_previous["avg_cost"] else 0.0
        )

        # Calculate 30-day trend percentage
        cost_trend_30day = 0.0
        if avg_cost_30day_previous > 0:
            cost_trend_30day = (
                (avg_cost_30day_current - avg_cost_30day_previous) / avg_cost_30day_previous * 100
            )

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
            "avg_cost_per_completion": avg_cost_per_completion,
            "cost_trend_7day": cost_trend_7day,
            "cost_trend_30day": cost_trend_30day,
            "avg_tokens": avg_tokens,
            "avg_cache_efficiency": avg_cache_efficiency,
        }

        logger.debug(f"[DB] Generated analytics: {analytics}")
        return analytics
