"""
Pattern learning statistics and observability endpoints.

Provides comprehensive pattern analytics for the pattern recognition system,
including distribution metrics, trend analysis, and automation status tracking.
"""

import logging
import traceback
from datetime import datetime, timedelta
from typing import Literal

from core.models.workflow import (
    PatternDistribution,
    PatternStatisticsItem,
    PatternStatisticsResponse,
    PatternStatisticsSummary,
    PatternTrend,
    PatternTrendDataPoint,
)
from fastapi import APIRouter
from utils.db_connection import get_connection

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/patterns", tags=["Pattern Learning"])


@router.get("/statistics", response_model=PatternStatisticsResponse)
async def get_pattern_statistics(
    limit: int = 20,
    offset: int = 0,
    sort_by: Literal["occurrence_count", "confidence_score", "potential_monthly_savings"] = "occurrence_count",
    filter_by_status: str | None = None,
    filter_by_type: str | None = None,
    trending_only: bool = False,
    trend_days: int = 30,
) -> PatternStatisticsResponse:
    """
    Get comprehensive pattern learning statistics.

    Query Parameters:
    - limit: Maximum number of patterns to return in top_patterns list (default 20)
    - offset: Number of patterns to skip for pagination (default 0)
    - sort_by: Sort patterns by occurrence_count, confidence_score, or potential_monthly_savings (default occurrence_count)
    - filter_by_status: Filter patterns by automation_status (detected, candidate, approved, implemented, active, deprecated)
    - filter_by_type: Filter patterns by pattern_type
    - trending_only: If true, only include patterns with increasing occurrence rates
    - trend_days: Number of days to include in trend analysis (default 30)

    Returns:
    - PatternStatisticsResponse with summary, distribution, top patterns, recent discoveries, and trend data
    """
    try:
        logger.info(f"[PATTERN_STATS] Fetching pattern statistics: limit={limit}, offset={offset}, sort_by={sort_by}, filter_by_status={filter_by_status}")

        with get_connection() as conn:
            cursor = conn.cursor()

            # Build WHERE clause for filters
            where_clauses = []
            params = []

            if filter_by_status:
                where_clauses.append("automation_status = ?")
                params.append(filter_by_status)

            if filter_by_type:
                where_clauses.append("pattern_type = ?")
                params.append(filter_by_type)

            where_sql = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""

            # ===== SUMMARY STATISTICS =====
            summary = PatternStatisticsSummary()

            # Total patterns
            cursor.execute(f"SELECT COUNT(*) FROM operation_patterns {where_sql}", params)
            summary.total_patterns = cursor.fetchone()[0]

            # Automated patterns (implemented or active)
            cursor.execute(
                f"SELECT COUNT(*) FROM operation_patterns {where_sql}{'AND' if where_sql else 'WHERE'} automation_status IN ('implemented', 'active')",
                params
            )
            summary.automated_patterns = cursor.fetchone()[0]

            # Average confidence score
            cursor.execute(f"SELECT AVG(confidence_score) FROM operation_patterns {where_sql}", params)
            result = cursor.fetchone()
            summary.avg_confidence_score = float(result[0]) if result[0] is not None else 0.0

            # Total potential savings
            cursor.execute(f"SELECT SUM(potential_monthly_savings) FROM operation_patterns {where_sql}", params)
            result = cursor.fetchone()
            summary.total_potential_monthly_savings = float(result[0]) if result[0] is not None else 0.0
            summary.total_potential_annual_savings = summary.total_potential_monthly_savings * 12

            # Automation rate
            if summary.total_patterns > 0:
                summary.automation_rate = (summary.automated_patterns / summary.total_patterns) * 100
            else:
                summary.automation_rate = 0.0

            # High confidence patterns (>= 75%)
            cursor.execute(
                f"SELECT COUNT(*) FROM operation_patterns {where_sql}{'AND' if where_sql else 'WHERE'} confidence_score >= 75.0",
                params
            )
            summary.high_confidence_patterns = cursor.fetchone()[0]

            # Recent discoveries (last 7 days)
            seven_days_ago = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d %H:%M:%S")
            cursor.execute(
                f"SELECT COUNT(*) FROM operation_patterns {where_sql}{'AND' if where_sql else 'WHERE'} first_detected >= ?",
                params + [seven_days_ago]
            )
            summary.recent_discoveries = cursor.fetchone()[0]

            # ===== DISTRIBUTION =====
            distribution = PatternDistribution()

            # By automation status
            cursor.execute(
                f"SELECT automation_status, COUNT(*) FROM operation_patterns {where_sql} GROUP BY automation_status",
                params
            )
            distribution.by_automation_status = {row[0]: row[1] for row in cursor.fetchall()}

            # By pattern type
            cursor.execute(
                f"SELECT pattern_type, COUNT(*) FROM operation_patterns {where_sql} GROUP BY pattern_type",
                params
            )
            distribution.by_pattern_type = {row[0]: row[1] for row in cursor.fetchall()}

            # By confidence range
            confidence_ranges = {
                "0-25%": (0.0, 25.0),
                "25-50%": (25.0, 50.0),
                "50-75%": (50.0, 75.0),
                "75-100%": (75.0, 100.0),
            }
            distribution.by_confidence_range = {}
            for range_name, (min_conf, max_conf) in confidence_ranges.items():
                cursor.execute(
                    f"SELECT COUNT(*) FROM operation_patterns {where_sql}{'AND' if where_sql else 'WHERE'} confidence_score >= ? AND confidence_score < ?",
                    params + [min_conf, max_conf]
                )
                distribution.by_confidence_range[range_name] = cursor.fetchone()[0]

            # ===== TOP PATTERNS =====
            # Build ORDER BY clause
            order_by_column = sort_by
            cursor.execute(
                f"""
                SELECT id, pattern_signature, pattern_type, automation_status, confidence_score,
                       occurrence_count, first_detected, last_seen, avg_tokens_with_llm,
                       avg_cost_with_llm, avg_tokens_with_tool, avg_cost_with_tool,
                       potential_monthly_savings, tool_name, typical_input_pattern,
                       typical_operations, typical_files_accessed
                FROM operation_patterns
                {where_sql}
                ORDER BY {order_by_column} DESC
                LIMIT ? OFFSET ?
                """,
                params + [limit, offset]
            )

            top_patterns = []
            for row in cursor.fetchall():
                top_patterns.append(PatternStatisticsItem(
                    id=row[0],
                    pattern_signature=row[1],
                    pattern_type=row[2],
                    automation_status=row[3],
                    confidence_score=float(row[4]),
                    occurrence_count=row[5],
                    first_detected=row[6],
                    last_seen=row[7],
                    avg_tokens_with_llm=row[8],
                    avg_cost_with_llm=float(row[9]) if row[9] is not None else 0.0,
                    avg_tokens_with_tool=row[10],
                    avg_cost_with_tool=float(row[11]) if row[11] is not None else 0.0,
                    potential_monthly_savings=float(row[12]) if row[12] is not None else 0.0,
                    tool_name=row[13],
                    typical_input_pattern=row[14],
                    typical_operations=row[15],
                    typical_files_accessed=row[16],
                ))

            # ===== RECENT DISCOVERIES =====
            thirty_days_ago = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d %H:%M:%S")
            cursor.execute(
                f"""
                SELECT id, pattern_signature, pattern_type, automation_status, confidence_score,
                       occurrence_count, first_detected, last_seen, avg_tokens_with_llm,
                       avg_cost_with_llm, avg_tokens_with_tool, avg_cost_with_tool,
                       potential_monthly_savings, tool_name, typical_input_pattern,
                       typical_operations, typical_files_accessed
                FROM operation_patterns
                {where_sql}{'AND' if where_sql else 'WHERE'} first_detected >= ?
                ORDER BY first_detected DESC
                LIMIT 10
                """,
                params + [thirty_days_ago]
            )

            recent_discoveries = []
            for row in cursor.fetchall():
                recent_discoveries.append(PatternStatisticsItem(
                    id=row[0],
                    pattern_signature=row[1],
                    pattern_type=row[2],
                    automation_status=row[3],
                    confidence_score=float(row[4]),
                    occurrence_count=row[5],
                    first_detected=row[6],
                    last_seen=row[7],
                    avg_tokens_with_llm=row[8],
                    avg_cost_with_llm=float(row[9]) if row[9] is not None else 0.0,
                    avg_tokens_with_tool=row[10],
                    avg_cost_with_tool=float(row[11]) if row[11] is not None else 0.0,
                    potential_monthly_savings=float(row[12]) if row[12] is not None else 0.0,
                    tool_name=row[13],
                    typical_input_pattern=row[14],
                    typical_operations=row[15],
                    typical_files_accessed=row[16],
                ))

            # ===== TRENDING PATTERNS =====
            # Patterns with increasing occurrence rates (detected in last 7 days)
            cursor.execute(
                f"""
                SELECT id, pattern_signature, pattern_type, automation_status, confidence_score,
                       occurrence_count, first_detected, last_seen, avg_tokens_with_llm,
                       avg_cost_with_llm, avg_tokens_with_tool, avg_cost_with_tool,
                       potential_monthly_savings, tool_name, typical_input_pattern,
                       typical_operations, typical_files_accessed
                FROM operation_patterns
                {where_sql}{'AND' if where_sql else 'WHERE'} last_seen >= ?
                ORDER BY occurrence_count DESC
                LIMIT 5
                """,
                params + [seven_days_ago]
            )

            trending_patterns = []
            for row in cursor.fetchall():
                trending_patterns.append(PatternStatisticsItem(
                    id=row[0],
                    pattern_signature=row[1],
                    pattern_type=row[2],
                    automation_status=row[3],
                    confidence_score=float(row[4]),
                    occurrence_count=row[5],
                    first_detected=row[6],
                    last_seen=row[7],
                    avg_tokens_with_llm=row[8],
                    avg_cost_with_llm=float(row[9]) if row[9] is not None else 0.0,
                    avg_tokens_with_tool=row[10],
                    avg_cost_with_tool=float(row[11]) if row[11] is not None else 0.0,
                    potential_monthly_savings=float(row[12]) if row[12] is not None else 0.0,
                    tool_name=row[13],
                    typical_input_pattern=row[14],
                    typical_operations=row[15],
                    typical_files_accessed=row[16],
                ))

            # ===== TREND DATA =====
            # Generate daily trend data for the requested period
            trend_start_date = datetime.now() - timedelta(days=trend_days)
            trend_data_points = []

            for day_offset in range(trend_days + 1):
                current_date = trend_start_date + timedelta(days=day_offset)
                date_str = current_date.strftime("%Y-%m-%d")
                date_end = current_date.strftime("%Y-%m-%d 23:59:59")

                # Patterns detected on this date
                cursor.execute(
                    "SELECT COUNT(*) FROM operation_patterns WHERE DATE(first_detected) = ?",
                    [date_str]
                )
                detected_count = cursor.fetchone()[0]

                # Cumulative automated patterns by this date
                cursor.execute(
                    """
                    SELECT COUNT(*) FROM operation_patterns
                    WHERE automation_status IN ('implemented', 'active')
                    AND first_detected <= ?
                    """,
                    [date_end]
                )
                automated_count = cursor.fetchone()[0]

                # Total patterns by this date
                cursor.execute(
                    "SELECT COUNT(*) FROM operation_patterns WHERE first_detected <= ?",
                    [date_end]
                )
                total_count = cursor.fetchone()[0]

                # Calculate automation rate
                automation_rate = (automated_count / total_count * 100) if total_count > 0 else 0.0

                trend_data_points.append(PatternTrendDataPoint(
                    date=date_str,
                    detected_count=detected_count,
                    automated_count=automated_count,
                    automation_rate=automation_rate
                ))

            trend = PatternTrend(
                trend_data=trend_data_points,
                period_days=trend_days
            )

            # ===== BUILD RESPONSE =====
            response = PatternStatisticsResponse(
                summary=summary,
                distribution=distribution,
                top_patterns=top_patterns,
                recent_discoveries=recent_discoveries,
                trending_patterns=trending_patterns,
                trend=trend,
                error=None
            )

            logger.info(f"[PATTERN_STATS] Successfully retrieved pattern statistics: {summary.total_patterns} patterns, {summary.automated_patterns} automated")
            return response

    except Exception as e:
        logger.error(f"[PATTERN_STATS] Failed to retrieve pattern statistics: {str(e)}")
        logger.error(f"[PATTERN_STATS] Full traceback:\n{traceback.format_exc()}")

        # Return error response with empty data
        return PatternStatisticsResponse(
            summary=PatternStatisticsSummary(),
            distribution=PatternDistribution(),
            top_patterns=[],
            recent_discoveries=[],
            trending_patterns=[],
            trend=PatternTrend(trend_data=[], period_days=trend_days),
            error=f"Failed to retrieve pattern statistics: {str(e)}"
        )
