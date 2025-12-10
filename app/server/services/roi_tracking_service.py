#!/usr/bin/env python3
"""
ROI Tracking Service

Business logic for pattern execution ROI tracking and validation.

Responsibilities:
- Record pattern execution instances
- Calculate actual vs estimated savings
- Update aggregated ROI summaries
- Calculate effectiveness ratings
- Generate ROI reports for confidence updates
"""

import logging
from datetime import datetime

from core.models.workflow import (
    PatternExecution,
    PatternROISummary,
    ROIReport,
)
from database import get_database_adapter

logger = logging.getLogger(__name__)


class ROITrackingService:
    """Service for ROI tracking operations."""

    def __init__(self):
        """Initialize ROITrackingService with database adapter."""
        self.adapter = get_database_adapter()
        logger.info("[INIT] ROITrackingService initialized")

    def record_execution(self, execution: PatternExecution) -> int:
        """
        Record a pattern execution instance and trigger ROI summary update.

        Args:
            execution: PatternExecution instance with execution metrics

        Returns:
            ID of the created execution record
        """
        with self.adapter.get_connection() as conn:
            cursor = conn.cursor()

            # Insert execution record
            cursor.execute(
                """
                INSERT INTO pattern_executions (
                    pattern_id, workflow_id, execution_time_seconds,
                    estimated_time_seconds, actual_cost, estimated_cost,
                    success, error_message, executed_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
                """,
                (
                    execution.pattern_id,
                    execution.workflow_id,
                    execution.execution_time_seconds,
                    execution.estimated_time_seconds,
                    execution.actual_cost,
                    execution.estimated_cost,
                    execution.success,
                    execution.error_message,
                    execution.executed_at or datetime.utcnow().isoformat(),
                ),
            )

            execution_id = cursor.fetchone()['id']
            conn.commit()

            logger.info(
                f"[ROITrackingService] Recorded execution {execution_id} for pattern {execution.pattern_id}"
            )

            # Update ROI summary
            self.update_roi_summary(execution.pattern_id)

            return execution_id

    def update_roi_summary(self, pattern_id: str):
        """
        Recalculate and update ROI summary from all executions.

        Args:
            pattern_id: Pattern identifier to update
        """
        with self.adapter.get_connection() as conn:
            cursor = conn.cursor()

            # Aggregate execution metrics
            cursor.execute(
                """
                SELECT
                    COUNT(*) as total_executions,
                    SUM(CASE WHEN success THEN 1 ELSE 0 END) as successful_executions,
                    SUM(CASE WHEN success THEN (estimated_time_seconds - execution_time_seconds) ELSE 0 END) as total_time_saved,
                    SUM(CASE WHEN success THEN (estimated_cost - actual_cost) ELSE 0 END) as total_cost_saved,
                    SUM(CASE WHEN success THEN estimated_cost ELSE 0 END) as total_investment
                FROM pattern_executions
                WHERE pattern_id = %s
                """,
                (pattern_id,),
            )

            row = cursor.fetchone()
            total_executions = row['total_executions'] or 0
            successful_executions = row['successful_executions'] or 0
            total_time_saved = row['total_time_saved'] or 0.0
            total_cost_saved = row['total_cost_saved'] or 0.0
            total_investment = row['total_investment'] or 0.0

            # Calculate derived metrics
            success_rate = (
                successful_executions / total_executions if total_executions > 0 else 0.0
            )
            average_time_saved = (
                total_time_saved / successful_executions if successful_executions > 0 else 0.0
            )
            average_cost_saved = (
                total_cost_saved / successful_executions if successful_executions > 0 else 0.0
            )
            roi_percentage = (
                (total_cost_saved / total_investment * 100) if total_investment > 0 else 0.0
            )

            # Upsert ROI summary
            cursor.execute(
                """
                INSERT INTO pattern_roi_summary (
                    pattern_id, total_executions, successful_executions,
                    success_rate, total_time_saved_seconds, total_cost_saved_usd,
                    average_time_saved_seconds, average_cost_saved_usd,
                    roi_percentage, last_updated
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (pattern_id) DO UPDATE SET
                    total_executions = EXCLUDED.total_executions,
                    successful_executions = EXCLUDED.successful_executions,
                    success_rate = EXCLUDED.success_rate,
                    total_time_saved_seconds = EXCLUDED.total_time_saved_seconds,
                    total_cost_saved_usd = EXCLUDED.total_cost_saved_usd,
                    average_time_saved_seconds = EXCLUDED.average_time_saved_seconds,
                    average_cost_saved_usd = EXCLUDED.average_cost_saved_usd,
                    roi_percentage = EXCLUDED.roi_percentage,
                    last_updated = EXCLUDED.last_updated
                """,
                (
                    pattern_id,
                    total_executions,
                    successful_executions,
                    success_rate,
                    total_time_saved,
                    total_cost_saved,
                    average_time_saved,
                    average_cost_saved,
                    roi_percentage,
                    datetime.utcnow().isoformat(),
                ),
            )

            conn.commit()

            logger.info(
                f"[ROITrackingService] Updated ROI summary for pattern {pattern_id}: "
                f"{total_executions} executions, {success_rate*100:.1f}% success, "
                f"${total_cost_saved:.2f} saved, {roi_percentage:.1f}% ROI"
            )

    def get_pattern_roi(self, pattern_id: str) -> PatternROISummary | None:
        """
        Get ROI summary for a specific pattern.

        Args:
            pattern_id: Pattern identifier

        Returns:
            PatternROISummary or None if not found
        """
        with self.adapter.get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT * FROM pattern_roi_summary
                WHERE pattern_id = %s
                """,
                (pattern_id,),
            )

            row = cursor.fetchone()
            if not row:
                logger.warning(f"[ROITrackingService] No ROI data found for pattern {pattern_id}")
                return None

            return self._row_to_summary(row)

    def get_all_roi_summaries(self) -> list[PatternROISummary]:
        """
        Get ROI summaries for all patterns.

        Returns:
            List of PatternROISummary objects ordered by total cost saved (descending)
        """
        with self.adapter.get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT * FROM pattern_roi_summary
                ORDER BY total_cost_saved_usd DESC
                """
            )

            rows = cursor.fetchall()
            summaries = [self._row_to_summary(row) for row in rows]

            logger.info(f"[ROITrackingService] Retrieved {len(summaries)} ROI summaries")
            return summaries

    def calculate_effectiveness(self, pattern_id: str) -> str:
        """
        Calculate effectiveness rating based on success rate and ROI.

        Args:
            pattern_id: Pattern identifier

        Returns:
            Effectiveness rating: 'excellent', 'good', 'acceptable', 'poor', 'failed'
        """
        summary = self.get_pattern_roi(pattern_id)
        if not summary:
            return "unknown"

        # Effectiveness criteria
        if summary.success_rate >= 0.95 and summary.roi_percentage >= 200:
            return "excellent"
        elif summary.success_rate >= 0.85 and summary.roi_percentage >= 100:
            return "good"
        elif summary.success_rate >= 0.70 and summary.roi_percentage >= 50:
            return "acceptable"
        elif summary.success_rate < 0.70 or summary.roi_percentage < 0:
            return "poor"
        else:
            return "failed"

    def get_roi_report(self, pattern_id: str) -> ROIReport | None:
        """
        Generate comprehensive ROI report for a pattern.

        Args:
            pattern_id: Pattern identifier

        Returns:
            ROIReport with executions, summary, and recommendations
        """
        with self.adapter.get_connection() as conn:
            cursor = conn.cursor()

            # Get pattern details
            cursor.execute(
                """
                SELECT pattern_id, tool_sequence, created_at
                FROM pattern_approvals
                WHERE pattern_id = %s
                """,
                (pattern_id,),
            )

            pattern_row = cursor.fetchone()
            if not pattern_row:
                logger.warning(f"[ROITrackingService] Pattern {pattern_id} not found")
                return None

            # Get executions
            cursor.execute(
                """
                SELECT * FROM pattern_executions
                WHERE pattern_id = %s
                ORDER BY executed_at DESC
                LIMIT 100
                """,
                (pattern_id,),
            )

            execution_rows = cursor.fetchall()
            executions = [self._row_to_execution(row) for row in execution_rows]

            # Get ROI summary
            summary = self.get_pattern_roi(pattern_id)
            if not summary:
                logger.warning(f"[ROITrackingService] No ROI summary for pattern {pattern_id}")
                return None

            # Calculate effectiveness and recommendation
            effectiveness = self.calculate_effectiveness(pattern_id)
            recommendation = self._generate_recommendation(effectiveness, summary)

            report = ROIReport(
                pattern_id=pattern_id,
                pattern_name=pattern_row['tool_sequence'],
                approval_date=pattern_row['created_at'],
                executions=executions,
                summary=summary,
                effectiveness_rating=effectiveness,
                recommendation=recommendation,
            )

            logger.info(
                f"[ROITrackingService] Generated ROI report for pattern {pattern_id}: "
                f"{effectiveness} rating, {len(executions)} executions"
            )

            return report

    def get_top_performers(self, limit: int = 10) -> list[PatternROISummary]:
        """
        Get top performing patterns by ROI.

        Args:
            limit: Maximum number of patterns to return

        Returns:
            List of PatternROISummary objects ordered by ROI percentage (descending)
        """
        with self.adapter.get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT * FROM pattern_roi_summary
                WHERE total_executions >= 5
                ORDER BY roi_percentage DESC, success_rate DESC
                LIMIT %s
                """,
                (limit,),
            )

            rows = cursor.fetchall()
            performers = [self._row_to_summary(row) for row in rows]

            logger.info(f"[ROITrackingService] Retrieved {len(performers)} top performers")
            return performers

    def get_underperformers(self, limit: int = 10) -> list[PatternROISummary]:
        """
        Get underperforming patterns by success rate and ROI.

        Args:
            limit: Maximum number of patterns to return

        Returns:
            List of PatternROISummary objects ordered by performance (ascending)
        """
        with self.adapter.get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT * FROM pattern_roi_summary
                WHERE total_executions >= 3
                ORDER BY success_rate ASC, roi_percentage ASC
                LIMIT %s
                """,
                (limit,),
            )

            rows = cursor.fetchall()
            underperformers = [self._row_to_summary(row) for row in rows]

            logger.info(f"[ROITrackingService] Retrieved {len(underperformers)} underperformers")
            return underperformers

    def _row_to_execution(self, row) -> PatternExecution:
        """Convert database row to PatternExecution model."""
        return PatternExecution(
            id=row['id'],
            pattern_id=row['pattern_id'],
            workflow_id=row['workflow_id'],
            execution_time_seconds=row['execution_time_seconds'],
            estimated_time_seconds=row['estimated_time_seconds'],
            actual_cost=row['actual_cost'],
            estimated_cost=row['estimated_cost'],
            success=row['success'],
            error_message=row['error_message'],
            executed_at=row['executed_at'].isoformat() if row['executed_at'] else None,
        )

    def _row_to_summary(self, row) -> PatternROISummary:
        """Convert database row to PatternROISummary model."""
        return PatternROISummary(
            pattern_id=row['pattern_id'],
            total_executions=row['total_executions'],
            successful_executions=row['successful_executions'],
            success_rate=row['success_rate'],
            total_time_saved_seconds=row['total_time_saved_seconds'],
            total_cost_saved_usd=row['total_cost_saved_usd'],
            average_time_saved_seconds=row['average_time_saved_seconds'],
            average_cost_saved_usd=row['average_cost_saved_usd'],
            roi_percentage=row['roi_percentage'],
            last_updated=row['last_updated'].isoformat() if row['last_updated'] else None,
        )

    def _generate_recommendation(self, effectiveness: str, summary: PatternROISummary) -> str:
        """
        Generate actionable recommendation based on effectiveness.

        Args:
            effectiveness: Effectiveness rating
            summary: ROI summary with metrics

        Returns:
            Recommendation string
        """
        if effectiveness == "excellent":
            return (
                f"Exceptional performance! Pattern achieves {summary.success_rate*100:.1f}% success rate "
                f"and {summary.roi_percentage:.1f}% ROI. Consider applying similar automation patterns "
                f"to related workflows."
            )
        elif effectiveness == "good":
            return (
                f"Strong performance with {summary.success_rate*100:.1f}% success rate "
                f"and {summary.roi_percentage:.1f}% ROI. Monitor for continued effectiveness."
            )
        elif effectiveness == "acceptable":
            return (
                f"Acceptable performance ({summary.success_rate*100:.1f}% success, {summary.roi_percentage:.1f}% ROI). "
                f"Consider investigating failure cases to improve reliability."
            )
        elif effectiveness == "poor":
            return (
                f"Poor performance detected. Success rate: {summary.success_rate*100:.1f}%, "
                f"ROI: {summary.roi_percentage:.1f}%. Review pattern logic and consider refinements or revocation."
            )
        else:
            return (
                f"Pattern has failed to deliver value. Success rate: {summary.success_rate*100:.1f}%, "
                f"ROI: {summary.roi_percentage:.1f}%. Recommend immediate revocation and investigation."
            )
